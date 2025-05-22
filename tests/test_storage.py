"""
Unit tests for storage module - Local Storage Management.

Tests cover atomic file operations, file locking, backup/recovery,
and all metadata storage functions.
"""

import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

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
from src.models import (
    BandMetadata,
    BandAnalysis,
    AlbumAnalysis,
    Album,
    CollectionInsight,
    CollectionIndex,
    BandIndexEntry
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
            
            # Mock fcntl to always raise exception (simulate locked file)
            with patch('src.tools.storage.fcntl.flock', side_effect=OSError("File locked")):
                with pytest.raises(StorageError, match="Could not acquire lock"):
                    with file_lock(file_path, timeout=1):
                        pass


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
            
            with pytest.raises(StorageError, match="Invalid JSON"):
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
        self.config_patch = patch('src.tools.storage.Config')
        self.mock_config = self.config_patch.start()
        self.mock_config.return_value.music_root_path = self.temp_dir

    def teardown_method(self):
        """Clean up test environment."""
        self.config_patch.stop()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_band_metadata_success(self):
        """Test successful band metadata save."""
        band_name = "Test Band"
        metadata = BandMetadata(
            band_name=band_name,
            formed="2000",
            genre=["Rock"],
            origin="USA",
            members=["John", "Jane"],
            description="A test band"
        )
        
        result = save_band_metadata(band_name, metadata)
        
        assert result["status"] == "success"
        assert band_name in result["message"]
        assert "albums_count" in result
        
        # Verify file was created
        band_folder = Path(self.temp_dir) / band_name
        metadata_file = band_folder / ".band_metadata.json"
        assert metadata_file.exists()

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

    def test_save_band_analyze_new_metadata(self):
        """Test saving analysis for band without existing metadata."""
        band_name = "New Band"
        analysis = BandAnalysis(
            review="Great band!",
            rate=8,
            albums=[AlbumAnalysis(review="Excellent album", rate=9)],
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
        
        # First save metadata
        metadata = BandMetadata(
            band_name=band_name,
            formed="1990",
            genre=["Metal"]
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
        assert loaded_metadata.formed == "1990"
        assert loaded_metadata.genre == ["Metal"]
        assert loaded_metadata.analyze.review == "Updated review"

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
        self.config_patch = patch('src.tools.storage.Config')
        self.mock_config = self.config_patch.start()
        self.mock_config.return_value.music_root_path = self.temp_dir

    def teardown_method(self):
        """Clean up test environment."""
        self.config_patch.stop()
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
                folder_path="Band A",
                missing_albums_count=1,
                has_metadata=True
            ),
            BandIndexEntry(
                name="Band B",
                albums_count=2,
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
        band_name = "Test Band"
        original_metadata = BandMetadata(
            band_name=band_name,
            formed="2000",
            genre=["Rock"]
        )
        
        # Save metadata
        save_band_metadata(band_name, original_metadata)
        
        # Load metadata
        loaded_metadata = load_band_metadata(band_name)
        
        assert loaded_metadata is not None
        assert loaded_metadata.band_name == band_name
        assert loaded_metadata.formed == "2000"
        assert loaded_metadata.genre == ["Rock"]

    def test_load_band_metadata_nonexistent(self):
        """Test loading non-existent band metadata."""
        result = load_band_metadata("Non-existent Band")
        assert result is None

    def test_load_collection_index_existing(self):
        """Test loading existing collection index."""
        # Create and save index
        original_index = CollectionIndex()
        update_collection_index(original_index)
        
        # Load index
        loaded_index = load_collection_index()
        
        assert loaded_index is not None
        assert isinstance(loaded_index, CollectionIndex)

    def test_load_collection_index_nonexistent(self):
        """Test loading non-existent collection index."""
        result = load_collection_index()
        assert result is None


class TestBackupOperations:
    """Test backup and cleanup operations."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_patch = patch('src.tools.storage.Config')
        self.mock_config = self.config_patch.start()
        self.mock_config.return_value.music_root_path = self.temp_dir

    def teardown_method(self):
        """Clean up test environment."""
        self.config_patch.stop()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cleanup_backups_with_excess_files(self):
        """Test cleanup removes old backup files."""
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
        self.config_patch = patch('src.tools.storage.Config')
        self.mock_config = self.config_patch.start()
        self.mock_config.return_value.music_root_path = self.temp_dir

    def teardown_method(self):
        """Clean up test environment."""
        self.config_patch.stop()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_metadata_invalid_path(self):        
        """Test saving metadata with invalid path."""        
        # Mock config to return invalid path that cannot be created        
        self.mock_config.return_value.music_root_path = "/proc/invalid/path"                
        metadata = BandMetadata(band_name="Test Band")               
        with pytest.raises(StorageError):            
            save_band_metadata("Test Band", metadata)

    def test_save_metadata_permission_error(self):
        """Test saving metadata with permission error."""
        with patch('src.tools.storage.JSONStorage.save_json', side_effect=PermissionError("Access denied")):
            metadata = BandMetadata(band_name="Test Band")
            
            with pytest.raises(StorageError, match="Failed to save band metadata"):
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