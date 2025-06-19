# Standard library imports
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Local imports
from src.di import get_config
from src.tools.performance import (
    BatchFileOperations,
    ProgressReporter,
    performance_monitor,
    track_operation,
    get_performance_summary,
)
from src.models import (
    Album,
    AlbumFolderParser,
    AlbumType,
    BandIndexEntry,
    BandMetadata,
    BandStructureDetector,
    CollectionIndex,
    ComplianceValidator,
    FolderCompliance,
)


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


@performance_monitor("music_collection_scan")
def scan_music_folders() -> Dict:
    """
    Scan the music directory structure to discover bands and albums, detecting all changes.
    
    This function performs a comprehensive scan of the music collection:
    - Discovers all band folders in the music directory
    - Detects new bands that have been added to the collection
    - Identifies bands that have been removed from the collection
    - Discovers changes in album structure (new albums, removed albums, renamed albums)
    - Finds album subfolders within each band folder
    - Counts music tracks in each album folder
    - Detects missing albums (in metadata but not in folders)
    - Updates the collection index with current state
    
    Returns:
        Dict containing scan results with bands, albums, and statistics including:
        - status: 'success' or 'error'
        - results: Dict with scan statistics and detailed change information
        - collection_path: Path to the scanned music collection
        - changes_made: True if any changes were detected and saved
        - performance_metrics: Performance metrics for the scan operation
        
    Raises:
        ValueError: If music root path is invalid
        OSError: If there are file system access issues
    """
    try:
        # Validate and prepare for scanning
        music_root, collection_index = _prepare_scan_environment()
        
        # Analyze collection changes
        current_band_folders, scan_results = _analyze_collection_changes(music_root, collection_index)
        
        # Process all band folders with progress reporting
        _process_band_folders(current_band_folders, music_root, collection_index, scan_results)
        
        # Finalize scan results with performance metrics
        result = _finalize_scan_results(music_root, collection_index, scan_results)
        
        # Add performance metrics to result
        result['performance_metrics'] = get_performance_summary()
        
        return result
        
    except Exception as e:
        error_msg = f"Music collection scan failed: {str(e)}"
        logging.error(error_msg)
        return {
            'status': 'error',
            'error': error_msg,
            'collection_path': str(get_config().MUSIC_ROOT_PATH) if get_config().MUSIC_ROOT_PATH else 'Not set',
            'performance_metrics': get_performance_summary()
        }


def _prepare_scan_environment() -> Tuple[Path, CollectionIndex]:
    """
    Validate music root path and load collection index.
    
    Returns:
        Tuple of (music_root_path, collection_index)
        
    Raises:
        ValueError: If music root path is invalid
    """
    config = get_config()
    music_root = Path(config.MUSIC_ROOT_PATH)
    if not music_root.exists():
        raise ValueError(f"Music root path does not exist: {music_root}")
    if not music_root.is_dir():
        raise ValueError(f"Music root path is not a directory: {music_root}")
        
    logging.info(f"Starting comprehensive music collection scan at: {music_root}")
    
    # Load existing collection index to detect changes
    collection_index = _load_or_create_collection_index(music_root)
    
    return music_root, collection_index


def _analyze_collection_changes(music_root: Path, collection_index: CollectionIndex) -> Tuple[List[Path], Dict]:
    """
    Analyze changes in the collection by comparing filesystem to existing index.
    
    Args:
        music_root: Path to music collection root
        collection_index: Current collection index
        
    Returns:
        Tuple of (current_band_folders, scan_results)
    """
    # Get current filesystem state vs existing index state
    current_band_folders = _discover_band_folders(music_root)
    current_band_names = {folder.name for folder in current_band_folders}
    existing_band_names = {band.name for band in collection_index.bands}
    
    # Initialize scan results tracking structure
    scan_results = {
        'bands_discovered': len(current_band_folders),
        'bands_added': len(current_band_names - existing_band_names),
        'bands_removed': len(existing_band_names - current_band_names),
        'bands_updated': 0,
        'albums_discovered': 0,
        'total_tracks': 0,
        'missing_albums': 0,
        'scan_errors': [],
        'scan_timestamp': datetime.now().isoformat(),
        'changes_detected': [],
        'bands': []
    }
    
    # Process removed bands (exist in index but not in filesystem)
    _process_removed_bands(collection_index, current_band_names, existing_band_names, scan_results)
    
    return current_band_folders, scan_results


