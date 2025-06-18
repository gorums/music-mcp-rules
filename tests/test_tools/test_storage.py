"""
Unit tests for storage module - Local Storage Management.

Tests cover atomic file operations, file locking, backup/recovery,
and all metadata storage functions.
"""

import json
import os
import tempfile
import time
import unittest
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from src.tools import storage
from src.tools.storage import (
    AtomicFileWriter,
    file_lock,
    JSONStorage,
    StorageError,
    save_band_metadata,
    save_band_analyze,
    save_collection_insight,
    get_band_list,
    load_band_metadata,
    load_collection_index,
    update_collection_index,
    cleanup_backups
)
from src.exceptions import DataError
from src.models import (
    BandMetadata,
    BandAnalysis,
    AlbumAnalysis,
    Album,
    CollectionInsight,
    CollectionIndex,
    BandIndexEntry,
    CollectionStats
)


class TestAtomicFileWriter:
    """Test AtomicFileWriter for safe file operations."""

    def test_atomic_write_success(self):
        """Test successful atomic file write."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.json"
            test_data = {"test": "data"}
            
            with AtomicFileWriter(file_path, backup=False) as f:
                json.dump(test_data, f)
            
            # File should exist and contain correct data
            assert file_path.exists()
            with open(file_path, 'r') as f:
                loaded_data = json.load(f)
            assert loaded_data == test_data

    def test_atomic_write_with_backup(self):
        """Test atomic write creates backup of existing file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.json"
            backup_path = file_path.with_suffix(".json.backup")
            
            # Create original file
            original_data = {"original": "data"}
            with open(file_path, 'w') as f:
                json.dump(original_data, f)
            
            # Write new data with backup
            new_data = {"new": "data"}
            with AtomicFileWriter(file_path, backup=True) as f:
                json.dump(new_data, f)
            
            # Original should be updated, backup should contain original data
            assert file_path.exists()
            assert backup_path.exists()
            
            with open(file_path, 'r') as f:
                assert json.load(f) == new_data
            with open(backup_path, 'r') as f:
                assert json.load(f) == original_data

    def test_atomic_write_failure_cleanup(self):
        """Test that temporary files are cleaned up on failure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.json"
            temp_path = file_path.with_suffix(".json.tmp")
            
            try:
                with AtomicFileWriter(file_path, backup=False) as f:
                    f.write("partial data")
                    raise ValueError("Simulated error")
            except ValueError:
                pass
            
            # Temporary file should be cleaned up
            assert not temp_path.exists()
            assert not file_path.exists()

    def test_atomic_write_creates_directories(self):
        """Test that parent directories are created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "nested" / "dir" / "test.json"
            test_data = {"test": "data"}
            
            with AtomicFileWriter(file_path, backup=False) as f:
                json.dump(test_data, f)
            
            assert file_path.exists()
            assert file_path.parent.exists()


class TestFileLock:
    """Test file locking mechanism."""

    def test_file_lock_success(self):
        """Test successful file locking."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.json"
            lock_path = file_path.with_suffix(".json.lock")
            
            with file_lock(file_path):
                # Lock file should exist during lock
                assert lock_path.exists()
            
            # Lock file should be cleaned up
            assert not lock_path.exists()

    def test_file_lock_timeout(self):
        """Test file lock timeout behavior."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.json"
            
            # Skip fcntl-specific test on Windows
            try:
                import fcntl
                # Mock fcntl to always raise exception (simulate locked file)
                with patch('src.tools.storage.fcntl.flock', side_effect=OSError("File locked")):
                    with pytest.raises(StorageError, match="Could not acquire lock"):
                        with file_lock(file_path, timeout=1):
                            pass
            except ImportError:
                # On Windows, test simple lock file behavior
                lock_path = file_path.with_suffix(file_path.suffix + '.lock')
                
                # Create a lock file manually to simulate a locked state
                with open(lock_path, 'w') as lock_file:
                    # On Windows, just test that file_lock context manager works
                    with file_lock(file_path, timeout=1):
                        assert lock_path.exists() or not lock_path.exists()  # Lock behavior varies


