"""
Local Storage Management for Music Collection MCP Server.

This module provides comprehensive JSON file operations including atomic writes,
file locking, backup/recovery, and metadata synchronization.
"""

import json
import os
import shutil
import fcntl
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
from datetime import datetime

from ..models import (
    BandMetadata, 
    BandAnalysis, 
    CollectionIndex, 
    CollectionInsight, 
    BandIndexEntry
)
from ..config import Config


class StorageError(Exception):
    """Base exception for storage operations."""
    pass


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
                if os.name != 'nt':  # Unix-like systems
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except (IOError, OSError):
                time.sleep(0.1)
        else:
            raise StorageError(f"Could not acquire lock for {file_path} within {timeout} seconds")
        
        yield
        
    finally:
        # Release lock and cleanup
        try:
            if os.name != 'nt':  # Unix-like systems
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
            raise StorageError(f"Failed to save JSON to {file_path}: {e}")
    
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
                raise StorageError(f"File not found: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise StorageError(f"Invalid JSON in {file_path}: {e}")
        except Exception as e:
            raise StorageError(f"Failed to load JSON from {file_path}: {e}")
    
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
        
    Returns:
        Dict with operation status and details
        
    Raises:
        StorageError: If save operation fails
    """
    try:
        config = Config()
        band_folder = Path(config.MUSIC_ROOT_PATH) / band_name
        metadata_file = band_folder / ".band_metadata.json"
        
        # Ensure band name matches metadata
        if metadata.band_name != band_name:
            metadata.band_name = band_name
        
        # Update timestamp
        metadata.update_timestamp()
        
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
        raise StorageError(f"Failed to save band metadata for {band_name}: {e}")


def save_band_analyze(band_name: str, analysis: BandAnalysis) -> Dict[str, Any]:
    """
    Save band analysis data with reviews and ratings.
    
    Args:
        band_name: Name of the band
        analysis: BandAnalysis instance to save
        
    Returns:
        Dict with operation status and details
        
    Raises:
        StorageError: If save operation fails
    """
    try:
        config = Config()
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
        
        # Update analysis section
        metadata.analyze = analysis
        metadata.update_timestamp()
        
        # Save updated metadata
        metadata_dict = metadata.model_dump()
        JSONStorage.save_json(metadata_file, metadata_dict, backup=True)
        
        return {
            "status": "success",
            "message": f"Band analysis saved for {band_name}",
            "file_path": str(metadata_file),
            "band_rating": analysis.rate,
            "albums_analyzed": len(analysis.albums),
            "similar_bands_count": len(analysis.similar_bands),
            "last_updated": metadata.last_updated
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
        config = Config()
        collection_file = Path(config.MUSIC_ROOT_PATH) / ".collection_index.json"
        
        # Load existing collection index or create new
        if collection_file.exists():
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
    sort_by: str = "name",
    sort_order: str = "asc",
    page: int = 1,
    page_size: int = 50,
    include_albums: bool = False
) -> Dict[str, Any]:
    """
    Get a list of all discovered bands with enhanced filtering, sorting, and pagination.
    
    Args:
        search_query: Search term to filter bands by name or album name
        filter_genre: Filter bands by genre (if metadata available)
        filter_has_metadata: Filter bands that have/don't have metadata files
        filter_missing_albums: Filter bands with/without missing albums
        sort_by: Field to sort by ('name', 'albums_count', 'last_updated', 'completion')
        sort_order: Sort order ('asc' or 'desc')
        page: Page number for pagination (1-based)
        page_size: Number of results per page (1-100)
        include_albums: Include album details for each band
        
    Returns:
        Dict containing filtered and paginated band list with metadata
        
    Raises:
        StorageError: If operation fails
    """
    try:
        config = Config()
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
                "filters_applied": _build_filters_summary(search_query, filter_genre, filter_has_metadata, filter_missing_albums),
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
        
        # Apply sorting
        bands_to_process = _sort_bands(bands_to_process, sort_by, sort_order)
        
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
            band_info = _build_band_info(band_entry, include_albums)
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
            "filters_applied": _build_filters_summary(search_query, filter_genre, filter_has_metadata, filter_missing_albums),
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


def _build_band_info(band_entry: BandIndexEntry, include_albums: bool = False) -> Dict[str, Any]:
    """Build detailed band information dictionary."""
    band_info = {
        "name": band_entry.name,
        "albums_count": band_entry.albums_count,
        "missing_albums_count": band_entry.missing_albums_count,
        "has_metadata": band_entry.has_metadata,
        "folder_path": band_entry.folder_path,
        "last_updated": band_entry.last_updated,
        "completion_percentage": round(
            ((band_entry.albums_count - band_entry.missing_albums_count) / 
             max(band_entry.albums_count, 1)) * 100, 1
        ),
        "cache_status": "cached" if band_entry.has_metadata else "no_cache"
    }
    
    # Include detailed album information if requested
    if include_albums and band_entry.has_metadata:
        try:
            metadata = load_band_metadata(band_entry.name)
            if metadata:
                band_info["metadata"] = {
                    "formed": metadata.formed,
                    "genres": metadata.genres,
                    "origin": metadata.origin,
                    "members": metadata.members,
                    "description": metadata.description
                }
                
                band_info["albums"] = []
                for album in metadata.albums:
                    album_info = {
                        "album_name": album.album_name,
                        "missing": album.missing,
                        "tracks_count": album.tracks_count,
                        "duration": album.duration,
                        "year": album.year,
                        "genres": album.genres
                    }
                    band_info["albums"].append(album_info)
                
                # Include analysis if available
                if metadata.analyze:
                    band_info["analysis"] = {
                        "review": metadata.analyze.review,
                        "rate": metadata.analyze.rate,
                        "similar_bands": metadata.analyze.similar_bands
                    }
                    
                    if metadata.analyze.albums:
                        band_info["album_analysis"] = []
                        for album_analysis in metadata.analyze.albums:
                            band_info["album_analysis"].append({
                                "review": album_analysis.review,
                                "rate": album_analysis.rate
                            })
        except:
            # If metadata can't be loaded, just mark as unavailable
            band_info["metadata_error"] = "Could not load band metadata"
    
    return band_info


def _build_filters_summary(search_query: Optional[str], filter_genre: Optional[str], 
                          filter_has_metadata: Optional[bool], filter_missing_albums: Optional[bool]) -> Dict[str, Any]:
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
        config = Config()
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
        config = Config()
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
        config = Config()
        collection_file = Path(config.MUSIC_ROOT_PATH) / ".collection_index.json"
        
        # Update timestamp
        index.last_scan = datetime.now().isoformat()
        
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
        config = Config()
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