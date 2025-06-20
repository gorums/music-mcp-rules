"""
Local Storage Management for Music Collection MCP Server.

This module provides comprehensive JSON file operations including atomic writes,
file locking, backup/recovery, and metadata synchronization.
"""

# Standard library imports
import json
import logging
import os
import shutil
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Try to import fcntl for Unix-like systems, handle Windows gracefully
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

# Local imports
from src.di import get_config
from src.exceptions import (
    DataError,
    StorageError,
    ValidationError,
    create_storage_error,
    wrap_exception,
)
from src.core.tools.performance import (
    performance_monitor,
    track_operation,
    get_performance_summary,
)
from src.models import (
    AlbumAnalysis,
    BandAnalysis,
    BandIndexEntry,
    BandMetadata,
    CollectionIndex,
    CollectionInsight,
)

# Configure logging
logger = logging.getLogger(__name__)


# Simple in-memory cache for frequently accessed data
class SimpleCache:
    """
    Simple thread-safe in-memory cache for frequently accessed data.
    """
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        self._cache = {}
        self._access_times = {}
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache if it exists and is not expired."""
        with self._lock:
            if key not in self._cache:
                return None
            
            # Check if expired
            access_time = self._access_times.get(key, 0)
            if time.time() - access_time > self._ttl_seconds:
                del self._cache[key]
                del self._access_times[key]
                return None
            
            # Update access time
            self._access_times[key] = time.time()
            return self._cache[key]
    
    def put(self, key: str, value: Any) -> None:
        """Put item in cache, evicting old items if necessary."""
        with self._lock:
            # Evict expired items
            self._evict_expired()
            
            # Evict oldest items if cache is full
            if len(self._cache) >= self._max_size and key not in self._cache:
                oldest_key = min(self._access_times.keys(), key=self._access_times.get)
                del self._cache[oldest_key]
                del self._access_times[oldest_key]
            
            self._cache[key] = value
            self._access_times[key] = time.time()
    
    def _evict_expired(self) -> None:
        """Remove expired items from cache."""
        current_time = time.time()
        expired_keys = [
            key for key, access_time in self._access_times.items()
            if current_time - access_time > self._ttl_seconds
        ]
        for key in expired_keys:
            del self._cache[key]
            del self._access_times[key]
    
    def clear(self) -> None:
        """Clear all items from cache."""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()


# Global cache instances
_collection_cache = SimpleCache(max_size=50, ttl_seconds=300)  # 5 minute TTL
_metadata_cache = SimpleCache(max_size=200, ttl_seconds=180)   # 3 minute TTL


class AtomicFileWriter:
    """
    Context manager for atomic file write operations.
    
    Ensures that file writes either complete fully or fail without
    corrupting the original file.
    """
    
    def __init__(self, file_path: Path, backup: bool = True):
        """
        Initialize atomic file writer.
        
        Args:
            file_path: Path to the target file
            backup: Whether to create a backup before writing
        """
        self.file_path = Path(file_path)
        self.temp_path = self.file_path.with_suffix(self.file_path.suffix + '.tmp')
        self.backup_path = self.file_path.with_suffix(self.file_path.suffix + '.backup')
        self.backup = backup
        self.file_handle = None
        
    def __enter__(self):
        """Enter context manager."""
        # Create backup if requested and file exists
        if self.backup and self.file_path.exists():
            shutil.copy2(self.file_path, self.backup_path)
        
        # Create parent directory if it doesn't exist
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Open temporary file for writing
        self.file_handle = open(self.temp_path, 'w', encoding='utf-8')
        return self.file_handle
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if self.file_handle:
            self.file_handle.close()
            
        if exc_type is None:
            # Success: atomically replace original file
            if os.name == 'nt':  # Windows
                if self.file_path.exists():
                    self.file_path.unlink()
                self.temp_path.rename(self.file_path)
            else:  # Unix-like systems
                self.temp_path.rename(self.file_path)
        else:
            # Error: cleanup temporary file
            if self.temp_path.exists():
                self.temp_path.unlink()


@contextmanager
def file_lock(file_path: Path, timeout: int = 10):
    """
    Context manager for file locking to prevent concurrent access.
    
    Args:
        file_path: Path to the file to lock
        timeout: Maximum time to wait for lock in seconds
        
    Raises:
        StorageError: If lock cannot be acquired within timeout
    """
    lock_path = file_path.with_suffix(file_path.suffix + '.lock')
    
    # Ensure parent directory exists for lock file
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create lock file
    try:
        lock_file = open(lock_path, 'w')
        
        # Try to acquire lock with timeout
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                if HAS_FCNTL:  # Unix-like systems
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                # On Windows, we just use the lock file existence as a simple lock
                break
            except (IOError, OSError):
                time.sleep(0.1)
        else:
            raise StorageError(f"Could not acquire lock for {file_path} within {timeout} seconds")
        
        yield
        
    finally:
        # Release lock and cleanup
        try:
            if HAS_FCNTL:  # Unix-like systems
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            lock_file.close()
            if lock_path.exists():
                lock_path.unlink()
        except Exception:
            pass  # Ignore cleanup errors


class JSONStorage:
    """
    Core JSON storage operations with atomic writes and file locking.
    """
    
    @staticmethod
    def save_json(file_path: Path, data: Dict[str, Any], backup: bool = True) -> None:
        """
        Save data to JSON file with atomic write operation.
        
        Args:
            file_path: Path to save the JSON file
            data: Data to serialize to JSON
            backup: Whether to create backup before writing
            
        Raises:
            StorageError: If save operation fails
        """
        try:
            with file_lock(file_path):
                with AtomicFileWriter(file_path, backup=backup) as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise create_storage_error("save", str(file_path), e)
    
    @staticmethod
    def load_json(file_path: Path) -> Dict[str, Any]:
        """
        Load data from JSON file with error handling.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Dict containing the loaded JSON data
            
        Raises:
            StorageError: If load operation fails
        """
        try:
            if not file_path.exists():
                raise StorageError(
                    f"File not found: {file_path}",
                    file_path=str(file_path),
                    operation="load",
                    user_message=f"The requested data file does not exist: {file_path.name}"
                )
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise DataError(
                f"Invalid JSON in {file_path}: {e}",
                data_type="JSON",
                data_source=str(file_path),
                user_message=f"The data file is corrupted or contains invalid JSON: {file_path.name}"
            )
        except Exception as e:
            raise create_storage_error("load", str(file_path), e)
    
    @staticmethod
    def file_exists(file_path: Path) -> bool:
        """Check if file exists."""
        return file_path.exists()
    
    @staticmethod
    def create_backup(file_path: Path) -> Path:
        """
        Create backup of existing file.
        
        Args:
            file_path: Path to file to backup
            
        Returns:
            Path to backup file
            
        Raises:
            StorageError: If backup creation fails
        """
        if not file_path.exists():
            raise StorageError(f"Cannot backup non-existent file: {file_path}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.with_suffix(f".backup_{timestamp}{file_path.suffix}")
        
        try:
            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception as e:
            raise StorageError(f"Failed to create backup: {e}")


def save_band_metadata(band_name: str, metadata: BandMetadata) -> Dict[str, Any]:
    """
    Save complete band metadata to .band_metadata.json file.
    
    Args:
        band_name: Name of the band
        metadata: BandMetadata instance to save
        preserve_analyze: If True (default), preserves existing analyze data.
                         If False, allows overwriting analyze data with the provided metadata.
        
    Returns:
        Dict with operation status and details
        
    Raises:
        StorageError: If save operation fails
    """
    try:
        # Validate input parameters
        _validate_band_metadata_input(metadata)
        
        # Get file paths
        band_folder, metadata_file = _get_band_metadata_paths(band_name)
        
        # Preserve existing data if file exists
        _preserve_existing_metadata(metadata, metadata_file, band_name)
        
        # Update timestamps
        _update_metadata_timestamps(metadata, band_name)
        
        # Save metadata to file
        _save_metadata_to_file(metadata, metadata_file)
        
        return _create_save_metadata_response(band_name, metadata_file, metadata)
        
    except Exception as e:
        if isinstance(e, (StorageError, ValidationError, DataError)):
            # Re-raise our standardized exceptions
            raise
        else:
            # Wrap generic exceptions
            raise create_storage_error("save band metadata", band_name, e)


def _validate_band_metadata_input(metadata: BandMetadata) -> None:
    """
    Validate the input metadata parameter.
    
    Args:
        metadata: BandMetadata instance to validate
        
    Raises:
        ValidationError: If metadata is invalid
    """
    if not isinstance(metadata, BandMetadata):
        raise ValidationError(
            f"metadata parameter must be BandMetadata instance, got {type(metadata)}",
            field_name="metadata",
            field_value=str(type(metadata)),
            user_message="Invalid metadata format provided. Expected BandMetadata object."
        )


def _get_band_metadata_paths(band_name: str) -> Tuple[Path, Path]:
    """
    Get the band folder and metadata file paths.
    
    Args:
        band_name: Name of the band
        
    Returns:
        Tuple of (band_folder_path, metadata_file_path)
    """
    config = get_config()
    band_folder = Path(config.MUSIC_ROOT_PATH) / band_name
    metadata_file = band_folder / ".band_metadata.json"
    return band_folder, metadata_file


def _preserve_existing_metadata(metadata: BandMetadata, metadata_file: Path, band_name: str) -> None:
    """
    Preserve existing analyze and folder_structure data if file exists.
    
    Args:
        metadata: BandMetadata instance to update with preserved data
        metadata_file: Path to existing metadata file
        band_name: Name of the band for logging
    """
    if not metadata_file.exists():
        return
    
    try:
        existing_metadata_dict = JSONStorage.load_json(metadata_file)
        existing_metadata = BandMetadata(**existing_metadata_dict)
        
        # Preserve existing analyze data
        if existing_metadata.analyze is not None:
            try:
                metadata.analyze = existing_metadata.analyze
            except Exception as e:
                logger.warning(f"Could not preserve analyze data for {band_name}: {e}")
        
        # Preserve existing folder_structure data
        if existing_metadata.folder_structure is not None:
            try:
                metadata.folder_structure = existing_metadata.folder_structure
            except Exception as e:
                logger.warning(f"Could not preserve folder_structure data for {band_name}: {e}")
                
    except Exception as e:
        # If loading fails, continue without preserving (file might be corrupted)
        logger.warning(f"Could not load existing metadata for {band_name}: {e}")


def _update_metadata_timestamps(metadata: BandMetadata, band_name: str) -> None:
    """
    Update metadata timestamps.
    
    Args:
        metadata: BandMetadata instance to update
        band_name: Name of the band for logging
    """
    try:
        metadata.update_metadata_saved_timestamp()  # This also calls update_timestamp()
    except Exception as e:
        logger.warning(f"Could not update metadata saved timestamp for {band_name}: {e}")


def _save_metadata_to_file(metadata: BandMetadata, metadata_file: Path) -> None:
    """
    Save metadata to JSON file with atomic write and backup.
    
    Args:
        metadata: BandMetadata instance to save
        metadata_file: Path to save the metadata file
    """
    metadata_dict = metadata.model_dump()
    JSONStorage.save_json(metadata_file, metadata_dict, backup=True)


def _create_save_metadata_response(band_name: str, metadata_file: Path, metadata: BandMetadata) -> Dict[str, Any]:
    """
    Create the response dictionary for save_band_metadata.
    
    Args:
        band_name: Name of the band
        metadata_file: Path to the metadata file
        metadata: BandMetadata instance that was saved
        
    Returns:
        Response dictionary
    """
    return {
        "status": "success",
        "message": f"Band metadata saved for {band_name}",
        "file_path": str(metadata_file),
        "last_updated": metadata.last_updated,
        "albums_count": metadata.albums_count
    }


def save_band_analyze(band_name: str, analysis: BandAnalysis) -> Dict[str, Any]:
    """
    Save band analysis data with reviews and ratings, with optional missing album inclusion.
    
    This function can filter out analysis for albums marked as missing in the metadata
    (default behavior) or include them when analyze_missing_albums=True.
    Album names are not stored in the final analysis to avoid redundancy.
    
    Args:
        band_name: Name of the band
        analysis: BandAnalysis instance to save
        
    Returns:
        Dict with operation status and details
        
    Raises:
        StorageError: If save operation fails
    """
    try:
        # Load or create band metadata
        band_folder, metadata_file, metadata = _load_or_create_band_metadata_for_analysis(band_name)
        
        # Process similar bands separation
        filtered_analysis = _process_similar_bands_separation(analysis)
        
        # Filter album analysis
        filtered_album_analysis = _filter_album_analysis(analysis.albums)
        
        # Create final filtered analysis
        final_analysis = _create_final_filtered_analysis(
            analysis, filtered_album_analysis, filtered_analysis
        )
        
        # Update and save metadata
        _update_metadata_with_analysis(metadata, final_analysis)
        _save_metadata_to_file(metadata, metadata_file)
        
        # Build response
        return _build_save_analysis_response(
            band_name, metadata_file, metadata, final_analysis, 
            len(filtered_album_analysis), 0  # excluded_count is 0 since we include all albums now
        )
        
    except Exception as e:
        raise StorageError(f"Failed to save band analysis for {band_name}: {e}")


def _load_or_create_band_metadata_for_analysis(band_name: str) -> Tuple[Path, Path, BandMetadata]:
    """
    Load existing metadata or create new metadata for analysis operations.
    
    Args:
        band_name: Name of the band
        
    Returns:
        Tuple of (band_folder, metadata_file, metadata)
    """
    config = get_config()
    band_folder = Path(config.MUSIC_ROOT_PATH) / band_name
    metadata_file = band_folder / ".band_metadata.json"
    
    # Load existing metadata or create new
    if metadata_file.exists():
        try:
            metadata_dict = JSONStorage.load_json(metadata_file)
            metadata = BandMetadata(**metadata_dict)
        except Exception as e:
            # If metadata is corrupted, create new
            metadata = BandMetadata(band_name=band_name)
    else:
        metadata = BandMetadata(band_name=band_name)
    
    return band_folder, metadata_file, metadata


def _process_similar_bands_separation(analysis: BandAnalysis) -> Dict[str, List[str]]:
    """
    Separate similar bands into in-collection and missing based on collection index.
    
    Args:
        analysis: BandAnalysis instance with similar bands data
        
    Returns:
        Dictionary with separated similar bands lists
    """
    # Load collection index for similar bands separation
    collection_index = load_collection_index()
    collection_band_names = set()
    if collection_index:
        collection_band_names = {b.name.lower() for b in collection_index.bands}
    
    similar_bands_in_collection = []
    similar_bands_missing = []
    
    # Backward compatibility: if only similar_bands is present
    if hasattr(analysis, 'similar_bands') and not hasattr(analysis, 'similar_bands_missing'):
        for band in getattr(analysis, 'similar_bands', []):
            if band.lower() in collection_band_names:
                similar_bands_in_collection.append(band)
            else:
                similar_bands_missing.append(band)
    else:
        # Process similar_bands list
        for band in getattr(analysis, 'similar_bands', []):
            if band.lower() in collection_band_names:
                similar_bands_in_collection.append(band)
            else:
                similar_bands_missing.append(band)
        
        # Process similar_bands_missing list
        for band in getattr(analysis, 'similar_bands_missing', []):
            if band.lower() in collection_band_names:
                if band not in similar_bands_in_collection:
                    similar_bands_in_collection.append(band)
            else:
                similar_bands_missing.append(band)
    
    return {
        "in_collection": similar_bands_in_collection,
        "missing": similar_bands_missing
    }


def _filter_album_analysis(albums: List[AlbumAnalysis]) -> List[AlbumAnalysis]:
    """
    Filter album analysis data. Currently includes all albums.
    
    Args:
        albums: List of album analysis data
        
    Returns:
        Filtered list of album analysis
    """
    filtered_album_analysis = []
    for album_analysis in albums:
        filtered_analysis = AlbumAnalysis(
            album_name=album_analysis.album_name,
            review=album_analysis.review,
            rate=album_analysis.rate
        )
        filtered_album_analysis.append(filtered_analysis)
    
    return filtered_album_analysis


def _create_final_filtered_analysis(analysis: BandAnalysis, filtered_album_analysis: List[AlbumAnalysis], 
                                   similar_bands_data: Dict[str, List[str]]) -> BandAnalysis:
    """
    Create the final filtered analysis with separated similar bands.
    
    Args:
        analysis: Original band analysis
        filtered_album_analysis: Filtered album analysis list
        similar_bands_data: Dictionary with separated similar bands
        
    Returns:
        Final BandAnalysis instance
    """
    return BandAnalysis(
        review=analysis.review,
        rate=analysis.rate,
        albums=filtered_album_analysis,
        similar_bands=similar_bands_data["in_collection"],
        similar_bands_missing=similar_bands_data["missing"]
    )


def _update_metadata_with_analysis(metadata: BandMetadata, analysis: BandAnalysis) -> None:
    """
    Update metadata with analysis data and timestamp.
    
    Args:
        metadata: BandMetadata instance to update
        analysis: BandAnalysis instance to save
    """
    metadata.analyze = analysis
    metadata.update_timestamp()


def _build_save_analysis_response(band_name: str, metadata_file: Path, metadata: BandMetadata,
                                 analysis: BandAnalysis, albums_analyzed: int, 
                                 excluded_count: int) -> Dict[str, Any]:
    """
    Build the response dictionary for save_band_analyze.
    
    Args:
        band_name: Name of the band
        metadata_file: Path to the metadata file
        metadata: BandMetadata instance
        analysis: Final analysis that was saved
        albums_analyzed: Number of albums analyzed
        excluded_count: Number of albums excluded
        
    Returns:
        Response dictionary
    """
    # Determine if we're analyzing missing albums
    analyze_missing_albums = any(
        album_analysis.album_name in [album.album_name for album in metadata.albums_missing] 
        for album_analysis in analysis.albums
    )
    
    # Create appropriate message based on settings
    if analyze_missing_albums and len(metadata.albums_missing) > 0:
        message = f"Band analysis saved for {band_name} including all albums"
    else:
        album_text = f"{albums_analyzed} album reviews"
        similar_bands_text = f"{analysis.total_similar_bands_count} similar bands"
        message = f"Band analysis saved for {band_name} including {album_text} and {similar_bands_text}"
    
    return {
        "status": "success",
        "message": message,
        "file_path": str(metadata_file),
        "band_rating": analysis.rate,
        "albums_analyzed": albums_analyzed,
        "albums_excluded": excluded_count,
        "similar_bands_count": analysis.total_similar_bands_count,
        "similar_bands_in_collection": len(analysis.similar_bands),
        "similar_bands_missing": len(analysis.similar_bands_missing),
        "last_updated": metadata.last_updated,
        "analyze_missing_albums": analyze_missing_albums or len(metadata.albums_missing) > 0
    }


def save_collection_insight(insights: CollectionInsight) -> Dict[str, Any]:
    """
    Save collection-wide insights and analytics.
    
    Args:
        insights: CollectionInsight instance to save
        
    Returns:
        Dict with operation status and details
        
    Raises:
        StorageError: If save operation fails
    """
    try:
        config = get_config()
        collection_file = Path(config.MUSIC_ROOT_PATH) / ".collection_index.json"
        
        # Check if file existed before we modify it
        file_existed_before = collection_file.exists()
        
        # Load existing collection index or create new
        if file_existed_before:
            try:
                index_dict = JSONStorage.load_json(collection_file)
                index = CollectionIndex(**index_dict)
            except Exception as e:
                # If index is corrupted, create new
                index = CollectionIndex()
        else:
            index = CollectionIndex()
        
        # Update insights
        index.update_insights(insights)
        
        # Save updated index
        index_dict = index.model_dump()
        JSONStorage.save_json(collection_file, index_dict, backup=True)
        
        return {
            "status": "success",
            "message": "Collection insights saved",
            "file_path": str(collection_file),
            "file_existed_before": file_existed_before,
            "insights_count": len(insights.insights),
            "recommendations_count": len(insights.recommendations),
            "collection_health": insights.collection_health,
            "generated_at": insights.generated_at
        }
        
    except Exception as e:
        raise StorageError(f"Failed to save collection insights: {e}")


@performance_monitor("get_band_list")
def get_band_list(
    search_query: Optional[str] = None,
    filter_genre: Optional[str] = None,
    filter_has_metadata: Optional[bool] = None,
    filter_missing_albums: Optional[bool] = None,
    filter_album_type: Optional[str] = None,
    filter_compliance_level: Optional[str] = None,
    filter_structure_type: Optional[str] = None,
    sort_by: str = "name",
    sort_order: str = "asc",
    page: int = 1,
    page_size: int = 50,
    include_albums: bool = False,
    album_details_filter: Optional[str] = None  # 'local', 'missing', or None
) -> Dict[str, Any]:
    """
    Get a list of all discovered bands with enhanced filtering, sorting, and pagination.
    
    Args:
        search_query: Search term to filter bands by name or album name
        filter_genre: Filter bands by genre (if metadata available)
        filter_has_metadata: Filter bands that have/don't have metadata files
        filter_missing_albums: Filter bands with/without missing albums
        filter_album_type: Filter bands that have albums of specific type (Album, EP, Live, etc.)
        filter_compliance_level: Filter by compliance level (excellent, good, fair, poor, critical)
        filter_structure_type: Filter by folder structure type (default, enhanced, mixed, legacy)
        sort_by: Field to sort by ('name', 'albums_count', 'last_updated', 'completion', 'compliance')
        sort_order: Sort order ('asc' or 'desc')
        page: Page number for pagination (1-based)
        page_size: Number of results per page (1-100)
        include_albums: Include album details for each band
        album_details_filter: If 'local', only include local albums in album details; if 'missing', only missing albums; None for all
        
    Returns:
        Dict containing filtered and paginated band list with enhanced metadata
        
    Raises:
        StorageError: If operation fails
    """
    try:
        # Load collection index or return empty result
        index = _load_collection_index_for_band_list()
        if not index:
            return _create_empty_band_list_result(page, page_size, search_query, filter_genre, 
                                                filter_has_metadata, filter_missing_albums, 
                                                filter_album_type, filter_compliance_level, 
                                                filter_structure_type, sort_by, sort_order)
        
        # Apply all filters to get filtered band list
        filtered_bands = _apply_all_band_filters(
            index.bands, search_query, filter_genre, filter_has_metadata, 
            filter_missing_albums, filter_album_type, filter_compliance_level, 
            filter_structure_type, include_albums
        )
        
        # Apply sorting
        sorted_bands = _sort_bands_enhanced(filtered_bands, sort_by, sort_order)
        
        # Apply pagination and build results
        paginated_results = _apply_pagination_and_build_results(
            sorted_bands, page, page_size, include_albums, album_details_filter
        )
        
        # Build final response with all metadata
        return _build_final_band_list_response(
            index, paginated_results, page, page_size, search_query, filter_genre,
            filter_has_metadata, filter_missing_albums, filter_album_type, 
            filter_compliance_level, filter_structure_type, sort_by, sort_order
        )
        
    except Exception as e:
        raise StorageError(f"Failed to get band list: {e}")


def _load_collection_index_for_band_list() -> Optional[CollectionIndex]:
    """
    Load collection index for band list operations with caching.
    
    Returns:
        CollectionIndex if found, None if not found
    """
    config = get_config()
    collection_file = Path(config.MUSIC_ROOT_PATH) / ".collection_index.json"
    cache_key = f"collection_index:{collection_file}"
    
    # Try to get from cache first
    cached_index = _collection_cache.get(cache_key)
    if cached_index:
        logger.debug("Using cached collection index")
        return cached_index
    
    with track_operation("load_collection_index") as metrics:
        if not collection_file.exists():
            return None
        
        try:
            # Check file modification time for cache invalidation
            file_mtime = collection_file.stat().st_mtime
            cached_mtime = _collection_cache.get(f"{cache_key}:mtime")
            
            if cached_mtime and cached_mtime == file_mtime and cached_index:
                # File hasn't changed, use cached version
                return cached_index
            
            # Load collection index
            index_dict = JSONStorage.load_json(collection_file)
            index = CollectionIndex(**index_dict)
            
            # Cache the loaded index
            _collection_cache.put(cache_key, index)
            _collection_cache.put(f"{cache_key}:mtime", file_mtime)
            
            metrics.items_processed = len(index.bands) if index.bands else 0
            logger.debug(f"Loaded collection index with {metrics.items_processed} bands")
            
            return index
            
        except Exception as e:
            logger.error(f"Failed to load collection index: {e}")
            metrics.errors += 1
            raise


def _create_empty_band_list_result(page: int, page_size: int, search_query: Optional[str], 
                                 filter_genre: Optional[str], filter_has_metadata: Optional[bool],
                                 filter_missing_albums: Optional[bool], filter_album_type: Optional[str],
                                 filter_compliance_level: Optional[str], filter_structure_type: Optional[str],
                                 sort_by: str, sort_order: str) -> Dict[str, Any]:
    """
    Create empty result when no collection index is found.
    
    Returns:
        Empty band list result dictionary
    """
    return {
        "status": "success",
        "message": "No collection index found",
        "bands": [],
        # Backward compatibility - keep original fields at top level
        "total_bands": 0,
        "total_albums": 0,
        "total_missing_albums": 0,
        "collection_completion": 100.0,
        "last_scan": "",
        # Enhanced functionality - new fields
        "pagination": {
            "total_bands": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0
        },
        "filters_applied": _build_filters_summary(search_query, filter_genre, filter_has_metadata, 
                                                filter_missing_albums, filter_album_type, 
                                                filter_compliance_level, filter_structure_type),
        "sort": {"by": sort_by, "order": sort_order}
    }


def _apply_all_band_filters(bands: List[BandIndexEntry], search_query: Optional[str],
                          filter_genre: Optional[str], filter_has_metadata: Optional[bool],
                          filter_missing_albums: Optional[bool], filter_album_type: Optional[str],
                          filter_compliance_level: Optional[str], filter_structure_type: Optional[str],
                          include_albums: bool) -> List[BandIndexEntry]:
    """
    Apply all filtering criteria to the band list.
    
    Args:
        bands: List of band entries to filter
        Various filter parameters
        include_albums: Whether to include albums in search
        
    Returns:
        Filtered list of band entries
    """
    bands_to_process = bands.copy()
    
    # Apply search filter
    if search_query:
        bands_to_process = _filter_bands_by_search(bands_to_process, search_query.lower(), include_albums)
    
    # Apply genre filter (requires loading metadata)
    if filter_genre:
        bands_to_process = _filter_bands_by_genre(bands_to_process, filter_genre.lower())
    
    # Apply metadata filter
    if filter_has_metadata is not None:
        bands_to_process = [b for b in bands_to_process if b.has_metadata == filter_has_metadata]
    
    # Apply missing albums filter
    if filter_missing_albums is not None:
        if filter_missing_albums:
            bands_to_process = [b for b in bands_to_process if b.missing_albums_count > 0]
        else:
            bands_to_process = [b for b in bands_to_process if b.missing_albums_count == 0]
    
    # Apply enhanced filters
    if filter_album_type:
        bands_to_process = _filter_bands_by_album_type(bands_to_process, filter_album_type)
    
    if filter_compliance_level:
        bands_to_process = _filter_bands_by_compliance(bands_to_process, filter_compliance_level)
    
    if filter_structure_type:
        bands_to_process = _filter_bands_by_structure_type(bands_to_process, filter_structure_type)
    
    return bands_to_process


def _apply_pagination_and_build_results(bands: List[BandIndexEntry], page: int, page_size: int,
                                       include_albums: bool, album_details_filter: Optional[str]) -> Dict[str, Any]:
    """
    Apply pagination to the filtered bands and build detailed band information.
    
    Args:
        bands: Filtered and sorted list of bands
        page: Page number
        page_size: Number of results per page
        include_albums: Whether to include album details
        album_details_filter: Filter for album details
        
    Returns:
        Dictionary with pagination info and band details
    """
    total_bands = len(bands)
    page_size = max(1, min(100, page_size))  # Clamp between 1-100
    page = max(1, page)  # Ensure page is at least 1
    total_pages = (total_bands + page_size - 1) // page_size if total_bands > 0 else 0
    
    # Apply pagination
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_bands = bands[start_idx:end_idx]
    
    # Build detailed band information
    bands_info = []
    for band_entry in paginated_bands:
        band_info = _build_band_info(band_entry, include_albums, album_details_filter)
        bands_info.append(band_info)
    
    return {
        "bands_info": bands_info,
        "total_bands": total_bands,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


def _build_final_band_list_response(index: CollectionIndex, paginated_results: Dict[str, Any], 
                                  page: int, page_size: int, search_query: Optional[str],
                                  filter_genre: Optional[str], filter_has_metadata: Optional[bool],
                                  filter_missing_albums: Optional[bool], filter_album_type: Optional[str],
                                  filter_compliance_level: Optional[str], filter_structure_type: Optional[str],
                                  sort_by: str, sort_order: str) -> Dict[str, Any]:
    """
    Build the final response dictionary with all metadata and pagination info.
    
    Args:
        index: Collection index with stats
        paginated_results: Results from pagination
        Various filter and sort parameters
        
    Returns:
        Complete response dictionary
    """
    return {
        "status": "success",
        "message": f"Found {paginated_results['total_bands']} bands (showing page {paginated_results['page']} of {paginated_results['total_pages']})",
        "bands": paginated_results["bands_info"],
        # Backward compatibility - keep original fields at top level
        "total_bands": index.stats.total_bands,
        "total_albums": index.stats.total_albums,
        "total_missing_albums": index.stats.total_missing_albums,
        "collection_completion": index.stats.completion_percentage,
        "last_scan": index.last_scan,
        # Enhanced functionality - new fields
        "pagination": {
            "total_bands": paginated_results["total_bands"],
            "page": paginated_results["page"],
            "page_size": paginated_results["page_size"],
            "total_pages": paginated_results["total_pages"],
            "has_next": paginated_results["page"] < paginated_results["total_pages"],
            "has_previous": paginated_results["page"] > 1
        },
        "collection_summary": {
            "total_bands": index.stats.total_bands,
            "total_albums": index.stats.total_albums,
            "total_missing_albums": index.stats.total_missing_albums,
            "collection_completion": index.stats.completion_percentage,
            "last_scan": index.last_scan
        },
        "filters_applied": _build_filters_summary(search_query, filter_genre, filter_has_metadata, 
                                                filter_missing_albums, filter_album_type, 
                                                filter_compliance_level, filter_structure_type),
        "sort": {"by": sort_by, "order": sort_order}
    }


def _filter_bands_by_search(bands: List[BandIndexEntry], search_query: str, include_albums: bool = False) -> List[BandIndexEntry]:
    """Filter bands by search query in band names or album names."""
    filtered_bands = []
    
    for band in bands:
        # Search in band name
        if search_query in band.name.lower():
            filtered_bands.append(band)
            continue
        
        # Search in album names if include_albums is True
        if include_albums:
            try:
                metadata = load_band_metadata(band.name)
                if metadata:
                    for album in metadata.albums:
                        if search_query in album.album_name.lower():
                            filtered_bands.append(band)
                            break
            except:
                # Skip if metadata can't be loaded
                continue
    
    return filtered_bands


def _filter_bands_by_genre(bands: List[BandIndexEntry], genre_filter: str) -> List[BandIndexEntry]:
    """Filter bands by genre (requires loading metadata)."""
    filtered_bands = []
    
    for band in bands:
        try:
            metadata = load_band_metadata(band.name)
            if metadata and metadata.genres:
                # Check if any of the band's genres match the filter
                band_genres = [g.lower() for g in metadata.genres]
                if any(genre_filter in genre for genre in band_genres):
                    filtered_bands.append(band)
        except Exception:
            # Skip bands with corrupted metadata
            continue
    
    return filtered_bands


def _sort_bands(bands: List[BandIndexEntry], sort_by: str, sort_order: str) -> List[BandIndexEntry]:
    """Sort bands by specified field and order."""
    reverse = sort_order.lower() == "desc"
    
    if sort_by == "name":
        return sorted(bands, key=lambda b: b.name.lower(), reverse=reverse)
    elif sort_by == "albums_count":
        return sorted(bands, key=lambda b: b.albums_count, reverse=reverse)
    elif sort_by == "last_updated":
        return sorted(bands, key=lambda b: b.last_updated, reverse=reverse)
    elif sort_by == "completion":
        def completion_percentage(band):
            if band.albums_count == 0:
                return 100.0
            return ((band.albums_count - band.missing_albums_count) / band.albums_count) * 100
        return sorted(bands, key=completion_percentage, reverse=reverse)
    else:
        # Default to name sorting
        return sorted(bands, key=lambda b: b.name.lower(), reverse=reverse)


def _filter_bands_by_album_type(bands: List[BandIndexEntry], album_type: str) -> List[BandIndexEntry]:
    """Filter bands that contain albums of specified type (local or missing)."""
    filtered_bands = []
    for band in bands:
        try:
            metadata = load_band_metadata(band.name)
            if metadata:
                # Check both local and missing albums
                for album in (metadata.albums or []) + (metadata.albums_missing or []):
                    album_type_str = album.type.value if hasattr(album.type, 'value') else str(album.type)
                    if album_type.lower() == album_type_str.lower():
                        filtered_bands.append(band)
                        break
        except Exception:
            continue
    return filtered_bands


def _filter_bands_by_compliance(bands: List[BandIndexEntry], compliance_level: str) -> List[BandIndexEntry]:
    """Filter bands by compliance level."""
    return bands


def _filter_bands_by_structure_type(bands: List[BandIndexEntry], structure_type: str) -> List[BandIndexEntry]:
    """Filter bands by folder structure type."""
    filtered_bands = []
    
    for band in bands:
        try:
            metadata = load_band_metadata(band.name)
            if metadata and metadata.folder_structure:
                if structure_type.lower() == metadata.folder_structure.structure_type.value.lower():
                    filtered_bands.append(band)
        except Exception:
            # Skip bands with corrupted metadata
            continue
    
    return filtered_bands


def _sort_bands_enhanced(bands: List[BandIndexEntry], sort_by: str, sort_order: str) -> List[BandIndexEntry]:
    """Sort bands by specified field and order with enhanced sorting options."""
    reverse = sort_order.lower() == "desc"
    
    if sort_by == "name":
        return sorted(bands, key=lambda b: b.name.lower(), reverse=reverse)
    elif sort_by == "albums_count":
        return sorted(bands, key=lambda b: b.albums_count, reverse=reverse)
    elif sort_by == "last_updated":
        return sorted(bands, key=lambda b: b.last_updated, reverse=reverse)
    elif sort_by == "completion":
        def completion_percentage(band):
            if band.albums_count == 0:
                return 100.0
            return ((band.albums_count - band.missing_albums_count) / band.albums_count) * 100
        return sorted(bands, key=completion_percentage, reverse=reverse)
    elif sort_by == "compliance":
        return sorted(bands, key=lambda b: b.name.lower(), reverse=reverse)
    else:
        # Default to name sorting
        return sorted(bands, key=lambda b: b.name.lower(), reverse=reverse)


def _build_band_info(band_entry: BandIndexEntry, include_albums: bool = False, album_details_filter: Optional[str] = None) -> Dict[str, Any]:
    """
    Build detailed band information dictionary with enhanced metadata.
    
    Args:
        band_entry: BandIndexEntry to build info from
        include_albums: Whether to include detailed album information
        album_details_filter: If 'local', only include local albums in album details; if 'missing', only missing albums; None for all
        
    Returns:
        Dictionary with enhanced band information
    """
    # Build basic band information
    band_info = _build_basic_band_info(band_entry)
    
    # Load and add enhanced metadata if available
    try:
        metadata = load_band_metadata(band_entry.name)
        if metadata:
            _add_enhanced_metadata_to_band_info(band_info, metadata)
            
            # Include detailed album information if requested
            if include_albums and (metadata.albums or metadata.albums_missing):
                _add_album_details_to_band_info(band_info, metadata, album_details_filter)
                
    except Exception as e:
        # If metadata loading fails, continue with basic info
        band_info["metadata_error"] = str(e)
    
    return band_info


def _build_basic_band_info(band_entry: BandIndexEntry) -> Dict[str, Any]:
    """
    Build basic band information from band index entry.
    
    Args:
        band_entry: BandIndexEntry to build info from
        
    Returns:
        Dictionary with basic band information
    """
    completion_percentage = 100.0
    if band_entry.albums_count > 0:
        completion_percentage = round(
            ((band_entry.albums_count - band_entry.missing_albums_count) / band_entry.albums_count * 100), 1
        )
    
    return {
        "name": band_entry.name,
        "albums_count": band_entry.albums_count,
        "folder_path": band_entry.folder_path,
        "missing_albums_count": band_entry.missing_albums_count,
        "has_metadata": band_entry.has_metadata,
        "has_analysis": band_entry.has_analysis,
        "last_updated": band_entry.last_updated,
        "completion_percentage": completion_percentage,
        "cache_status": "cached" if band_entry.has_metadata else "no_cache"
    }


def _add_enhanced_metadata_to_band_info(band_info: Dict[str, Any], metadata: BandMetadata) -> None:
    """
    Add enhanced metadata fields to band info dictionary.
    
    Args:
        band_info: Dictionary to update with enhanced metadata
        metadata: BandMetadata instance with enhanced data
    """
    # Add basic metadata fields
    _add_basic_metadata_fields(band_info, metadata)
    
    # Add folder structure information
    _add_folder_structure_info(band_info, metadata)
    
    # Add album type distribution
    _add_album_type_distribution(band_info, metadata)
    
    # Add analysis information
    _add_analysis_info(band_info, metadata)


def _add_basic_metadata_fields(band_info: Dict[str, Any], metadata: BandMetadata) -> None:
    """
    Add basic metadata fields to band info.
    
    Args:
        band_info: Dictionary to update
        metadata: BandMetadata instance
    """
    if metadata.formed:
        band_info["formed"] = metadata.formed
    if metadata.genres:
        band_info["genres"] = metadata.genres
    if metadata.origin:
        band_info["origin"] = metadata.origin


def _add_folder_structure_info(band_info: Dict[str, Any], metadata: BandMetadata) -> None:
    """
    Add folder structure information to band info.
    
    Args:
        band_info: Dictionary to update
        metadata: BandMetadata instance
    """
    if metadata.folder_structure:
        band_info["folder_structure"] = {
            "structure_type": metadata.folder_structure.structure_type.value,
            "consistency": metadata.folder_structure.consistency.value,
            "structure_score": metadata.folder_structure.structure_score,
            "organization_health": metadata.folder_structure.get_organization_health(),
            "needs_migration": metadata.folder_structure.is_migration_recommended(),
            "recommendations_count": len(metadata.folder_structure.recommendations)
        }


def _add_album_type_distribution(band_info: Dict[str, Any], metadata: BandMetadata) -> None:
    """
    Add album type distribution to band info.
    
    Args:
        band_info: Dictionary to update
        metadata: BandMetadata instance
    """
    if metadata.albums:
        album_types = {}
        for album in metadata.albums:
            album_type = album.type.value if hasattr(album.type, 'value') else str(album.type)
            album_types[album_type] = album_types.get(album_type, 0) + 1
        
        band_info["album_types_distribution"] = album_types


def _add_analysis_info(band_info: Dict[str, Any], metadata: BandMetadata) -> None:
    """
    Add analysis information to band info.
    
    Args:
        band_info: Dictionary to update
        metadata: BandMetadata instance
    """
    if metadata.analyze:
        band_info["analysis"] = {
            "band_rating": metadata.analyze.rate,
            "has_review": bool(metadata.analyze.review),
            "albums_analyzed": len(metadata.analyze.albums),
            "similar_bands_count": len(metadata.analyze.similar_bands)
        }


def _add_album_details_to_band_info(band_info: Dict[str, Any], metadata: BandMetadata, 
                                   album_details_filter: Optional[str]) -> None:
    """
    Add detailed album information to band info.
    
    Args:
        band_info: Dictionary to update
        metadata: BandMetadata instance
        album_details_filter: Filter for album details ('local', 'missing', or None)
    """
    band_info["metadata"] = True
    album_details = []
    
    # Add local albums (found in folder structure)
    if album_details_filter in (None, "local"):
        for album in metadata.albums:
            if album_details_filter == "missing":
                continue
            album_detail = _create_album_detail_dict(album, missing=False)
            album_details.append(album_detail)
    
    # Add missing albums (not found in folder structure)
    if album_details_filter in (None, "missing"):
        for album in metadata.albums_missing:
            if album_details_filter == "local":
                continue
            album_detail = _create_album_detail_dict(album, missing=True)
            album_details.append(album_detail)
    
    band_info["albums"] = album_details


def _create_album_detail_dict(album, missing: bool) -> Dict[str, Any]:
    """
    Create album detail dictionary.
    
    Args:
        album: Album instance
        missing: Whether the album is missing
        
    Returns:
        Album detail dictionary
    """
    return {
        "album_name": album.album_name,
        "year": album.year,
        "type": album.type.value if hasattr(album.type, 'value') else str(album.type),
        "edition": album.edition,
        "track_count": album.track_count,
        "missing": missing,
        "folder_path": album.folder_path
    }


def _build_filters_summary(search_query: Optional[str], filter_genre: Optional[str], 
                          filter_has_metadata: Optional[bool], filter_missing_albums: Optional[bool],
                          filter_album_type: Optional[str], filter_compliance_level: Optional[str],
                          filter_structure_type: Optional[str]) -> Dict[str, Any]:
    """Build a summary of applied filters."""
    filters = {}
    
    if search_query:
        filters["search_query"] = search_query
    if filter_genre:
        filters["genre"] = filter_genre
    if filter_has_metadata is not None:
        filters["has_metadata"] = filter_has_metadata
    if filter_missing_albums is not None:
        filters["missing_albums"] = filter_missing_albums
    if filter_album_type:
        filters["album_type"] = filter_album_type
    if filter_compliance_level:
        filters["compliance_level"] = filter_compliance_level
    if filter_structure_type:
        filters["structure_type"] = filter_structure_type
    
    return filters


def load_band_metadata(band_name: str) -> Optional[BandMetadata]:
    """
    Load band metadata from JSON file.
    
    Args:
        band_name: Name of the band
        
    Returns:
        BandMetadata instance or None if not found
        
    Raises:
        StorageError: If load operation fails
    """
    try:
        config = get_config()
        band_folder = Path(config.MUSIC_ROOT_PATH) / band_name
        metadata_file = band_folder / ".band_metadata.json"
        
        if not metadata_file.exists():
            return None
        
        metadata_dict = JSONStorage.load_json(metadata_file)
        return BandMetadata(**metadata_dict)
        
    except Exception as e:
        raise StorageError(f"Failed to load band metadata for {band_name}: {e}")


def load_collection_index() -> Optional[CollectionIndex]:
    """
    Load collection index from JSON file.
    
    Returns:
        CollectionIndex instance or None if not found
        
    Raises:
        StorageError: If load operation fails
    """
    try:
        config = get_config()
        collection_file = Path(config.MUSIC_ROOT_PATH) / ".collection_index.json"
        
        if not collection_file.exists():
            return None
        
        index_dict = JSONStorage.load_json(collection_file)
        return CollectionIndex(**index_dict)
        
    except Exception as e:
        raise StorageError(f"Failed to load collection index: {e}")


def update_collection_index(index: CollectionIndex) -> Dict[str, Any]:
    """
    Update collection index with new data.
    
    Args:
        index: CollectionIndex instance to save
        
    Returns:
        Dict with operation status and details
        
    Raises:
        StorageError: If save operation fails
    """
    try:
        config = get_config()
        collection_file = Path(config.MUSIC_ROOT_PATH) / ".collection_index.json"
        
        # Update timestamp
        index.last_scan = datetime.now().isoformat()
        
        # Recalculate stats before saving to ensure they're accurate
        index._update_stats()
        
        # Save with atomic write and backup
        index_dict = index.model_dump()
        JSONStorage.save_json(collection_file, index_dict, backup=True)
        
        return {
            "status": "success",
            "message": "Collection index updated",
            "file_path": str(collection_file),
            "total_bands": index.stats.total_bands,
            "total_albums": index.stats.total_albums,
            "last_scan": index.last_scan
        }
        
    except Exception as e:
        raise StorageError(f"Failed to update collection index: {e}")


def cleanup_backups(max_backups: int = 5) -> Dict[str, Any]:
    """
    Cleanup old backup files, keeping only the most recent ones.
    
    Args:
        max_backups: Maximum number of backup files to keep per original file
        
    Returns:
        Dict with cleanup statistics
    """
    try:
        config = get_config()
        music_root = Path(config.MUSIC_ROOT_PATH)
        
        cleaned_count = 0
        total_freed_size = 0
        
        # Find all backup files
        backup_files = list(music_root.rglob("*.backup*"))
        
        # Group by original file
        backup_groups = {}
        for backup_file in backup_files:
            # Extract original file path
            original_name = backup_file.name.split('.backup')[0]
            original_path = backup_file.parent / original_name
            
            if original_path not in backup_groups:
                backup_groups[original_path] = []
            backup_groups[original_path].append(backup_file)
        
        # Keep only recent backups
        for original_path, backups in backup_groups.items():
            if len(backups) > max_backups:
                # Sort by modification time (newest first)
                backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                
                # Remove old backups
                for old_backup in backups[max_backups:]:
                    try:
                        file_size = old_backup.stat().st_size
                        old_backup.unlink()
                        cleaned_count += 1
                        total_freed_size += file_size
                    except Exception:
                        continue  # Skip files that can't be deleted
        
        return {
            "status": "success",
            "message": f"Cleanup completed: {cleaned_count} backup files removed",
            "files_removed": cleaned_count,
            "space_freed_bytes": total_freed_size,
            "space_freed_mb": round(total_freed_size / (1024 * 1024), 2)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Backup cleanup failed: {e}",
            "files_removed": 0,
            "space_freed_bytes": 0
        } 