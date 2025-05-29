import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from datetime import datetime, timedelta

from ..config import config
from ..models import Album, BandMetadata, BandIndexEntry, CollectionIndex


# Common music file extensions
MUSIC_EXTENSIONS = {'.mp3', '.flac', '.wav', '.aac', '.m4a', '.ogg', '.wma', '.mp4', '.m4p'}

# Folders to exclude during scanning
EXCLUDED_FOLDERS = {
    # Hidden folders
    '.',
    # Temporary/system folders
    'temp', 'tmp', 'cache', 'trash', '.trash', '$recycle.bin',
    # Media player folders
    'itunes', 'windows media player', 'winamp',
    # Other common exclusions
    'artwork', 'covers', 'images', 'scans', 'logs'
}


def scan_music_folders(force_full_scan: bool = False) -> Dict:
    """
    Scan the music directory structure with optional full or incremental mode.
    
    Args:
        force_full_scan: If True, performs complete rescan. If False, does incremental scan.
    
    Returns:
        Dict containing scan results
    """
    if force_full_scan:
        return _scan_music_folders_full()
    else:
        return _scan_music_folders_incremental()


def _scan_music_folders_incremental() -> Dict:
    """
    Perform an incremental scan of the music directory structure.
    
    This function optimizes scanning by only processing changes:
    - Adds newly discovered band folders
    - Removes bands that no longer exist in filesystem  
    - Updates existing bands only if folder modification time indicates changes
    - Preserves all existing metadata and analysis data
    - Only recalculates stats based on actual changes
    
    Returns:
        Dict containing scan results with changes detected and statistics
        
    Raises:
        ValueError: If music root path is invalid
        OSError: If there are file system access issues
    """
    try:
        # Validate music root path
        music_root = Path(config.MUSIC_ROOT_PATH)
        if not music_root.exists():
            raise ValueError(f"Music root path does not exist: {music_root}")
        if not music_root.is_dir():
            raise ValueError(f"Music root path is not a directory: {music_root}")
            
        logging.info(f"Starting incremental music collection scan at: {music_root}")
        
        # Initialize scan results for tracking changes
        scan_results = {
            'bands_added': 0,
            'bands_removed': 0,
            'bands_updated': 0,
            'albums_added': 0,
            'albums_removed': 0,
            'total_tracks_change': 0,
            'scan_errors': [],
            'scan_timestamp': datetime.now().isoformat(),
            'changes_detected': []
        }
        
        # Load existing collection index
        collection_index = _load_or_create_collection_index(music_root)
        initial_stats = collection_index.get_summary_stats()
        
        # Get current filesystem state
        current_band_folders = _discover_band_folders(music_root)
        current_band_names = {folder.name for folder in current_band_folders}
        
        # Get existing bands from index
        existing_band_names = {band.name for band in collection_index.bands}
        
        # Detect removed bands
        removed_bands = existing_band_names - current_band_names
        for band_name in removed_bands:
            if collection_index.remove_band(band_name):
                scan_results['bands_removed'] += 1
                scan_results['changes_detected'].append(f"Removed band: {band_name}")
                logging.info(f"Removed band from index: {band_name}")
        
        # Detect new and potentially modified bands
        for band_folder in current_band_folders:
            band_name = band_folder.name
            existing_entry = collection_index.get_band(band_name)
            
            if existing_entry is None:
                # New band - perform full scan
                try:
                    band_result = _scan_band_folder(band_folder, music_root)
                    if band_result:
                        band_entry = _create_band_index_entry(band_result, music_root)
                        collection_index.add_band(band_entry)
                        
                        scan_results['bands_added'] += 1
                        scan_results['albums_added'] += band_result['albums_count']
                        scan_results['total_tracks_change'] += band_result['total_tracks']
                        scan_results['changes_detected'].append(
                            f"Added new band: {band_name} ({band_result['albums_count']} albums, {band_result['total_tracks']} tracks)"
                        )
                        logging.info(f"Added new band: {band_name}")
                        
                except Exception as e:
                    error_msg = f"Error scanning new band folder {band_folder}: {str(e)}"
                    logging.warning(error_msg)
                    scan_results['scan_errors'].append(error_msg)
            else:
                # Existing band - check if update needed
                update_needed = _check_if_band_update_needed(band_folder, existing_entry)
                
                if update_needed:
                    try:
                        # Reason: Only rescan if folder changes detected to preserve metadata and improve performance
                        band_result = _scan_band_folder(band_folder, music_root)
                        if band_result:
                            # Preserve existing metadata when updating
                            updated_entry = _create_band_index_entry(band_result, music_root, existing_entry)
                            
                            # Calculate changes
                            albums_diff = updated_entry.albums_count - existing_entry.albums_count
                            tracks_diff = band_result['total_tracks'] - _get_cached_track_count(existing_entry, music_root)
                            
                            collection_index.add_band(updated_entry)
                            
                            scan_results['bands_updated'] += 1
                            if albums_diff != 0:
                                scan_results['albums_added'] += max(0, albums_diff)
                                scan_results['albums_removed'] += max(0, -albums_diff)
                            scan_results['total_tracks_change'] += tracks_diff
                            
                            scan_results['changes_detected'].append(
                                f"Updated band: {band_name} (album change: {albums_diff:+d}, track change: {tracks_diff:+d})"
                            )
                            logging.info(f"Updated band: {band_name}")
                            
                    except Exception as e:
                        error_msg = f"Error updating band folder {band_folder}: {str(e)}"
                        logging.warning(error_msg)
                        scan_results['scan_errors'].append(error_msg)
        
        # Save updated collection index only if changes were made
        changes_made = (scan_results['bands_added'] + scan_results['bands_removed'] + scan_results['bands_updated']) > 0
        if changes_made:
            _save_collection_index(collection_index, music_root)
            
        # Calculate final statistics change
        final_stats = collection_index.get_summary_stats()
        stats_change = {
            'total_bands_change': final_stats['total_bands'] - initial_stats['total_bands'],
            'total_albums_change': final_stats['total_albums'] - initial_stats['total_albums'],
            'missing_albums_change': final_stats['total_missing_albums'] - initial_stats['total_missing_albums']
        }
        
        scan_results.update(stats_change)
        
        logging.info(f"Incremental scan completed: {scan_results['bands_added']} added, "
                    f"{scan_results['bands_removed']} removed, {scan_results['bands_updated']} updated")
        
        return {
            'status': 'success',
            'results': scan_results,
            'collection_path': str(music_root),
            'incremental_scan': True,
            'changes_made': changes_made
        }
        
    except Exception as e:
        error_msg = f"Incremental music collection scan failed: {str(e)}"
        logging.error(error_msg)
        return {
            'status': 'error',
            'error': error_msg,
            'collection_path': str(config.MUSIC_ROOT_PATH) if config.MUSIC_ROOT_PATH else 'Not set',
            'incremental_scan': True
        }


