"""
Cache Management for Music Collection MCP Server.

This module provides comprehensive cache management including expiration logic,
validation functions, statistics tracking, cleanup utilities, and migration tools.
"""

import json
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

from src.models import BandMetadata, CollectionIndex, BandIndexEntry
from src.config import Config


class CacheStatus(Enum):
    """Cache status enumeration."""
    VALID = "valid"
    EXPIRED = "expired"
    CORRUPTED = "corrupted"
    MISSING = "missing"


@dataclass
class CacheEntry:
    """
    Individual cache entry with metadata.
    
    Attributes:
        file_path: Path to cached file
        size: File size in bytes
        created_at: Creation timestamp
        last_accessed: Last access timestamp
        last_modified: Last modification timestamp
        status: Current cache status
    """
    file_path: Path
    size: int
    created_at: datetime
    last_accessed: datetime
    last_modified: datetime
    status: CacheStatus


@dataclass
class CacheStats:
    """
    Cache statistics tracking.
    
    Attributes:
        total_entries: Total number of cache entries
        valid_entries: Number of valid cache entries
        expired_entries: Number of expired cache entries
        corrupted_entries: Number of corrupted cache entries
        total_size: Total cache size in bytes
        oldest_entry: Oldest cache entry date
        newest_entry: Newest cache entry date
        cache_hit_rate: Cache hit rate percentage
        last_cleanup: Last cleanup operation timestamp
    """
    total_entries: int = 0
    valid_entries: int = 0
    expired_entries: int = 0
    corrupted_entries: int = 0
    total_size: int = 0
    oldest_entry: Optional[datetime] = None
    newest_entry: Optional[datetime] = None
    cache_hit_rate: float = 0.0
    last_cleanup: Optional[datetime] = None


class CacheError(Exception):
    """Base exception for cache operations."""
    pass