def _process_removed_bands(collection_index: CollectionIndex, current_band_names: Set[str], 
                          existing_band_names: Set[str], scan_results: Dict) -> None:
    """
    Process bands that have been removed from the filesystem.
    
    Args:
        collection_index: Collection index to update
        current_band_names: Set of band names currently in filesystem
        existing_band_names: Set of band names in existing index
        scan_results: Scan results dictionary to update
    """
    removed_bands = existing_band_names - current_band_names
    for band_name in removed_bands:
        if collection_index.remove_band(band_name):
            scan_results['changes_detected'].append(f"Removed band: {band_name}")
            logging.info(f"Removed band from index: {band_name}")


def _process_band_folders(current_band_folders: List[Path], music_root: Path, 
                         collection_index: CollectionIndex, scan_results: Dict) -> None:
    """
    Process all current band folders and detect changes with progress reporting.
    
    Args:
        current_band_folders: List of band folder paths
        music_root: Path to music collection root
        collection_index: Collection index to update
        scan_results: Scan results dictionary to update
    """
    num_bands = len(current_band_folders)
    logging.info(f"Scanning {num_bands} band folders")
    
    # Initialize progress reporter for large collections
    progress_reporter = None
    if num_bands > 50:  # Use progress reporting for larger collections
        progress_reporter = ProgressReporter(num_bands, "Band Folder Scanning")
    
    with track_operation("process_band_folders", total_bands=num_bands) as metrics:
        for i, band_folder in enumerate(current_band_folders):
            try:
                # Scan individual band folder for albums and tracks
                band_result = _scan_band_folder(band_folder, music_root)
                if not band_result:
                    continue
                    
                # Add band results to overall scan results
                scan_results['bands'].append(band_result)
                scan_results['albums_discovered'] += band_result['albums_count']
                scan_results['total_tracks'] += band_result['total_tracks']
                
                # Detect if this is a new band or an updated existing band
                _detect_band_changes(collection_index, band_result, scan_results)
                
                # Update collection index with current band state
                band_entry = _create_band_index_entry(band_result, music_root, 
                                                     collection_index.get_band(band_result['band_name']))
                collection_index.add_band(band_entry)
                
                # Update progress tracking
                metrics.items_processed += 1
                if progress_reporter:
                    progress_reporter.update()
                
            except Exception as e:
                error_msg = f"Error scanning band folder {band_folder}: {str(e)}"
                logging.warning(error_msg)
                scan_results['scan_errors'].append(error_msg)
                metrics.errors += 1
                if progress_reporter:
                    progress_reporter.update()  # Still update progress on error
        
        # Finish progress reporting
        if progress_reporter:
            progress_reporter.finish()


def _detect_band_changes(collection_index: CollectionIndex, band_result: Dict, scan_results: Dict) -> None:
    """
    Detect if a band is new or has been updated.
    
    Args:
        collection_index: Collection index to check against
        band_result: Results from band folder scan
        scan_results: Scan results dictionary to update
    """
    existing_entry = collection_index.get_band(band_result['band_name'])
    if existing_entry is None:
        # This is a completely new band
        scan_results['changes_detected'].append(
            f"Added new band: {band_result['band_name']} ({band_result['albums_count']} albums)"
        )
    else:
        # Check for changes in existing band (album count differences)
        if existing_entry.albums_count != band_result['albums_count']:
            album_diff = band_result['albums_count'] - existing_entry.albums_count
            scan_results['bands_updated'] += 1
            scan_results['changes_detected'].append(
                f"Updated band: {band_result['band_name']} (album change: {album_diff:+d})"
            )


