#!/usr/bin/env python3
"""
Music Collection MCP Server - Save Band Metadata Tool

This module contains the save_band_metadata_tool implementation.
"""

import logging
from typing import Any, Dict

from ..core import mcp

# Import tool implementation - using absolute imports
from src.tools.storage import save_band_metadata, load_band_metadata
from src.models.band import BandMetadata

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
        # Validate input parameters
        if not band_name or not isinstance(band_name, str):
            return {
                'status': 'error',
                'error': 'Invalid band_name parameter: must be non-empty string',
                'validation_results': {
                    "schema_valid": False,
                    "validation_errors": ["band_name is required and must be a string"],
                    "fields_validated": [],
                    "albums_count": 0,
                    "missing_albums_count": 0
                }
            }
            
        if not metadata or not isinstance(metadata, dict):
            return {
                'status': 'error',
                'error': 'Invalid metadata parameter: must be non-empty dictionary',
                'validation_results': {
                    "schema_valid": False,
                    "validation_errors": ["metadata is required and must be a dictionary"],
                    "fields_validated": [],
                    "albums_count": 0,
                    "missing_albums_count": 0
                }
            }

        # Load existing metadata to preserve analyze and folder_structure data
        local_metadata = load_band_metadata(band_name)
        band_existed_before = local_metadata is not None
        
        # Convert old format to new format if needed
        if 'albums' in metadata and isinstance(metadata['albums'], list):
            albums_with_missing = metadata['albums']
            if albums_with_missing and isinstance(albums_with_missing[0], dict) and 'missing' in albums_with_missing[0]:
                # Old format - separate into albums and albums_missing
                albums = [album for album in albums_with_missing if not album.get('missing', False)]
                albums_missing = [album for album in albums_with_missing if album.get('missing', False)]
                
                # Remove missing field from albums
                for album in albums:
                    album.pop('missing', None)
                for album in albums_missing:
                    album.pop('missing', None)
                    
                metadata['albums'] = albums
                metadata['albums_missing'] = albums_missing

        # Preserve analyze data if it exists in local metadata
        if local_metadata and hasattr(local_metadata, 'analyze') and local_metadata.analyze:
            metadata['analyze'] = local_metadata.analyze.model_dump()
            
        # Preserve folder_structure data if it exists in local metadata
        if local_metadata and hasattr(local_metadata, 'folder_structure') and local_metadata.folder_structure:
            metadata['folder_structure'] = local_metadata.folder_structure.model_dump()
            
        # Only preserve albums if not provided in input
        if 'albums' not in metadata:
            if local_metadata:
                metadata['albums'] = [album.model_dump() for album in local_metadata.albums]
                
        # Preserve albums_missing if not provided in input
        if 'albums_missing' not in metadata:
            if local_metadata:
                metadata['albums_missing'] = [album.model_dump() for album in local_metadata.albums_missing]

        # Convert dictionary to BandMetadata object with validation
        try:
            # Ensure band_name is set correctly (remove from metadata if present to avoid duplicate)
            metadata_copy = metadata.copy()
            metadata_copy.pop('band_name', None)  # Remove if present to avoid duplicate
            band_metadata = BandMetadata(band_name=band_name, **metadata_copy)
        except Exception as validation_error:
            return {
                'status': 'error',
                'error': f'Metadata validation failed: {str(validation_error)}',
                'validation_results': {
                    "schema_valid": False,
                    "validation_errors": [str(validation_error)],
                    "fields_validated": ['band_name'] + list(metadata.keys()),
                    "albums_count": 0,
                    "missing_albums_count": 0
                },
                'tool_info': {
                    'tool_name': 'save_band_metadata',
                    'version': '1.3.0'
                }
            }
        
        # Save the metadata
        result = save_band_metadata(band_name, band_metadata)
        
        # Load the saved metadata to get accurate counts
        band_metadata = load_band_metadata(band_name)
        
        # Build comprehensive response
        response = {
            'status': result.get('status', 'success'),
            'message': result.get('message', f'Successfully saved metadata for {band_name}'),
            'validation_results': {
                'schema_valid': True,
                'validation_errors': [],
                'fields_validated': ['band_name'] + list(metadata.keys()),
                'albums_count': band_metadata.albums_count if band_metadata else 0,
                'missing_albums_count': band_metadata.missing_albums_count if band_metadata else 0
            },
            'file_operations': {
                'backup_created': True,
                'last_updated': result.get('last_updated', ''),
                'metadata_file': result.get('file_path', '')
            },
            'collection_sync': {
                'index_updated': True,
                'band_entry_created': not band_existed_before,
                'index_errors': []
            },
            'band_info': {
                'band_name': band_name,
                'albums_count': band_metadata.albums_count if band_metadata else 0,
                'local_albums_count': band_metadata.local_albums_count if band_metadata else 0,
                'missing_albums_count': band_metadata.missing_albums_count if band_metadata else 0,
                'completion_percentage': round(
                    (band_metadata.local_albums_count / band_metadata.albums_count * 100) 
                    if band_metadata and band_metadata.albums_count > 0 
                    else 100.0, 1
                ),
                'has_analysis': bool(band_metadata and band_metadata.analyze),
                'has_folder_structure': bool(band_metadata and band_metadata.folder_structure),
                'genre_count': len(band_metadata.genres) if band_metadata else 0,
                'members_count': len(band_metadata.members) if band_metadata else 0,
                'albums': [
                    {
                        'album_name': album.album_name,
                        'year': album.year,
                        'track_count': album.track_count,
                        'type': album.type.value if album.type else None,
                        'edition': album.edition,
                        'duration': album.duration,
                        'genres': album.genres
                    }
                    for album in band_metadata.albums
                ] if band_metadata else [],
                'albums_missing': [
                    {
                        'album_name': album.album_name,
                        'year': album.year,
                        'track_count': album.track_count,
                        'type': album.type.value if album.type else None,
                        'edition': album.edition,
                        'duration': album.duration,
                        'genres': album.genres
                    }
                    for album in band_metadata.albums_missing
                ] if band_metadata else []
            },
            'tool_info': {
                'tool_name': 'save_band_metadata',
                'version': '1.3.0',
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