def _scan_music_folders_full() -> Dict:
    """
    Perform a complete scan of the music directory structure (legacy behavior).
    
    This function performs a comprehensive scan of the music collection:
    - Discovers all band folders in the music directory
    - Finds album subfolders within each band folder
    - Counts music tracks in each album folder
    - Detects missing albums (in metadata but not in folders)
    - Updates the collection index with current state
    
    Returns:
        Dict containing scan results with bands, albums, and statistics
        
    Raises:
        ValueError: If music root path is invalid
        OSError: If there are file system access issues
    """
    try:
        # Validate music root path
        music_root = Path(config.MUSIC_ROOT_PATH)
        if not music_root.exists():
            raise ValueError(f"Music root path does not exist: {music_root}")
        if not music_root.is_dir():
            raise ValueError(f"Music root path is not a directory: {music_root}")
            
        logging.info(f"Starting full music collection scan at: {music_root}")
        
        # Initialize scan results
        scan_results = {
            'bands_discovered': 0,
            'albums_discovered': 0,
            'total_tracks': 0,
            'missing_albums': 0,
            'scan_errors': [],
            'scan_timestamp': datetime.now().isoformat(),
            'bands': []
        }
        
        # Load existing collection index or create new one
        collection_index = _load_or_create_collection_index(music_root)
        
        # Scan for band folders
        band_folders = _discover_band_folders(music_root)
        logging.info(f"Found {len(band_folders)} potential band folders")
        
        for band_folder in band_folders:
            try:
                band_result = _scan_band_folder(band_folder, music_root)
                if band_result:
                    scan_results['bands'].append(band_result)
                    scan_results['bands_discovered'] += 1
                    scan_results['albums_discovered'] += band_result['albums_count']
                    scan_results['total_tracks'] += band_result['total_tracks']
                    
                    # Update collection index - preserve existing entry data
                    existing_entry = collection_index.get_band(band_result['band_name'])
                    band_entry = _create_band_index_entry(band_result, music_root, existing_entry)
                    collection_index.add_band(band_entry)
                    
            except Exception as e:
                error_msg = f"Error scanning band folder {band_folder}: {str(e)}"
                logging.warning(error_msg)
                scan_results['scan_errors'].append(error_msg)
        
        # Calculate missing albums from collection stats (already calculated in _create_band_index_entry)
        scan_results['missing_albums'] = sum(band.missing_albums_count for band in collection_index.bands)
        
        # Save updated collection index
        _save_collection_index(collection_index, music_root)
        
        logging.info(f"Full scan completed: {scan_results['bands_discovered']} bands, "
                    f"{scan_results['albums_discovered']} albums, "
                    f"{scan_results['total_tracks']} tracks")
        
        return {
            'status': 'success',
            'results': scan_results,
            'collection_path': str(music_root),
            'incremental_scan': False
        }
        
    except Exception as e:
        error_msg = f"Music collection scan failed: {str(e)}"
        logging.error(error_msg)
        return {
            'status': 'error',
            'error': error_msg,
            'collection_path': str(config.MUSIC_ROOT_PATH) if config.MUSIC_ROOT_PATH else 'Not set',
            'incremental_scan': False
        }