def _finalize_scan_results(music_root: Path, collection_index: CollectionIndex, 
                          scan_results: Dict) -> Dict:
    """
    Finalize scan results and save collection index.
    
    Args:
        music_root: Path to music collection root
        collection_index: Updated collection index
        scan_results: Scan results dictionary
        
    Returns:
        Final scan results dictionary
    """
    # Calculate missing albums from updated collection stats
    scan_results['missing_albums'] = sum(band.missing_albums_count for band in collection_index.bands)
    
    # Determine if any changes were detected and need to be saved
    changes_made = (
        scan_results['bands_added'] + 
        scan_results['bands_removed'] + 
        scan_results['bands_updated']
    ) > 0
    
    # Save updated collection index with all changes
    _save_collection_index(collection_index, music_root)
    
    # Log comprehensive scan summary
    logging.info(
        f"Comprehensive scan completed: {scan_results['bands_discovered']} total bands, "
        f"{scan_results['bands_added']} added, {scan_results['bands_removed']} removed, "
        f"{scan_results['bands_updated']} updated, {scan_results['albums_discovered']} albums, "
        f"{scan_results['total_tracks']} tracks"
    )
    
    return {
        'status': 'success',
        'results': scan_results,
        'collection_path': str(music_root),
        'changes_made': changes_made
    }


def _discover_band_folders(music_root: Path) -> List[Path]:
    """
    Discover all potential band folders in the music directory using optimized batch operations.
    
    Args:
        music_root: Path to music collection root
        
    Returns:
        List of paths to potential band folders
    """
    with track_operation("discover_band_folders", music_root=str(music_root)) as metrics:
        try:
            # Use optimized batch scanning for better performance
            all_items = BatchFileOperations.scan_directory_batch(
                music_root, 
                recursive=False, 
                exclude_hidden=True
            )
            
            # Filter for valid band folders
            band_folders = []
            for item in all_items:
                if (item.is_dir() and 
                    not item.name.startswith('.') and 
                    item.name.lower() not in EXCLUDED_FOLDERS):
                    band_folders.append(item)
                    metrics.items_processed += 1
            
            # Log performance info for large collections
            if len(band_folders) > 100:
                logging.info(f"Discovered {len(band_folders)} band folders in {music_root}")
            
            return sorted(band_folders, key=lambda x: x.name.lower())
            
        except PermissionError as e:
            logging.warning(f"Permission denied accessing {music_root}: {e}")
            metrics.errors += 1
            return []
        except OSError as e:
            logging.warning(f"OS error accessing {music_root}: {e}")
            metrics.errors += 1
            return []


def _scan_band_folder(band_folder: Path, music_root: Path) -> Optional[Dict]:
    """
    Scan a single band folder for album information with enhanced metadata detection.
    Also updates or creates .band_metadata.json with folder structure information and local albums.
    
    Args:
        band_folder: Path to the band folder
        music_root: Path to music collection root
        
    Returns:
        Dictionary with band scan results including structure analysis or None if invalid
    """
    band_name = band_folder.name
    logging.debug(f"Scanning band folder: {band_name}")
    
    try:
        # Initialize scanning components and discover albums
        albums, total_tracks = _scan_band_albums(band_folder)
        
        # Detect folder structure and load/create metadata
        folder_structure, metadata = _process_band_metadata(band_folder, band_name, albums)
        
        # Check metadata status
        has_metadata = _check_band_metadata_status(band_folder / '.band_metadata.json', band_name)
        
        # Create result with enhanced information
        return _create_band_scan_result(band_name, band_folder, music_root, albums, 
                                       total_tracks, has_metadata, folder_structure)
        
    except Exception as e:
        logging.error(f"Error scanning band folder {band_name}: {e}")
        return None


