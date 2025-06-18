"""
Unit tests for cache management functionality.

Tests cache expiration, validation, statistics tracking, cleanup utilities,
and migration tools for the Music Collection MCP Server.
"""

import pytest
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.tools.cache import (
    CacheManager,
    CacheStatus,
    CacheStats,
    CacheEntry,
    CacheError,
    is_metadata_cache_valid,
    cleanup_expired_caches,
    get_collection_cache_stats
)


# Module-level fixtures
@pytest.fixture
def temp_music_root():
    """Create temporary music root directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def cache_manager(temp_music_root):
    """Create CacheManager instance for testing."""
    return CacheManager(str(temp_music_root), cache_duration_days=30)


@pytest.fixture
def sample_band_metadata():
    """Create sample band metadata for testing."""
    return {
        "band_name": "Test Band",
        "formed": "2000",
        "genre": ["Rock"],
        "origin": "USA",
        "members": ["Singer", "Guitarist"],
        "albums_count": 2,
        "description": "A test band",
        "albums": [
            {
                "album_name": "First Album",
                "track_count": 10,
                "duration": "45min",
                "year": "2005",
                "genre": ["Rock"]
            }
        ],
        "albums_missing": [
            {
                "album_name": "Second Album", 
                "track_count": 12,
                "duration": "50min",
                "year": "2010",
                "genre": ["Rock"]
            }
        ],
        "last_updated": datetime.now().isoformat()
    }


class TestCacheManager:
    """Test CacheManager core functionality."""
    
    def test_cache_manager_initialization(self, temp_music_root):
        """Test CacheManager initialization with custom parameters."""
        cache_manager = CacheManager(str(temp_music_root), cache_duration_days=15)
        
        assert cache_manager.music_root == temp_music_root
        assert cache_manager.cache_duration_days == 15
        assert cache_manager.cache_duration == timedelta(days=15)
        assert cache_manager._access_count == 0
        assert cache_manager._hit_count == 0


class TestCacheValidation:
    """Test cache validation functionality."""
    
    def test_is_cache_valid_missing_file(self, cache_manager, temp_music_root):
        """Test cache validation for missing file."""
        missing_file = temp_music_root / "missing.json"
        assert not cache_manager.is_cache_valid(missing_file)
    
    def test_is_cache_valid_fresh_file(self, cache_manager, temp_music_root):
        """Test cache validation for fresh valid file."""
        fresh_file = temp_music_root / "fresh.json"
        fresh_file.write_text('{"test": "data"}', encoding='utf-8')
        
        assert cache_manager.is_cache_valid(fresh_file)
    
    def test_get_cache_status_missing(self, cache_manager, temp_music_root):
        """Test get_cache_status for missing file."""
        missing_file = temp_music_root / "missing.json"
        assert cache_manager.get_cache_status(missing_file) == CacheStatus.MISSING
    
    def test_get_cache_status_valid(self, cache_manager, temp_music_root):
        """Test get_cache_status for valid file."""
        valid_file = temp_music_root / "valid.json"
        valid_file.write_text('{"test": "data"}', encoding='utf-8')
        
        assert cache_manager.get_cache_status(valid_file) == CacheStatus.VALID
    
    def test_get_cache_status_corrupted(self, cache_manager, temp_music_root):
        """Test get_cache_status for corrupted file."""
        corrupted_file = temp_music_root / "corrupted.json"
        corrupted_file.write_text('invalid json', encoding='utf-8')
        
        assert cache_manager.get_cache_status(corrupted_file) == CacheStatus.CORRUPTED


class TestBandMetadataValidation:
    """Test band-specific metadata cache validation."""
    
    def test_validate_band_metadata_cache_missing(self, cache_manager):
        """Test validation of missing band metadata cache."""
        result = cache_manager.validate_band_metadata_cache("Test Band")
        
        assert result["band_name"] == "Test Band"
        assert not result["exists"]
        assert result["status"] == "missing"
        assert not result["is_valid"]
        assert "No metadata cache found" in result["recommendations"][0]
    
    def test_validate_band_metadata_cache_valid(self, cache_manager, temp_music_root, sample_band_metadata):
        """Test validation of valid band metadata cache."""
        # Create band folder and metadata file
        band_folder = temp_music_root / "Test Band"
        band_folder.mkdir()
        metadata_file = band_folder / ".band_metadata.json"
        metadata_file.write_text(json.dumps(sample_band_metadata), encoding='utf-8')
        
        result = cache_manager.validate_band_metadata_cache("Test Band")
        
        assert result["band_name"] == "Test Band"
        assert result["exists"]
        assert result["status"] == "valid"
        assert result["is_valid"]
        assert result["size_bytes"] > 0
        assert result["last_modified"] is not None
        assert result["age_days"] is not None
        assert "Cache is valid and current" in result["recommendations"][0]


class TestCacheStatistics:
    """Test cache statistics functionality."""
    
    def test_get_cache_statistics_empty(self, cache_manager):
        """Test cache statistics for empty collection."""
        stats = cache_manager.get_cache_statistics()
        
        assert isinstance(stats, CacheStats)
        assert stats.total_entries == 0
        assert stats.valid_entries == 0
        assert stats.expired_entries == 0
        assert stats.corrupted_entries == 0
        assert stats.total_size == 0
        assert stats.cache_hit_rate == 0.0
    
    def test_get_cache_statistics_with_bands(self, cache_manager, temp_music_root, sample_band_metadata):
        """Test cache statistics with band metadata files."""
        # Create multiple band folders with metadata
        for i in range(3):
            band_folder = temp_music_root / f"Band {i}"
            band_folder.mkdir()
            metadata_file = band_folder / ".band_metadata.json"
            metadata = sample_band_metadata.copy()
            metadata["band_name"] = f"Band {i}"
            metadata_file.write_text(json.dumps(metadata), encoding='utf-8')
        
        stats = cache_manager.get_cache_statistics()
        
        assert stats.total_entries == 3
        assert stats.valid_entries == 3
        assert stats.expired_entries == 0
        assert stats.corrupted_entries == 0
        assert stats.total_size > 0


class TestCacheCleanup:
    """Test cache cleanup functionality."""
    
    def test_cleanup_expired_cache_empty(self, cache_manager):
        """Test cleanup of empty collection."""
        result = cache_manager.cleanup_expired_cache()
        
        assert result["total_cleaned"] == 0
        assert result["space_freed_bytes"] == 0
        assert len(result["errors"]) == 0
        assert len(result["cleaned_files"]) == 0
    
    def test_cleanup_expired_cache_with_expired_files(self, cache_manager, temp_music_root, sample_band_metadata):
        """Test cleanup of expired cache files."""
        # Create expired metadata file
        band_folder = temp_music_root / "Test Band"
        band_folder.mkdir()
        metadata_file = band_folder / ".band_metadata.json"
        metadata_file.write_text(json.dumps(sample_band_metadata), encoding='utf-8')
        
        # Mock expired status
        with patch.object(cache_manager, 'get_cache_status') as mock_status:
            mock_status.return_value = CacheStatus.EXPIRED
            
            result = cache_manager.cleanup_expired_cache()
            
            assert result["total_cleaned"] == 1
            assert result["space_freed_bytes"] > 0
            assert len(result["errors"]) == 0
            assert not metadata_file.exists()


class TestCacheMigration:
    """Test cache migration functionality."""
    
    def test_migrate_cache_format_empty(self, cache_manager):
        """Test cache migration for empty collection."""
        result = cache_manager.migrate_cache_format("1.0")
        
        assert result["target_version"] == "1.0"
        assert result["total_migrated"] == 0
        assert len(result["errors"]) == 0
    
    def test_migrate_cache_format_band_metadata(self, cache_manager, temp_music_root):
        """Test migration of band metadata files."""
        # Create old format band metadata (missing v1.0 fields)
        band_folder = temp_music_root / "Test Band"
        band_folder.mkdir()
        metadata_file = band_folder / ".band_metadata.json"
        old_metadata = {
            "band_name": "Test Band",
            "formed": "2000",
            "genre": ["Rock"],
            "albums": [
                {"album_name": "Album 1", "year": "2005"},
                {"album_name": "Album 2", "year": "2010"}
            ]
        }
        metadata_file.write_text(json.dumps(old_metadata), encoding='utf-8')
        
        result = cache_manager.migrate_cache_format("1.0")
        
        assert result["total_migrated"] == 1
        assert len(result["backup_files"]) == 1
        assert any("Test Band" in mf["band"] for mf in result["migrated_files"])
        
        # Verify migration
        with open(metadata_file, 'r', encoding='utf-8') as f:
            updated_metadata = json.load(f)
        
        assert "last_updated" in updated_metadata
        assert "albums_count" in updated_metadata
        assert updated_metadata["albums_count"] == 2
        for album in updated_metadata["albums"]:
            assert "missing" in album
            assert "track_count" in album


class TestConvenienceFunctions:
    """Test convenience functions for cache operations."""
    
    def test_is_metadata_cache_valid_function(self, temp_music_root, sample_band_metadata):
        """Test is_metadata_cache_valid convenience function."""
        # Create band folder and metadata
        band_folder = temp_music_root / "Test Band"
        band_folder.mkdir()
        metadata_file = band_folder / ".band_metadata.json"
        metadata_file.write_text(json.dumps(sample_band_metadata), encoding='utf-8')
        
        with patch('src.di.get_config') as mock_config:
            mock_config.return_value.MUSIC_ROOT_PATH = str(temp_music_root)
            mock_config.return_value.CACHE_DURATION_DAYS = 30
            
            result = is_metadata_cache_valid("Test Band")
            assert result is True
    
    def test_cleanup_expired_caches_function(self, temp_music_root):
        """Test cleanup_expired_caches convenience function."""
        with patch('src.di.get_config') as mock_config:
            mock_config.return_value.MUSIC_ROOT_PATH = str(temp_music_root)
            mock_config.return_value.CACHE_DURATION_DAYS = 30
            
            result = cleanup_expired_caches()
            assert "total_cleaned" in result
            assert "space_freed_bytes" in result
    
    def test_get_collection_cache_stats_function(self, temp_music_root):
        """Test get_collection_cache_stats convenience function."""
        # Use a completely isolated directory to avoid cross-test contamination
        with tempfile.TemporaryDirectory() as isolated_temp_dir:
            with patch('src.di.get_config') as mock_config:
                mock_config.return_value.MUSIC_ROOT_PATH = isolated_temp_dir
                mock_config.return_value.CACHE_DURATION_DAYS = 30
                
                # Also patch the cache manager's get_config calls
                with patch('src.tools.cache.get_config') as mock_cache_config:
                    mock_cache_config.return_value.MUSIC_ROOT_PATH = isolated_temp_dir
                    mock_cache_config.return_value.CACHE_DURATION_DAYS = 30
                    
                    # Now get stats from the clean directory
                    stats = get_collection_cache_stats()
                    assert isinstance(stats, CacheStats)
                    assert stats.total_entries == 0
                    assert stats.valid_entries == 0
                    assert stats.expired_entries == 0
                    assert stats.corrupted_entries == 0
                    assert stats.total_size == 0
                    assert stats.cache_hit_rate == 0.0


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_cache_error_exception(self):
        """Test CacheError exception."""
        with pytest.raises(CacheError):
            raise CacheError("Test error")
    
    def test_cache_validation_with_permission_error(self, cache_manager):
        """Test cache validation with permission errors."""
        result = cache_manager.validate_band_metadata_cache("Test Band")
        
        # Should handle missing band gracefully
        assert result["band_name"] == "Test Band"
        assert not result["exists"]
        assert result["status"] == "missing"
        assert not result["is_valid"]
        assert "No metadata cache found" in result["recommendations"][0] 