"""
Local Storage Management for Music Collection MCP Server.

This module provides comprehensive JSON file operations including atomic writes,
file locking, backup/recovery, and metadata synchronization.
"""

import json
import logging
import os
import shutil
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
from datetime import datetime

# Try to import fcntl for Unix-like systems, handle Windows gracefully
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

from src.models import (
    BandMetadata, 
    BandAnalysis, 
    CollectionIndex, 
    CollectionInsight, 
    BandIndexEntry,
    AlbumAnalysis
)
from src.di import get_config

# Import standardized exceptions
from src.exceptions import (
    StorageError, 
    ValidationError, 
    DataError,
    create_storage_error,
    wrap_exception
)

# Configure logging
logger = logging.getLogger(__name__)


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
        # Validate input parameter type for safety
        if not isinstance(metadata, BandMetadata):
            raise ValidationError(
                f"metadata parameter must be BandMetadata instance, got {type(metadata)}",
                field_name="metadata",
                field_value=str(type(metadata)),
                user_message="Invalid metadata format provided. Expected BandMetadata object."
            )
            
        config = get_config()
        band_folder = Path(config.MUSIC_ROOT_PATH) / band_name
        metadata_file = band_folder / ".band_metadata.json"
        
        # If file exists, preserve existing analyze and folder_structure data
        existing_analyze = None
        existing_folder_structure = None
        if metadata_file.exists():
            try:
                existing_metadata_dict = JSONStorage.load_json(metadata_file)
                existing_metadata = BandMetadata(**existing_metadata_dict)
                existing_analyze = existing_metadata.analyze
                existing_folder_structure = existing_metadata.folder_structure
            except Exception as e:
                # If loading fails, continue without preserving (file might be corrupted)
                logger.warning(f"Could not load existing metadata for {band_name}: {e}")
                existing_analyze = None
                existing_folder_structure = None
        
        # Safely preserve existing analyze data if it exists
        if existing_analyze is not None:
            try:
                metadata.analyze = existing_analyze
            except Exception as e:
                logger.warning(f"Could not set analyze data for {band_name}: {e}")
            
        # Safely preserve existing folder_structure data if it exists
        if existing_folder_structure is not None:
            try:
                metadata.folder_structure = existing_folder_structure
            except Exception as e:
                logger.warning(f"Could not set folder_structure data for {band_name}: {e}")

        # Update timestamp and metadata saved timestamp
        try:
            metadata.update_metadata_saved_timestamp()  # This also calls update_timestamp()
        except Exception as e:
            logger.warning(f"Could not update metadata saved timestamp for {band_name}: {e}")
        
        # Convert to dict for JSON serialization
        metadata_dict = metadata.model_dump()
        
        # Save with atomic write and backup
        JSONStorage.save_json(metadata_file, metadata_dict, backup=True)
        
        return {
            "status": "success",
            "message": f"Band metadata saved for {band_name}",
            "file_path": str(metadata_file),
            "last_updated": metadata.last_updated,
            "albums_count": metadata.albums_count
        }
        
    except Exception as e:
        if isinstance(e, (StorageError, ValidationError, DataError)):
            # Re-raise our standardized exceptions
            raise
        else:
            # Wrap generic exceptions
            raise create_storage_error("save band metadata", band_name, e)


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
        
        # Load collection index for similar bands separation
        collection_index = load_collection_index()
        collection_band_names = set()
        if collection_index:
            collection_band_names = {b.name.lower() for b in collection_index.bands}
        
        # Separate similar bands into in-collection and missing
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
            for band in getattr(analysis, 'similar_bands', []):
                if band.lower() in collection_band_names:
                    similar_bands_in_collection.append(band)
                else:
                    similar_bands_missing.append(band)
            for band in getattr(analysis, 'similar_bands_missing', []):
                if band.lower() in collection_band_names:
                    if band not in similar_bands_in_collection:
                        similar_bands_in_collection.append(band)
                else:
                    similar_bands_missing.append(band)
        
        # Filter album analysis based on analyze_missing_albums parameter
        filtered_album_analysis = []
        excluded_count = 0
        for album_analysis in analysis.albums:
            filtered_analysis = AlbumAnalysis(
                album_name=album_analysis.album_name,
                review=album_analysis.review,
                rate=album_analysis.rate
            )
            filtered_album_analysis.append(filtered_analysis)
        
        # Create filtered analysis with separated similar bands
        filtered_analysis = BandAnalysis(
            review=analysis.review,
            rate=analysis.rate,
            albums=filtered_album_analysis,
            similar_bands=similar_bands_in_collection,
            similar_bands_missing=similar_bands_missing
        )
        
        # Update analysis section
        metadata.analyze = filtered_analysis
        metadata.update_timestamp()
        
        # Save updated metadata
        metadata_dict = metadata.model_dump()
        JSONStorage.save_json(metadata_file, metadata_dict, backup=True)
        
        # Calculate statistics
        filtered_albums_count = len(filtered_album_analysis)
        
        # Determine if we're analyzing missing albums (default True since we include all albums by default now)
        analyze_missing_albums = any(album_analysis.album_name in [album.album_name for album in metadata.albums_missing] for album_analysis in analysis.albums)
        
        # Create appropriate message based on settings
        if analyze_missing_albums and len(metadata.albums_missing) > 0:
            message = f"Band analysis saved for {band_name} including all albums"
        else:
            album_text = f"{filtered_albums_count} album reviews"
            similar_bands_text = f"{filtered_analysis.total_similar_bands_count} similar bands"
            message = f"Band analysis saved for {band_name} including {album_text} and {similar_bands_text}"
        
        return {
            "status": "success",
            "message": message,
            "file_path": str(metadata_file),
            "band_rating": filtered_analysis.rate,
            "albums_analyzed": filtered_albums_count,
            "albums_excluded": excluded_count,
            "similar_bands_count": filtered_analysis.total_similar_bands_count,
            "similar_bands_in_collection": len(filtered_analysis.similar_bands),
            "similar_bands_missing": len(filtered_analysis.similar_bands_missing),
            "last_updated": metadata.last_updated,
            "analyze_missing_albums": analyze_missing_albums or len(metadata.albums_missing) > 0
        }
        
    except Exception as e:
        raise StorageError(f"Failed to save band analysis for {band_name}: {e}")


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
        config = get_config()
        collection_file = Path(config.MUSIC_ROOT_PATH) / ".collection_index.json"
        
        if not collection_file.exists():
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
                "filters_applied": _build_filters_summary(search_query, filter_genre, filter_has_metadata, filter_missing_albums, filter_album_type, filter_compliance_level, filter_structure_type),
                "sort": {"by": sort_by, "order": sort_order}
            }
        
        # Load collection index
        index_dict = JSONStorage.load_json(collection_file)
        index = CollectionIndex(**index_dict)
        
        # Start with all bands
        bands_to_process = index.bands.copy()
        
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
        
        # Apply sorting
        bands_to_process = _sort_bands_enhanced(bands_to_process, sort_by, sort_order)
        
        # Calculate pagination
        total_bands = len(bands_to_process)
        page_size = max(1, min(100, page_size))  # Clamp between 1-100
        page = max(1, page)  # Ensure page is at least 1
        total_pages = (total_bands + page_size - 1) // page_size if total_bands > 0 else 0
        
        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_bands = bands_to_process[start_idx:end_idx]
        
        # Build detailed band information
        bands_info = []
        for band_entry in paginated_bands:
            band_info = _build_band_info(band_entry, include_albums, album_details_filter)
            bands_info.append(band_info)
        
        return {
            "status": "success",
            "message": f"Found {total_bands} bands (showing page {page} of {total_pages})",
            "bands": bands_info,
            # Backward compatibility - keep original fields at top level
            "total_bands": index.stats.total_bands,
            "total_albums": index.stats.total_albums,
            "total_missing_albums": index.stats.total_missing_albums,
            "collection_completion": index.stats.completion_percentage,
            "last_scan": index.last_scan,
            # Enhanced functionality - new fields
            "pagination": {
                "total_bands": total_bands,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1
            },
            "collection_summary": {
                "total_bands": index.stats.total_bands,
                "total_albums": index.stats.total_albums,
                "total_missing_albums": index.stats.total_missing_albums,
                "collection_completion": index.stats.completion_percentage,
                "last_scan": index.last_scan
            },
            "filters_applied": _build_filters_summary(search_query, filter_genre, filter_has_metadata, filter_missing_albums, filter_album_type, filter_compliance_level, filter_structure_type),
            "sort": {"by": sort_by, "order": sort_order}
        }
        
    except Exception as e:
        raise StorageError(f"Failed to get band list: {e}")


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
    config = get_config()
    band_folder = Path(config.MUSIC_ROOT_PATH) / band_entry.folder_path
    
    # Basic band information
    band_info = {
        "name": band_entry.name,
        "albums_count": band_entry.albums_count,
        "folder_path": band_entry.folder_path,
        "missing_albums_count": band_entry.missing_albums_count,
        "has_metadata": band_entry.has_metadata,
        "has_analysis": band_entry.has_analysis,
        "last_updated": band_entry.last_updated,
        "completion_percentage": round(((band_entry.albums_count - band_entry.missing_albums_count) / band_entry.albums_count * 100), 1) if band_entry.albums_count > 0 else 100.0,
        "cache_status": "cached" if band_entry.has_metadata else "no_cache"
    }
    
    # Load enhanced metadata if available
    try:
        metadata = load_band_metadata(band_entry.name)
        if metadata:
            # Add basic metadata fields
            if metadata.formed:
                band_info["formed"] = metadata.formed
            if metadata.genres:
                band_info["genres"] = metadata.genres
            if metadata.origin:
                band_info["origin"] = metadata.origin
                
            # Add enhanced features
            if metadata.folder_structure:
                band_info["folder_structure"] = {
                    "structure_type": metadata.folder_structure.structure_type.value,
                    "consistency": metadata.folder_structure.consistency.value,
                    "structure_score": metadata.folder_structure.structure_score,
                    "organization_health": metadata.folder_structure.get_organization_health(),
                    "needs_migration": metadata.folder_structure.is_migration_recommended(),
                    "recommendations_count": len(metadata.folder_structure.recommendations)
                }
            
            # Add album type distribution
            if metadata.albums:
                album_types = {}
                for album in metadata.albums:
                    album_type = album.type.value if hasattr(album.type, 'value') else str(album.type)
                    album_types[album_type] = album_types.get(album_type, 0) + 1
                
                band_info["album_types_distribution"] = album_types
            
            # Add analysis information
            if metadata.analyze:
                band_info["analysis"] = {
                    "band_rating": metadata.analyze.rate,
                    "has_review": bool(metadata.analyze.review),
                    "albums_analyzed": len(metadata.analyze.albums),
                    "similar_bands_count": len(metadata.analyze.similar_bands)
                }
            
            # Include detailed album information if requested
            if include_albums and (metadata.albums or metadata.albums_missing):
                band_info["metadata"] = True
                album_details = []
                # Add local albums (found in folder structure)
                if album_details_filter in (None, "local"):
                    for album in metadata.albums:
                        if album_details_filter == "missing":
                            continue
                        album_detail = {
                            "album_name": album.album_name,
                            "year": album.year,
                            "type": album.type.value if hasattr(album.type, 'value') else str(album.type),
                            "edition": album.edition,
                            "track_count": album.track_count,
                            "missing": False,
                            "folder_path": album.folder_path
                        }
                        album_details.append(album_detail)
                # Add missing albums (not found in folder structure)
                if album_details_filter in (None, "missing"):
                    for album in metadata.albums_missing:
                        if album_details_filter == "local":
                            continue
                        album_detail = {
                            "album_name": album.album_name,
                            "year": album.year,
                            "type": album.type.value if hasattr(album.type, 'value') else str(album.type),
                            "edition": album.edition,
                            "track_count": album.track_count,
                            "missing": True,
                            "folder_path": album.folder_path
                        }
                        album_details.append(album_detail)
                band_info["albums"] = album_details
                
    except Exception as e:
        # If metadata loading fails, continue with basic info
        band_info["metadata_error"] = str(e)
    
    return band_info


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