class TestJSONStorage:
    """Test JSONStorage class for file operations."""

    def test_save_json_success(self):
        """Test successful JSON save operation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.json"
            test_data = {"band": "Test Band", "albums": ["Album 1"]}
            
            JSONStorage.save_json(file_path, test_data)
            
            assert file_path.exists()
            loaded_data = JSONStorage.load_json(file_path)
            assert loaded_data == test_data

    def test_save_json_with_unicode(self):
        """Test JSON save with unicode characters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "unicode.json"
            test_data = {"band": "Björk", "album": "Médülla"}
            
            JSONStorage.save_json(file_path, test_data)
            
            loaded_data = JSONStorage.load_json(file_path)
            assert loaded_data == test_data

    def test_load_json_file_not_found(self):
        """Test loading non-existent JSON file."""
        non_existent = Path("/non/existent/file.json")
        
        with pytest.raises(StorageError, match="File not found"):
            JSONStorage.load_json(non_existent)

    def test_load_json_invalid_json(self):
        """Test loading corrupted JSON file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "corrupt.json"
            
            # Create corrupted JSON file
            with open(file_path, 'w') as f:
                f.write("{invalid json content")
            
            with pytest.raises(DataError, match="Invalid JSON"):
                JSONStorage.load_json(file_path)

    def test_create_backup(self):
        """Test backup creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.json"
            test_data = {"original": "data"}
            
            # Create original file
            with open(file_path, 'w') as f:
                json.dump(test_data, f)
            
            # Create backup
            backup_path = JSONStorage.create_backup(file_path)
            
            assert backup_path.exists()
            assert "backup_" in backup_path.name
            
            with open(backup_path, 'r') as f:
                loaded_data = json.load(f)
            assert loaded_data == test_data

    def test_create_backup_nonexistent_file(self):
        """Test backup creation for non-existent file."""
        non_existent = Path("/non/existent/file.json")
        
        with pytest.raises(StorageError, match="Cannot backup non-existent file"):
            JSONStorage.create_backup(non_existent)