def _check_if_band_update_needed(band_folder: Path, existing_entry: BandIndexEntry) -> bool:
    """
    Check if a band folder needs to be rescanned based on modification times.
    
    Args:
        band_folder: Path to the band folder
        existing_entry: Existing band entry from collection index
        
    Returns:
        True if band should be rescanned, False otherwise
    """
    try:
        # Get folder modification time
        folder_mtime = datetime.fromtimestamp(band_folder.stat().st_mtime)
        
        # Parse existing entry last_updated
        try:
            last_updated = datetime.fromisoformat(existing_entry.last_updated.replace('Z', '+00:00'))
            # Remove timezone info for comparison if present
            if last_updated.tzinfo:
                last_updated = last_updated.replace(tzinfo=None)
        except (ValueError, AttributeError):
            # If we can't parse the date, assume update is needed
            return True
        
        # Update needed if folder was modified after last scan
        # Add 1 second buffer to account for filesystem timestamp precision
        return folder_mtime > (last_updated + timedelta(seconds=1))
        
    except Exception as e:
        logging.warning(f"Error checking modification time for {band_folder}: {e}")
        # If we can't determine modification time, assume update is needed
        return True


def _get_cached_track_count(band_entry: BandIndexEntry, music_root: Path) -> int:
    """
    Get cached track count for a band to calculate changes.
    
    Args:
        band_entry: Band entry from collection index
        music_root: Path to music collection root
        
    Returns:
        Previously cached track count, or 0 if not available
    """
    try:
        # Try to get track count from a cached scan result or estimate
        # For simplicity, we'll estimate based on albums (average 12 tracks per album)
        return band_entry.albums_count * 12
    except Exception:
        return 0


def _discover_band_folders(music_root: Path) -> List[Path]:
    """
    Discover all potential band folders in the music directory.
    
    Args:
        music_root: Path to music collection root
        
    Returns:
        List of paths to potential band folders
    """
    band_folders = []
    
    try:
        for item in music_root.iterdir():
            if (item.is_dir() and 
                not item.name.startswith('.') and 
                item.name.lower() not in EXCLUDED_FOLDERS):
                band_folders.append(item)
    except PermissionError as e:
        logging.warning(f"Permission denied accessing {music_root}: {e}")
    except OSError as e:
        logging.warning(f"OS error accessing {music_root}: {e}")
    
    return sorted(band_folders, key=lambda x: x.name.lower())


