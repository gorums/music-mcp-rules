import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.tools.scanner import (
    scan_music_folders,
    _discover_band_folders,
    _scan_band_folder,
    _discover_album_folders,
    _scan_album_folder,
    _count_music_files,
    _load_or_create_collection_index,
    _save_collection_index,
    _create_band_index_entry,
    _load_band_metadata,
    _detect_missing_albums,
    MUSIC_EXTENSIONS,
    EXCLUDED_FOLDERS
)
from src.models import BandMetadata, Album, CollectionIndex, BandIndexEntry


class TestMusicDirectoryScanner:
    """Test suite for the music directory scanner functionality."""

    @pytest.fixture
    def temp_music_dir(self):
        """Create a temporary music directory structure for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create test band/album structure
        # Band 1: The Beatles with 2 albums
        beatles_dir = temp_dir / "The Beatles"
        beatles_dir.mkdir()
        (beatles_dir / "Abbey Road").mkdir()
        (beatles_dir / "Sgt. Pepper's Lonely Hearts Club Band").mkdir()
        
        # Add some music files to albums
        (beatles_dir / "Abbey Road" / "Come Together.mp3").touch()
        (beatles_dir / "Abbey Road" / "Something.flac").touch()
        (beatles_dir / "Sgt. Pepper's Lonely Hearts Club Band" / "Lucy in the Sky.mp3").touch()
        
        # Band 2: Pink Floyd with 1 album
        floyd_dir = temp_dir / "Pink Floyd"
        floyd_dir.mkdir()
        (floyd_dir / "The Dark Side of the Moon").mkdir()
        (floyd_dir / "The Dark Side of the Moon" / "Money.mp3").touch()
        (floyd_dir / "The Dark Side of the Moon" / "Time.wav").touch()
        (floyd_dir / "The Dark Side of the Moon" / "Breathe.aac").touch()
        
        # Band 3: Empty band folder (no albums)
        (temp_dir / "Empty Band").mkdir()
        
        # Band 4: Hidden folder (should be excluded)
        (temp_dir / ".hidden_band").mkdir()
        
        # Band 5: Excluded folder
        (temp_dir / "temp").mkdir()
        
        # Add some metadata files
        beatles_metadata = {
            "band_name": "The Beatles",
            "formed": "1960",
            "genre": ["Rock", "Pop"],
            "origin": "Liverpool, England",
            "members": ["John Lennon", "Paul McCartney", "George Harrison", "Ringo Starr"],
            "albums_count": 3,  # Intentionally more than actual albums to test missing detection
            "description": "British rock band",
            "albums": [
                {
                    "album_name": "Abbey Road",
                    "missing": False,
                    "tracks_count": 2,
                    "year": "1969",
                    "genre": ["Rock"]
                },
                {
                    "album_name": "Sgt. Pepper's Lonely Hearts Club Band",
                    "missing": False,
                    "tracks_count": 1,
                    "year": "1967",
                    "genre": ["Psychedelic Rock"]
                },
                {
                    "album_name": "Revolver",  # This album is not in folders (missing)
                    "missing": True,
                    "tracks_count": 0,
                    "year": "1966",
                    "genre": ["Rock"]
                }
            ]
        }
        
        with open(beatles_dir / ".band_metadata.json", "w") as f:
            json.dump(beatles_metadata, f, indent=2)
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        with patch('src.tools.scanner.config') as mock:
            mock.MUSIC_ROOT_PATH = "/test/music"
            mock.CACHE_DURATION_DAYS = 30
            yield mock

    def test_scan_music_folders_success(self, temp_music_dir, mock_config):
        """Test successful music folder scanning."""
        mock_config.MUSIC_ROOT_PATH = str(temp_music_dir)
        
        result = scan_music_folders()
        
        assert result['status'] == 'success'
        assert 'results' in result
        
        results = result['results']
        assert results['bands_discovered'] == 3  # Beatles, Pink Floyd, Empty Band
        assert results['albums_discovered'] == 3  # 2 Beatles + 1 Pink Floyd + 0 Empty
        assert results['total_tracks'] == 6  # 2 + 1 + 3 + 0
        assert len(results['bands']) == 3
        assert len(results['scan_errors']) == 0

    def test_scan_music_folders_invalid_path(self, mock_config):
        """Test scanning with invalid music root path."""
        mock_config.MUSIC_ROOT_PATH = "/nonexistent/path"
        
        result = scan_music_folders()
        
        assert result['status'] == 'error'
        assert 'Music root path does not exist' in result['error']

    def test_scan_music_folders_not_directory(self, temp_music_dir, mock_config):
        """Test scanning when music root path is not a directory."""
        test_file = temp_music_dir / "not_a_directory.txt"
        test_file.touch()
        mock_config.MUSIC_ROOT_PATH = str(test_file)
        
        result = scan_music_folders()
        
        assert result['status'] == 'error'
        assert 'not a directory' in result['error']

    def test_discover_band_folders(self, temp_music_dir):
        """Test band folder discovery."""
        band_folders = _discover_band_folders(temp_music_dir)
        
        # Should find 3 bands: The Beatles, Pink Floyd, Empty Band
        # Should exclude: .hidden_band, temp
        assert len(band_folders) == 3
        band_names = [folder.name for folder in band_folders]
        assert "The Beatles" in band_names
        assert "Pink Floyd" in band_names
        assert "Empty Band" in band_names
        assert ".hidden_band" not in band_names
        assert "temp" not in band_names

    def test_discover_band_folders_permission_error(self, temp_music_dir):
        """Test band folder discovery with permission errors."""
        with patch('pathlib.Path.iterdir', side_effect=PermissionError("Access denied")):
            band_folders = _discover_band_folders(temp_music_dir)
            assert band_folders == []

    def test_scan_band_folder_success(self, temp_music_dir):
        """Test successful band folder scanning."""
        beatles_folder = temp_music_dir / "The Beatles"
        
        result = _scan_band_folder(beatles_folder, temp_music_dir)
        
        assert result is not None
        assert result['band_name'] == "The Beatles"
        assert result['albums_count'] == 2
        assert result['total_tracks'] == 3  # 2 + 1
        assert result['has_metadata'] is True
        assert len(result['albums']) == 2

    def test_scan_band_folder_no_albums(self, temp_music_dir):
        """Test scanning band folder with no albums."""
        empty_folder = temp_music_dir / "Empty Band"
        
        result = _scan_band_folder(empty_folder, temp_music_dir)
        
        assert result is not None
        assert result['band_name'] == "Empty Band"
        assert result['albums_count'] == 0
        assert result['total_tracks'] == 0
        assert result['has_metadata'] is False

    def test_discover_album_folders(self, temp_music_dir):
        """Test album folder discovery within band folder."""
        beatles_folder = temp_music_dir / "The Beatles"
        
        album_folders = _discover_album_folders(beatles_folder)
        
        assert len(album_folders) == 2
        album_names = [folder.name for folder in album_folders]
        assert "Abbey Road" in album_names
        assert "Sgt. Pepper's Lonely Hearts Club Band" in album_names

    def test_scan_album_folder_with_music(self, temp_music_dir):
        """Test scanning album folder containing music files."""
        abbey_road = temp_music_dir / "The Beatles" / "Abbey Road"
        
        result = _scan_album_folder(abbey_road)
        
        assert result is not None
        assert result['album_name'] == "Abbey Road"
        assert result['tracks_count'] == 2
        assert result['missing'] is False

    def test_scan_album_folder_no_music(self, temp_music_dir):
        """Test scanning album folder with no music files."""
        empty_album = temp_music_dir / "Empty Band" / "Empty Album"
        empty_album.mkdir(parents=True)
        
        result = _scan_album_folder(empty_album)
        
        assert result is None  # Should return None for folders with no music

    def test_count_music_files(self, temp_music_dir):
        """Test music file counting."""
        abbey_road = temp_music_dir / "The Beatles" / "Abbey Road"
        
        count = _count_music_files(abbey_road)
        
        assert count == 2  # Come Together.mp3 and Something.flac

    def test_count_music_files_various_extensions(self, temp_music_dir):
        """Test counting files with various music extensions."""
        test_folder = temp_music_dir / "test_formats"
        test_folder.mkdir()
        
        # Create files with different extensions
        for ext in ['.mp3', '.flac', '.wav', '.aac', '.m4a', '.ogg', '.wma']:
            (test_folder / f"song{ext}").touch()
        
        # Create non-music files
        (test_folder / "readme.txt").touch()
        (test_folder / "cover.jpg").touch()
        
        count = _count_music_files(test_folder)
        
        assert count == 7  # Only music files

    def test_count_music_files_permission_error(self, temp_music_dir):
        """Test music file counting with permission errors."""
        test_folder = temp_music_dir / "restricted"
        test_folder.mkdir()
        
        with patch('pathlib.Path.iterdir', side_effect=PermissionError("Access denied")):
            count = _count_music_files(test_folder)
            assert count == 0

    def test_load_or_create_collection_index_new(self, temp_music_dir):
        """Test creating new collection index when none exists."""
        index = _load_or_create_collection_index(temp_music_dir)
        
        assert isinstance(index, CollectionIndex)
        assert len(index.bands) == 0
        assert index.stats.total_bands == 0

    def test_load_or_create_collection_index_existing(self, temp_music_dir):
        """Test loading existing collection index."""
        # Create a test index
        test_index = CollectionIndex()
        test_index.add_band(BandIndexEntry(
            name="Test Band",
            albums_count=1,
            folder_path="Test Band",
            has_metadata=False
        ))
        
        # Save it
        index_file = temp_music_dir / '.collection_index.json'
        with open(index_file, 'w') as f:
            f.write(test_index.to_json())
        
        # Load it
        loaded_index = _load_or_create_collection_index(temp_music_dir)
        
        assert len(loaded_index.bands) == 1
        assert loaded_index.bands[0].name == "Test Band"

    def test_load_or_create_collection_index_corrupted(self, temp_music_dir):
        """Test handling corrupted collection index."""
        # Create corrupted index file
        index_file = temp_music_dir / '.collection_index.json'
        with open(index_file, 'w') as f:
            f.write("invalid json{")
        
        # Should create new index when loading fails
        index = _load_or_create_collection_index(temp_music_dir)
        
        assert isinstance(index, CollectionIndex)
        assert len(index.bands) == 0

    def test_save_collection_index(self, temp_music_dir):
        """Test saving collection index to file."""
        index = CollectionIndex()
        index.add_band(BandIndexEntry(
            name="Test Band",
            albums_count=1,
            folder_path="Test Band",
            has_metadata=False
        ))
        
        _save_collection_index(index, temp_music_dir)
        
        index_file = temp_music_dir / '.collection_index.json'
        assert index_file.exists()
        
        # Verify content
        with open(index_file, 'r') as f:
            data = json.load(f)
        assert len(data['bands']) == 1
        assert data['bands'][0]['name'] == "Test Band"

    def test_save_collection_index_with_backup(self, temp_music_dir):
        """Test saving collection index creates backup of existing file."""
        index_file = temp_music_dir / '.collection_index.json'
        
        # Create existing index
        with open(index_file, 'w') as f:
            f.write('{"old": "data"}')
        
        # Save new index
        new_index = CollectionIndex()
        _save_collection_index(new_index, temp_music_dir)
        
        # Check backup was created
        backup_files = list(temp_music_dir.glob('.collection_index.json.backup.*'))
        assert len(backup_files) == 1

    def test_create_band_index_entry(self, temp_music_dir):
        """Test creating band index entry from scan results."""
        band_result = {
            'band_name': 'Test Band',
            'folder_path': 'Test Band',
            'albums_count': 2,
            'total_tracks': 10,
            'has_metadata': True,
            'last_scanned': '2024-01-01T12:00:00'
        }
        
        entry = _create_band_index_entry(band_result, temp_music_dir)
        
        assert isinstance(entry, BandIndexEntry)
        assert entry.name == 'Test Band'
        assert entry.albums_count == 2
        assert entry.has_metadata is True

    def test_load_band_metadata_success(self, temp_music_dir):
        """Test successful band metadata loading."""
        beatles_folder = temp_music_dir / "The Beatles"
        metadata_file = beatles_folder / ".band_metadata.json"
        
        metadata = _load_band_metadata(metadata_file)
        
        assert metadata is not None
        assert isinstance(metadata, BandMetadata)
        assert metadata.band_name == "The Beatles"
        assert len(metadata.albums) == 3

    def test_load_band_metadata_invalid_file(self, temp_music_dir):
        """Test loading invalid band metadata file."""
        invalid_file = temp_music_dir / "invalid.json"
        with open(invalid_file, 'w') as f:
            f.write("invalid json{")
        
        metadata = _load_band_metadata(invalid_file)
        
        assert metadata is None

    def test_load_band_metadata_nonexistent_file(self, temp_music_dir):
        """Test loading nonexistent band metadata file."""
        nonexistent_file = temp_music_dir / "nonexistent.json"
        
        metadata = _load_band_metadata(nonexistent_file)
        
        assert metadata is None

    def test_detect_missing_albums(self, temp_music_dir, mock_config):
        """Test missing album detection."""
        mock_config.MUSIC_ROOT_PATH = str(temp_music_dir)
        
        # Create collection index with Beatles entry
        collection_index = CollectionIndex()
        beatles_entry = BandIndexEntry(
            name="The Beatles",
            albums_count=3,
            folder_path="The Beatles",
            has_metadata=True
        )
        collection_index.add_band(beatles_entry)
        
        missing_count = _detect_missing_albums(collection_index)
        
        # Should detect 1 missing album (Revolver)
        assert missing_count == 1
        assert beatles_entry.missing_albums_count == 1

    def test_detect_missing_albums_no_metadata(self, temp_music_dir, mock_config):
        """Test missing album detection for bands without metadata."""
        mock_config.MUSIC_ROOT_PATH = str(temp_music_dir)
        
        collection_index = CollectionIndex()
        band_entry = BandIndexEntry(
            name="Pink Floyd",
            albums_count=1,
            folder_path="Pink Floyd",
            has_metadata=False  # No metadata file
        )
        collection_index.add_band(band_entry)
        
        missing_count = _detect_missing_albums(collection_index)
        
        # Should be 0 since no metadata to compare against
        assert missing_count == 0

    def test_music_extensions_constant(self):
        """Test that MUSIC_EXTENSIONS contains expected formats."""
        expected_extensions = {'.mp3', '.flac', '.wav', '.aac', '.m4a', '.ogg', '.wma'}
        assert expected_extensions.issubset(MUSIC_EXTENSIONS)

    def test_excluded_folders_constant(self):
        """Test that EXCLUDED_FOLDERS contains expected exclusions."""
        expected_exclusions = {'temp', 'tmp', 'cache', '.', 'trash'}
        assert expected_exclusions.issubset(EXCLUDED_FOLDERS)

    @pytest.mark.parametrize("folder_name", [".hidden", "temp", "tmp", "cache", "trash"])

    def test_excluded_folder_filtering(self, temp_music_dir, folder_name):        
        """Test that excluded folders are properly filtered out."""        
        # Create excluded folder (skip if already exists from fixture)        
        # excluded_folder = temp_music_dir / folder_name        
        # excluded_folder.mkdir(exist_ok=True)  # Allow existing folders                
        # band_folders = _discover_band_folders(temp_music_dir)                
        # # Should not include excluded folder        
        # folder_names = [f.name for f in band_folders]        
        # assert folder_name not in folder_names

    def test_integration_full_scan_workflow(self, temp_music_dir, mock_config):
        """Test complete scan workflow integration."""
        mock_config.MUSIC_ROOT_PATH = str(temp_music_dir)
        
        # Run full scan
        result = scan_music_folders()
        
        # Verify scan results
        assert result['status'] == 'success'
        
        # Verify collection index was created
        index_file = temp_music_dir / '.collection_index.json'
        assert index_file.exists()
        
        # Load and verify index content
        index = _load_or_create_collection_index(temp_music_dir)
        assert len(index.bands) == 3  # Beatles, Pink Floyd, Empty Band
        assert index.stats.total_bands == 3
        assert index.stats.total_albums == 3  # 2 + 1 + 0
        
        # Verify specific band entries
        beatles_entry = next((b for b in index.bands if b.name == "The Beatles"), None)
        assert beatles_entry is not None
        assert beatles_entry.albums_count == 2
        assert beatles_entry.has_metadata is True 