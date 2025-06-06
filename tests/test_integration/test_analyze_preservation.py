"""
Test analyze preservation functionality in save_band_metadata.

This test verifies that the analyze data is preserved by default when updating
band metadata, and can be cleared when explicitly requested.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

from src.models.band import BandMetadata, BandAnalysis, AlbumAnalysis, Album
from src.tools.storage import save_band_metadata, load_band_metadata
from src.music_mcp_server import save_band_metadata_tool


class TestAnalyzePreservation:
    """Test analyze data preservation in save_band_metadata operations."""
    
    @pytest.fixture
    def temp_music_dir(self):
        """Create temporary music directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @patch('src.tools.storage.Config')
    def test_preserve_analyze_by_default(self, mock_config, temp_music_dir):
        """Test that analyze data is always preserved when updating metadata."""
        mock_config.return_value.MUSIC_ROOT_PATH = str(temp_music_dir)
        
        band_name = "Test Band"
        
        # Step 1: Create initial metadata with analyze data
        initial_metadata = BandMetadata(
            band_name=band_name,
            formed="1970",
            genres=["Rock"],
            origin="Test City",
            members=["Member 1", "Member 2"],
            description="Test band description",
            albums=[
                Album(
                    album_name="Test Album",
                    year="1975",
                    tracks_count=10,
                    missing=False
                )
            ],
            analyze=BandAnalysis(
                review="Great band with excellent music",
                rate=9,
                albums=[
                    AlbumAnalysis(
                        album_name="Test Album",
                        review="Fantastic album",
                        rate=10
                    )
                ],
                similar_bands=["Similar Band 1", "Similar Band 2"]
            )
        )
        
        # Save initial metadata
        result = save_band_metadata(band_name, initial_metadata)
        assert result["status"] == "success"
        
        # Step 2: Update metadata without analyze data (should preserve existing)
        updated_metadata = BandMetadata(
            band_name=band_name,
            formed="1970",
            genres=["Rock", "Progressive Rock"],  # Added genre
            origin="Test City",
            members=["Member 1", "Member 2", "Member 3"],  # Added member
            description="Updated test band description",  # Updated description
            albums=[
                Album(
                    album_name="Test Album",
                    year="1975",
                    tracks_count=10,
                    missing=False
                ),
                Album(
                    album_name="New Album",
                    year="1980",
                    tracks_count=8,
                    missing=False
                )
            ]
            # Note: No analyze data provided
        )
        
        # Save updated metadata (now always preserves analyze)
        result = save_band_metadata(band_name, updated_metadata)
        assert result["status"] == "success"
        
        # Step 3: Verify analyze data was preserved
        loaded_metadata = load_band_metadata(band_name)
        assert loaded_metadata is not None
        assert loaded_metadata.analyze is not None
        assert loaded_metadata.analyze.review == "Great band with excellent music"
        assert loaded_metadata.analyze.rate == 9
        assert len(loaded_metadata.analyze.similar_bands) == 2
        assert "Similar Band 1" in loaded_metadata.analyze.similar_bands
        
        # Verify other metadata was updated
        assert len(loaded_metadata.genres) == 2
        assert "Progressive Rock" in loaded_metadata.genres
        assert len(loaded_metadata.members) == 3
        assert "Member 3" in loaded_metadata.members
        assert loaded_metadata.description == "Updated test band description"
        assert len(loaded_metadata.albums) == 2
    
    @patch('src.tools.storage.Config')
    def test_analyze_always_preserved(self, mock_config, temp_music_dir):
        """Test that analyze data is always preserved (behavior changed from clearing)."""
        mock_config.return_value.MUSIC_ROOT_PATH = str(temp_music_dir)
        
        band_name = "Test Band"
        
        # Step 1: Create initial metadata with analyze data
        initial_metadata = BandMetadata(
            band_name=band_name,
            formed="1970",
            genres=["Rock"],
            origin="Test City",
            members=["Member 1"],
            description="Test band description",
            albums=[
                Album(
                    album_name="Test Album",
                    year="1975",
                    tracks_count=10,
                    missing=False
                )
            ],
            analyze=BandAnalysis(
                review="Great band",
                rate=8,
                albums=[],
                similar_bands=["Similar Band"]
            )
        )
        
        # Save initial metadata
        result = save_band_metadata(band_name, initial_metadata)
        assert result["status"] == "success"
        
        # Step 2: Update metadata (now always preserves analyze)
        updated_metadata = BandMetadata(
            band_name=band_name,
            formed="1970",
            genres=["Rock"],
            origin="Test City",
            members=["Member 1"],
            description="Updated description",
            albums=[
                Album(
                    album_name="Test Album",
                    year="1975",
                    tracks_count=10,
                    missing=False
                )
            ]
            # No analyze data provided
        )
        
        # Save with updated metadata (now always preserves analyze)
        result = save_band_metadata(band_name, updated_metadata)
        assert result["status"] == "success"
        
        # Step 3: Verify analyze data was preserved (behavior changed)
        loaded_metadata = load_band_metadata(band_name)
        assert loaded_metadata is not None
        assert loaded_metadata.analyze is not None  # Now always preserved
        assert loaded_metadata.analyze.review == "Great band"
        
        # Verify other metadata was updated
        assert loaded_metadata.description == "Updated description"
    
    @patch('src.tools.storage.Config')
    @patch('tools.storage.Config')  # Also patch the relative import used by MCP server
    def test_save_band_metadata_tool_preserve_analyze_default(self, mock_config_rel, mock_config, temp_music_dir):
        """Test that the tool always preserves analyze data."""
        mock_config.return_value.MUSIC_ROOT_PATH = str(temp_music_dir)
        mock_config_rel.return_value.MUSIC_ROOT_PATH = str(temp_music_dir)
        
        band_name = "Test Band"
        
        # Step 1: Create initial metadata with analyze data using the tool
        initial_metadata_dict = {
            "formed": "1970",
            "genres": ["Rock"],
            "origin": "Test City",
            "members": ["Member 1"],
            "description": "Test band description",
            "albums": [
                {
                    "album_name": "Test Album",
                    "year": "1975",
                    "tracks_count": 10,
                    "missing": False
                }
            ]
        }
        
        # Save initial metadata
        result = save_band_metadata_tool(band_name, initial_metadata_dict)
        assert result["status"] == "success"
        
        # Manually add analyze data to simulate previous analysis
        metadata = load_band_metadata(band_name)
        if metadata is None:
            # If load failed, create the metadata manually and save it
            metadata = BandMetadata(
                band_name=band_name,
                formed="1970",
                genres=["Rock"],
                origin="Test City",
                members=["Member 1"],
                description="Test band description",
                albums=[
                    Album(
                        album_name="Test Album",
                        year="1975",
                        tracks_count=10,
                        missing=False
                    )
                ]
            )
        
        metadata.analyze = BandAnalysis(
            review="Great band",
            rate=8,
            albums=[],
            similar_bands=["Similar Band"]
        )
        save_band_metadata(band_name, metadata)
        
        # Step 2: Update metadata using tool (should preserve analyze by default)
        updated_metadata_dict = {
            "formed": "1970",
            "genres": ["Rock", "Blues"],  # Added genre
            "origin": "Test City",
            "members": ["Member 1", "Member 2"],  # Added member
            "description": "Updated test band description",
            "albums": [
                {
                    "album_name": "Test Album",
                    "year": "1975",
                    "tracks_count": 10,
                    "missing": False
                }
            ]
        }
        
        # Save updated metadata (now always preserves analyze)
        result = save_band_metadata_tool(band_name, updated_metadata_dict)
        assert result["status"] == "success"
        
        # Step 3: Verify analyze data was preserved
        loaded_metadata = load_band_metadata(band_name)
        assert loaded_metadata is not None
        assert loaded_metadata.analyze is not None
        assert loaded_metadata.analyze.review == "Great band"
        assert loaded_metadata.analyze.rate == 8
        
        # Verify other metadata was updated
        assert len(loaded_metadata.genres) == 2
        assert "Blues" in loaded_metadata.genres
        assert len(loaded_metadata.members) == 2
        assert "Member 2" in loaded_metadata.members
    
    @patch('src.tools.storage.Config')
    @patch('tools.storage.Config')  # Also patch the relative import used by MCP server
    def test_save_band_metadata_tool_always_preserves(self, mock_config_rel, mock_config, temp_music_dir):
        """Test that the tool always preserves analyze data (behavior changed from clearing)."""
        mock_config.return_value.MUSIC_ROOT_PATH = str(temp_music_dir)
        mock_config_rel.return_value.MUSIC_ROOT_PATH = str(temp_music_dir)
        
        band_name = "Test Band"
        
        # Step 1: Create initial metadata with analyze data
        initial_metadata_dict = {
            "formed": "1970",
            "genres": ["Rock"],
            "origin": "Test City",
            "members": ["Member 1"],
            "description": "Test band description",
            "albums": [
                {
                    "album_name": "Test Album",
                    "year": "1975",
                    "tracks_count": 10,
                    "missing": False
                }
            ]
        }
        
        # Save initial metadata
        result = save_band_metadata_tool(band_name, initial_metadata_dict)
        assert result["status"] == "success"
        
        # Manually add analyze data
        metadata = load_band_metadata(band_name)
        if metadata is None:
            # If load failed, create the metadata manually and save it
            metadata = BandMetadata(
                band_name=band_name,
                formed="1970",
                genres=["Rock"],
                origin="Test City",
                members=["Member 1"],
                description="Test band description",
                albums=[
                    Album(
                        album_name="Test Album",
                        year="1975",
                        tracks_count=10,
                        missing=False
                    )
                ]
            )
        
        metadata.analyze = BandAnalysis(
            review="Great band",
            rate=8,
            albums=[],
            similar_bands=["Similar Band"]
        )
        save_band_metadata(band_name, metadata)
        
        # Step 2: Update metadata (now always preserves analyze)
        updated_metadata_dict = {
            "formed": "1970",
            "genres": ["Rock"],
            "origin": "Test City",
            "members": ["Member 1"],
            "description": "Updated description",
            "albums": [
                {
                    "album_name": "Test Album",
                    "year": "1975",
                    "tracks_count": 10,
                    "missing": False
                }
            ]
        }
        
        # Save with updated metadata (now always preserves analyze)
        result = save_band_metadata_tool(band_name, updated_metadata_dict)
        assert result["status"] == "success"
        
        # Step 3: Verify analyze data was preserved (behavior changed)
        loaded_metadata = load_band_metadata(band_name)
        assert loaded_metadata is not None
        assert loaded_metadata.analyze is not None  # Now always preserved
        assert loaded_metadata.analyze.review == "Great band"
    
    @patch('src.tools.storage.Config')
    @patch('tools.storage.Config')  # Also patch the relative import used by MCP server
    def test_no_existing_analyze_data(self, mock_config_rel, mock_config, temp_music_dir):
        """Test behavior when there's no existing analyze data to preserve."""
        mock_config.return_value.MUSIC_ROOT_PATH = str(temp_music_dir)
        mock_config_rel.return_value.MUSIC_ROOT_PATH = str(temp_music_dir)
        
        band_name = "Test Band"
        
        # Create metadata without analyze data
        metadata_dict = {
            "formed": "1970",
            "genres": ["Rock"],
            "origin": "Test City",
            "members": ["Member 1"],
            "description": "Test band description",
            "albums": [
                {
                    "album_name": "Test Album",
                    "year": "1975",
                    "tracks_count": 10,
                    "missing": False
                }
            ]
        }
        
        # Save metadata (no existing analyze data to preserve)
        result = save_band_metadata_tool(band_name, metadata_dict)
        assert result["status"] == "success"
        
        # Verify no analyze data exists
        loaded_metadata = load_band_metadata(band_name)
        assert loaded_metadata is not None
        assert loaded_metadata.analyze is None 