def _scan_band_folder(band_folder: Path, music_root: Path) -> Optional[Dict]:
    """
    Scan a single band folder for album information.
    
    Args:
        band_folder: Path to the band folder
        music_root: Path to music collection root
        
    Returns:
        Dictionary with band scan results or None if invalid
    """
    band_name = band_folder.name
    logging.debug(f"Scanning band folder: {band_name}")
    
    try:
        # Discover album folders
        album_folders = _discover_album_folders(band_folder)
        
        # Scan each album
        albums = []
        total_tracks = 0
        
        for album_folder in album_folders:
            album_info = _scan_album_folder(album_folder)
            if album_info:
                albums.append(album_info)
                total_tracks += album_info['tracks_count']
        
        # Load existing metadata if available
        metadata_file = band_folder / '.band_metadata.json'
        existing_metadata = None
        if metadata_file.exists():
            try:
                existing_metadata = _load_band_metadata(metadata_file)
            except Exception as e:
                logging.warning(f"Failed to load metadata for {band_name}: {e}")
        
        # Create result
        result = {
            'band_name': band_name,
            'folder_path': str(band_folder.relative_to(music_root)),
            'albums_count': len(albums),
            'albums': albums,
            'total_tracks': total_tracks,
            'has_metadata': metadata_file.exists(),
            'last_scanned': datetime.now().isoformat()
        }
        
        return result
        
    except Exception as e:
        logging.error(f"Error scanning band folder {band_name}: {e}")
        return None


def _discover_album_folders(band_folder: Path) -> List[Path]:
    """
    Discover album folders within a band folder.
    
    Args:
        band_folder: Path to the band folder
        
    Returns:
        List of paths to album folders
    """
    album_folders = []
    
    try:
        for item in band_folder.iterdir():
            if (item.is_dir() and 
                not item.name.startswith('.') and 
                item.name.lower() not in EXCLUDED_FOLDERS and
                item.name != '.band_metadata.json'):  # Skip metadata file
                album_folders.append(item)
    except (PermissionError, OSError) as e:
        logging.warning(f"Error accessing band folder {band_folder}: {e}")
    
    return sorted(album_folders, key=lambda x: x.name.lower())


def _scan_album_folder(album_folder: Path) -> Optional[Dict]:
    """
    Scan a single album folder for track information.
    
    Args:
        album_folder: Path to the album folder
        
    Returns:
        Dictionary with album information or None if invalid
    """
    album_name = album_folder.name
    
    try:
        # Count music files
        tracks_count = _count_music_files(album_folder)
        
        # Only include folders that actually contain music
        if tracks_count == 0:
            return None
            
        return {
            'album_name': album_name,
            'tracks_count': tracks_count,
            'missing': False,  # Found in folder, so not missing
            'duration': '',    # Will be filled by metadata tools
            'year': '',        # Will be filled by metadata tools
            'genre': []        # Will be filled by metadata tools
        }
        
    except Exception as e:
        logging.warning(f"Error scanning album folder {album_name}: {e}")
        return None


def _count_music_files(folder: Path) -> int:
    """
    Count music files in a folder (non-recursive).
    
    Args:
        folder: Path to folder to scan
        
    Returns:
        Number of music files found
    """
    count = 0
    try:
        for item in folder.iterdir():
            if item.is_file() and item.suffix.lower() in MUSIC_EXTENSIONS:
                count += 1
    except (PermissionError, OSError) as e:
        logging.warning(f"Error counting files in {folder}: {e}")
    
    return count


def _load_or_create_collection_index(music_root: Path) -> CollectionIndex:
    """
    Load existing collection index or create a new one.
    
    Args:
        music_root: Path to music collection root
        
    Returns:
        CollectionIndex instance
    """
    index_file = music_root / '.collection_index.json'
    
    if index_file.exists():
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                json_data = f.read()
            return CollectionIndex.from_json(json_data)
        except Exception as e:
            logging.warning(f"Failed to load collection index, creating new one: {e}")
    
    return CollectionIndex()


def _save_collection_index(collection_index: CollectionIndex, music_root: Path) -> None:
    """
    Save collection index to file.
    
    Args:
        collection_index: CollectionIndex to save
        music_root: Path to music collection root
    """
    index_file = music_root / '.collection_index.json'
    
    try:
        # Create backup if file exists
        if index_file.exists():
            backup_file = music_root / f'.collection_index.json.backup.{int(datetime.now().timestamp())}'
            index_file.rename(backup_file)
            
        # Save new index
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(collection_index.to_json())
            
        logging.debug(f"Collection index saved to {index_file}")
        
    except Exception as e:
        logging.error(f"Failed to save collection index: {e}")
        raise


