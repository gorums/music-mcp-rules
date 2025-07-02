#!/usr/bin/env python3
"""
Music Collection MCP Server - Save Band Analyze Tool

This module contains the save_band_analyze_tool implementation.
"""

from datetime import datetime, timezone
from typing import Any, Dict

from ..mcp_instance import mcp
from ..base_handlers import BaseToolHandler

# Import tool implementation - using absolute imports
from src.core.tools.storage import save_band_analyze, load_collection_index, update_collection_index, load_band_metadata
from src.models.band import BandAnalysis, AlbumAnalysis


class SaveBandAnalyzeHandler(BaseToolHandler):
    """Handler for the save_band_analyze tool."""
    
    def __init__(self):
        super().__init__("save_band_analyze", "1.0.0")
    
    def _execute_tool(self, **kwargs) -> Dict[str, Any]:
        """Execute the band analysis saving logic."""
        band_name = kwargs.get('band_name')
        analysis = kwargs.get('analysis')
        
        # Initialize response structure
        response = {
            'status': 'success',
            'message': '',
            'validation_results': {
                'schema_valid': False,
                'validation_errors': [],
                'overall_rating': 0,
                'albums_analyzed': 0,
                'similar_bands_count': 0,
                'similar_bands_in_collection': 0,
                'similar_bands_missing': 0,
                'rating_distribution': {},
                'fields_validated': []
            },
            'analysis_summary': {},
            'collection_sync': {
                'band_entry_found': False,
                'index_updated': False,
                'index_errors': []
            },
            'file_operations': {
                'metadata_file': '',
                'backup_created': False,
                'last_updated': '',
                'merged_with_existing': False
            }
        }
        
        # Parameter validation - return message field for errors
        if not band_name or not isinstance(band_name, str) or band_name.strip() == "":
            response['status'] = 'error'
            response['message'] = 'Invalid band_name parameter: must be a non-empty string'
            return response
            
        if not analysis or not isinstance(analysis, dict):
            response['status'] = 'error'
            response['message'] = 'Invalid analysis parameter: must be a dictionary'
            return response
        
        band_name = band_name.strip()
        
        # Validation errors collection
        validation_errors = []
        
        # Validate required fields
        if "review" not in analysis:
            validation_errors.append("Missing required field: 'review'")
        elif not isinstance(analysis["review"], str):
            validation_errors.append("Field 'review' must be a string")
            
        if "rate" not in analysis:
            validation_errors.append("Missing required field: 'rate'")
        elif not isinstance(analysis["rate"], int):
            validation_errors.append("Field 'rate' must be an integer")
        elif analysis["rate"] < 1 or analysis["rate"] > 10:
            validation_errors.append("Field 'rate' must be between 1-10")
        
        # Validate albums field (optional)
        albums_analysis = []
        if "albums" in analysis:
            if not isinstance(analysis["albums"], list):
                validation_errors.append("Field 'albums' must be a list")
            else:
                for i, album_data in enumerate(analysis["albums"]):
                    if not isinstance(album_data, dict):
                        validation_errors.append(f"Album {i}: must be a dictionary")
                        continue
                        
                    album_errors = []
                    # album_name is required
                    if "album_name" not in album_data:
                        album_errors.append("'album_name' is required")
                    elif not isinstance(album_data["album_name"], str):
                        album_errors.append("'album_name' must be a string")
                        
                    if "review" in album_data and not isinstance(album_data["review"], str):
                        album_errors.append("'review' must be a string")
                        
                    if "rate" in album_data:
                        if not isinstance(album_data["rate"], int):
                            album_errors.append("'rate' must be an integer")
                        elif album_data["rate"] < 0 or album_data["rate"] > 10:
                            album_errors.append("'rate' must be between 0-10")
                    
                    if album_errors:
                        # Format error messages to match test expectations
                        for err in album_errors:
                            if "'album_name' is required" in err:
                                validation_errors.append(f"Missing 'album_name' in album {i+1}")
                            else:
                                validation_errors.append(f"Album {i+1} ({album_data.get('album_name', 'unnamed')}): {err}")
                    else:
                        try:
                            album_analysis = AlbumAnalysis(
                                album_name=album_data["album_name"],
                                review=album_data.get("review", ""),
                                rate=album_data.get("rate", 0)
                            )
                            albums_analysis.append(album_analysis)
                        except Exception as e:
                            validation_errors.append(f"Album {i}: validation failed - {str(e)}")
        
        # Check optional similar_bands and similar_bands_missing fields
        similar_bands = []
        similar_bands_missing = []
        if "similar_bands" in analysis:
            if not isinstance(analysis["similar_bands"], list):
                validation_errors.append("Field 'similar_bands' must be a list")
            else:
                similar_bands = [b for b in analysis["similar_bands"] if isinstance(b, str)]
        if "similar_bands_missing" in analysis:
            if not isinstance(analysis["similar_bands_missing"], list):
                validation_errors.append("Field 'similar_bands_missing' must be a list")
            else:
                similar_bands_missing = [b for b in analysis["similar_bands_missing"] if isinstance(b, str)]

        # If only similar_bands is provided, split into present/missing using collection index
        if similar_bands and not similar_bands_missing:
            collection_index = load_collection_index()
            collection_band_names = set()
            if collection_index:
                collection_band_names = {b.name.lower() for b in collection_index.bands}
            in_collection = []
            missing = []
            for band in similar_bands:
                if band.lower() in collection_band_names:
                    in_collection.append(band)
                else:
                    missing.append(band)
            similar_bands = in_collection
            similar_bands_missing = missing

        # Validate no duplicates between arrays
        if set(b.lower() for b in similar_bands).intersection(b.lower() for b in similar_bands_missing):
            validation_errors.append("A band cannot appear in both similar_bands and similar_bands_missing.")

        # If validation errors, return early
        if validation_errors:
            response["status"] = "error"
            response["message"] = f"Analysis validation failed: {len(validation_errors)} errors found"
            response["validation_results"]["validation_errors"] = validation_errors
            return response
        
        # Create BandAnalysis object
        try:
            band_analysis = BandAnalysis(
                review=analysis["review"],
                rate=analysis["rate"],
                albums=albums_analysis,
                similar_bands=similar_bands,
                similar_bands_missing=similar_bands_missing
            )
            response["validation_results"]["schema_valid"] = True
            response["validation_results"]["fields_validated"] = list(analysis.keys())
        except Exception as e:
            response["status"] = "error"
            response["message"] = f"Failed to create BandAnalysis object: {str(e)}"
            response["validation_results"]["validation_errors"].append(f"Schema validation failed: {str(e)}")
            return response
        
        # Call storage function
        try:
            storage_result = save_band_analyze(band_name, band_analysis)
            
            # Update response with storage results
            response["message"] = storage_result.get("message", f"Analysis saved for {band_name}")
            response["file_operations"]["metadata_file"] = storage_result.get("file_path", "")
            response["file_operations"]["backup_created"] = True  # Storage always creates backups
            response["file_operations"]["last_updated"] = storage_result.get("last_updated", "")
            response["file_operations"]["merged_with_existing"] = True  # Analysis is merged with existing metadata
            
            # Include information about excluded albums
            albums_excluded = storage_result.get("albums_excluded", 0)
            albums_analyzed_final = storage_result.get("albums_analyzed", len(band_analysis.albums))
            
        except Exception as e:
            response["status"] = "error"
            response["message"] = f"Failed to save analysis: {str(e)}"
            return response
        
        # Update collection index
        try:
            index = load_collection_index()
            if index:
                # Find and update band entry if it exists
                for band_entry in index.bands:
                    if band_entry.name == band_name:
                        # Load current metadata to get accurate album counts
                        current_metadata = load_band_metadata(band_name)
                        if current_metadata:
                            # Calculate proper album counts from metadata using new separated schema
                            total_albums = current_metadata.albums_count  # Total albums (local + missing)
                            local_albums = current_metadata.local_albums_count  # Local albums only
                            missing_albums = current_metadata.missing_albums_count  # Missing albums only
                            
                            # Update band entry with accurate data
                            band_entry.albums_count = total_albums
                            band_entry.local_albums_count = local_albums
                            band_entry.missing_albums_count = missing_albums
                            band_entry.has_analysis = True
                            band_entry.last_updated = current_metadata.last_updated
                        else:
                            # If no metadata, just mark as having analysis
                            band_entry.has_analysis = True
                        
                        response["collection_sync"]["band_entry_found"] = True
                        break
                
                # Save updated index
                update_result = update_collection_index(index)
                response["collection_sync"]["index_updated"] = update_result.get("status") == "success"
                if update_result.get("status") != "success":
                    response["collection_sync"]["index_errors"].append(update_result.get("error", "Unknown index update error"))
            else:
                response["collection_sync"]["index_errors"].append("Collection index not found")
                
        except Exception as e:
            response["collection_sync"]["index_errors"].append(f"Index update failed: {str(e)}")
        
        # Build validation results summary (use original input for validation stats)
        response["validation_results"]["overall_rating"] = band_analysis.rate
        response["validation_results"]["albums_analyzed"] = len(band_analysis.albums)
        response["validation_results"]["similar_bands_count"] = band_analysis.total_similar_bands_count  # Total count (in collection + missing)
        response["validation_results"]["similar_bands_in_collection"] = len(band_analysis.similar_bands)
        response["validation_results"]["similar_bands_missing"] = len(band_analysis.similar_bands_missing)
        
        # Calculate rating distribution
        rating_counts = {}
        if band_analysis.rate > 0:
            rating_counts[f"overall"] = band_analysis.rate
        for album in band_analysis.albums:
            if album.rate > 0:
                rating_key = f"album_rate_{album.rate}"
                rating_counts[rating_key] = rating_counts.get(rating_key, 0) + 1
        response["validation_results"]["rating_distribution"] = rating_counts
        
        # Build analysis summary (use actual saved data)
        albums_with_ratings = len([a for a in band_analysis.albums if a.rate > 0])
        album_ratings = [a.rate for a in band_analysis.albums if a.rate > 0]
        
        response["analysis_summary"] = {
            "band_name": band_name,
            "overall_rating": band_analysis.rate,
            "albums_analyzed": albums_analyzed_final,      # Actually saved count
            "albums_analyzed_input": len(band_analysis.albums),  # Original input count
            "albums_analyzed_saved": albums_analyzed_final,      # Actually saved count (duplicate for compatibility)
            "albums_excluded": albums_excluded,                  # Excluded missing albums
            "albums_with_ratings": albums_with_ratings,
            "similar_bands_count": band_analysis.total_similar_bands_count,  # Total count (in collection + missing)
            "similar_bands_in_collection": len(band_analysis.similar_bands),
            "similar_bands_missing": len(band_analysis.similar_bands_missing),
            "has_review": len(band_analysis.review.strip()) > 0,
            "average_album_rating": round(sum(album_ratings) / len(album_ratings), 1) if album_ratings else 0.0,
            "rating_range": {
                "min": min(album_ratings) if album_ratings else 0,
                "max": max(album_ratings) if album_ratings else 0
            }
        }
        
        # Final success message with filtering information
        if albums_excluded > 0:
            response["message"] += f" ({albums_excluded} missing albums excluded from analysis)"
        
        # Add tool info for compatibility
        response['tool_info'] = {
            'tool_name': 'save_band_analyze',
            'version': self.version,
            'execution_time': datetime.now(timezone.utc).isoformat(),
            'parameters_used': {'band_name': band_name, 'analysis_fields': list(analysis.keys())}
        }
        
        return response