def _scan_band_albums(band_folder: Path) -> Tuple[List[Dict], int]:
    """
    Discover and scan all album folders in a band folder.
    
    Args:
        band_folder: Path to the band folder
        
    Returns:
        Tuple of (albums_list, total_tracks_count)
    """
    # Initialize enhanced detection components
    album_parser = AlbumFolderParser()
    compliance_validator = ComplianceValidator()
    
    # Discover album folders (including type folders)
    album_folders = _discover_album_folders_enhanced(band_folder, album_parser)
    
    # Scan each album with enhanced metadata
    albums = []
    total_tracks = 0
    
    for album_folder_info in album_folders:
        album_info = _scan_album_folder_enhanced(album_folder_info, album_parser, compliance_validator)
        if album_info:
            albums.append(album_info)
            total_tracks += album_info['track_count']
    
    return albums, total_tracks


def _process_band_metadata(band_folder: Path, band_name: str, albums: List[Dict]) -> Tuple[Any, Any]:
    """
    Detect folder structure and load/create/update band metadata.
    
    Args:
        band_folder: Path to the band folder
        band_name: Name of the band
        albums: List of discovered albums
        
    Returns:
        Tuple of (folder_structure, metadata)
    """
    # Detect band folder structure
    structure_detector = BandStructureDetector()
    folder_structure = structure_detector.detect_band_structure(str(band_folder))
    
    # Load or create metadata
    metadata = _load_or_create_band_metadata(band_folder, band_name)
    
    # Update metadata with current state
    metadata.folder_structure = folder_structure
    metadata = _synchronize_metadata_with_local_albums(metadata, albums, band_name)
    metadata.update_timestamp()
    
    # Save updated metadata
    _save_band_metadata_file(band_folder, band_name, metadata)
    
    return folder_structure, metadata


def _load_or_create_band_metadata(band_folder: Path, band_name: str):
    """
    Load existing metadata or create new metadata structure.
    
    Args:
        band_folder: Path to the band folder
        band_name: Name of the band
        
    Returns:
        BandMetadata instance
    """
    metadata_file = band_folder / '.band_metadata.json'
    metadata = None
    
    if metadata_file.exists():
        try:
            # Load existing metadata
            from src.tools.storage import JSONStorage
            metadata_dict = JSONStorage.load_json(metadata_file)
            from src.models.band import BandMetadata
            metadata = BandMetadata(**metadata_dict)
            logging.debug(f"Loaded existing metadata for {band_name}")
        except Exception as e:
            logging.warning(f"Failed to load existing metadata for {band_name}: {e}")
            # Will create new metadata below
    
    # Create new metadata if none exists or loading failed
    if metadata is None:
        from src.models.band import BandMetadata
        metadata = BandMetadata(
            band_name=band_name,
            formed="",
            genres=[],
            origin="",
            members=[],
            description="",
            albums=[]
        )
        logging.debug(f"Created new metadata structure for {band_name}")
    
    return metadata


def _save_band_metadata_file(band_folder: Path, band_name: str, metadata) -> None:
    """
    Save band metadata to file.
    
    Args:
        band_folder: Path to the band folder
        band_name: Name of the band
        metadata: BandMetadata instance to save
    """
    metadata_file = band_folder / '.band_metadata.json'
    try:
        from src.tools.storage import JSONStorage
        metadata_dict = metadata.model_dump()
        JSONStorage.save_json(metadata_file, metadata_dict, backup=metadata_file.exists())
        logging.debug(f"Updated metadata with folder structure and local albums for {band_name}")
    except Exception as e:
        logging.warning(f"Failed to save metadata for {band_name}: {e}")
        # Continue with scan even if save fails