class CacheManager:
    """
    Comprehensive cache management for music collection metadata.
    
    Handles cache expiration, validation, statistics, cleanup, and migration.
    """
    
    def __init__(self, music_root: Optional[str] = None, cache_duration_days: Optional[int] = None):
        """
        Initialize cache manager.
        
        Args:
            music_root: Path to music root directory (uses config default if None)
            cache_duration_days: Cache duration in days (uses config default if None)
        """
        config = Config()
        self.music_root = Path(music_root or config.MUSIC_ROOT_PATH)
        self.cache_duration_days = cache_duration_days or config.CACHE_DURATION_DAYS
        self.cache_duration = timedelta(days=self.cache_duration_days)
        
        # Cache statistics tracking
        self._access_count = 0
        self._hit_count = 0
        
    def is_cache_valid(self, file_path: Path) -> bool:
        """
        Check if cache file is valid and not expired.
        
        Args:
            file_path: Path to cache file
            
        Returns:
            True if cache is valid and not expired
        """
        try:
            if not file_path.exists():
                return False
            
            # Check file modification time
            mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            now = datetime.now()
            
            # Check if expired
            if now - mod_time > self.cache_duration:
                return False
            
            # Check if file is readable and contains valid JSON
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    json.load(f)
                return True
            except (json.JSONDecodeError, IOError):
                return False
                
        except Exception:
            return False
    
    def get_cache_status(self, file_path: Path) -> CacheStatus:
        """
        Get detailed cache status for a file.
        
        Args:
            file_path: Path to cache file
            
        Returns:
            CacheStatus indicating current status
        """
        if not file_path.exists():
            return CacheStatus.MISSING
        
        try:
            # Check file modification time
            mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            now = datetime.now()
            
            # Check if expired
            if now - mod_time > self.cache_duration:
                return CacheStatus.EXPIRED
            
            # Check if file is readable and contains valid JSON
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    json.load(f)
                return CacheStatus.VALID
            except (json.JSONDecodeError, IOError):
                return CacheStatus.CORRUPTED
                
        except Exception:
            return CacheStatus.CORRUPTED
    
    def validate_band_metadata_cache(self, band_name: str) -> Dict[str, Any]:
        """
        Validate cache for specific band metadata.
        
        Args:
            band_name: Name of band to validate cache for
            
        Returns:
            Dict with validation results and recommendations
        """
        band_folder = self.music_root / band_name
        metadata_file = band_folder / ".band_metadata.json"
        
        self._access_count += 1
        
        result = {
            "band_name": band_name,
            "metadata_file": str(metadata_file),
            "exists": metadata_file.exists(),
            "status": self.get_cache_status(metadata_file).value,
            "size_bytes": 0,
            "last_modified": None,
            "age_days": None,
            "is_valid": False,
            "recommendations": []
        }
        
        if metadata_file.exists():
            try:
                stat = metadata_file.stat()
                result["size_bytes"] = stat.st_size
                mod_time = datetime.fromtimestamp(stat.st_mtime)
                result["last_modified"] = mod_time.isoformat()
                result["age_days"] = (datetime.now() - mod_time).days
                
                if self.is_cache_valid(metadata_file):
                    result["is_valid"] = True
                    self._hit_count += 1
                    result["recommendations"].append("Cache is valid and current")
                else:
                    if result["age_days"] > self.cache_duration_days:
                        result["recommendations"].append("Cache is expired - consider refreshing metadata")
                    else:
                        result["recommendations"].append("Cache file may be corrupted - consider regenerating")
                        
            except Exception as e:
                result["recommendations"].append(f"Error reading cache file: {e}")
        else:
            result["recommendations"].append("No metadata cache found - consider fetching band information")
        
        return result
    
    def get_cache_statistics(self) -> CacheStats:
        """
        Generate comprehensive cache statistics.
        
        Returns:
            CacheStats object with current statistics
        """
        stats = CacheStats()
        
        try:
            # Scan all band folders for metadata files
            cache_entries = []
            
            if self.music_root.exists():
                for band_folder in self.music_root.iterdir():
                    if band_folder.is_dir() and not band_folder.name.startswith('.'):
                        metadata_file = band_folder / ".band_metadata.json"
                        if metadata_file.exists():
                            try:
                                stat = metadata_file.stat()
                                mod_time = datetime.fromtimestamp(stat.st_mtime)
                                access_time = datetime.fromtimestamp(stat.st_atime)
                                
                                entry = CacheEntry(
                                    file_path=metadata_file,
                                    size=stat.st_size,
                                    created_at=mod_time,  # Use mod time as creation time
                                    last_accessed=access_time,
                                    last_modified=mod_time,
                                    status=self.get_cache_status(metadata_file)
                                )
                                cache_entries.append(entry)
                                
                            except Exception:
                                continue
                
                # Calculate statistics
                stats.total_entries = len(cache_entries)
                stats.total_size = sum(entry.size for entry in cache_entries)
                
                # Count by status
                status_counts = {}
                for entry in cache_entries:
                    status_counts[entry.status] = status_counts.get(entry.status, 0) + 1
                
                stats.valid_entries = status_counts.get(CacheStatus.VALID, 0)
                stats.expired_entries = status_counts.get(CacheStatus.EXPIRED, 0)
                stats.corrupted_entries = status_counts.get(CacheStatus.CORRUPTED, 0)
                
                # Find oldest and newest entries
                if cache_entries:
                    dates = [entry.last_modified for entry in cache_entries]
                    stats.oldest_entry = min(dates)
                    stats.newest_entry = max(dates)
                
                # Calculate hit rate
                if self._access_count > 0:
                    stats.cache_hit_rate = (self._hit_count / self._access_count) * 100
            
            # Check for collection index cache
            collection_index_file = self.music_root / ".collection_index.json"
            if collection_index_file.exists():
                try:
                    stat = collection_index_file.stat()
                    mod_time = datetime.fromtimestamp(stat.st_mtime)
                    
                    # Add collection index to total size
                    stats.total_size += stat.st_size
                    
                    # Update oldest/newest if collection index is involved
                    if stats.oldest_entry is None or mod_time < stats.oldest_entry:
                        stats.oldest_entry = mod_time
                    if stats.newest_entry is None or mod_time > stats.newest_entry:
                        stats.newest_entry = mod_time
                        
                except Exception:
                    pass
                    
        except Exception as e:
            raise CacheError(f"Failed to generate cache statistics: {e}")
        
        return stats
    
    def cleanup_expired_cache(self) -> Dict[str, Any]:
        """
        Clean up expired cache files.
        
        Returns:
            Dict with cleanup results and statistics
        """
        result = {
            "cleaned_files": [],
            "total_cleaned": 0,
            "space_freed_bytes": 0,
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            if not self.music_root.exists():
                result["errors"].append(f"Music root directory does not exist: {self.music_root}")
                return result
            
            # Clean up expired band metadata files
            for band_folder in self.music_root.iterdir():
                if band_folder.is_dir() and not band_folder.name.startswith('.'):
                    metadata_file = band_folder / ".band_metadata.json"
                    
                    if metadata_file.exists():
                        status = self.get_cache_status(metadata_file)
                        
                        if status in [CacheStatus.EXPIRED, CacheStatus.CORRUPTED]:
                            try:
                                size = metadata_file.stat().st_size
                                metadata_file.unlink()
                                
                                result["cleaned_files"].append({
                                    "file": str(metadata_file),
                                    "reason": status.value,
                                    "size_bytes": size
                                })
                                result["space_freed_bytes"] += size
                                
                            except Exception as e:
                                result["errors"].append(f"Failed to delete {metadata_file}: {e}")
            
            # Clean up expired collection index if corrupted
            collection_index_file = self.music_root / ".collection_index.json"
            if collection_index_file.exists():
                status = self.get_cache_status(collection_index_file)
                
                if status == CacheStatus.CORRUPTED:
                    try:
                        size = collection_index_file.stat().st_size
                        collection_index_file.unlink()
                        
                        result["cleaned_files"].append({
                            "file": str(collection_index_file),
                            "reason": status.value,
                            "size_bytes": size
                        })
                        result["space_freed_bytes"] += size
                        
                    except Exception as e:
                        result["errors"].append(f"Failed to delete {collection_index_file}: {e}")
            
            result["total_cleaned"] = len(result["cleaned_files"])
            
        except Exception as e:
            result["errors"].append(f"Cache cleanup failed: {e}")
        
        return result
    
    def cleanup_cache_by_age(self, max_age_days: Optional[int] = None) -> Dict[str, Any]:
        """
        Clean up cache files older than specified age.
        
        Args:
            max_age_days: Maximum age in days (uses cache_duration_days if None)
            
        Returns:
            Dict with cleanup results
        """
        max_age = max_age_days or self.cache_duration_days
        cutoff_date = datetime.now() - timedelta(days=max_age)
        
        result = {
            "max_age_days": max_age,
            "cutoff_date": cutoff_date.isoformat(),
            "cleaned_files": [],
            "total_cleaned": 0,
            "space_freed_bytes": 0,
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            if not self.music_root.exists():
                result["errors"].append(f"Music root directory does not exist: {self.music_root}")
                return result
            
            # Clean up old band metadata files
            for band_folder in self.music_root.iterdir():
                if band_folder.is_dir() and not band_folder.name.startswith('.'):
                    metadata_file = band_folder / ".band_metadata.json"
                    
                    if metadata_file.exists():
                        try:
                            mod_time = datetime.fromtimestamp(metadata_file.stat().st_mtime)
                            
                            if mod_time < cutoff_date:
                                size = metadata_file.stat().st_size
                                metadata_file.unlink()
                                
                                result["cleaned_files"].append({
                                    "file": str(metadata_file),
                                    "age_days": (datetime.now() - mod_time).days,
                                    "size_bytes": size
                                })
                                result["space_freed_bytes"] += size
                                
                        except Exception as e:
                            result["errors"].append(f"Failed to process {metadata_file}: {e}")
            
            result["total_cleaned"] = len(result["cleaned_files"])
            
        except Exception as e:
            result["errors"].append(f"Age-based cache cleanup failed: {e}")
        
        return result
    
    def validate_collection_cache(self) -> Dict[str, Any]:
        """
        Validate cache consistency across entire collection.
        
        Returns:
            Dict with validation results and recommendations
        """
        result = {
            "collection_index_status": "missing",
            "band_cache_summary": {
                "total_bands": 0,
                "cached_bands": 0,
                "valid_cache": 0,
                "expired_cache": 0,
                "corrupted_cache": 0,
                "missing_cache": 0
            },
            "inconsistencies": [],
            "recommendations": [],
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Check collection index
            collection_index_file = self.music_root / ".collection_index.json"
            result["collection_index_status"] = self.get_cache_status(collection_index_file).value
            
            # Load collection index if valid
            collection_index = None
            if collection_index_file.exists() and self.is_cache_valid(collection_index_file):
                try:
                    with open(collection_index_file, 'r', encoding='utf-8') as f:
                        index_data = json.load(f)
                        collection_index = CollectionIndex(**index_data)
                except Exception as e:
                    result["inconsistencies"].append(f"Failed to load collection index: {e}")
            
            # Scan band folders
            band_folders = []
            if self.music_root.exists():
                for item in self.music_root.iterdir():
                    if item.is_dir() and not item.name.startswith('.'):
                        band_folders.append(item.name)
            
            result["band_cache_summary"]["total_bands"] = len(band_folders)
            
            # Check each band's cache
            for band_name in band_folders:
                metadata_file = self.music_root / band_name / ".band_metadata.json"
                
                if metadata_file.exists():
                    result["band_cache_summary"]["cached_bands"] += 1
                    status = self.get_cache_status(metadata_file)
                    
                    if status == CacheStatus.VALID:
                        result["band_cache_summary"]["valid_cache"] += 1
                    elif status == CacheStatus.EXPIRED:
                        result["band_cache_summary"]["expired_cache"] += 1
                    elif status == CacheStatus.CORRUPTED:
                        result["band_cache_summary"]["corrupted_cache"] += 1
                        result["inconsistencies"].append(f"Corrupted cache for band: {band_name}")
                else:
                    result["band_cache_summary"]["missing_cache"] += 1
            
            # Cross-check with collection index
            if collection_index:
                indexed_bands = {band.name for band in collection_index.bands}
                folder_bands = set(band_folders)
                
                # Find bands in index but not in folders
                missing_folders = indexed_bands - folder_bands
                if missing_folders:
                    result["inconsistencies"].extend([
                        f"Band in index but folder missing: {band}" for band in missing_folders
                    ])
                
                # Find bands in folders but not in index
                missing_index = folder_bands - indexed_bands
                if missing_index:
                    result["inconsistencies"].extend([
                        f"Band folder exists but not in index: {band}" for band in missing_index
                    ])
            
            # Generate recommendations
            if result["collection_index_status"] != "valid":
                result["recommendations"].append("Rebuild collection index")
            
            if result["band_cache_summary"]["expired_cache"] > 0:
                result["recommendations"].append(f"Refresh {result['band_cache_summary']['expired_cache']} expired band caches")
            
            if result["band_cache_summary"]["corrupted_cache"] > 0:
                result["recommendations"].append(f"Regenerate {result['band_cache_summary']['corrupted_cache']} corrupted band caches")
            
            if result["band_cache_summary"]["missing_cache"] > 0:
                result["recommendations"].append(f"Create metadata for {result['band_cache_summary']['missing_cache']} bands without cache")
            
            if result["inconsistencies"]:
                result["recommendations"].append("Resolve collection index inconsistencies")
                
        except Exception as e:
            result["inconsistencies"].append(f"Cache validation failed: {e}")
        
        return result
    
    def migrate_cache_format(self, target_version: str = "1.0") -> Dict[str, Any]:
        """
        Migrate cache files to new format version.
        
        Args:
            target_version: Target schema version
            
        Returns:
            Dict with migration results
        """
        result = {
            "target_version": target_version,
            "migrated_files": [],
            "backup_files": [],
            "errors": [],
            "total_migrated": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            if not self.music_root.exists():
                result["errors"].append(f"Music root directory does not exist: {self.music_root}")
                return result
            
            # Migrate collection index
            collection_index_file = self.music_root / ".collection_index.json"
            if collection_index_file.exists():
                try:
                    with open(collection_index_file, 'r', encoding='utf-8') as f:
                        index_data = json.load(f)
                    
                    current_version = index_data.get('metadata_version', '0.9')
                    
                    if current_version != target_version:
                        # Create backup
                        backup_file = collection_index_file.with_suffix(f'.{current_version}.backup')
                        shutil.copy2(collection_index_file, backup_file)
                        result["backup_files"].append(str(backup_file))
                        
                        # Update version
                        index_data['metadata_version'] = target_version
                        
                        # Save updated file
                        with open(collection_index_file, 'w', encoding='utf-8') as f:
                            json.dump(index_data, f, indent=2, ensure_ascii=False)
                        
                        result["migrated_files"].append({
                            "file": str(collection_index_file),
                            "from_version": current_version,
                            "to_version": target_version
                        })
                        
                except Exception as e:
                    result["errors"].append(f"Failed to migrate collection index: {e}")
            
            # Migrate band metadata files
            for band_folder in self.music_root.iterdir():
                if band_folder.is_dir() and not band_folder.name.startswith('.'):
                    metadata_file = band_folder / ".band_metadata.json"
                    
                    if metadata_file.exists():
                        try:
                            with open(metadata_file, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                            
                            # Check if migration is needed
                            needs_migration = False
                            
                            # Add missing fields that were introduced in v1.0
                            if 'last_updated' not in metadata:
                                metadata['last_updated'] = datetime.now().isoformat()
                                needs_migration = True
                            
                            if 'albums_count' not in metadata:
                                metadata['albums_count'] = len(metadata.get('albums', []))
                                needs_migration = True
                            
                            # Ensure albums have all required fields
                            albums = metadata.get('albums', [])
                            for album in albums:
                                if 'missing' not in album:
                                    album['missing'] = False
                                    needs_migration = True
                                if 'track_count' not in album:
                                    album['track_count'] = album.get('tracks_count', 0)
                                if 'tracks_count' in album:
                                    del album['tracks_count']
                            
                            if needs_migration:
                                # Create backup
                                backup_file = metadata_file.with_suffix('.backup')
                                shutil.copy2(metadata_file, backup_file)
                                result["backup_files"].append(str(backup_file))
                                
                                # Save updated metadata
                                with open(metadata_file, 'w', encoding='utf-8') as f:
                                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                                
                                result["migrated_files"].append({
                                    "file": str(metadata_file),
                                    "band": band_folder.name,
                                    "changes": "Added missing v1.0 fields"
                                })
                                
                        except Exception as e:
                            result["errors"].append(f"Failed to migrate {metadata_file}: {e}")
            
            result["total_migrated"] = len(result["migrated_files"])
            
        except Exception as e:
            result["errors"].append(f"Cache migration failed: {e}")
        
        return result
    
    def update_cache_access_time(self, file_path: Path) -> None:
        """
        Update access time for cache file (for statistics tracking).
        
        Args:
            file_path: Path to cache file
        """
        try:
            if file_path.exists():
                # Touch file to update access time
                file_path.touch(exist_ok=True)
        except Exception:
            pass  # Ignore access time update errors


# Convenience functions for common cache operations

def is_metadata_cache_valid(band_name: str, music_root: Optional[str] = None) -> bool:
    """
    Check if band metadata cache is valid.
    
    Args:
        band_name: Name of band to check
        music_root: Path to music root (uses config if None)
        
    Returns:
        True if cache is valid and not expired
    """
    cache_manager = CacheManager(music_root)
    band_folder = cache_manager.music_root / band_name
    metadata_file = band_folder / ".band_metadata.json"
    return cache_manager.is_cache_valid(metadata_file)


def cleanup_expired_caches(music_root: Optional[str] = None) -> Dict[str, Any]:
    """
    Clean up all expired cache files.
    
    Args:
        music_root: Path to music root (uses config if None)
        
    Returns:
        Dict with cleanup results
    """
    cache_manager = CacheManager(music_root)
    return cache_manager.cleanup_expired_cache()


def get_collection_cache_stats(music_root: Optional[str] = None) -> CacheStats:
    """
    Get cache statistics for entire collection.
    
    Args:
        music_root: Path to music root (uses config if None)
        
    Returns:
        CacheStats object with current statistics
    """
    cache_manager = CacheManager(music_root)
    return cache_manager.get_cache_statistics() 