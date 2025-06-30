#!/usr/bin/env python3
"""
Music Collection MCP Server - Save Band Metadata Tool

This module contains the save_band_metadata_tool implementation.
"""

from typing import Any, Dict
from datetime import datetime, timezone

from ..mcp_instance import mcp
from ..base_handlers import BaseToolHandler

# Import tool implementation - using absolute imports
from src.core.tools.storage import save_band_metadata, load_band_metadata, load_collection_index, update_collection_index
from src.models.band import BandMetadata
from src.models.collection import BandIndexEntry


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
        
        # If input does NOT include 'albums', preserve existing albums and albums_missing
        if 'albums' not in metadata or not isinstance(metadata.get('albums'), list):
            if existing_metadata is not None:
                # Preserve previous albums and albums_missing
                metadata['albums'] = [a.dict() if hasattr(a, 'dict') else dict(a) for a in getattr(existing_metadata, 'albums', [])]
                metadata['albums_missing'] = [a.dict() if hasattr(a, 'dict') else dict(a) for a in getattr(existing_metadata, 'albums_missing', [])]
            else:
                # No albums provided and no existing metadata, set to empty
                metadata['albums'] = []
                metadata['albums_missing'] = []
        else:
            # --- Old format conversion: only if any album has 'missing' field ---
            input_albums = metadata.get('albums', [])
            if any(isinstance(album, dict) and 'missing' in album for album in input_albums):
                albums_local = []
                albums_missing = []
                for album in input_albums:
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
                input_albums = albums_local + albums_missing  # Rebuild input for next step
                # Do not set metadata['albums'] yet; let the next step handle it

            # --- Split input albums into local and missing (by file system) ---
            # Get music root path from config
            from src.di.dependencies import get_config
            from pathlib import Path
            config = get_config()
            music_root = Path(config.MUSIC_ROOT_PATH)
            band_folder = music_root / band_name
            if band_folder.exists():
                for sub in band_folder.iterdir():
                    if sub.is_dir():
                        pass

            # Discover local albums for this band (from folder structure)
            from src.core.tools.scanner import _scan_band_albums
            if band_folder.exists() and band_folder.is_dir():
                local_album_dicts, _ = _scan_band_albums(band_folder)
            else:
                local_album_dicts = []

            def album_key(album):
                # Normalize type and edition for matching
                album_name = album.get('album_name', '').strip().lower()
                year = str(album.get('year', '')).strip()
                # Default type to 'Album' if missing or empty
                type_val = album.get('type', '').strip()
                if not type_val:
                    type_val = 'Album'
                type_val = type_val.lower()
                # Default edition to '' if missing
                edition = album.get('edition', '').strip().lower() if album.get('edition') else ''
                return (album_name, year, type_val, edition)

            # Log local album keys
            local_album_keys = set()
            for a in local_album_dicts:
                k = album_key(a)
                local_album_keys.add(k)

            # Log input album keys
            for a in input_albums:
                k = album_key(a)

            albums_local = []
            albums_missing = []
            seen_keys = set()
            for album in input_albums:
                key = album_key(album)
                if key in seen_keys:
                    continue  # Prevent duplicates
                seen_keys.add(key)
                if key in local_album_keys:
                    albums_local.append(album)
                else:
                    albums_missing.append(album)

            # --- Final deduplication: ensure no album appears in both arrays ---
            local_keys = set(album_key(a) for a in albums_local)
            albums_missing = [a for a in albums_missing if album_key(a) not in local_keys]

            metadata['albums'] = albums_local
            metadata['albums_missing'] = albums_missing
        
        # Add band_name to metadata if not present
        if 'band_name' not in metadata:
            metadata['band_name'] = band_name
        
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
    Save band metadata to the local storage.

    =================================
    The MCP client must send exactly 2 parameters:

    1. band_name (string): The exact name of the band (e.g., "Pink Floyd", "The Beatles")
    2. metadata (object): A JSON object containing the band's metadata following the schema below

    **IMPORTANT:**
    - The client should send a *full* `albums` array (the complete discography, both local and missing albums).
    - The server will automatically split this into local and missing albums based on what is present in the file system.

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
                "albums": [
                    {
                        "album_name": "Wish You Were Here",
                        "year": "1975",
                        "track_count": 5,
                        "type": "Album",
                        "genres": ["Progressive Rock", "Psychedelic Rock"]
                    },
                    {
                        "album_name": "Animals",
                        "year": "1977",
                        "track_count": 5,
                        "type": "Album",
                        "genres": ["Progressive Rock", "Art Rock"]
                    }
                ]
            }
        }
    }

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
    - albums (array): List of all albums (local and missing) for the band (see below)

    ALBUMS STRUCTURE:
    =================
    - The client sends a single `albums` array containing all known albums for the band (local and missing).
    - The server will split this into local and missing albums based on the file system.
    - Do NOT send `albums_missing` (deprecated).

    ALBUM SCHEMA (for items in albums array):
    =========================================
    REQUIRED:
    - album_name (string): Name of the album
    - year (string): Release year in "YYYY" format
    - track_count (integer): Number of tracks (must be >= 0)
    - genres (array of strings): Album-specific genres (can differ from band genres)
    - type (string): Album type - "Album", "EP", "Live", "Demo", "Compilation", "Single", "Instrumental", "Split"
    - edition (string): Edition info like "Deluxe Edition", "Remastered", etc. (omit for standard releases)
    - duration (string): Album length (format: "43min", "1h 23min", etc.)

    COMPLETE EXAMPLE of METADATA JSON:
    ==================================
    {
        "formed": "1965",
        "genres": ["Progressive Rock", "Psychedelic Rock", "Art Rock"],
        "origin": "London, England",
        "members": ["David Gilmour", "Roger Waters", "Nick Mason", "Richard Wright", "Syd Barrett"],
        "description": "English rock band formed in London in 1965. Achieved international acclaim with their progressive and psychedelic music.",
        "albums": [
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
    ❌ Using "albums_missing" (deprecated, will be ignored)
    ❌ Using old "missing" field in albums (now use only the full `albums` array)
    ❌ Using "tracks_count" (should be "track_count")
    ❌ Missing required album fields (album_name, year, track_count)
    ❌ Using integer for album year (should be string "1973")
    ❌ Negative track_count (must be >= 0)
    ❌ Invalid album type (must be: Album, EP, Live, Demo, Compilation, Single, Instrumental, Split)

    VALIDATION NOTES:
    ================
    - All year fields must be 4-digit strings (e.g., "1975", not 1975)
    - Members array should include all members (past and present) as flat list
    - Duration format is flexible but should include time unit (min, h, etc.)
    - Genres should be specific and accurate music genres
    - The old "missing" field in individual albums is no longer used or supported
    - The server will split the albums into local/missing based on the file system
    """
    return _handler.execute(band_name=band_name, metadata=metadata)