def _check_band_metadata_status(metadata_file: Path, band_name: str) -> bool:
    """
    Check if band metadata exists and was properly saved.
    
    Args:
        metadata_file: Path to the metadata file
        band_name: Name of the band
        
    Returns:
        True if metadata exists and was properly saved, False otherwise
    """
    has_metadata = False
    if metadata_file.exists():
        try:
            metadata = _load_band_metadata(metadata_file)
            if metadata:
                has_metadata = metadata.has_metadata_saved()
        except Exception as e:
            logging.warning(f"Failed to validate metadata for {band_name}: {e}")
            has_metadata = False
    
    return has_metadata


def _create_band_scan_result(band_name: str, band_folder: Path, music_root: Path, 
                           albums: List[Dict], total_tracks: int, has_metadata: bool, 
                           folder_structure: Any) -> Dict:
    """
    Create the final band scan result dictionary.
    
    Args:
        band_name: Name of the band
        band_folder: Path to the band folder
        music_root: Path to music collection root
        albums: List of discovered albums
        total_tracks: Total number of tracks
        has_metadata: Whether metadata was properly saved
        folder_structure: Detected folder structure
        
    Returns:
        Dictionary with band scan results
    """
    return {
        'band_name': band_name,
        'folder_path': str(band_folder.relative_to(music_root)),
        'albums_count': len(albums),
        'albums': albums,
        'total_tracks': total_tracks,
        'has_metadata': has_metadata,  # Now uses the has_metadata_saved() method
        'last_scanned': datetime.now().isoformat(),
        'folder_structure': folder_structure.model_dump() if folder_structure else None,
        'album_types_distribution': _calculate_album_types_distribution(albums),
        'compliance_summary': _calculate_compliance_summary(albums)
    }


def _synchronize_metadata_with_local_albums(metadata: 'BandMetadata', local_albums: List[Dict], band_name: str) -> 'BandMetadata':
    """
    Synchronize metadata albums with actual local albums found during scanning.
    
    This function:
    - Updates albums array with local albums found during scanning
    - Moves albums to albums_missing array if they're not found locally
    - Adds new albums found locally that aren't in metadata
    - Preserves existing metadata like year, genres, duration for known albums
    
    Args:
        metadata: BandMetadata object to update
        local_albums: List of album dictionaries found during local scanning
        band_name: Name of the band for logging
        
    Returns:
        Updated BandMetadata object with separated albums arrays
    """
    from src.models.band import Album, AlbumType
    
    logging.debug(f"Synchronizing metadata with {len(local_albums)} local albums for {band_name}")
    
    # Prepare data structures for synchronization
    local_albums_lookup, processed_local_albums = _prepare_album_synchronization(local_albums)
    
    # Process existing albums and separate into local/missing
    updated_local_albums, updated_missing_albums = _process_existing_albums(
        metadata, local_albums_lookup, processed_local_albums, band_name
    )
    
    # Add new local albums not in metadata
    new_local_albums = _process_new_local_albums(
        local_albums, processed_local_albums, band_name
    )
    updated_local_albums.extend(new_local_albums)
    
    # Update metadata with final results
    return _update_metadata_with_synchronized_albums(
        metadata, updated_local_albums, updated_missing_albums, band_name
    )


def _prepare_album_synchronization(local_albums: List[Dict]) -> Tuple[Dict[str, Dict], set]:
    """
    Prepare data structures needed for album synchronization.
    
    Args:
        local_albums: List of album dictionaries found during local scanning
        
    Returns:
        Tuple of (local_albums_lookup, processed_local_albums_set)
    """
    # Create a lookup of local albums by name (case-insensitive)
    local_albums_lookup = {album['album_name'].lower(): album for album in local_albums}
    
    # Track which local albums we've processed
    processed_local_albums = set()
    
    return local_albums_lookup, processed_local_albums