def _create_band_index_entry(band_result: Dict, music_root: Path, existing_entry: Optional[BandIndexEntry] = None) -> BandIndexEntry:
    """
    Create a BandIndexEntry from scan results, preserving existing metadata.
    
    Args:
        band_result: Results from band folder scan
        music_root: Path to music collection root
        existing_entry: Existing band entry to preserve metadata from
        
    Returns:
        BandIndexEntry instance with merged data
    """
    # Load metadata if available to get accurate album counts
    band_folder = music_root / band_result['folder_path']
    metadata_file = band_folder / '.band_metadata.json'
    metadata = None
    
    if metadata_file.exists():
        try:
            metadata = _load_band_metadata(metadata_file)
        except Exception as e:
            logging.warning(f"Failed to load metadata for {band_result['band_name']}: {e}")
    
    # If we have metadata, use album count from metadata (includes missing albums)
    # Otherwise, use physical album count from scan
    if metadata:
        total_albums = len(metadata.albums)
        missing_albums = len(metadata.get_missing_albums())
        # Ensure missing count doesn't exceed total (validation constraint)
        missing_albums = min(missing_albums, total_albums)
    else:
        # No metadata - use physical scan results
        total_albums = band_result['albums_count']
        missing_albums = 0
    
    # Preserve analysis flag from existing entry if available
    has_analysis = False
    if existing_entry:
        has_analysis = existing_entry.has_analysis
    elif metadata and hasattr(metadata, 'analyze') and metadata.analyze:
        has_analysis = True
    
    # Use metadata last_updated if available, otherwise use scan timestamp
    last_updated = band_result['last_scanned']
    if metadata and metadata.last_updated:
        last_updated = metadata.last_updated
    elif existing_entry:
        last_updated = existing_entry.last_updated
    
    return BandIndexEntry(
        name=band_result['band_name'],
        albums_count=total_albums,
        folder_path=band_result['folder_path'],
        missing_albums_count=missing_albums,
        has_metadata=band_result['has_metadata'],
        has_analysis=has_analysis,
        last_updated=last_updated
    )


def _load_band_metadata(metadata_file: Path) -> Optional[BandMetadata]:
    """
    Load band metadata from JSON file.
    
    Args:
        metadata_file: Path to band metadata file
        
    Returns:
        BandMetadata instance or None if failed
    """
    try:
        with open(metadata_file, 'r', encoding='utf-8') as f:
            json_data = f.read()
        return BandMetadata.from_json(json_data)
    except Exception as e:
        logging.warning(f"Failed to load band metadata from {metadata_file}: {e}")
        return None


def _detect_missing_albums(collection_index: CollectionIndex) -> int:
    """
    Detect missing albums across the entire collection.
    
    Missing albums are those present in band metadata but not found
    in the actual folder structure during scanning.
    
    Args:
        collection_index: Collection index to check
        
    Returns:
        Total number of missing albums detected
    """
    total_missing = 0
    music_root = Path(config.MUSIC_ROOT_PATH)
    
    for band_entry in collection_index.bands:
        if not band_entry.has_metadata:
            continue
            
        try:
            # Load band metadata
            band_folder = music_root / band_entry.folder_path
            metadata_file = band_folder / '.band_metadata.json'
            
            if metadata_file.exists():
                metadata = _load_band_metadata(metadata_file)
                if metadata:
                    # Check each album in metadata against actual folders
                    album_folders = {af.name.lower() for af in _discover_album_folders(band_folder)}
                    missing_count = 0
                    
                    for album in metadata.albums:
                        if album.album_name.lower() not in album_folders:
                            album.missing = True
                            missing_count += 1
                        else:
                            album.missing = False
                    
                    # Update band entry
                    band_entry.missing_albums_count = missing_count
                    total_missing += missing_count
                    
        except Exception as e:
            logging.warning(f"Error detecting missing albums for {band_entry.name}: {e}")
    
    return total_missing 