#!/usr/bin/env python3
"""
Music Collection MCP Server

A Model Context Protocol server that provides intelligent access to your local music collection.
The server exposes tools, resources, and prompts to discover, analyze, and retrieve information
about bands and artists based on your folder structure.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

# Import tool implementations - using absolute imports
from tools.scanner import scan_music_folders as scanner_scan_music_folders
from tools.storage import get_band_list, save_band_metadata, save_band_analyze, save_collection_insight

# Import resource implementations - using absolute imports
from resources.band_info import get_band_info_markdown
from resources.collection_summary import get_collection_summary

# Import prompt implementations - using absolute imports
from prompts.fetch_band_info import get_fetch_band_info_prompt
from prompts.analyze_band import get_analyze_band_prompt
from prompts.compare_bands import get_compare_bands_prompt
from prompts.collection_insights import get_collection_insights_prompt

# Configure logging
logger = logging.getLogger(__name__)

# Create FastMCP server instance with ERROR log level to fix MCP client visibility
mcp = FastMCP("music-collection-mcp")

@mcp.tool()
def scan_music_folders() -> Dict[str, Any]:
    """
    Scan the music directory structure to discover bands and albums, detecting all changes.
    
    This tool performs a comprehensive scan of the music collection:
    - Detects new bands that have been added to the collection
    - Identifies bands that have been removed from the collection  
    - Discovers changes in album structure (new albums, removed albums, renamed albums)
    - Updates collection index with all detected changes
    - Preserves existing metadata and analysis data during scanning
    - Optimized for performance while ensuring complete change detection
    
    Returns:
        Dict containing scan results including:
        - status: 'success' or 'error'
        - results: Dict with scan statistics and detailed change information
        - collection_path: Path to the scanned music collection
        - changes_made: True if any changes were detected and saved
        - bands_added: Number of new bands discovered
        - bands_removed: Number of bands no longer found
        - albums_changed: Number of bands with album structure changes
    """
    try:
        # Call the scanner to perform comprehensive change detection
        # Reason: Always perform full scan to detect all types of changes
        result = scanner_scan_music_folders()
            
        # Add tool-specific metadata
        if result.get('status') == 'success':
            result['tool_info'] = {
                'tool_name': 'scan_music_folders',
                'version': '3.0.0',  # Updated version for always-scan behavior
                'scan_mode': 'comprehensive_change_detection',
                'change_detection': 'enabled'
            }
            
        return result
        
    except Exception as e:
        logger.error(f"Error in scan_music_folders tool: {str(e)}")
        return {
            'status': 'error',
            'error': f"Tool execution failed: {str(e)}",
            'tool_info': {
                'tool_name': 'scan_music_folders',
                'version': '3.0.0'
            }
        }

@mcp.tool()
def get_band_list_tool(
    search_query: Optional[str] = None,
    filter_genre: Optional[str] = None,
    filter_has_metadata: Optional[bool] = None,
    filter_missing_albums: Optional[bool] = None,
    sort_by: str = "name",
    sort_order: str = "asc", 
    page: int = 1,
    page_size: int = 50,
    include_albums: bool = False
) -> Dict[str, Any]:
    """
    Get a list of all discovered bands with enhanced filtering, sorting, and pagination.
    
    This tool provides comprehensive band listing functionality:
    - Search bands by name or album names
    - Filter by genre, metadata availability, or missing albums
    - Sort by name, album count, last update, or completion percentage
    - Paginate results for large collections
    - Include detailed album information and analysis data
    - Show cached metadata status and last updated info
    
    Args:
        search_query: Search term to filter bands by name or album name
        filter_genre: Filter bands by genre (requires metadata to be available)
        filter_has_metadata: If True, show only bands with metadata; if False, only without
        filter_missing_albums: If True, show only bands with missing albums; if False, only complete bands
        sort_by: Field to sort by - 'name', 'albums_count', 'last_updated', or 'completion'
        sort_order: Sort order - 'asc' for ascending or 'desc' for descending
        page: Page number for pagination (starts at 1)
        page_size: Number of results per page (1-100)
        include_albums: If True, include detailed album information for each band
    
    Returns:
        Dict containing filtered and paginated band list with metadata including:
        - status: 'success' or 'error'
        - bands: List of band information with albums and analysis if requested
        - pagination: Page information with total counts and navigation info
        - collection_summary: Overall collection statistics
        - filters_applied: Summary of filters that were applied
        - sort: Information about the applied sorting
    """
    try:
        result = get_band_list(
            search_query=search_query,
            filter_genre=filter_genre,
            filter_has_metadata=filter_has_metadata,
            filter_missing_albums=filter_missing_albums,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size,
            include_albums=include_albums
        )
        
        # Add tool-specific metadata
        if result.get('status') == 'success':
            result['tool_info'] = {
                'tool_name': 'get_band_list',
                'version': '1.0.0',
                'parameters_used': {
                    'search_query': search_query,
                    'filter_genre': filter_genre,
                    'filter_has_metadata': filter_has_metadata,
                    'filter_missing_albums': filter_missing_albums,
                    'sort_by': sort_by,
                    'sort_order': sort_order,
                    'page': page,
                    'page_size': page_size,
                    'include_albums': include_albums
                }
            }
            
        return result
        
    except Exception as e:
        logger.error(f"Error in get_band_list tool: {str(e)}")
        return {
            'status': 'error',
            'error': f"Tool execution failed: {str(e)}",
            'tool_info': {
                'tool_name': 'get_band_list',
                'version': '1.0.0'
            }
        }

@mcp.tool()
def save_band_metadata_tool(
    band_name: str,
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Save band metadata to the local storage. Chek very careful how is the metadata passed to the tool, check the examples too.
    Ignore ANALYSIS SCHEMA for this tool
    
    Args:
        band_name: The name of the band
        metadata: Complete metadata dictionary for the band
        
    Returns:
        Dict containing the operation status
    
    METADATA SCHEMA:
    The metadata parameter must be a dictionary with the following structure:
    
    REQUIRED FIELDS:
    ================
    - formed (string): Formation year in "YYYY" format
    - genres (array of strings): List of music genres
    - origin (string): Country/city of origin
    - members (array of strings): List of all band member names
    - description (string): Band biography or description
    - albums (array): List of album objects (see Album Schema below)
        
    ALBUM SCHEMA (for each item in albums array):
    =============================================
    REQUIRED:
    - album_name (string): Name of the album
    - year (string): Release year in "YYYY" format  
    - tracks_count (integer): Number of tracks (must be >= 0)
    - missing (boolean): true if album not found in local folders, false if present
    
    OPTIONAL:
    - duration (string): Album length (format: "43min", "1h 23min", etc.)
    - genres (array of strings): Album-specific genres (can differ from band genres)
        
    COMPLETE EXAMPLE of METADATA JSON:
    =============================
    {
        "formed": "1965", 
        "genres": ["Progressive Rock", "Psychedelic Rock", "Art Rock"],
        "origin": "London, England",
        "members": ["David Gilmour", "Roger Waters", "Nick Mason", "Richard Wright", "Syd Barrett"],
        "description": "English rock band formed in London in 1965. Achieved international acclaim with their progressive and psychedelic music.",
        "albums": [
            {
                "album_name": "The Dark Side of the Moon",
                "year": "1973",
                "tracks_count": 10,
                "missing": false,
                "duration": "43min",
                "genres": ["Progressive Rock", "Art Rock"]
            },
            {
                "album_name": "The Wall", 
                "year": "1979",
                "tracks_count": 26,
                "missing": false,
                "duration": "81min",
                "genres": ["Progressive Rock", "Rock Opera"]
            },
            {
                "album_name": "Wish You Were Here",
                "year": "1975", 
                "tracks_count": 5,
                "missing": true,
                "duration": "44min"
            }
        ]
    }

    COMMON MISTAKES TO AVOID:
    ========================
    ❌ Using "formed_year" (should be "formed")
    ❌ Using integer for formed year (should be string "1965")
    ❌ Using nested member structure like {"current": [...], "former": [...]} (should be flat array)
    ❌ Using "notable_albums" or "discography" (should be "albums")
    ❌ Missing required album fields (album_name, year, tracks_count, missing)
    ❌ Using integer for album year (should be string "1973")
    ❌ Negative tracks_count (must be >= 0)
    ❌ Rating outside 1-10 range
    
    VALIDATION NOTES:
    ================
    - All year fields must be 4-digit strings (e.g., "1975", not 1975)
    - Albums array can be empty but must be present
    - Members array should include all members (past and present) as flat list
    - Duration format is flexible but should include time unit (min, h, etc.)
    - Genres should be specific and accurate music genres
    
    DATA PRESERVATION:
    ==================
    - Existing analyze data is always preserved when updating metadata
    - Existing folder_structure data is always preserved when updating metadata
    - Use save_band_analyze_tool to add or update analysis data specifically
    """
    try:
        # Import required models and functions
        from models.band import BandMetadata
        from tools.storage import update_collection_index, load_collection_index
        from models.collection import BandIndexEntry
        
        # Step 1: Data validation against enhanced schema
        validation_results = {
            "schema_valid": False,
            "validation_errors": [],
            "fields_validated": [],
            "albums_count": 0,
            "missing_albums_count": 0
        }
        
        try:
            # Ensure band_name is set correctly in metadata
            metadata['band_name'] = band_name
            
            # Handle schema conversion from old format to new separated albums format
            if 'albums' in metadata and metadata['albums'] and any('missing' in album for album in metadata['albums']):
                # Old format: albums array with missing field - convert to separated arrays
                local_albums = []
                missing_albums = []
                
                for album in metadata['albums']:
                    # Remove the missing field from the album data as it's no longer part of Album model
                    album_copy = dict(album)
                    is_missing = album_copy.pop('missing', False)  # Remove and get missing status
                    
                    if is_missing:
                        missing_albums.append(album_copy)
                    else:
                        local_albums.append(album_copy)
                
                # Update metadata with separated arrays
                metadata['albums'] = local_albums
                metadata['albums_missing'] = missing_albums
            else:
                # New format: already has separated arrays or no albums - ensure both arrays exist
                metadata['albums'] = metadata.get('albums', [])
                metadata['albums_missing'] = metadata.get('albums_missing', [])
            
            # Create BandMetadata object for validation
            band_metadata = BandMetadata(**metadata)
            
            # Update the metadata saved timestamp before saving
            # Reason: Track when metadata was saved via this tool for has_metadata determination
            band_metadata.update_metadata_saved_timestamp()
            
            validation_results["schema_valid"] = True
            validation_results["fields_validated"] = list(metadata.keys())
            validation_results["albums_count"] = len(band_metadata.albums) + len(band_metadata.albums_missing)
            validation_results["missing_albums_count"] = len(band_metadata.albums_missing)
            
        except Exception as e:
            validation_results["validation_errors"].append(f"Schema validation failed: {str(e)}")
            return {
                'status': 'error',
                'error': f"Metadata validation failed: {str(e)}",
                'validation_results': validation_results,
                'tool_info': {
                    'tool_name': 'save_band_metadata',
                    'version': '1.1.0'
                }
            }
        
        # Step 2: Save metadata with backup mechanism (handled by storage layer)
        # Reason: Always preserve existing analyze and folder_structure data
        storage_result = save_band_metadata(band_name, band_metadata)
        
        # Step 3: Sync with collection index
        collection_sync_results = {
            "index_updated": False,
            "index_errors": [],
            "band_entry_created": False
        }
        
        try:
            # Load existing collection index or create new
            collection_index = load_collection_index()
            if collection_index is None:
                from models.collection import CollectionIndex
                collection_index = CollectionIndex()
            
            # Create or update band entry
            local_albums_count = len(band_metadata.albums)
            missing_albums_count = len(band_metadata.albums_missing)
            total_albums_count = local_albums_count + missing_albums_count
            
            band_entry = BandIndexEntry(
                name=band_name,
                albums_count=total_albums_count,
                local_albums_count=local_albums_count,
                folder_path=band_name,
                missing_albums_count=missing_albums_count,
                has_metadata=band_metadata.has_metadata_saved(),  # Use the new method to determine if metadata was saved
                has_analysis=band_metadata.analyze is not None,
                last_updated=band_metadata.last_updated
            )
            
            # Check if band already exists in index
            existing_band = None
            for i, existing in enumerate(collection_index.bands):
                if existing.name == band_name:
                    existing_band = i
                    break
            
            if existing_band is not None:
                # Update existing entry
                collection_index.bands[existing_band] = band_entry
            else:
                # Add new entry
                collection_index.bands.append(band_entry)
                collection_sync_results["band_entry_created"] = True
            
            # Update collection index
            index_update_result = update_collection_index(collection_index)
            if index_update_result.get("status") == "success":
                collection_sync_results["index_updated"] = True
            else:
                collection_sync_results["index_errors"].append("Failed to update collection index")
                
        except Exception as e:
            collection_sync_results["index_errors"].append(f"Collection sync failed: {str(e)}")
        
        # Step 4: Prepare comprehensive response
        response = {
            'status': 'success',
            'message': f"Band metadata successfully saved and validated for {band_name}",
            'validation_results': validation_results,
            'file_operations': {
                'metadata_file': storage_result.get('file_path', ''),
                'backup_created': True,  # Always true due to JSONStorage.save_json(backup=True)
                'last_updated': storage_result.get('last_updated', ''),
                'last_metadata_saved': band_metadata.last_metadata_saved,  # Include the new timestamp
                'file_size_bytes': 0,  # Could be enhanced to get actual file size
            },
            'collection_sync': collection_sync_results,
            'band_info': {
                'band_name': band_name,
                'albums_count': validation_results["albums_count"],
                'local_albums_count': len(band_metadata.albums),
                'missing_albums_count': validation_results["missing_albums_count"],
                'completion_percentage': round(
                    (len(band_metadata.albums) / max(validation_results["albums_count"], 1)) * 100, 1
                ) if validation_results["albums_count"] > 0 else 100.0,
                'has_metadata': band_metadata.has_metadata_saved(),  # Include has_metadata status
                'has_analysis': band_metadata.analyze is not None,
                'genre_count': len(band_metadata.genres),
                'members_count': len(band_metadata.members)
            },
            'tool_info': {
                'tool_name': 'save_band_metadata',
                'version': '1.3.0',  # Updated version for always preserve analyze and folder_structure behavior
                'parameters_used': {
                    'band_name': band_name,
                    'metadata_fields': list(metadata.keys())
                }
            }
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error in save_band_metadata tool: {str(e)}")
        return {
            'status': 'error',
            'error': f"Tool execution failed: {str(e)}",
            'validation_results': {
                "schema_valid": False,
                "validation_errors": [str(e)],
                "fields_validated": [],
                "albums_count": 0,
                "missing_albums_count": 0
            },
            'tool_info': {
                'tool_name': 'save_band_metadata',
                'version': '1.3.0'
            }
        }

@mcp.tool()
def save_band_analyze_tool(
    band_name: str,    
    analysis: Dict[str, Any],
    analyze_missing_albums: bool = False,
) -> Dict[str, Any]:
    """
    Save band analysis data including reviews, ratings, and similar bands.
    
    This tool stores comprehensive analysis data for a band:
    - Overall band review and rating
    - Album-specific reviews and ratings (1-10 scale)
    - Similar bands information
    - Optionally includes or excludes analysis for missing albums
    - Merges with existing metadata preserving structure
    - Validates analyze section structure
    - Updates collection statistics
    
    Args:
        band_name: The name of the band        
        analysis: Analysis data dictionary containing review, rating, albums analysis, and similar bands 
        analyze_missing_albums: If True, includes analysis for missing albums too. Default False.
        
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
    - By default (analyze_missing_albums=False): Analysis is only saved for albums that exist locally
    - When analyze_missing_albums=True: Analysis is saved for all albums, including missing ones
    
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
    try:
        # Import required models
        from models.band import BandAnalysis, AlbumAnalysis
        from tools.storage import update_collection_index, load_collection_index
        
        # Prepare comprehensive response structure
        response = {
            "status": "success",
            "message": "",
            "validation_results": {
                "schema_valid": False,
                "validation_errors": [],
                "fields_validated": [],
                "overall_rating": 0,
                "albums_analyzed": 0,
                "similar_bands_count": 0,
                "rating_distribution": {}
            },
            "file_operations": {
                "metadata_file": "",
                "backup_created": False,
                "last_updated": "",
                "file_size_bytes": 0,
                "merged_with_existing": False
            },
            "collection_sync": {
                "index_updated": False,
                "index_errors": [],
                "band_entry_found": False
            },
            "analysis_summary": {
                "band_name": band_name,
                "overall_rating": 0,
                "albums_analyzed": 0,
                "albums_with_ratings": 0,
                "similar_bands_count": 0,
                "has_review": False,
                "average_album_rating": 0.0,
                "rating_range": {"min": 0, "max": 0}
            },
            "tool_info": {
                "tool_name": "save_band_analyze",
                "version": "1.0.0",
                "parameters_used": {
                    "band_name": band_name,
                    "analysis_fields": list(analysis.keys()) if isinstance(analysis, dict) else [],
                    "analyze_missing_albums": analyze_missing_albums
                }
            }
        }
        
        # Validate input parameters
        if not band_name or not isinstance(band_name, str):
            response["status"] = "error"
            response["message"] = "Invalid band_name parameter: must be non-empty string"
            response["validation_results"]["validation_errors"].append("band_name is required and must be a string")
            return response
            
        if not analysis or not isinstance(analysis, dict):
            response["status"] = "error" 
            response["message"] = "Invalid analysis parameter: must be non-empty dictionary"
            response["validation_results"]["validation_errors"].append("analysis is required and must be a dictionary")
            return response
        
        # Validate and convert analysis data to BandAnalysis object
        validation_errors = []
        
        # Check required fields
        if "review" not in analysis:
            validation_errors.append("Missing required field: 'review'")
        elif not isinstance(analysis["review"], str):
            validation_errors.append("Field 'review' must be a string")
            
        if "rate" not in analysis:
            validation_errors.append("Missing required field: 'rate'")
        elif not isinstance(analysis["rate"], int):
            validation_errors.append("Field 'rate' must be an integer")
        elif analysis["rate"] < 0 or analysis["rate"] > 10:
            validation_errors.append("Field 'rate' must be between 0-10")
        
        # Check optional albums field
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
                                validation_errors.append(f"Album {i}: Missing 'album_name'")
                            else:
                                validation_errors.append(f"Album {i} ({album_data.get('album_name', 'unnamed')}): {err}")
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
        
        # Check optional similar_bands field
        similar_bands = []
        if "similar_bands" in analysis:
            if not isinstance(analysis["similar_bands"], list):
                validation_errors.append("Field 'similar_bands' must be a list")
            else:
                for i, band in enumerate(analysis["similar_bands"]):
                    if not isinstance(band, str):
                        validation_errors.append(f"Similar band {i}: must be a string")
                    else:
                        similar_bands.append(band)
        
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
                similar_bands=similar_bands
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
            storage_result = save_band_analyze(band_name, band_analysis, analyze_missing_albums)
            
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
                        from tools.storage import load_band_metadata
                        current_metadata = load_band_metadata(band_name)
                        if current_metadata:
                            # Calculate proper album counts from metadata
                            total_albums = len(current_metadata.albums)
                            missing_albums = len(current_metadata.get_missing_albums())
                            
                            # Ensure missing count doesn't exceed total (validation constraint)
                            missing_albums = min(missing_albums, total_albums)
                            
                            # Update band entry with accurate data
                            band_entry.albums_count = total_albums
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
        response["validation_results"]["similar_bands_count"] = len(band_analysis.similar_bands)
        
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
            "similar_bands_count": len(band_analysis.similar_bands),
            "has_review": len(band_analysis.review.strip()) > 0,
            "average_album_rating": round(sum(album_ratings) / len(album_ratings), 1) if album_ratings else 0.0,
            "rating_range": {
                "min": min(album_ratings) if album_ratings else 0,
                "max": max(album_ratings) if album_ratings else 0
            }
        }
        
        # Final success message with filtering information
        if analyze_missing_albums:
            if albums_excluded > 0:
                response["message"] = f"Band analysis successfully saved for {band_name} with {albums_analyzed_final} album reviews and {len(band_analysis.similar_bands)} similar bands (including missing albums)"
            else:
                response["message"] = f"Band analysis successfully saved for {band_name} with {albums_analyzed_final} album reviews and {len(band_analysis.similar_bands)} similar bands (all albums included)"
        else:
            if albums_excluded > 0:
                response["message"] = f"Band analysis successfully saved for {band_name} with {albums_analyzed_final} album reviews and {len(band_analysis.similar_bands)} similar bands ({albums_excluded} missing albums excluded)"
            else:
                response["message"] = f"Band analysis successfully saved for {band_name} with {albums_analyzed_final} album reviews and {len(band_analysis.similar_bands)} similar bands"
        
        return response
        
    except Exception as e:
        logger.error(f"Error in save_band_analyze tool: {str(e)}")
        return {
            'status': 'error',
            'error': f"Tool execution failed: {str(e)}",
            'tool_info': {
                'tool_name': 'save_band_analyze',
                'version': '1.0.0'
            }
        }

@mcp.tool()
def save_collection_insight_tool(
    insights: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Save collection-wide insights and analytics.
    
    This tool stores comprehensive collection insights including:
    - Collection insights and analysis text
    - Actionable recommendations for the collection
    - Top-rated bands listing
    - Suggested album purchases
    - Overall collection health assessment
    - Generated at timestamp for tracking
    
    Args:
        insights: Insights data dictionary containing collection analytics
        
    Returns:
        Dict containing comprehensive operation status with validation results,
        file operations, collection sync, and insights summary
    
    INSIGHTS SCHEMA:
    ===============
    The insights parameter must be a dictionary with the following structure:
    
    OPTIONAL FIELDS:
    ================
    - insights (array of strings): Collection insight text descriptions
    - recommendations (array of strings): Actionable recommendations for improving collection
    - top_rated_bands (array of strings): Names of highest rated bands in collection
    - suggested_purchases (array of strings): Albums suggested for acquisition
    - collection_health (string): Overall collection health ('Excellent', 'Good', 'Fair', 'Poor')
    
    COLLECTION HEALTH VALUES:
    =========================
    - 'Excellent': Collection is in optimal state
    - 'Good': Collection is in good condition with minor improvements needed
    - 'Fair': Collection has some issues that should be addressed
    - 'Poor': Collection has significant issues requiring attention
    
    EXAMPLE INSIGHTS:
    =================
    {
        "insights": [
            "Your collection shows strong representation in rock and metal genres",
            "Missing albums are concentrated in 1990s releases",
            "Average collection rating is 7.8/10 indicating high quality selection"
        ],
        "recommendations": [
            "Consider adding more jazz albums to diversify genres",
            "Focus on completing Pink Floyd discography - 3 albums missing",
            "Review low-rated albums for potential removal"
        ],
        "top_rated_bands": ["Pink Floyd", "Led Zeppelin", "The Beatles"],
        "suggested_purchases": [
            "Pink Floyd - Wish You Were Here",
            "Led Zeppelin - Physical Graffiti",
            "The Beatles - Revolver"
        ],
        "collection_health": "Good"
    }
    """
    try:
        # Import required models
        from models.collection import CollectionInsight
        from tools.storage import save_collection_insight as storage_save_collection_insight
        
        # Prepare comprehensive response structure
        response = {
            "status": "success",
            "message": "",
            "validation_results": {
                "schema_valid": False,
                "validation_errors": [],
                "fields_validated": [],
                "insights_count": 0,
                "recommendations_count": 0,
                "top_rated_bands_count": 0,
                "suggested_purchases_count": 0,
                "collection_health_valid": False
            },
            "file_operations": {
                "collection_index_file": "",
                "backup_created": False,
                "merged_with_existing": False,
                "last_updated": "",
                "file_size_bytes": 0
            },
            "collection_sync": {
                "index_updated": False,
                "index_errors": [],
                "insights_added": False
            },
            "insights_summary": {
                "insights_count": 0,
                "recommendations_count": 0,
                "top_rated_bands_count": 0,
                "suggested_purchases_count": 0,
                "collection_health": "Good",
                "has_insights": False,
                "has_recommendations": False,
                "generated_at": ""
            },
            "tool_info": {
                "tool_name": "save_collection_insight",
                "version": "1.0.0",
                "parameters_used": {
                    "insights_fields": list(insights.keys()) if isinstance(insights, dict) else []
                }
            }
        }
        
        # Validate input parameters
        if insights is None or not isinstance(insights, dict):
            response["status"] = "error"
            response["message"] = "Invalid insights parameter: must be a dictionary"
            response["validation_results"]["validation_errors"].append("insights is required and must be a dictionary")
            return response
        
        # Validate and convert insights data to CollectionInsight object
        validation_errors = []
        fields_validated = []
        
        # Check optional fields and their types
        insights_list = insights.get("insights", [])
        if "insights" in insights:
            fields_validated.append("insights")
            if not isinstance(insights_list, list):
                validation_errors.append("Field 'insights' must be a list of strings")
            elif not all(isinstance(item, str) for item in insights_list):
                validation_errors.append("All items in 'insights' must be strings")
        
        recommendations_list = insights.get("recommendations", [])
        if "recommendations" in insights:
            fields_validated.append("recommendations")
            if not isinstance(recommendations_list, list):
                validation_errors.append("Field 'recommendations' must be a list of strings")
            elif not all(isinstance(item, str) for item in recommendations_list):
                validation_errors.append("All items in 'recommendations' must be strings")
        
        top_rated_bands_list = insights.get("top_rated_bands", [])
        if "top_rated_bands" in insights:
            fields_validated.append("top_rated_bands")
            if not isinstance(top_rated_bands_list, list):
                validation_errors.append("Field 'top_rated_bands' must be a list of strings")
            elif not all(isinstance(item, str) for item in top_rated_bands_list):
                validation_errors.append("All items in 'top_rated_bands' must be strings")
        
        suggested_purchases_list = insights.get("suggested_purchases", [])
        if "suggested_purchases" in insights:
            fields_validated.append("suggested_purchases")
            if not isinstance(suggested_purchases_list, list):
                validation_errors.append("Field 'suggested_purchases' must be a list of strings")
            elif not all(isinstance(item, str) for item in suggested_purchases_list):
                validation_errors.append("All items in 'suggested_purchases' must be strings")
        
        collection_health = insights.get("collection_health", "Good")
        collection_health_valid = True  # Default value is always valid
        if "collection_health" in insights:
            fields_validated.append("collection_health")
            if not isinstance(collection_health, str):
                validation_errors.append("Field 'collection_health' must be a string")
                collection_health_valid = False
            else:
                allowed_health_values = ['Excellent', 'Good', 'Fair', 'Poor']
                if collection_health not in allowed_health_values:
                    validation_errors.append(f"Field 'collection_health' must be one of: {allowed_health_values}")
                    collection_health_valid = False
        
        # If there are validation errors, return error response
        if validation_errors:
            response["status"] = "error"
            response["message"] = "Insights validation failed"
            response["validation_results"]["validation_errors"] = validation_errors
            response["validation_results"]["fields_validated"] = fields_validated
            return response
        
        # Try to create CollectionInsight object for full validation
        try:
            collection_insight = CollectionInsight(
                insights=insights_list,
                recommendations=recommendations_list,
                top_rated_bands=top_rated_bands_list,
                suggested_purchases=suggested_purchases_list,
                collection_health=collection_health
            )
            
            # Validation successful
            response["validation_results"]["schema_valid"] = True
            response["validation_results"]["fields_validated"] = fields_validated
            response["validation_results"]["insights_count"] = len(insights_list)
            response["validation_results"]["recommendations_count"] = len(recommendations_list)
            response["validation_results"]["top_rated_bands_count"] = len(top_rated_bands_list)
            response["validation_results"]["suggested_purchases_count"] = len(suggested_purchases_list)
            response["validation_results"]["collection_health_valid"] = collection_health_valid
            
        except Exception as e:
            validation_error = str(e)
            response["status"] = "error"
            response["message"] = "Insights schema validation failed"
            response["validation_results"]["validation_errors"].append(f"Schema validation failed: {validation_error}")
            response["validation_results"]["fields_validated"] = fields_validated
            return response
        
        # Save the insights using storage function
        try:
            storage_result = storage_save_collection_insight(collection_insight)
            
            # Update response with storage results
            response["status"] = storage_result["status"]
            response["message"] = f"Collection insights saved successfully with {len(insights_list)} insights and {len(recommendations_list)} recommendations"
            
            # File operations
            response["file_operations"]["collection_index_file"] = storage_result.get("file_path", "")
            response["file_operations"]["backup_created"] = True  # Storage always creates backup
            response["file_operations"]["merged_with_existing"] = storage_result.get("file_existed_before", False)
            response["file_operations"]["last_updated"] = collection_insight.generated_at
            
            # Get file size if path is available
            collection_file_path = Path(storage_result.get("file_path", ""))
            if collection_file_path.exists():
                response["file_operations"]["file_size_bytes"] = collection_file_path.stat().st_size
            
            # Collection sync
            response["collection_sync"]["index_updated"] = True
            response["collection_sync"]["insights_added"] = True
            response["collection_sync"]["index_errors"] = []
            
            # Insights summary
            response["insights_summary"]["insights_count"] = len(insights_list)
            response["insights_summary"]["recommendations_count"] = len(recommendations_list)
            response["insights_summary"]["top_rated_bands_count"] = len(top_rated_bands_list)
            response["insights_summary"]["suggested_purchases_count"] = len(suggested_purchases_list)
            response["insights_summary"]["collection_health"] = collection_health
            response["insights_summary"]["has_insights"] = len(insights_list) > 0
            response["insights_summary"]["has_recommendations"] = len(recommendations_list) > 0
            response["insights_summary"]["generated_at"] = collection_insight.generated_at
            
        except Exception as e:
            response["status"] = "error"
            response["message"] = f"Failed to save collection insights: {str(e)}"
            response["validation_results"]["validation_errors"].append(f"Storage operation failed: {str(e)}")
            response["collection_sync"]["index_errors"].append(str(e))
        
        return response
        
    except Exception as e:
        logger.error(f"Error in save_collection_insight tool: {str(e)}")
        return {
            'status': 'error',
            'error': f"Tool execution failed: {str(e)}",
            'validation_results': {
                "schema_valid": False,
                "validation_errors": [str(e)],
                "fields_validated": [],
                "insights_count": 0,
                "recommendations_count": 0,
                "top_rated_bands_count": 0,
                "suggested_purchases_count": 0,
                "collection_health_valid": False
            },
            'tool_info': {
                'tool_name': 'save_collection_insight',
                'version': '1.0.0'
            }
        }

@mcp.tool()
def validate_band_metadata_tool(
    band_name: str,
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate band metadata structure without saving it.
    
    This tool performs dry-run validation to help clients test their metadata format:
    - Validates metadata against the BandMetadata schema
    - Returns detailed validation results and errors
    - Does NOT save any data or modify files
    - Useful for testing metadata structure before calling save_band_metadata_tool
    
    Args:
        band_name: The name of the band
        metadata: Metadata dictionary to validate (same format as save_band_metadata_tool)
    
    Returns:
        Dict containing validation results:
        - status: 'valid' or 'invalid'
        - validation_results: Detailed schema validation information
        - suggestions: Helpful suggestions to fix validation errors
        - example_corrections: Examples of how to fix common errors
    """
    try:
        # Import required models
        from models.band import BandMetadata
        
        # Prepare validation results
        validation_results = {
            "schema_valid": False,
            "validation_errors": [],
            "fields_validated": [],
            "albums_count": 0,
            "missing_albums_count": 0,
            "field_types_correct": {},
            "missing_required_fields": [],
            "unexpected_fields": []
        }
        
        suggestions = []
        example_corrections = {}
        
        # Check for common field name errors
        common_field_errors = {
            "genre": "genres",
            "formed_year": "formed", 
            "formed_location": "origin",
            "notable_albums": "albums"
        }
        
        for wrong_field, correct_field in common_field_errors.items():
            if wrong_field in metadata:
                validation_results["validation_errors"].append(
                    f"Field '{wrong_field}' should be '{correct_field}'"
                )
                suggestions.append(f"Rename '{wrong_field}' to '{correct_field}'")
                example_corrections[wrong_field] = correct_field
        
        # Check for nested members structure
        if isinstance(metadata.get("members"), dict):
            validation_results["validation_errors"].append(
                "Field 'members' should be a flat list, not nested object with 'former'/'current'"
            )
            suggestions.append("Flatten members structure: combine all members into single array")
            example_corrections["members"] = {
                "wrong": {"former": ["..."], "current": ["..."]},
                "correct": ["member1", "member2", "member3"]
            }
        
        # Check required fields
        required_fields = ["band_name", "formed", "genres", "origin", "members", "description", "albums"]
        for field in required_fields:
            if field not in metadata:
                validation_results["missing_required_fields"].append(field)
                suggestions.append(f"Add required field '{field}'")
        
        # Check field types
        if "formed" in metadata and not isinstance(metadata["formed"], str):
            validation_results["validation_errors"].append(
                f"Field 'formed' should be string (YYYY format), got {type(metadata['formed']).__name__}"
            )
            suggestions.append("Convert 'formed' to string format: '1965' not 1965")
            example_corrections["formed"] = {
                "wrong": 1965,
                "correct": "1965"
            }
        
        # Ensure band_name consistency
        if 'band_name' not in metadata:
            metadata['band_name'] = band_name
        elif metadata['band_name'] != band_name:
            metadata['band_name'] = band_name
            validation_results["validation_errors"].append(
                f"band_name updated to match parameter: '{band_name}'"
            )
        
        # Try to create BandMetadata object for full validation
        try:
            band_metadata = BandMetadata(**metadata)
            validation_results["schema_valid"] = True
            validation_results["fields_validated"] = list(metadata.keys())
            validation_results["albums_count"] = len(band_metadata.albums) + len(band_metadata.albums_missing)
            validation_results["missing_albums_count"] = len(band_metadata.albums_missing)
            
            # Validate each field type
            validation_results["field_types_correct"] = {
                "band_name": isinstance(metadata.get("band_name"), str),
                "formed": isinstance(metadata.get("formed"), str),
                "genres": isinstance(metadata.get("genres"), list),
                "origin": isinstance(metadata.get("origin"), str),
                "members": isinstance(metadata.get("members"), list),
                "description": isinstance(metadata.get("description"), str),
                "albums": isinstance(metadata.get("albums"), list)
            }
            
        except Exception as e:
            validation_error = str(e)
            validation_results["validation_errors"].append(f"Schema validation failed: {validation_error}")
            
            # Add specific suggestions based on error message
            if "String should match pattern" in validation_error and "formed" in validation_error:
                suggestions.append("'formed' field must be 4-digit year as string (e.g., '1965')")
            if "ensure this value is greater than or equal to 0" in validation_error:
                suggestions.append("'tracks_count' must be 0 or positive integer")
            if "ensure this value is less than or equal to 10" in validation_error:
                suggestions.append("'rate' fields must be between 0-10")
        
        # Check for unexpected fields
        expected_fields = ["band_name", "formed", "genres", "origin", "members", "description", "albums", "albums_missing", "analyze", "last_updated", "albums_count"]
        for field in metadata.keys():
            if field not in expected_fields:
                validation_results["unexpected_fields"].append(field)
                suggestions.append(f"Unexpected field '{field}' - check field name spelling")
        
        # Determine overall status
        has_validation_errors = len(validation_results["validation_errors"]) > 0
        has_missing_required = len(validation_results["missing_required_fields"]) > 0
        schema_invalid = not validation_results["schema_valid"]
        
        status = "valid" if (validation_results["schema_valid"] and not has_validation_errors and not has_missing_required) else "invalid"
        
        return {
            "status": status,
            "message": f"Metadata validation {'successful' if status == 'valid' else 'failed'} for {band_name}",
            "validation_results": validation_results,
            "suggestions": suggestions,
            "example_corrections": example_corrections,
            "schema_resource": "Use resource 'schema://band_metadata' for complete documentation",
            "tool_info": {
                "tool_name": "validate_band_metadata",
                "version": "1.0.0",
                "dry_run": True
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": f"Validation tool failed: {str(e)}",
            "suggestions": ["Check that metadata is a valid JSON object"],
            "schema_resource": "Use resource 'schema://band_metadata' for complete documentation",
            "tool_info": {
                "tool_name": "validate_band_metadata",
                "version": "1.0.0",
                "dry_run": True
            }
        }

# Register resources
@mcp.resource("band://info/{band_name}")
def band_info_resource(band_name: str) -> str:
    """
    Get detailed band information in markdown format.
    
    Args:
        band_name: Name of the band to retrieve information for
        
    Returns:
        Markdown-formatted band information
    """
    try:
        return get_band_info_markdown(band_name)
    except Exception as e:
        logger.error(f"Error in band_info resource: {str(e)}")
        return f"Error retrieving band information: {str(e)}"

@mcp.resource("collection://summary")
def collection_summary_resource() -> str:
    """
    Get collection summary statistics in markdown format.
    
    Returns:
        Markdown-formatted collection summary
    """
    try:
        return get_collection_summary()
    except Exception as e:
        logger.error(f"Error in collection_summary resource: {str(e)}")
        return f"Error retrieving collection summary: {str(e)}"

# Register prompts
@mcp.prompt()
def fetch_band_info_prompt(band_name: str, existing_albums: List[str] = None, information_scope: str = "full") -> Dict[str, Any]:
    """
    Prompt template for fetching band information using external sources.
    
    Returns:
        Prompt template for band information retrieval
    """
    try:
        return get_fetch_band_info_prompt(band_name, existing_albums, information_scope)
    except Exception as e:
        logger.error(f"Error in fetch_band_info prompt: {str(e)}")
        return {
            'name': 'fetch_band_info',
            'description': 'Error loading prompt template',
            'messages': [{'role': 'user', 'content': f'Error: {str(e)}'}]
        }

@mcp.prompt()
def analyze_band_prompt(
    band_name: str = "",
    albums: List[str] = None,
    analyze_missing_albums: bool = False,
    analysis_scope: str = "full"
) -> Dict[str, Any]:
    """
    Prompt template for comprehensive band analysis.
    
    Args:
        band_name: Name of the band to analyze (optional parameter for dynamic prompts)
        albums: List of albums to include in analysis (optional)
        analyze_missing_albums: If True, include analysis for missing albums too
        analysis_scope: Scope of analysis - "basic", "full", or "albums_only" (default: "full")
    
    Returns:
        Prompt template for band analysis
    """
    try:
        return get_analyze_band_prompt(band_name, albums, analyze_missing_albums, analysis_scope)
    except Exception as e:
        logger.error(f"Error in analyze_band prompt: {str(e)}")
        return {
            'name': 'analyze_band',
            'description': 'Error loading prompt template', 
            'messages': [{'role': 'user', 'content': f'Error: {str(e)}'}]
        }

@mcp.prompt()
def compare_bands_prompt(
    band_names: List[str] = None,
    comparison_aspects: List[str] = None,
    comparison_scope: str = "full"
) -> Dict[str, Any]:
    """
    Prompt template for comparing multiple bands.
    
    Args:
        band_names: List of band names to compare (minimum 2 required)
        comparison_aspects: Specific aspects to focus on: style, discography, influence, legacy, innovation, commercial, critical
        comparison_scope: Scope of comparison - "basic", "full", or "summary" (default: "full")
    
    Returns:
        Prompt template for band comparison
    """
    try:
        return get_compare_bands_prompt(band_names, comparison_aspects, comparison_scope)
    except Exception as e:
        logger.error(f"Error in compare_bands prompt: {str(e)}")
        return {
            'name': 'compare_bands',
            'description': 'Error loading prompt template',
            'messages': [{'role': 'user', 'content': f'Error: {str(e)}'}]
        }

@mcp.prompt()
def collection_insights_prompt() -> Dict[str, Any]:
    """
    Prompt template for generating collection insights.
    
    Returns:
        Prompt template for collection insights
    """
    try:
        return get_collection_insights_prompt()
    except Exception as e:
        logger.error(f"Error in collection_insights prompt: {str(e)}")
        return {
            'name': 'collection_insights',
            'description': 'Error loading prompt template',
            'messages': [{'role': 'user', 'content': f'Error: {str(e)}'}]
        }

def main():
    """Main entry point for the MCP server."""
    # Remove startup message to minimize output
    
    try:
        # Try to run the MCP server
        mcp.run()
    except KeyboardInterrupt:
        pass  # Silently handle user interruption
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        # In development mode, keep server alive even if no client connects
        try:
            # Keep the process alive
            while True:
                import time
                time.sleep(60)  # Sleep for 60 seconds at a time
        except KeyboardInterrupt:
            pass  # Silently handle user interruption

if __name__ == "__main__":
    main()