def _process_existing_albums(metadata: 'BandMetadata', local_albums_lookup: Dict[str, Dict], 
                           processed_local_albums: set, band_name: str) -> Tuple[List, List]:
    """
    Process existing albums from metadata and separate into local and missing arrays.
    
    Args:
        metadata: BandMetadata object being updated
        local_albums_lookup: Dictionary mapping lowercase album names to album data
        processed_local_albums: Set to track which local albums have been processed
        band_name: Name of the band for logging
        
    Returns:
        Tuple of (updated_local_albums, updated_missing_albums)
    """
    from src.models.band import AlbumType
    
    updated_local_albums = []
    updated_missing_albums = []
    
    # Process existing albums from both arrays
    all_existing_albums = list(metadata.albums) + list(metadata.albums_missing)
    
    for existing_album in all_existing_albums:
        album_name_lower = existing_album.album_name.lower()
        
        if album_name_lower in local_albums_lookup:
            # Album exists locally - update and add to local albums array
            updated_album = _update_existing_album_with_local_data(
                existing_album, local_albums_lookup[album_name_lower]
            )
            updated_local_albums.append(updated_album)
            processed_local_albums.add(album_name_lower)
            logging.debug(f"Updated existing album in local array: {existing_album.album_name}")
        else:
            # Album not found locally - add to missing albums array
            missing_album = _prepare_missing_album(existing_album)
            updated_missing_albums.append(missing_album)
            logging.debug(f"Moved album to missing array: {existing_album.album_name}")
    
    return updated_local_albums, updated_missing_albums


def _update_existing_album_with_local_data(existing_album, local_album: Dict):
    """
    Update an existing album with local filesystem data while preserving metadata.
    
    Args:
        existing_album: Existing album object from metadata
        local_album: Dictionary with local album data
        
    Returns:
        Updated album object
    """
    from src.models.band import AlbumType
    
    # Update the existing album with local info while preserving metadata
    existing_album.track_count = local_album['track_count']
    existing_album.folder_path = local_album['folder_path']
    
    # Update type if it was detected from folder structure
    if local_album.get('type'):
        try:
            existing_album.type = AlbumType(local_album['type'])
        except ValueError:
            # Keep existing type if new type is invalid
            pass
    
    # Update edition if detected
    if local_album.get('edition'):
        existing_album.edition = local_album['edition']
    
    # Update year if detected and not set
    if local_album.get('year') and not existing_album.year:
        existing_album.year = local_album['year']
    
    return existing_album


def _prepare_missing_album(existing_album):
    """
    Prepare an album for the missing albums array.
    
    Args:
        existing_album: Album object to prepare as missing
        
    Returns:
        Album object prepared for missing status
    """
    # Album not found locally - clear local-specific data
    existing_album.track_count = 0  # No tracks since it's missing
    existing_album.folder_path = ""  # No folder path since it's missing
    return existing_album


def _process_new_local_albums(local_albums: List[Dict], processed_local_albums: set, 
                            band_name: str) -> List:
    """
    Process local albums that aren't in the existing metadata.
    
    Args:
        local_albums: List of all local album dictionaries
        processed_local_albums: Set of already processed album names (lowercase)
        band_name: Name of the band for logging
        
    Returns:
        List of new Album objects for albums found locally but not in metadata
    """
    from src.models.band import Album, AlbumType
    
    new_local_albums = []
    
    for local_album in local_albums:
        album_name_lower = local_album['album_name'].lower()
        
        if album_name_lower not in processed_local_albums:
            # This is a new album not in metadata
            new_album = _create_new_album_from_local_data(local_album)
            new_local_albums.append(new_album)
            logging.debug(f"Added new local album: {new_album.album_name}")
    
    return new_local_albums


def _create_new_album_from_local_data(local_album: Dict):
    """
    Create a new Album object from local filesystem data.
    
    Args:
        local_album: Dictionary with local album data
        
    Returns:
        New Album object
    """
    from src.models.band import Album, AlbumType
    
    try:
        album_type = AlbumType(local_album.get('type', AlbumType.ALBUM.value))
    except ValueError:
        album_type = AlbumType.ALBUM
    
    # Create new album entry for local albums array
    return Album(
        album_name=local_album['album_name'],
        year=local_album.get('year', ''),
        type=album_type,
        edition=local_album.get('edition', ''),
        track_count=local_album['track_count'],
        duration=local_album.get('duration', ''),
        genres=local_album.get('genres', []),
        folder_path=local_album['folder_path']
    )


