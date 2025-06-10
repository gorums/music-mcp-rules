"""
Test analyze and folder_structure preservation functionality in save_band_metadata.

This test verifies that both analyze and folder_structure data are preserved by default 
when updating band metadata, ensuring no data loss during metadata updates.
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
                    track_count=10
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
                    track_count=10
                ),
                Album(
                    album_name="New Album",
                    year="1980",
                    track_count=8
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
    @patch('tools.storage.Config')  # Also patch the relative import used by MCP server
    def test_preserve_folder_structure_by_default(self, mock_config_rel, mock_config, temp_music_dir):
        """Test that folder_structure data is preserved when updating metadata."""
        mock_config.return_value.MUSIC_ROOT_PATH = str(temp_music_dir)
        mock_config_rel.return_value.MUSIC_ROOT_PATH = str(temp_music_dir)
        
        band_name = "Test Band"
        
        # Step 1: Create initial metadata with folder_structure data
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
                    "track_count": 10
                }
            ]
        }
        
        # Save initial metadata
        result = save_band_metadata_tool(band_name, initial_metadata_dict)
        assert result["status"] == "success"
        
        # Manually add folder_structure data to simulate existing data
        from models.band_structure import FolderStructure, StructureType, StructureConsistency
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
                        track_count=10
                    )
                ]
            )
        
        # Add folder_structure data
        metadata.folder_structure = FolderStructure(
            structure_type=StructureType.DEFAULT,
            consistency=StructureConsistency.CONSISTENT,
            structure_score=95,
            recommendations=["Test recommendation"]
        )
        save_band_metadata(band_name, metadata)
        
        # Step 2: Update metadata using tool (should preserve folder_structure by default)
        # Note: The save_band_metadata_tool always preserves existing albums, so the new album won't be added
        updated_metadata_dict = {
            "formed": "1970",
            "genres": ["Rock", "Blues"],  # Added genre
            "origin": "Test City",
            "members": ["Member 1", "Member 2"],  # Added member
            "description": "Updated test band description"
            # Note: Not including albums here since they get overwritten with existing albums anyway
        }
        
        # Save updated metadata (should preserve folder_structure)
        result = save_band_metadata_tool(band_name, updated_metadata_dict)
        assert result["status"] == "success"
        
        # Step 3: Verify folder_structure data was preserved
        loaded_metadata = load_band_metadata(band_name)
        assert loaded_metadata is not None
        assert loaded_metadata.folder_structure is not None
        assert loaded_metadata.folder_structure.structure_type == StructureType.DEFAULT
        assert loaded_metadata.folder_structure.consistency == StructureConsistency.CONSISTENT
        assert loaded_metadata.folder_structure.structure_score == 95
        assert len(loaded_metadata.folder_structure.recommendations) == 1
        assert "Test recommendation" in loaded_metadata.folder_structure.recommendations
        
        # Verify other metadata was updated
        assert len(loaded_metadata.genres) == 2
        assert "Blues" in loaded_metadata.genres
        assert len(loaded_metadata.members) == 2
        assert "Member 2" in loaded_metadata.members
        assert loaded_metadata.description == "Updated test band description"
        # Note: Albums are preserved from original metadata (save_band_metadata_tool always preserves existing albums)
        assert len(loaded_metadata.albums) == 1
    
    @patch('src.tools.storage.Config')
    @patch('tools.storage.Config')  # Also patch the relative import used by MCP server
    def test_preserve_both_analyze_and_folder_structure(self, mock_config_rel, mock_config, temp_music_dir):
        """Test that both analyze and folder_structure data are preserved together."""
        mock_config.return_value.MUSIC_ROOT_PATH = str(temp_music_dir)
        mock_config_rel.return_value.MUSIC_ROOT_PATH = str(temp_music_dir)
        
        band_name = "Test Band"
        
        # Step 1: Create initial metadata
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
                    "track_count": 10
                }
            ]
        }
        
        # Save initial metadata
        result = save_band_metadata_tool(band_name, initial_metadata_dict)
        assert result["status"] == "success"
        
        # Manually add both analyze and folder_structure data
        from models.band_structure import FolderStructure, StructureType, StructureConsistency
        metadata = load_band_metadata(band_name)
        if metadata is None:
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
                        track_count=10
                    )
                ]
            )
        
        # Add both analyze and folder_structure data
        metadata.analyze = BandAnalysis(
            review="Great band",
            rate=8,
            albums=[],
            similar_bands=["Similar Band"]
        )
        metadata.folder_structure = FolderStructure(
            structure_type=StructureType.ENHANCED,
            consistency=StructureConsistency.MOSTLY_CONSISTENT,
            structure_score=75,
            recommendations=["Organize by type", "Fix naming"]
        )
        save_band_metadata(band_name, metadata)
        
        # Step 2: Update metadata (should preserve both)
        # Note: The save_band_metadata_tool always preserves existing albums
        updated_metadata_dict = {
            "formed": "1970",
            "genres": ["Rock", "Progressive"],  # Added genre
            "origin": "Test City",
            "members": ["Member 1", "Member 2"],  # Added member
            "description": "Updated description"
            # Note: Not including albums here since they get overwritten with existing albums anyway
        }
        
        # Save updated metadata
        result = save_band_metadata_tool(band_name, updated_metadata_dict)
        assert result["status"] == "success"
        
        # Step 3: Verify both analyze and folder_structure data were preserved
        loaded_metadata = load_band_metadata(band_name)
        assert loaded_metadata is not None
        
        # Check analyze data preserved
        assert loaded_metadata.analyze is not None
        assert loaded_metadata.analyze.review == "Great band"
        assert loaded_metadata.analyze.rate == 8
        
        # Check folder_structure data preserved  
        assert loaded_metadata.folder_structure is not None
        assert loaded_metadata.folder_structure.structure_type == StructureType.ENHANCED
        assert loaded_metadata.folder_structure.consistency == StructureConsistency.MOSTLY_CONSISTENT
        assert loaded_metadata.folder_structure.structure_score == 75
        assert len(loaded_metadata.folder_structure.recommendations) == 2
        
        # Verify other metadata was updated
        assert len(loaded_metadata.genres) == 2
        assert "Progressive" in loaded_metadata.genres
        assert len(loaded_metadata.members) == 2
        assert "Member 2" in loaded_metadata.members 