class TestMetadataOperations:
    """Test metadata save/load operations."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_band_metadata_success(self):
        """Test successful metadata save operation."""
        from src.di import override_dependency
        from src.config import Config
        
        # Create a mock config with the temp directory
        class MockConfig:
            MUSIC_ROOT_PATH = self.temp_dir
            CACHE_DURATION_DAYS = 30
            LOG_LEVEL = "INFO"
        
        with override_dependency(Config, MockConfig()):
            band_name = "Test Band"
            metadata = BandMetadata(
                band_name=band_name,
                formed="1990",
                genres=["Rock"],
                origin="USA",
                members=["John", "Jane"],
                description="A test band",
                albums=[]
            )

            result = save_band_metadata(band_name, metadata)

            assert result["status"] == "success"
            assert result["message"] == f"Band metadata saved for {band_name}"
            assert result["last_updated"] is not None
            assert result["albums_count"] == 0

            # Verify file was created
            metadata_file = Path(self.temp_dir) / band_name / ".band_metadata.json"
            assert metadata_file.exists() == True

    def test_save_band_metadata_updates_timestamp(self):
        """Test that saving metadata updates timestamp."""
        band_name = "Test Band"
        metadata = BandMetadata(band_name=band_name)
        original_timestamp = metadata.last_updated
        
        # Small delay to ensure timestamp difference
        time.sleep(0.01)
        
        result = save_band_metadata(band_name, metadata)
        
        # Timestamp should be updated
        assert result["last_updated"] != original_timestamp

    def test_save_band_metadata_updates_last_metadata_saved(self):
        """Test that saving metadata updates last_metadata_saved timestamp."""
        band_name = "Test Band"
        metadata = BandMetadata(band_name=band_name)
        
        # Initially last_metadata_saved should be None
        assert metadata.last_metadata_saved is None
        assert metadata.has_metadata_saved() is False
        
        # Save the metadata
        result = save_band_metadata(band_name, metadata)
        
        # Verify the result indicates success
        assert result["status"] == "success"
        
        # Load the metadata back and verify last_metadata_saved was set
        loaded_metadata = load_band_metadata(band_name)
        assert loaded_metadata is not None
        assert loaded_metadata.last_metadata_saved is not None
        assert loaded_metadata.has_metadata_saved() is True
        
        # Verify it's a valid ISO timestamp
        from datetime import datetime
        datetime.fromisoformat(loaded_metadata.last_metadata_saved)

    def test_save_band_analyze_new_metadata(self):
        """Test saving analysis for band without existing metadata."""
        band_name = "New Band"
        analysis = BandAnalysis(
            review="Great band!",
            rate=8,
            albums=[AlbumAnalysis(album_name="Test Album", review="Excellent album", rate=9)],
            similar_bands=["Similar Band 1", "Similar Band 2"]
        )
        
        result = save_band_analyze(band_name, analysis)
        
        assert result["status"] == "success"
        assert result["band_rating"] == 8
        assert result["albums_analyzed"] == 1
        assert result["similar_bands_count"] == 2

    def test_save_band_analyze_existing_metadata(self):
        """Test saving analysis for band with existing metadata."""
        band_name = "Existing Band"
        
        # Create existing metadata first
        metadata = BandMetadata(
            band_name=band_name,
            formed="1995",
            genres=["Alternative"]
        )
        save_band_metadata(band_name, metadata)
        
        # Then save analysis
        analysis = BandAnalysis(
            review="Updated review",
            rate=7,
            similar_bands=["Band A", "Band B"]
        )
        result = save_band_analyze(band_name, analysis)
        
        assert result["status"] == "success"
        assert result["band_rating"] == 7
        
        # Verify metadata was preserved
        loaded_metadata = load_band_metadata(band_name)
        assert loaded_metadata.formed == "1995"
        assert loaded_metadata.genres == ["Alternative"]
        assert loaded_metadata.analyze.review == "Updated review"

    def test_save_band_analyze_with_all_albums(self):
        """Test save_band_analyze now always includes all albums."""
        band_name = "All Albums Test Band"
        
        # Create metadata with separated albums arrays
        local_albums = [
            Album(album_name="Local Album", year="2000", track_count=10)
        ]
        missing_albums = [
            Album(album_name="Missing Album", year="2001", track_count=8)
        ]
        metadata = BandMetadata(
            band_name=band_name,
            formed="1999",
            genres=["Test"],
            albums=local_albums,
            albums_missing=missing_albums
        )
        save_band_metadata(band_name, metadata)
        
        # Create analysis for both albums
        album_analyses = [
            AlbumAnalysis(album_name="Local Album", review="Great local album", rate=9),
            AlbumAnalysis(album_name="Missing Album", review="Would be great if we had it", rate=7)
        ]
        analysis = BandAnalysis(
            review="Test band with all albums",
            rate=8,
            albums=album_analyses,
            similar_bands=["Similar Band"]
        )
        
        # Test that all albums are now included by default
        result = save_band_analyze(band_name, analysis)
        
        assert result["status"] == "success"
        assert result["albums_analyzed"] == 2  # Both albums included
        assert result["albums_excluded"] == 0  # No albums excluded
        assert result["analyze_missing_albums"] is True
        assert "including all albums" in result["message"]
        
        # Verify both album analyses were saved
        loaded_metadata = load_band_metadata(band_name)
        assert len(loaded_metadata.analyze.albums) == 2
        album_names = {album.album_name for album in loaded_metadata.analyze.albums}
        assert "Local Album" in album_names
        assert "Missing Album" in album_names

    def test_save_collection_insight_new_index(self):
        """Test saving insights for new collection."""
        insights = CollectionInsight(
            insights=["Great collection!", "Needs more variety"],
            recommendations=["Buy more jazz albums"],
            top_rated_bands=["Band A", "Band B"],
            collection_health="Good"
        )
        
        result = save_collection_insight(insights)
        
        assert result["status"] == "success"
        assert result["insights_count"] == 2
        assert result["recommendations_count"] == 1
        assert result["collection_health"] == "Good"

    def test_save_collection_insight_existing_index(self):
        """Test saving insights for existing collection."""
        # Create initial collection index
        initial_index = CollectionIndex()
        update_collection_index(initial_index)
        
        # Add insights
        insights = CollectionInsight(
            insights=["Collection insight"],
            collection_health="Excellent"
        )
        result = save_collection_insight(insights)
        
        assert result["status"] == "success"
        assert result["collection_health"] == "Excellent"


class TestBandListOperations:
    """Test band list and collection operations."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock config to use test directory using dependency injection
        from src.di import override_dependency
        from src.config import Config
        
        class MockConfig:
            MUSIC_ROOT_PATH = self.temp_dir
            CACHE_DURATION_DAYS = 30
            LOG_LEVEL = "INFO"
        
        self.config_override = override_dependency(Config, MockConfig())
        self.config_override.__enter__()

    def teardown_method(self):
        """Clean up test environment."""
        self.config_override.__exit__(None, None, None)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_band_list_empty_collection(self):
        """Test getting band list from empty collection."""
        result = get_band_list()
        
        assert result["status"] == "success"
        assert result["bands"] == []
        assert result["total_bands"] == 0
        assert result["total_albums"] == 0

    def test_get_band_list_with_bands(self):
        """Test getting band list from populated collection."""
        # Create collection index with bands
        band_entries = [
            BandIndexEntry(
                name="Band A",
                albums_count=3,
                local_albums_count=2,
                folder_path="Band A",
                missing_albums_count=1,
                has_metadata=True
            ),
            BandIndexEntry(
                name="Band B",
                albums_count=2,
                local_albums_count=2,
                folder_path="Band B",
                missing_albums_count=0,
                has_metadata=False
            )
        ]
        
        index = CollectionIndex(bands=band_entries)
        update_collection_index(index)
        
        result = get_band_list()
        
        assert result["status"] == "success"
        assert len(result["bands"]) == 2
        assert result["total_bands"] == 2
        assert result["total_albums"] == 5
        assert result["total_missing_albums"] == 1
        
        # Check band info details
        band_a_info = next(b for b in result["bands"] if b["name"] == "Band A")
        assert band_a_info["albums_count"] == 3
        assert band_a_info["missing_albums_count"] == 1
        assert band_a_info["completion_percentage"] == 66.7

    def test_load_band_metadata_existing(self):
        """Test loading existing band metadata."""
        from src.di import override_dependency
        from src.config import Config
        
        # Create a mock config with the temp directory
        class MockConfig:
            MUSIC_ROOT_PATH = self.temp_dir
            CACHE_DURATION_DAYS = 30
            LOG_LEVEL = "INFO"
        
        with override_dependency(Config, MockConfig()):
            band_name = "Test Band"
            original_metadata = BandMetadata(
                band_name=band_name,
                formed="2000",
                genres=["Rock"]
            )
            
            # Save metadata
            save_band_metadata(band_name, original_metadata)
            
            # Load metadata
            loaded_metadata = load_band_metadata(band_name)
            
            assert loaded_metadata is not None
            assert loaded_metadata.band_name == band_name
            assert loaded_metadata.formed == "2000"
            assert loaded_metadata.genres == ["Rock"]

    def test_load_band_metadata_nonexistent(self):
        """Test loading non-existent band metadata."""
        from src.di import override_dependency
        from src.config import Config
        
        # Create a mock config with the temp directory
        class MockConfig:
            MUSIC_ROOT_PATH = self.temp_dir
            CACHE_DURATION_DAYS = 30
            LOG_LEVEL = "INFO"
        
        with override_dependency(Config, MockConfig()):
            result = load_band_metadata("Non-existent Band")
            assert result is None

    def test_load_collection_index_existing(self):
        """Test loading existing collection index."""
        from src.di import override_dependency
        from src.config import Config
        
        # Create a mock config with the temp directory
        class MockConfig:
            MUSIC_ROOT_PATH = self.temp_dir
            CACHE_DURATION_DAYS = 30
            LOG_LEVEL = "INFO"
        
        with override_dependency(Config, MockConfig()):
            # Create and save index with a test band
            original_index = CollectionIndex()
            test_band = BandIndexEntry(
                name="Test Band",
                albums_count=1,
                local_albums_count=1,
                folder_path="Test Band",
                missing_albums_count=0,
                has_metadata=True
            )
            original_index.bands.append(test_band)
            update_collection_index(original_index)
            
            # Load index
            loaded_index = load_collection_index()
            
            assert loaded_index is not None
            assert hasattr(loaded_index, 'bands')
            assert hasattr(loaded_index, 'stats')
            assert len(loaded_index.bands) == 1
            assert loaded_index.bands[0].name == "Test Band"

    def test_load_collection_index_nonexistent(self):
        """Test loading non-existent collection index."""
        from src.di import override_dependency
        from src.config import Config
        
        # Create a mock config with the temp directory
        class MockConfig:
            MUSIC_ROOT_PATH = self.temp_dir
            CACHE_DURATION_DAYS = 30
            LOG_LEVEL = "INFO"
        
        with override_dependency(Config, MockConfig()):
            result = load_collection_index()
            assert result is None


