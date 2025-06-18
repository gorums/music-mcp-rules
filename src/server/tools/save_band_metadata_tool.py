#!/usr/bin/env python3
"""
Music Collection MCP Server - Save Band Metadata Tool

This module contains the save_band_metadata_tool implementation.
"""

import logging
from typing import Any, Dict
from datetime import datetime, timezone

from ..mcp_instance import mcp
from ..base_handlers import BaseToolHandler

# Import tool implementation - using absolute imports
from src.tools.storage import save_band_metadata, load_band_metadata, load_collection_index, update_collection_index
from src.models.band import BandMetadata
from src.models.collection import BandIndexEntry

# Configure logging
logger = logging.getLogger(__name__)


class SaveBandMetadataHandler(BaseToolHandler):
    """Handler for the save_band_metadata tool."""
    
    def __init__(self):
        super().__init__("save_band_metadata", "1.3.0")
    
    def _execute_tool(self, **kwargs) -> Dict[str, Any]:
        """Execute band metadata saving with comprehensive validation and response formatting."""
        band_name = kwargs.get('band_name')
        metadata = kwargs.get('metadata')
        
        # Initialize response structure that tests expect
        response = {
            'status': 'success',
            'message': '',
            'validation_results': {
                'schema_valid': False,
                'validation_errors': [],
                'albums_count': 0,
                'missing_albums_count': 0,
                'fields_validated': []
            },
            'band_info': {},
            'collection_sync': {
                'index_updated': False,
                'band_entry_created': False,
                'band_entry_found': False,
                'index_errors': []
            },
            'file_operations': {
                'metadata_file': '',
                'backup_created': False,
                'last_updated': '',
                'merged_with_existing': False
            }
        }
        
        # Validate required parameters
        if not band_name or not isinstance(band_name, str) or band_name.strip() == "":
            response['status'] = 'error'
            response['message'] = 'band_name is required and must be a non-empty string'
            response['error'] = response['message']  # Add error field for test compatibility
            return response
            
        if not metadata or not isinstance(metadata, dict):
            response['status'] = 'error'
            response['message'] = 'metadata is required and must be a dictionary'
            response['error'] = response['message']  # Add error field for test compatibility
            return response
        
        band_name = band_name.strip()
        
        # Load existing metadata first to check if albums should be preserved
        try:
            existing_metadata = load_band_metadata(band_name)
        except Exception:
            existing_metadata = None
        
        # Preserve existing albums if albums key is not provided
        if existing_metadata and 'albums' not in metadata:
            metadata['albums'] = [album.model_dump() for album in existing_metadata.albums]
        
        # Add band_name to metadata if not present
        if 'band_name' not in metadata:
            metadata['band_name'] = band_name
        
        # Convert from old format if needed
        if 'albums' in metadata and isinstance(metadata['albums'], list):
            albums_local = []
            albums_missing = []
            for album in metadata['albums']:
                if isinstance(album, dict):
                    # Remove missing field if present (old format)
                    if 'missing' in album:
                        if album['missing']:
                            albums_missing.append({k: v for k, v in album.items() if k != 'missing'})
                        else:
                            albums_local.append({k: v for k, v in album.items() if k != 'missing'})
                    else:
                        # No missing field, assume local
                        albums_local.append(album)
            
            # Update metadata with separated arrays
            metadata['albums'] = albums_local
            if 'albums_missing' not in metadata:
                metadata['albums_missing'] = albums_missing
        
        # Validate metadata and create BandMetadata object
        try:
            band_metadata = BandMetadata(**metadata)
            response['validation_results']['schema_valid'] = True
            response['validation_results']['fields_validated'] = list(metadata.keys())
            response['validation_results']['albums_count'] = band_metadata.albums_count
            response['validation_results']['missing_albums_count'] = band_metadata.missing_albums_count
        except Exception as e:
            response['status'] = 'error'
            response['message'] = f'Metadata validation failed: {str(e)}'
            response['error'] = response['message']  # Add error field for test compatibility
            response['validation_results']['validation_errors'].append(str(e))
            return response
        
        # Save metadata to storage
        try:
            save_result = save_band_metadata(band_name, band_metadata)
            response['message'] = save_result.get('message', f'Metadata saved for {band_name}')
            response['file_operations']['metadata_file'] = save_result.get('file_path', '')
            response['file_operations']['backup_created'] = True
            response['file_operations']['last_updated'] = save_result.get('last_updated', '')
            response['file_operations']['merged_with_existing'] = existing_metadata is not None
        except Exception as e:
            response['status'] = 'error'
            response['message'] = f'Failed to save metadata: {str(e)}'
            response['error'] = response['message']  # Add error field for test compatibility
            return response
        
        # Update collection index
        try:
            index = load_collection_index()
            band_entry_existed = False
            
            if index is None:
                # Create new collection index if it doesn't exist
                from src.models.collection import CollectionIndex
                index = CollectionIndex()
            
            # Check if band already exists
            for band_entry in index.bands:
                if band_entry.name == band_name:
                    band_entry_existed = True
                    # Update existing band entry
                    band_entry.albums_count = band_metadata.albums_count
                    band_entry.local_albums_count = band_metadata.local_albums_count
                    band_entry.missing_albums_count = band_metadata.missing_albums_count
                    band_entry.has_metadata = True
                    band_entry.last_updated = band_metadata.last_updated
                    break
            else:
                # Band doesn't exist, create new entry
                from src.models.collection import BandIndexEntry
                new_entry = BandIndexEntry(
                    name=band_name,
                    albums_count=band_metadata.albums_count,
                    local_albums_count=band_metadata.local_albums_count,
                    folder_path=band_name,
                    missing_albums_count=band_metadata.missing_albums_count,
                    has_metadata=True
                )
                index.bands.append(new_entry)
            
            # Save updated index
            update_result = update_collection_index(index)
            if update_result.get('status') == 'success':
                response['collection_sync']['index_updated'] = True
                response['collection_sync']['band_entry_created'] = not band_entry_existed
                response['collection_sync']['band_entry_found'] = band_entry_existed
            else:
                response['collection_sync']['index_errors'].append(update_result.get('error', 'Unknown error'))
                
        except Exception as e:
            response['collection_sync']['index_errors'].append(f'Index update failed: {str(e)}')
        
        # Build band info summary
        response['band_info'] = {
            'band_name': band_metadata.band_name,
            'albums_count': band_metadata.albums_count,
            'missing_albums_count': band_metadata.missing_albums_count,
            'completion_percentage': round((band_metadata.local_albums_count / band_metadata.albums_count * 100) if band_metadata.albums_count > 0 else 100.0, 1),
            'has_analysis': band_metadata.analyze is not None,
            'genre_count': len(band_metadata.genres) if band_metadata.genres else 0,
            'members_count': len(band_metadata.members) if band_metadata.members else 0,
            'has_description': bool(band_metadata.description),
            'albums': [
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
        }
        
        # Add tool info for compatibility
        response['tool_info'] = {
            'tool_name': 'save_band_metadata',
            'version': self.version,
            'execution_time': datetime.now(timezone.utc).isoformat(),
            'parameters_used': {'band_name': band_name, 'metadata_fields': list(metadata.keys())}
        }
        
        return response


# Create handler instance
_handler = SaveBandMetadataHandler()

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
    return _handler.execute(band_name=band_name, metadata=metadata)