def _update_metadata_with_synchronized_albums(metadata: 'BandMetadata', updated_local_albums: List, 
                                            updated_missing_albums: List, band_name: str) -> 'BandMetadata':
    """
    Update metadata object with synchronized album arrays and statistics.
    
    Args:
        metadata: BandMetadata object to update
        updated_local_albums: List of local albums
        updated_missing_albums: List of missing albums
        band_name: Name of the band for logging
        
    Returns:
        Updated BandMetadata object
    """
    # Update metadata with separated albums arrays
    metadata.albums = updated_local_albums
    metadata.albums_missing = updated_missing_albums
    metadata.albums_count = len(updated_local_albums) + len(updated_missing_albums)
    
    logging.debug(f"Synchronized metadata: {len(updated_local_albums)} local albums, "
                 f"{len(updated_missing_albums)} missing albums, "
                 f"{metadata.albums_count} total albums")
    
    return metadata


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


def _discover_album_folders_enhanced(band_folder: Path, album_parser: AlbumFolderParser) -> List[Dict]:
    """
    Discover album folders with enhanced metadata including type detection.
    
    Args:
        band_folder: Path to the band folder
        album_parser: AlbumFolderParser instance for parsing folder names
        
    Returns:
        List of dictionaries containing album folder info with metadata
    """
    album_folders = []
    
    try:
        for item in band_folder.iterdir():
            if (item.is_dir() and 
                not item.name.startswith('.') and 
                item.name.lower() not in EXCLUDED_FOLDERS and
                item.name != '.band_metadata.json'):
                
                # Check if this is a type folder (Album/, Live/, Demo/, etc.)
                type_folder_info = album_parser._detect_type_folder(item.name)
                
                if type_folder_info['is_type_folder']:
                    # This is a type folder, scan its contents regardless of structure type
                    # (needed for mixed structures that have both type folders and direct albums)
                    try:
                        for album_item in item.iterdir():
                            if (album_item.is_dir() and 
                                not album_item.name.startswith('.') and
                                album_item.name.lower() not in EXCLUDED_FOLDERS):
                                album_folders.append({
                                    'path': album_item,
                                    'type_folder': item.name,
                                    'album_type': type_folder_info['album_type'],
                                    'in_type_folder': True
                                })
                    except (PermissionError, OSError) as e:
                        logging.warning(f"Error accessing type folder {item}: {e}")
                else:
                    # Regular album folder (default, mixed, or non-type folder)
                    album_folders.append({
                        'path': item,
                        'type_folder': '',
                        'album_type': None,  # Will be detected from folder name
                        'in_type_folder': False
                    })
                    
    except (PermissionError, OSError) as e:
        logging.warning(f"Error accessing band folder {band_folder}: {e}")
    
    return sorted(album_folders, key=lambda x: x['path'].name.lower())