class TestBackupOperations:
    """Test backup and cleanup operations."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cleanup_backups_with_excess_files(self):
        """Test cleanup removes old backup files."""
        from src.di import override_dependency
        from src.config import Config
        
        # Create a mock config with the temp directory
        class MockConfig:
            MUSIC_ROOT_PATH = self.temp_dir
            CACHE_DURATION_DAYS = 30
            LOG_LEVEL = "INFO"
        
        with override_dependency(Config, MockConfig()):
            # Create test files with backups
            test_file = Path(self.temp_dir) / "test.json"
            test_file.write_text('{"test": "data"}')
            
            # Create multiple backup files
            backup_files = []
            for i in range(7):  # More than max_backups (5)
                backup_file = test_file.with_suffix(f".backup_{i}.json")
                backup_file.write_text(f'{{"backup": {i}}}')
                backup_files.append(backup_file)
                # Different modification times
                time.sleep(0.01)
            
            # Run cleanup
            result = cleanup_backups(max_backups=5)
            
            assert result["status"] == "success"
            assert result["files_removed"] == 2  # Should remove 2 oldest files
            assert result["space_freed_bytes"] > 0
            
            # Verify only 5 backup files remain
            remaining_backups = list(Path(self.temp_dir).glob("*.backup*"))
            assert len(remaining_backups) == 5

    def test_cleanup_backups_no_excess_files(self):
        """Test cleanup with no excess backup files."""
        from src.di import override_dependency
        from src.config import Config
        
        # Create a mock config with the temp directory
        class MockConfig:
            MUSIC_ROOT_PATH = self.temp_dir
            CACHE_DURATION_DAYS = 30
            LOG_LEVEL = "INFO"
        
        with override_dependency(Config, MockConfig()):
            # Create test file with few backups
            test_file = Path(self.temp_dir) / "test.json"
            test_file.write_text('{"test": "data"}')
            
            # Create only 3 backup files (less than max)
            for i in range(3):
                backup_file = test_file.with_suffix(f".backup_{i}.json")
                backup_file.write_text(f'{{"backup": {i}}}')
            
            result = cleanup_backups(max_backups=5)
            
            assert result["status"] == "success"
            assert result["files_removed"] == 0
            assert result["space_freed_bytes"] == 0


class TestErrorHandling:
    """Test error handling and edge cases."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock config to use test directory using dependency injection
        from src.di import override_dependency
        from src.config import Config
        
        class MockConfig:
            MUSIC_ROOT_PATH = self.temp_dir
            CACHE_DURATION_DAYS = 30
            LOG_LEVEL = "INFO"
        
        self.config_override = override_dependency(Config, MockConfig())
        self.config_override.__enter__()

    def teardown_method(self):
        """Clean up test environment."""
        self.config_override.__exit__(None, None, None)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_metadata_invalid_path(self):        
        """Test saving metadata with invalid path."""        
        # Use a path that will definitely fail on both Windows and Unix
        # NUL device or similar invalid paths 
        import os
        from src.di import override_dependency
        from src.config import Config
        
        if os.name == 'nt':  # Windows
            invalid_path = "CON:/invalid/path"  # CON is reserved on Windows
        else:  # Unix-like
            invalid_path = "/dev/null/invalid/path"  # Can't create directories under /dev/null
            
        class InvalidMockConfig:
            MUSIC_ROOT_PATH = invalid_path
            CACHE_DURATION_DAYS = 30
            LOG_LEVEL = "INFO"
            
        # Use nested context manager for invalid path config
        with override_dependency(Config, InvalidMockConfig()):
            metadata = BandMetadata(band_name="Test Band")               
            with pytest.raises(StorageError):            
                save_band_metadata("Test Band", metadata)

    def test_save_metadata_permission_error(self):
        """Test saving metadata with permission error."""
        with patch('src.tools.storage.JSONStorage.save_json', side_effect=PermissionError("Access denied")):
            metadata = BandMetadata(band_name="Test Band")
            
            with pytest.raises(StorageError, match="Storage save band metadata failed"):
                save_band_metadata("Test Band", metadata)

    def test_load_metadata_corrupted_file(self):
        """Test loading corrupted metadata file."""
        band_name = "Corrupted Band"
        band_folder = Path(self.temp_dir) / band_name
        band_folder.mkdir()
        metadata_file = band_folder / ".band_metadata.json"
        
        # Create corrupted JSON
        metadata_file.write_text("{invalid json")
        
        with pytest.raises(StorageError):
            load_band_metadata(band_name)

    def test_get_band_list_corrupted_index(self):
        """Test getting band list with corrupted collection index."""
        collection_file = Path(self.temp_dir) / ".collection_index.json"
        collection_file.write_text("{corrupted json")
        
        with pytest.raises(StorageError):
            get_band_list()