# Create handler instance
_handler = SaveBandAnalyzeHandler()

@mcp.tool()
def save_band_analyze_tool(
    band_name: str,    
    analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Save band analysis data including reviews, ratings, and similar bands.
    
    This tool stores comprehensive analysis data for a band:
    - Overall band review and rating
    - Album-specific reviews and ratings (1-10 scale)
    - Similar bands information
    - Always includes analysis for all albums (both local and missing)
    - Merges with existing metadata preserving structure
    - Validates analyze section structure
    - Updates collection statistics
    
    Args:
        band_name: The name of the band        
        analysis: Analysis data dictionary containing review, rating, albums analysis, and similar bands 
        
    Returns:
        Dict containing comprehensive operation status with validation results, 
        file operations, collection sync, and analysis summary
    
    ANALYSIS SCHEMA:
    ================
    The analysis parameter must be a dictionary with the following structure:
    
    REQUIRED FIELDS:
    ================
    - review (string): Overall band review text
    - rate (integer): Overall band rating from 1-10 (0 = unrated)
    
    OPTIONAL FIELDS FOR EACH ALBUM:
    ================
    - albums (array): Per-album analysis objects with:
        - album_name (string, REQUIRED): Name of the album (used for filtering missing albums)
        - review (string): Album review text
        - rate (integer): Album rating 1-10 (0 = unrated)
    - similar_bands (array of strings): Names of similar/related bands
    
    MISSING ALBUMS FILTERING:
    =========================
    - Analysis is always saved for all albums, including both local and missing albums
    
    RATING VALIDATION:
    ==================
    - All ratings must be integers between 0-10
    - 0 means unrated/no rating given
    - 1-10 represents actual ratings (1=lowest, 10=highest)
    
    EXAMPLE ANALYSIS:
    =================
    {
        "review": "Legendary progressive rock band known for conceptual albums...",
        "rate": 9,
        "albums": [
            {
                "album_name": "The Dark Side of the Moon",  // REQUIRED
                "review": "Masterpiece of progressive rock with innovative sound design...",
                "rate": 10
            },
            {
                "album_name": "The Wall",  // REQUIRED
                "review": "Epic rock opera exploring themes of isolation...",
                "rate": 9
            }
        ],
        "similar_bands": ["King Crimson", "Genesis", "Yes", "Led Zeppelin"]
    }
    """
    return _handler.execute(band_name=band_name, analysis=analysis) 