def _scan_album_folder_enhanced(album_folder_info: Dict, album_parser: AlbumFolderParser, compliance_validator: ComplianceValidator) -> Optional[Dict]:
    """
    Scan a single album folder with enhanced metadata detection.
    
    Args:
        album_folder_info: Dictionary with album folder path and metadata
        album_parser: AlbumFolderParser instance for parsing folder names
        compliance_validator: ComplianceValidator for compliance analysis (unused)
        
    Returns:
        Dictionary with enhanced album information or None if invalid
    """
    album_folder = album_folder_info['path']
    album_name = album_folder.name
    
    try:
        # Count music files
        tracks_count = _count_music_files(album_folder)
        
        # Only include folders that actually contain music
        if tracks_count == 0:
            return None
        
        # Parse album folder name for enhanced metadata
        parsed_info = album_parser.parse_album_folder(album_name)
        
        # Determine album type
        album_type = album_folder_info.get('album_type')
        if album_type is None:
            # Detect type from folder name if not determined by type folder
            album_type = album_parser.detect_album_type_from_folder(album_name, album_folder_info['type_folder'])
        
        # Determine folder path - include type folder for enhanced structure
        if album_folder_info['in_type_folder'] and album_folder_info['type_folder']:
            folder_path = f"{album_folder_info['type_folder']}/{album_name}"
        else:
            folder_path = album_name
        
        return {
            'album_name': parsed_info.get('album_name', album_name),
            'year': parsed_info.get('year', ''),
            'type': album_type.value if album_type else AlbumType.ALBUM.value,
            'edition': parsed_info.get('edition', ''),
            'track_count': tracks_count,
            'missing': False,  # Found in folder, so not missing
            'duration': '',    # Will be filled by metadata tools
            'genres': [],      # Will be filled by metadata tools
            'folder_path': folder_path
        }
        
    except Exception as e:
        logging.warning(f"Error scanning album folder {album_name}: {e}")
        return None


def _calculate_album_types_distribution(albums: List[Dict]) -> Dict[str, int]:
    """
    Calculate distribution of album types in the scanned albums.
    
    Args:
        albums: List of album dictionaries with type information
        
    Returns:
        Dictionary with album type counts
    """
    distribution = {}
    for album in albums:
        album_type = album.get('type', AlbumType.ALBUM.value)
        distribution[album_type] = distribution.get(album_type, 0) + 1
    
    return distribution


def _calculate_compliance_summary(albums: List[Dict]) -> Dict[str, Any]:
    """
    Calculate compliance summary for scanned albums.
    
    Args:
        albums: List of album dictionaries with compliance information
        
    Returns:
        Dictionary with compliance summary statistics
    """
    return {'average_score': 0, 'compliant_albums': 0, 'total_albums': len(albums), 'compliance_percentage': 0}


def _count_music_files(folder: Path) -> int:
    """
    Count music files in a folder (non-recursive) using optimized batch operations.
    
    Args:
        folder: Path to folder to scan
        
    Returns:
        Number of music files found
    """
    # Use optimized batch file counting for better performance
    return BatchFileOperations.count_files_in_directory(folder, MUSIC_EXTENSIONS)


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
                data = json.load(f)
            return CollectionIndex(**data)
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
            f.write(collection_index.model_dump_json(indent=2))
            
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
        local_albums = len(metadata.albums)
        missing_albums = len(metadata.albums_missing)
        total_albums = local_albums + missing_albums
    else:
        # No metadata - use physical scan results
        local_albums = band_result['albums_count']
        missing_albums = 0
        total_albums = local_albums
    
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
        local_albums_count=local_albums,
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
            data = json.load(f)
        return BandMetadata(**data)
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
    music_root = Path(get_config().MUSIC_ROOT_PATH)
    
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
                    # With separated albums schema, missing count is already tracked
                    missing_count = len(metadata.albums_missing)
                    
                    # Update band entry
                    band_entry.missing_albums_count = missing_count
                    total_missing += missing_count
                    
        except Exception as e:
            logging.warning(f"Error detecting missing albums for {band_entry.name}: {e}")
    
    return total_missing


def _scan_album_folder(album_folder: Path) -> Optional[Dict]:
    """
    Scan a single album folder for track information (backward compatibility).
    
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
            'track_count': tracks_count,
            'duration': '',    # Will be filled by metadata tools
            'year': '',        # Will be filled by metadata tools
            'genres': [],      # Will be filled by metadata tools
            'folder_path': album_name  # Store the folder name
        }
        
    except Exception as e:
        logging.warning(f"Error scanning album folder {album_name}: {e}")
        return None 