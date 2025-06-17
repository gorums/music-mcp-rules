#!/usr/bin/env python3
"""
Music Collection MCP Server - Save Band Metadata Tool

This module contains the save_band_metadata_tool implementation.
"""

import logging
from typing import Any, Dict

from ..core import mcp

# Import tool implementation - using absolute imports
from src.tools.storage import save_band_metadata, load_band_metadata, load_collection_index, update_collection_index
from src.models.band import BandMetadata
from src.models.collection import BandIndexEntry

# Configure logging
logger = logging.getLogger(__name__)

@mcp.tool()
def save_band_metadata_tool(
    band_name: str,
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Save band metadata to the local storage. Check very careful how is the metadata passed to the tool, check the examples too.
        
    WHAT THE MCP CLIENT MUST SEND:
    ==============================
    The MCP client must send exactly 2 parameters:
    
    1. band_name (string): The exact name of the band (e.g., "Pink Floyd", "The Beatles")
    2. metadata (object): A JSON object containing the band's metadata following the schema below
    
    CLIENT CALL EXAMPLE:
    ===================
    {
        "tool": "save_band_metadata_tool",
        "arguments": {
            "band_name": "Pink Floyd",
            "metadata": {
                "formed": "1965",
                "genres": ["Progressive Rock", "Psychedelic Rock"],
                "origin": "London, England", 
                "members": ["David Gilmour", "Roger Waters"],
                "description": "English rock band...",                
                "albums_missing": [
                    {
                        "album_name": "Wish You Were Here",
                        "year": "1975",
                        "track_count": 5,
                        "type": "Album",
                        "genres": ["Progressive Rock", "Psychedelic Rock"]
                    }
                ]
            }
        }
    }
    
    NOTE: "albums_missing" are not optional.
    
    Args:
        band_name: The name of the band (must match metadata.band_name if present)
        metadata: Complete metadata dictionary for the band following the schema below
        
    Returns:
        Dict containing the operation status, validation results, and file operations
    
    METADATA SCHEMA:
    ================
    The metadata parameter must be a JSON object with the following structure:
    
    REQUIRED FIELDS:
    ================
    - formed (string): Formation year in "YYYY" format
    - genres (array of strings): List of music genres
    - origin (string): Country/city of origin
    - members (array of strings): List of all band member names
    - description (string): Band biography or description
    
    OPTIONAL FIELDS:
    ================
    - albums_missing (array): List of missing album objects (if not provided, preserves existing data)

    ALBUMS STRUCTURE:
    ==================
    Albums are now organized into TWO separate arrays based on availability:
    
    1. albums (array): Albums found locally in your music collection
    2. albums_missing (array): Albums not found locally but part of band's discography
    
    ALBUM SCHEMA (for items in both albums and albums_missing arrays):
    ==================================================================
    REQUIRED:
    - album_name (string): Name of the album
    - year (string): Release year in "YYYY" format  
    - track_count (integer): Number of tracks (must be >= 0)
    - genres (array of strings): Album-specific genres (can differ from band genres)
    - type (string): Album type - "Album", "EP", "Live", "Demo", "Compilation", "Single", "Instrumental", "Split"
    - edition (string): Edition info like "Deluxe Edition", "Remastered", etc. (omit for standard releases)
    - duration (string): Album length (format: "43min", "1h 23min", etc.)
        
    COMPLETE EXAMPLE of METADATA JSON:
    =============================
    {
        "formed": "1965", 
        "genres": ["Progressive Rock", "Psychedelic Rock", "Art Rock"],
        "origin": "London, England",
        "members": ["David Gilmour", "Roger Waters", "Nick Mason", "Richard Wright", "Syd Barrett"],
        "description": "English rock band formed in London in 1965. Achieved international acclaim with their progressive and psychedelic music.",        
        "albums_missing": [
            {
                "album_name": "Wish You Were Here",
                "year": "1975", 
                "track_count": 5,
                "type": "Album",
                "duration": "44min",
                "genres": ["Progressive Rock", "Art Rock"]
            },
            {
                "album_name": "Animals",
                "year": "1977",
                "track_count": 5,
                "type": "Album",
                "duration": "44min",
                "genres": ["Progressive Rock", "Art Rock"]
            }
        ]
    }

    COMMON MISTAKES TO AVOID:
    ========================
    ❌ Using "formed_year" (should be "formed")
    ❌ Using integer for formed year (should be string "1965")
    ❌ Using nested member structure like {"current": [...], "former": [...]} (should be flat array)
    ❌ Using "notable_albums" or "discography" (should be "albums")
    ❌ Using old "missing" field in albums (now use separate "albums" and "albums_missing" arrays)
    ❌ Using "tracks_count" (should be "track_count")
    ❌ Missing required album fields (album_name, year, track_count)
    ❌ Using integer for album year (should be string "1973")
    ❌ Negative track_count (must be >= 0)
    ❌ Invalid album type (must be: Album, EP, Live, Demo, Compilation, Single, Instrumental, Split)
    
    CLIENT TRANSMISSION FORMAT:
    ===========================
    The MCP client should send the metadata as a JSON object, not as a JSON string.
    
    ✅ CORRECT - Send as object:
    {
        "band_name": "Pink Floyd",
        "metadata": {
            "formed": "1965",
            "genres": ["Progressive Rock"]
        }
    }
    
    ❌ INCORRECT - Don't send as JSON string:
    {
        "band_name": "Pink Floyd", 
        "metadata": "{\"formed\": \"1965\", \"genres\": [\"Progressive Rock\"]}"
    }
    
    VALIDATION NOTES:
    ================
    - All year fields must be 4-digit strings (e.g., "1975", not 1975)
    - Both albums and albums_missing arrays can be empty but must be present
    - Members array should include all members (past and present) as flat list
    - Duration format is flexible but should include time unit (min, h, etc.)
    - Genres should be specific and accurate music genres
    - Albums are automatically separated: found locally go to "albums", not found go to "albums_missing"
    - The old "missing" field in individual albums is no longer used or supported
    
    DATA PRESERVATION:
    ==================
    - Existing analyze data is always preserved when updating metadata
    - Existing folder_structure data is always preserved when updating metadata
    - Existing albums data is always preserved when updating metadata
    - If albums_missing array is not provided in metadata, existing missing albums are preserved
    - Providing arrays in metadata will replace the existing data for those arrays
    """
    try:        
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
            
            # Handle albums preservation logic
            local_metadata = load_band_metadata(band_name)
            if local_metadata is not None:
                # If albums is not provided in metadata, preserve existing local albums
                metadata['albums'] = [album.model_dump() for album in local_metadata.albums]
                # If albums_missing is not provided in metadata, preserve existing
                if 'albums_missing' not in metadata:
                    metadata['albums_missing'] = [album.model_dump() for album in local_metadata.albums_missing]
            else:
                # New band: ensure both arrays exist
                metadata['albums'] = metadata.get('albums', [])
                metadata['albums_missing'] = metadata.get('albums_missing', [])
            
            # Create BandMetadata object for validation
            band_metadata = BandMetadata(**metadata)
            
            # Ensure we have a proper BandMetadata object, not a dict
            if not isinstance(band_metadata, BandMetadata):
                raise ValueError(f"Failed to create BandMetadata object, got {type(band_metadata)}")
            
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
                from src.models.collection import CollectionIndex
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
                collection_sync_results["index_updated"] = False
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
                'members_count': len(band_metadata.members),
                # Add detailed album information
                'local_albums': [
                    {
                        'album_name': album.album_name,
                        'year': album.year,
                        'track_count': album.track_count,
                        'type': album.type.value if hasattr(album.type, 'value') else str(album.type),
                        'edition': album.edition,
                        'duration': album.duration,
                        'genres': album.genres
                    }
                    for album in band_metadata.albums
                ],
                'missing_albums': [
                    {
                        'album_name': album.album_name,
                        'year': album.year,
                        'track_count': album.track_count,
                        'type': album.type.value if hasattr(album.type, 'value') else str(album.type),
                        'edition': album.edition,
                        'duration': album.duration,
                        'genres': album.genres
                    }
                    for album in band_metadata.albums_missing
                ]
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