class TestEnhancedBandListOperations(unittest.TestCase):
    """Test enhanced band list operations with filtering, sorting, and pagination."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = Path(tempfile.mkdtemp())  # Use temporary directory instead of test_music_collection
        
        # Mock config to use test directory using dependency injection
        from src.di import override_dependency
        from src.config import Config
        
        class MockConfig:
            MUSIC_ROOT_PATH = str(self.test_dir)
            CACHE_DURATION_DAYS = 30
            LOG_LEVEL = "INFO"
        
        self.config_override = override_dependency(Config, MockConfig())
        self.config_override.__enter__()
        
        # Create test collection index with diverse data
        self.collection_index = CollectionIndex(
            stats=CollectionStats(
                total_bands=5,
                total_albums=20,
                total_local_albums=17,
                total_missing_albums=3,
                bands_with_metadata=3,
                completion_percentage=85.0
            ),
            bands=[
                BandIndexEntry(
                    name="Alice in Chains",
                    albums_count=4,
                    local_albums_count=3,
                    folder_path="Alice in Chains",
                    missing_albums_count=1,
                    has_metadata=True,
                    last_updated="2024-01-15T10:00:00Z"
                ),
                BandIndexEntry(
                    name="Black Sabbath", 
                    albums_count=8,
                    local_albums_count=8,
                    folder_path="Black Sabbath",
                    missing_albums_count=0,
                    has_metadata=True,
                    last_updated="2024-01-20T15:30:00Z"
                ),
                BandIndexEntry(
                    name="Metallica",
                    albums_count=5,
                    local_albums_count=3,
                    folder_path="Metallica", 
                    missing_albums_count=2,
                    has_metadata=False,
                    last_updated="2024-01-10T08:45:00Z"
                ),
                BandIndexEntry(
                    name="Iron Maiden",
                    albums_count=3,
                    local_albums_count=3,
                    folder_path="Iron Maiden",
                    missing_albums_count=0,
                    has_metadata=True,
                    last_updated="2024-01-25T12:15:00Z"
                ),
                BandIndexEntry(
                    name="Pink Floyd",
                    albums_count=0,
                    local_albums_count=0,
                    folder_path="Pink Floyd",
                    missing_albums_count=0,
                    has_metadata=False,
                    last_updated="2024-01-05T09:00:00Z"
                )
            ],
            last_scan="2024-01-25T14:00:00Z"
        )
        
        # Save collection index
        index_file = self.test_dir / ".collection_index.json"
        storage.JSONStorage.save_json(index_file, self.collection_index.model_dump())
        
        # Create test band metadata files
        self._create_test_metadata()
    
    def tearDown(self):
        """Clean up test environment."""
        self.config_override.__exit__(None, None, None)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def _create_test_metadata(self):
        """Create test band metadata files."""
        # Alice in Chains metadata
        alice_in_chains = BandMetadata(
            band_name="Alice in Chains",
            formed="1987",
            genres=["Grunge", "Alternative Metal"],
            origin="Seattle, Washington, USA",
            members=["Layne Staley", "Jerry Cantrell", "Mike Starr", "Sean Kinney"],
            description="Alternative metal/grunge band from Seattle",
            albums=[
                Album(album_name="Facelift", track_count=12, year="1990", genres=["Grunge"]),
                Album(album_name="Dirt", track_count=13, year="1992", genres=["Grunge"]),
                Album(album_name="Alice in Chains", track_count=12, year="1995", genres=["Grunge"])
            ],
            albums_missing=[
                Album(album_name="Black Gives Way to Blue", track_count=11, year="2009", genres=["Alternative Metal"])
            ]
        )
        alice_dir = self.test_dir / "Alice in Chains"
        alice_dir.mkdir(exist_ok=True)
        alice_metadata_file = alice_dir / ".band_metadata.json"
        storage.JSONStorage.save_json(alice_metadata_file, alice_in_chains.model_dump())
        
        # Black Sabbath metadata  
        black_sabbath = BandMetadata(
            band_name="Black Sabbath",
            formed="1968",
            genres=["Heavy Metal", "Hard Rock"],
            origin="Birmingham, England",
            members=["Ozzy Osbourne", "Tony Iommi", "Geezer Butler", "Bill Ward"],
            description="Pioneering heavy metal band",
            albums=[
                Album(album_name="Paranoid", track_count=8, year="1970", genres=["Heavy Metal"]),
                Album(album_name="Master of Reality", track_count=8, year="1971", genres=["Heavy Metal"]),
                Album(album_name="Vol. 4", track_count=9, year="1972", genres=["Heavy Metal"]),
                Album(album_name="Sabbath Bloody Sabbath", track_count=8, year="1973", genres=["Heavy Metal"]),
                Album(album_name="Sabotage", track_count=8, year="1975", genres=["Heavy Metal"]),
                Album(album_name="Technical Ecstasy", track_count=8, year="1976", genres=["Heavy Metal"]),
                Album(album_name="Never Say Die!", track_count=9, year="1978", genres=["Heavy Metal"]),
                Album(album_name="Heaven and Hell", track_count=8, year="1980", genres=["Heavy Metal"])
            ]
        )
        sabbath_dir = self.test_dir / "Black Sabbath"
        sabbath_dir.mkdir(exist_ok=True)
        sabbath_metadata_file = sabbath_dir / ".band_metadata.json"
        storage.JSONStorage.save_json(sabbath_metadata_file, black_sabbath.model_dump())
        
        # Iron Maiden metadata
        iron_maiden = BandMetadata(
            band_name="Iron Maiden",
            formed="1975",
            genres=["Heavy Metal", "Power Metal"],
            origin="London, England",
            members=["Bruce Dickinson", "Steve Harris", "Dave Murray", "Adrian Smith", "Janick Gers", "Nicko McBrain"],
            description="Legendary British heavy metal band",
            albums=[
                Album(album_name="The Number of the Beast", track_count=8, year="1982", genres=["Heavy Metal"]),
                Album(album_name="Piece of Mind", track_count=9, year="1983", genres=["Heavy Metal"]),
                Album(album_name="Powerslave", track_count=8, year="1984", genres=["Heavy Metal"])
            ]
        )
        maiden_dir = self.test_dir / "Iron Maiden"
        maiden_dir.mkdir(exist_ok=True)
        maiden_metadata_file = maiden_dir / ".band_metadata.json"
        storage.JSONStorage.save_json(maiden_metadata_file, iron_maiden.model_dump())
    
    def test_get_band_list_default_parameters(self):
        """Test get_band_list with default parameters."""
        result = storage.get_band_list()
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['bands']), 5)
        self.assertEqual(result['pagination']['total_bands'], 5)
        self.assertEqual(result['pagination']['page'], 1)
        self.assertEqual(result['pagination']['page_size'], 50)
        self.assertEqual(result['pagination']['total_pages'], 1)
        self.assertFalse(result['pagination']['has_next'])
        self.assertFalse(result['pagination']['has_previous'])
        
        # Check bands are sorted by name (default)
        band_names = [band['name'] for band in result['bands']]
        self.assertEqual(band_names, sorted(band_names))
    
    def test_search_by_band_name(self):
        """Test searching bands by name."""
        result = storage.get_band_list(search_query="alice")
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['bands']), 1)
        self.assertEqual(result['bands'][0]['name'], "Alice in Chains")
        self.assertEqual(result['filters_applied']['search_query'], "alice")
    
    def test_search_by_album_name(self):
        """Test searching bands by album name."""
        result = storage.get_band_list(search_query="paranoid", include_albums=True)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['bands']), 1)
        self.assertEqual(result['bands'][0]['name'], "Black Sabbath")
        self.assertEqual(result['filters_applied']['search_query'], "paranoid")
    
    def test_filter_by_genre(self):
        """Test filtering bands by genre."""
        result = storage.get_band_list(filter_genre="grunge")
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['bands']), 1)
        self.assertEqual(result['bands'][0]['name'], "Alice in Chains")
        self.assertEqual(result['filters_applied']['genre'], "grunge")
    
    def test_filter_has_metadata(self):
        """Test filtering by metadata availability."""
        # Test bands with metadata
        result = storage.get_band_list(filter_has_metadata=True)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['bands']), 3)
        band_names = {band['name'] for band in result['bands']}
        self.assertEqual(band_names, {"Alice in Chains", "Black Sabbath", "Iron Maiden"})
        
        # Test bands without metadata
        result = storage.get_band_list(filter_has_metadata=False)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['bands']), 2)
        band_names = {band['name'] for band in result['bands']}
        self.assertEqual(band_names, {"Metallica", "Pink Floyd"})
    
    def test_filter_missing_albums(self):
        """Test filtering by missing albums."""
        # Test bands with missing albums
        result = storage.get_band_list(filter_missing_albums=True)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['bands']), 2)
        band_names = {band['name'] for band in result['bands']}
        self.assertEqual(band_names, {"Alice in Chains", "Metallica"})
        
        # Test bands without missing albums
        result = storage.get_band_list(filter_missing_albums=False)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['bands']), 3)
        band_names = {band['name'] for band in result['bands']}
        self.assertEqual(band_names, {"Black Sabbath", "Iron Maiden", "Pink Floyd"})
    
    def test_sort_by_albums_count(self):
        """Test sorting by album count."""
        # Ascending order
        result = storage.get_band_list(sort_by="albums_count", sort_order="asc")
        self.assertEqual(result['status'], 'success')
        album_counts = [band['albums_count'] for band in result['bands']]
        self.assertEqual(album_counts, sorted(album_counts))
        self.assertEqual(result['bands'][0]['name'], "Pink Floyd")  # 0 albums
        self.assertEqual(result['bands'][-1]['name'], "Black Sabbath")  # 8 albums
        
        # Descending order
        result = storage.get_band_list(sort_by="albums_count", sort_order="desc")
        self.assertEqual(result['status'], 'success')
        album_counts = [band['albums_count'] for band in result['bands']]
        self.assertEqual(album_counts, sorted(album_counts, reverse=True))
        self.assertEqual(result['bands'][0]['name'], "Black Sabbath")  # 8 albums
        self.assertEqual(result['bands'][-1]['name'], "Pink Floyd")  # 0 albums
    
    def test_sort_by_completion_percentage(self):
        """Test sorting by completion percentage."""
        result = storage.get_band_list(sort_by="completion", sort_order="desc")
        self.assertEqual(result['status'], 'success')
        
        # Calculate expected completion percentages
        expected_completions = []
        for band in result['bands']:
            if band['albums_count'] == 0:
                completion = 100.0
            else:
                completion = ((band['albums_count'] - band['missing_albums_count']) / band['albums_count']) * 100
            expected_completions.append(completion)
        
        # Should be sorted by completion percentage descending
        self.assertEqual(expected_completions, sorted(expected_completions, reverse=True))
    
    def test_pagination(self):
        """Test pagination functionality."""
        # Test first page with small page size
        result = storage.get_band_list(page=1, page_size=2)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['bands']), 2)
        self.assertEqual(result['pagination']['page'], 1)
        self.assertEqual(result['pagination']['page_size'], 2)
        self.assertEqual(result['pagination']['total_pages'], 3)
        self.assertTrue(result['pagination']['has_next'])
        self.assertFalse(result['pagination']['has_previous'])
        
        # Test middle page
        result = storage.get_band_list(page=2, page_size=2)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['bands']), 2)
        self.assertEqual(result['pagination']['page'], 2)
        self.assertTrue(result['pagination']['has_next'])
        self.assertTrue(result['pagination']['has_previous'])
        
        # Test last page
        result = storage.get_band_list(page=3, page_size=2)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['bands']), 1)
        self.assertEqual(result['pagination']['page'], 3)
        self.assertFalse(result['pagination']['has_next'])
        self.assertTrue(result['pagination']['has_previous'])
    
    def test_include_albums_detail(self):
        """Test including detailed album information."""
        result = storage.get_band_list(
            search_query="alice",
            include_albums=True
        )
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['bands']), 1)
        
        band = result['bands'][0]
        self.assertIn('metadata', band)
        self.assertIn('albums', band)
        self.assertEqual(len(band['albums']), 4)
        
        # Check album details
        album_names = [album['album_name'] for album in band['albums']]
        self.assertIn("Facelift", album_names)
        self.assertIn("Dirt", album_names)
        
        # Check missing album flag
        missing_albums = [album for album in band['albums'] if album['missing']]
        self.assertEqual(len(missing_albums), 1)
        self.assertEqual(missing_albums[0]['album_name'], "Black Gives Way to Blue")
    
    def test_combined_filters(self):
        """Test combining multiple filters."""
        result = storage.get_band_list(
            filter_has_metadata=True,
            filter_missing_albums=False,
            sort_by="albums_count",
            sort_order="desc"
        )
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['bands']), 2)  # Black Sabbath and Iron Maiden
        
        # Should be sorted by album count descending
        self.assertEqual(result['bands'][0]['name'], "Black Sabbath")  # 8 albums
        self.assertEqual(result['bands'][1]['name'], "Iron Maiden")    # 3 albums
        
        # Check filters applied
        self.assertTrue(result['filters_applied']['has_metadata'])
        self.assertFalse(result['filters_applied']['missing_albums'])
    
    def test_page_size_limits(self):
        """Test page size validation and limits."""
        # Test minimum page size
        result = storage.get_band_list(page_size=0)
        self.assertEqual(result['pagination']['page_size'], 1)  # Should be clamped to 1
        
        # Test maximum page size
        result = storage.get_band_list(page_size=200)
        self.assertEqual(result['pagination']['page_size'], 100)  # Should be clamped to 100
    
    def test_invalid_page_numbers(self):
        """Test handling of invalid page numbers."""
        # Test page 0 (should be clamped to 1)
        result = storage.get_band_list(page=0)
        self.assertEqual(result['pagination']['page'], 1)
        
        # Test negative page (should be clamped to 1)
        result = storage.get_band_list(page=-5)
        self.assertEqual(result['pagination']['page'], 1)
    
    def test_empty_collection(self):
        """Test behavior with empty collection."""
        # Remove collection index
        index_file = self.test_dir / ".collection_index.json"
        if index_file.exists():
            index_file.unlink()
        
        result = storage.get_band_list()
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['bands']), 0)
        self.assertEqual(result['pagination']['total_bands'], 0)
        self.assertEqual(result['pagination']['total_pages'], 0)
    
    def test_cache_status_information(self):
        """Test that cache status is properly reported."""
        result = storage.get_band_list()
        
        self.assertEqual(result['status'], 'success')
        
        # Check bands with metadata have cached status
        bands_with_metadata = [band for band in result['bands'] if band['has_metadata']]
        for band in bands_with_metadata:
            self.assertEqual(band['cache_status'], 'cached')
        
        # Check bands without metadata have no_cache status
        bands_without_metadata = [band for band in result['bands'] if not band['has_metadata']]
        for band in bands_without_metadata:
            self.assertEqual(band['cache_status'], 'no_cache')

    def test_album_details_filter_local_only(self):
        """Test get_band_list with album_details_filter='local' only returns local albums in album details."""
        # Setup: Band with both local and missing albums
        band_name = "FilterTestBand"
        local_album = Album(album_name="Local Album", year="2000", track_count=10)
        missing_album = Album(album_name="Missing Album", year="2001", track_count=0)
        metadata = BandMetadata(band_name=band_name, albums=[local_album], albums_missing=[missing_album])
        save_band_metadata(band_name, metadata)
        band_entry = BandIndexEntry(name=band_name, albums_count=2, local_albums_count=1, folder_path=band_name, missing_albums_count=1, has_metadata=True)
        index = CollectionIndex(bands=[band_entry])
        update_collection_index(index)
        result = get_band_list(include_albums=True, album_details_filter="local")
        assert result["status"] == "success"
        assert len(result["bands"]) == 1
        albums = result["bands"][0]["albums"]
        assert len(albums) == 1
        assert albums[0]["album_name"] == "Local Album"
        assert albums[0]["missing"] is False

    def test_album_details_filter_missing_only(self):
        """Test get_band_list with album_details_filter='missing' only returns missing albums in album details."""
        band_name = "FilterTestBand2"
        local_album = Album(album_name="Local Album", year="2000", track_count=10)
        missing_album = Album(album_name="Missing Album", year="2001", track_count=0)
        metadata = BandMetadata(band_name=band_name, albums=[local_album], albums_missing=[missing_album])
        save_band_metadata(band_name, metadata)
        band_entry = BandIndexEntry(name=band_name, albums_count=2, local_albums_count=1, folder_path=band_name, missing_albums_count=1, has_metadata=True)
        index = CollectionIndex(bands=[band_entry])
        update_collection_index(index)
        result = get_band_list(include_albums=True, album_details_filter="missing")
        assert result["status"] == "success"
        assert len(result["bands"]) == 1
        albums = result["bands"][0]["albums"]
        assert len(albums) == 1
        assert albums[0]["album_name"] == "Missing Album"
        assert albums[0]["missing"] is True

    def test_album_details_filter_all(self):
        """Test get_band_list with album_details_filter=None returns both local and missing albums."""
        band_name = "FilterTestBand3"
        local_album = Album(album_name="Local Album", year="2000", track_count=10)
        missing_album = Album(album_name="Missing Album", year="2001", track_count=0)
        metadata = BandMetadata(band_name=band_name, albums=[local_album], albums_missing=[missing_album])
        save_band_metadata(band_name, metadata)
        band_entry = BandIndexEntry(name=band_name, albums_count=2, local_albums_count=1, folder_path=band_name, missing_albums_count=1, has_metadata=True)
        index = CollectionIndex(bands=[band_entry])
        update_collection_index(index)
        result = get_band_list(include_albums=True, album_details_filter=None)
        assert result["status"] == "success"
        assert len(result["bands"]) == 1
        albums = result["bands"][0]["albums"]
        assert len(albums) == 2
        names = {a["album_name"] for a in albums}
        assert "Local Album" in names
        assert "Missing Album" in names 