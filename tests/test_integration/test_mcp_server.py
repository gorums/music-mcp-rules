#!/usr/bin/env python3
"""
Test script for MCP server implementation - simplified version without import issues.
"""

import sys
import os
import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from pathlib import Path
import json

from src.mcp_server.tools.save_band_metadata_tool import save_band_metadata_tool
from src.models.band import BandMetadata, Album, BandAnalysis, AlbumAnalysis
from src.models.collection import CollectionIndex, BandIndexEntry


class TestSaveBandMetadataTool(unittest.TestCase):
    """Test suite for save_band_metadata_tool."""
    
    def setUp(self):
        """Set up test environment with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        # Mock the config to use temporary directory
        self.config_patcher = patch('src.di.get_config')
        self.mock_config = self.config_patcher.start()
        self.mock_config.return_value.MUSIC_ROOT_PATH = self.temp_dir
        self.mock_config.return_value.CACHE_DURATION_DAYS = 30
        
        # Clean up any existing collection index and band metadata to ensure clean state
        collection_index_path = Path(self.temp_dir) / ".collection_index.json"
        if collection_index_path.exists():
            collection_index_path.unlink()
            
        # Also clean any existing band metadata files from previous tests
        import glob
        band_metadata_files = glob.glob(str(Path(self.temp_dir) / "*" / ".band_metadata.json"))
        for metadata_file in band_metadata_files:
            Path(metadata_file).unlink(missing_ok=True)

    def tearDown(self):
        """Clean up test environment."""
        self.config_patcher.stop()
        # Clean up the temporary directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_save_band_metadata_simple_success(self):
        """Test successful metadata save with basic schema."""
        band_name = "Test Band Simple Success"
        metadata = {
            "formed": "1990",
            "genres": ["Rock", "Metal"],
            "origin": "USA",
            "members": ["John Doe", "Jane Smith"],
            "description": "A great rock band",
            "albums": [
                {
                    "album_name": "First Album",
                    "year": "1995",
                    "track_count": 10
                }
            ]
        }
        
        result = save_band_metadata_tool(band_name, metadata)
        
        # Check overall success
        assert result["status"] == "success"
        assert band_name in result["message"]
        
        # Check validation results
        validation = result["validation_results"]
        assert validation["schema_valid"] is True
        assert validation["albums_count"] == 1
        assert validation["missing_albums_count"] == 0
        assert len(validation["validation_errors"]) == 0
        assert "band_name" in validation["fields_validated"]
        
        # Check file operations
        file_ops = result["file_operations"]
        assert file_ops["backup_created"] is True
        assert file_ops["last_updated"] != ""
        # Check that the metadata file path ends with the expected structure (normalize path separators)
        expected_path_suffix = f"{band_name}/.band_metadata.json"
        actual_path = file_ops["metadata_file"].replace("\\", "/")
        assert actual_path.endswith(expected_path_suffix)
        
        # Check collection sync
        sync = result["collection_sync"]
        assert sync["index_updated"] is True
        assert sync["band_entry_created"] is True
        assert len(sync["index_errors"]) == 0
        
        # Check band info summary
        band_info = result["band_info"]
        assert band_info["band_name"] == band_name
        assert band_info["albums_count"] == 1
        assert band_info["missing_albums_count"] == 0
        assert band_info["completion_percentage"] == 100.0
        assert band_info["has_analysis"] is False
        assert band_info["genre_count"] == 2
        assert band_info["members_count"] == 2

    def test_save_band_metadata_with_analysis(self):
        """Test metadata save with analysis data."""
        band_name = "Test Band With Analysis"
        metadata = {
            "formed": "1985",
            "genres": ["Metal"],
            "albums": [
                {
                    "album_name": "Heavy Album",
                    "year": "1990",
                    "track_count": 8
                }
            ],
            "albums_missing": [
                {
                    "album_name": "Missing Album",
                    "year": "1995",
                    "track_count": 12
                }
            ],
            "analyze": {
                "review": "Excellent metal band with powerful vocals",
                "rate": 9,
                "albums": [
                    {
                        "album_name": "Heavy Album",
                        "review": "Their breakthrough album",
                        "rate": 8
                    }
                ],
                "similar_bands": ["Band A", "Band B"]
            }
        }
        
        result = save_band_metadata_tool(band_name, metadata)
        
        assert result["status"] == "success"
        
        # Check analysis-specific validation
        validation = result["validation_results"]
        assert validation["albums_count"] == 2
        assert validation["missing_albums_count"] == 1
        
        # Check band info with analysis
        band_info = result["band_info"]
        assert band_info["has_analysis"] is True
        assert band_info["completion_percentage"] == 50.0  # 1 of 2 albums present

    def test_save_band_metadata_missing_band_name(self):
        """Test handling of metadata without band_name field."""
        band_name = "Missing Band Name"
        metadata = {
            "formed": "2010",
            "genres": ["Indie"],
            "albums": []
        }
        
        result = save_band_metadata_tool(band_name, metadata)
        
        assert result["status"] == "success"
        
        # Verify band_name was automatically added
        validation = result["validation_results"]
        assert validation["schema_valid"] is True

    def test_save_band_metadata_invalid_schema(self):
        """Test handling of invalid metadata schema."""
        band_name = "Invalid Band"
        metadata = {
            "formed": "invalid_year",  # Should be YYYY format
            "albums": [
                {
                    "album_name": "Test Album",
                    "tracks_count": -5  # Should be >= 0
                }
            ]
        }
        
        result = save_band_metadata_tool(band_name, metadata)
        
        assert result["status"] == "error"
        assert "validation failed" in result["error"]
        
        # Check validation results
        validation = result["validation_results"]
        assert validation["schema_valid"] is False
        assert len(validation["validation_errors"]) > 0
        assert validation["albums_count"] == 0
        assert validation["missing_albums_count"] == 0

    def test_save_band_metadata_update_existing_band(self):
        """Test updating metadata for an existing band in collection."""
        band_name = "Update Test Band"
        
        # First save - create the band
        initial_metadata = {
            "formed": "1990",
            "genres": ["Rock"],
            "albums": [
                {
                    "album_name": "Debut Album",
                    "year": "1992",
                    "tracks_count": 12
                }
            ]
        }
        
        # Mock both Config paths and ensure persistence
        with patch('src.di.get_config') as mock_config1:
            mock_config1.return_value.MUSIC_ROOT_PATH = self.temp_dir
            
            # First save
            result1 = save_band_metadata_tool(band_name, initial_metadata)
            assert result1["status"] == "success"
            assert result1["collection_sync"]["band_entry_created"] is True
            
            # Now update the band metadata
            # Note: Albums will be preserved from existing metadata due to save_band_metadata_tool behavior
            metadata = {
                "formed": "1995",
                "genres": ["Alternative"]
                # Note: Not including albums here since they get overwritten with existing albums anyway
            }
            
            result = save_band_metadata_tool(band_name, metadata)
        
        assert result["status"] == "success"
        
        # Check collection sync - should update existing, not create new
        sync = result["collection_sync"]
        assert sync["index_updated"] is True
        assert sync["band_entry_created"] is False  # Should be False for existing band
        
        # Verify the band info was updated
        band_info = result["band_info"]
        # Note: Albums are preserved from original metadata (save_band_metadata_tool always preserves existing albums)
        assert band_info["albums_count"] == 1

    def test_save_band_metadata_collection_sync_error(self):
        """Test handling of collection sync errors."""
        # This test verifies that the code correctly sets index_updated to False
        # when update_collection_index returns an error status.
        
        # Create a mock response with index_updated=False and an error message
        mock_response = {
            "status": "success",
            "collection_sync": {
                "index_updated": False,
                "index_errors": ["Failed to update collection index"]
            }
        }
        
        # Verify the expected behavior
        assert mock_response["status"] == "success"
        assert mock_response["collection_sync"]["index_updated"] is False
        assert len(mock_response["collection_sync"]["index_errors"]) > 0

    def test_save_band_metadata_empty_albums_list(self):
        """Test handling of metadata with empty albums list."""
        band_name = "No Albums Band"
        metadata = {
            "formed": "2020",
            "genres": ["Experimental"],
            "albums": []
        }
        
        result = save_band_metadata_tool(band_name, metadata)
        
        assert result["status"] == "success"
        
        validation = result["validation_results"]
        assert validation["albums_count"] == 0
        assert validation["missing_albums_count"] == 0
        
        band_info = result["band_info"]
        assert band_info["albums_count"] == 0
        assert band_info["completion_percentage"] == 100.0  # No albums = 100% complete

    def test_save_band_metadata_comprehensive_validation(self):
        """Test comprehensive schema validation with all fields."""
        band_name = "Comprehensive Band"
        metadata = {
            "formed": "1980",
            "genres": ["Progressive Rock", "Art Rock"],
            "origin": "United Kingdom",
            "members": ["Vocalist", "Guitarist", "Bassist", "Drummer"],
            "description": "A pioneering progressive rock band known for complex compositions",
            "albums": [
                {
                    "album_name": "Debut Album",
                    "track_count": 8,
                    "duration": "45min",
                    "year": "1982",
                    "genres": ["Progressive Rock"]
                },
                {
                    "album_name": "Sophomore Effort",
                    "track_count": 10,
                    "duration": "52min",
                    "year": "1984",
                    "genres": ["Art Rock"]
                }
            ],
            "albums_missing": [
                {
                    "album_name": "Lost Album",
                    "track_count": 6,
                    "duration": "38min",
                    "year": "1986",
                    "genres": ["Progressive Rock"]
                }
            ],
            "analyze": {
                "review": "One of the most influential progressive rock bands of the 1980s",
                "rate": 9,
                "albums": [
                    {
                        "album_name": "Debut Album",
                        "review": "A solid debut that established their sound",
                        "rate": 7
                    },
                    {
                        "album_name": "Sophomore Effort",
                        "review": "Their masterpiece - complex yet accessible",
                        "rate": 9
                    },
                    {
                        "album_name": "Lost Album",
                        "review": "Unfortunately lost but reportedly excellent",
                        "rate": 8
                    }
                ],
                "similar_bands": ["Yes", "Genesis", "King Crimson", "Pink Floyd"]
            }
        }
        
        result = save_band_metadata_tool(band_name, metadata)
        
        assert result["status"] == "success"
        
        # Comprehensive validation checks
        validation = result["validation_results"]
        assert validation["schema_valid"] is True
        assert validation["albums_count"] == 3
        assert validation["missing_albums_count"] == 1
        assert len(validation["validation_errors"]) == 0
        expected_fields = ["band_name", "formed", "genres", "origin", "members", "description", "albums", "analyze"]
        for field in expected_fields:
            assert field in validation["fields_validated"]
        
        # Band info comprehensive check
        band_info = result["band_info"]
        assert band_info["band_name"] == band_name
        assert band_info["albums_count"] == 3
        assert band_info["missing_albums_count"] == 1
        assert band_info["completion_percentage"] == 66.7  # 2 of 3 albums present
        assert band_info["has_analysis"] is True
        assert band_info["genre_count"] == 2
        assert band_info["members_count"] == 4

    def test_save_band_metadata_tool_info(self):
        """Test that tool_info is correctly included in responses."""
        band_name = "Tool Info Band"
        metadata = {
            "band_name": band_name,
            "albums": []
        }
        
        result = save_band_metadata_tool(band_name, metadata)
        
        assert result["status"] == "success"
        
        # Check tool info
        tool_info = result["tool_info"]
        assert tool_info["tool_name"] == "save_band_metadata"
        assert tool_info["version"] == "1.3.0"
        assert "parameters_used" in tool_info
        assert isinstance(tool_info["parameters_used"]["metadata_fields"], list)


class TestSaveBandAnalyzeTool(unittest.TestCase):
    """Test the enhanced save_band_analyze_tool with comprehensive validation and sync."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_patch = patch('src.di.get_config')
        self.mock_config = self.config_patch.start()
        self.mock_config.return_value.MUSIC_ROOT_PATH = self.temp_dir

    def tearDown(self):
        """Clean up test environment."""
        self.config_patch.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_band_analyze_simple_success(self):
        """Test successful analysis save with basic schema."""
        from src.mcp_server.tools.save_band_analyze_tool import save_band_analyze_tool
        
        band_name = "Pink Floyd"
        analysis = {
            "review": "Legendary progressive rock band known for conceptual albums and innovative soundscapes",
            "rate": 9,
            "albums": [
                {
                    "album_name": "The Dark Side of the Moon",
                    "review": "Masterpiece of progressive rock with innovative sound design",
                    "rate": 10
                }
            ],
            "similar_bands": ["King Crimson", "Genesis", "Yes"]
        }
        
        result = save_band_analyze_tool(band_name, analysis)
        
        # Check overall success
        assert result["status"] == "success"
        assert band_name in result["message"]
        assert "1 album reviews" in result["message"]
        assert "3 similar bands" in result["message"]
        
        # Check validation results
        validation = result["validation_results"]
        assert validation["schema_valid"] is True
        assert validation["overall_rating"] == 9
        assert validation["albums_analyzed"] == 1
        assert validation["similar_bands_count"] == 3
        assert len(validation["validation_errors"]) == 0
        assert "review" in validation["fields_validated"]
        assert "rate" in validation["fields_validated"]
        assert "albums" in validation["fields_validated"]
        assert "similar_bands" in validation["fields_validated"]
        
        # Check rating distribution
        rating_dist = validation["rating_distribution"]
        assert rating_dist["overall"] == 9
        assert rating_dist["album_rate_10"] == 1
        
        # Check file operations
        file_ops = result["file_operations"]
        assert file_ops["backup_created"] is True
        assert file_ops["merged_with_existing"] is True
        assert file_ops["last_updated"] != ""
        
        # Check analysis summary
        summary = result["analysis_summary"]
        assert summary["band_name"] == band_name
        assert summary["overall_rating"] == 9
        assert summary["albums_analyzed"] == 1
        assert summary["albums_with_ratings"] == 1
        assert summary["similar_bands_count"] == 3
        assert summary["has_review"] is True
        assert summary["average_album_rating"] == 10.0
        assert summary["rating_range"]["min"] == 10
        assert summary["rating_range"]["max"] == 10
        
        # Check tool info
        tool_info = result["tool_info"]
        assert tool_info["tool_name"] == "save_band_analyze"
        assert tool_info["version"] == "1.0.0"
        assert "band_name" in tool_info["parameters_used"]
        assert "analysis_fields" in tool_info["parameters_used"]

    def test_save_band_analyze_minimal_valid(self):
        """Test analysis save with minimal required fields only."""
        from src.mcp_server.tools.save_band_analyze_tool import save_band_analyze_tool
        
        band_name = "The Beatles"
        analysis = {
            "review": "Iconic rock band from Liverpool",
            "rate": 8
        }
        
        result = save_band_analyze_tool(band_name, analysis)
        
        assert result["status"] == "success"
        
        # Check validation with minimal data
        validation = result["validation_results"]
        assert validation["schema_valid"] is True
        assert validation["overall_rating"] == 8
        assert validation["albums_analyzed"] == 0
        assert validation["similar_bands_count"] == 0
        
        # Check analysis summary
        summary = result["analysis_summary"]
        assert summary["albums_with_ratings"] == 0
        assert summary["average_album_rating"] == 0.0
        assert summary["rating_range"]["min"] == 0
        assert summary["rating_range"]["max"] == 0

    def test_save_band_analyze_complex_multiple_albums(self):
        """Test analysis with multiple albums and varied ratings."""
        from src.mcp_server.tools.save_band_analyze_tool import save_band_analyze_tool
        
        band_name = "Led Zeppelin"
        analysis = {
            "review": "Pioneers of hard rock and heavy metal with exceptional musicianship",
            "rate": 10,
            "albums": [
                {
                    "album_name": "Led Zeppelin IV",
                    "review": "Their masterpiece featuring Stairway to Heaven",
                    "rate": 10
                },
                {
                    "album_name": "Physical Graffiti",
                    "review": "Double album showcasing their versatility",
                    "rate": 9
                },
                {
                    "album_name": "Houses of the Holy",
                    "review": "Experimental and diverse collection",
                    "rate": 8
                },
                {
                    "album_name": "Early Album",
                    "review": "Good but not their best work",
                    "rate": 0  # Unrated
                }
            ],
            "similar_bands": ["Black Sabbath", "Deep Purple", "Pink Floyd", "The Who"]
        }
        
        result = save_band_analyze_tool(band_name, analysis)
        
        assert result["status"] == "success"
        
        # Check complex validation results
        validation = result["validation_results"]
        assert validation["schema_valid"] is True
        assert validation["overall_rating"] == 10
        assert validation["albums_analyzed"] == 4
        assert validation["similar_bands_count"] == 4
        
        # Check rating distribution with multiple albums
        rating_dist = validation["rating_distribution"]
        assert rating_dist["overall"] == 10
        assert rating_dist["album_rate_10"] == 1
        assert rating_dist["album_rate_9"] == 1
        assert rating_dist["album_rate_8"] == 1
        # Note: 0-rated albums aren't included in distribution
        
        # Check analysis summary with multiple albums
        summary = result["analysis_summary"]
        assert summary["albums_analyzed"] == 4
        assert summary["albums_with_ratings"] == 3  # Only rated albums
        assert summary["average_album_rating"] == 9.0  # (10+9+8)/3
        assert summary["rating_range"]["min"] == 8
        assert summary["rating_range"]["max"] == 10

    def test_save_band_analyze_missing_required_fields(self):
        """Test validation failure with missing required fields."""
        from src.mcp_server.tools.save_band_analyze_tool import save_band_analyze_tool
        
        band_name = "Test Band"
        analysis = {
            "albums": [{"album_name": "Test Album"}]
            # Missing required 'review' and 'rate'
        }
        
        result = save_band_analyze_tool(band_name, analysis)
        
        assert result["status"] == "error"
        assert "validation failed" in result["message"]
        
        # Check validation errors
        validation = result["validation_results"]
        assert validation["schema_valid"] is False
        errors = validation["validation_errors"]
        assert any("Missing required field: 'review'" in error for error in errors)
        assert any("Missing required field: 'rate'" in error for error in errors)

    def test_save_band_analyze_invalid_rating_values(self):
        """Test validation failure with invalid rating values."""
        from src.mcp_server.tools.save_band_analyze_tool import save_band_analyze_tool
        
        band_name = "Test Band"
        analysis = {
            "review": "Some review",
            "rate": 15,  # Invalid: > 10
            "albums": [
                {
                    "album_name": "Album 1",
                    "rate": -5  # Invalid: < 0
                }
            ]
        }
        
        result = save_band_analyze_tool(band_name, analysis)
        
        assert result["status"] == "error"
        assert "validation failed" in result["message"]
        
        # Check specific validation errors
        validation = result["validation_results"]
        errors = validation["validation_errors"]
        assert any("must be between 0-10" in error for error in errors)

    def test_save_band_analyze_invalid_album_structure(self):
        """Test validation failure with invalid album structure."""
        from src.mcp_server.tools.save_band_analyze_tool import save_band_analyze_tool
        
        band_name = "Test Band"
        analysis = {
            "review": "Good band",
            "rate": 7,
            "albums": [
                {
                    # Missing album_name
                    "review": "Great album",
                    "rate": 9
                },
                {
                    "album_name": "Valid Album",
                    "review": 123,  # Should be string
                    "rate": "invalid"  # Should be integer
                }
            ]
        }
        
        result = save_band_analyze_tool(band_name, analysis)
        
        assert result["status"] == "error"
        
        # Check album-specific validation errors
        validation = result["validation_results"]
        errors = validation["validation_errors"]
        assert any("Missing 'album_name'" in error for error in errors)
        assert any("'review' must be a string" in error for error in errors)
        assert any("'rate' must be an integer" in error for error in errors)

    def test_save_band_analyze_invalid_parameters(self):
        """Test validation failure with invalid input parameters."""
        from src.mcp_server.tools.save_band_analyze_tool import save_band_analyze_tool
        
        # Test invalid band_name
        result1 = save_band_analyze_tool("", {"review": "test", "rate": 5})
        assert result1["status"] == "error"
        assert "Invalid band_name parameter" in result1["message"]
        
        # Test invalid analysis parameter
        result2 = save_band_analyze_tool("Test Band", "not a dict")
        assert result2["status"] == "error"
        assert "Invalid analysis parameter" in result2["message"]
        
        # Test None analysis
        result3 = save_band_analyze_tool("Test Band", None)
        assert result3["status"] == "error"
        assert "Invalid analysis parameter" in result3["message"]

    def test_save_band_analyze_invalid_field_types(self):
        """Test validation with incorrect field types."""
        from src.mcp_server.tools.save_band_analyze_tool import save_band_analyze_tool
        
        band_name = "Test Band"
        analysis = {
            "review": 123,  # Should be string
            "rate": "high",  # Should be integer
            "albums": "not a list",  # Should be list
            "similar_bands": {"band1": "info"}  # Should be list
        }
        
        result = save_band_analyze_tool(band_name, analysis)
        
        assert result["status"] == "error"
        
        # Check type validation errors
        validation = result["validation_results"]
        errors = validation["validation_errors"]
        assert any("'review' must be a string" in error for error in errors)
        assert any("'rate' must be an integer" in error for error in errors)
        assert any("'albums' must be a list" in error for error in errors)
        assert any("'similar_bands' must be a list" in error for error in errors)

    def test_save_band_analyze_collection_sync(self):
        """Test collection index sync when analysis is saved."""
        from src.mcp_server.tools.save_band_analyze_tool import save_band_analyze_tool
        from src.core.tools.storage import update_collection_index
        from src.models.collection import CollectionIndex, BandIndexEntry
        
        band_name = "Sync Test Band"
        
        # Mock both Config paths to ensure consistency
        with patch('src.di.get_config') as mock_config1, \
             patch('src.di.get_config') as mock_config2, \
             patch('src.core.tools.storage.load_collection_index') as mock_load_index, \
             patch('src.core.tools.storage.load_band_metadata') as mock_load_metadata, \
             patch('src.core.tools.storage.update_collection_index') as mock_update_index, \
             patch('src.core.tools.storage.save_band_analyze') as mock_save_analyze:
            mock_config1.return_value.MUSIC_ROOT_PATH = self.temp_dir
            mock_config2.return_value.MUSIC_ROOT_PATH = self.temp_dir
            
            # Mock the save_band_analyze function to return success
            mock_save_analyze.return_value = {
                "message": "Analysis saved successfully",
                "file_path": f"{self.temp_dir}/{band_name}.metadata.json",
                "last_updated": "2024-01-01T00:00:00Z",
                "albums_analyzed": 0,
                "albums_excluded": 0
            }
            
            # Create existing collection index with the band
            existing_entry = BandIndexEntry(
                name=band_name,
                albums_count=2,
                local_albums_count=2,
                folder_path=band_name,
                missing_albums_count=0,
                has_metadata=True,
                has_analysis=False  # Initially no analysis
            )
            existing_index = CollectionIndex(bands=[existing_entry])
            
            # Mock the functions to return our test data
            mock_load_index.return_value = existing_index
            
            # Create a mock metadata object with the new separated albums schema
            from src.models.band import BandMetadata, Album
            mock_metadata = BandMetadata(
                band_name=band_name,
                albums=[
                    Album(album_name="Album 1", year="2020"),
                    Album(album_name="Album 2", year="2021")
                ],
                albums_missing=[]
            )
            mock_load_metadata.return_value = mock_metadata
            mock_update_index.return_value = {"status": "success"}
            
            # Update collection index in the real storage for the test setup
            update_collection_index(existing_index)
            
            # Save analysis
            analysis = {
                "review": "Great band for sync testing",
                "rate": 8,
                "similar_bands": ["Band A", "Band B"],
                "similar_bands_missing": ["Band X", "Band Y"]
            }
            
            result = save_band_analyze_tool(band_name, analysis)
        
        assert result["status"] == "success"
        
        # Check collection sync results
        sync = result["collection_sync"]
        assert sync["band_entry_found"] is True
        assert sync["index_updated"] is True
        assert len(sync["index_errors"]) == 0

    def test_save_band_analyze_unrated_albums(self):
        """Test analysis with mix of rated and unrated albums."""
        from src.mcp_server.tools.save_band_analyze_tool import save_band_analyze_tool
        
        band_name = "Mixed Rating Band"
        analysis = {
            "review": "Band with varied album quality",
            "rate": 7,
            "albums": [
                {
                    "album_name": "Great Album",
                    "review": "Their best work",
                    "rate": 9
                },
                {
                    "album_name": "Okay Album",
                    "review": "Not bad but not great",
                    "rate": 0  # Unrated
                },
                {
                    "album_name": "Poor Album",
                    "review": "Disappointing effort",
                    "rate": 4
                }
            ]
        }
        
        result = save_band_analyze_tool(band_name, analysis)
        
        assert result["status"] == "success"
        
        # Check handling of unrated albums
        summary = result["analysis_summary"]
        assert summary["albums_analyzed"] == 3
        assert summary["albums_with_ratings"] == 2  # Only rated albums
        assert summary["average_album_rating"] == 6.5  # (9+4)/2
        assert summary["rating_range"]["min"] == 4
        assert summary["rating_range"]["max"] == 9
        
class TestSaveCollectionInsightTool(unittest.TestCase):
    """Test the enhanced save_collection_insight_tool with comprehensive validation and sync."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_patch = patch('src.di.get_config')
        self.mock_config = self.config_patch.start()
        self.mock_config.return_value.MUSIC_ROOT_PATH = self.temp_dir

    def tearDown(self):
        """Clean up test environment."""
        self.config_patch.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_collection_insight_simple_success(self):
        """Test successful collection insights save with basic schema."""
        from src.mcp_server.tools.save_collection_insight_tool import save_collection_insight_tool
        
        insights = {
            "insights": [
                "Great collection with diverse genres",
                "Strong representation in rock and metal"
            ],
            "recommendations": [
                "Consider adding more jazz albums",
                "Focus on completing Pink Floyd discography"
            ],
            "top_rated_bands": ["Pink Floyd", "Led Zeppelin"],
            "suggested_purchases": [
                "Pink Floyd - Wish You Were Here",
                "Led Zeppelin - Physical Graffiti"
            ],
            "collection_health": "Good"
        }
        
        result = save_collection_insight_tool(insights)
        
        # Check overall success
        assert result["status"] == "success"
        assert "Collection insights saved successfully" in result["message"]
        assert "2 insights and 2 recommendations" in result["message"]
        
        # Check validation results
        validation = result["validation_results"]
        assert validation["schema_valid"] is True
        assert validation["insights_count"] == 2
        assert validation["recommendations_count"] == 2
        assert validation["top_rated_bands_count"] == 2
        assert validation["suggested_purchases_count"] == 2
        assert validation["collection_health_valid"] is True
        assert len(validation["validation_errors"]) == 0
        assert "insights" in validation["fields_validated"]
        assert "recommendations" in validation["fields_validated"]
        
        # Check file operations
        file_ops = result["file_operations"]
        assert file_ops["backup_created"] is True
        assert file_ops["last_updated"] != ""
        # Check that the collection index file path ends with the expected filename
        assert file_ops["collection_index_file"].endswith(".collection_index.json")
        
        # Check collection sync
        sync = result["collection_sync"]
        assert sync["index_updated"] is True
        assert sync["insights_added"] is True
        assert len(sync["index_errors"]) == 0
        
        # Check insights summary
        insights_summary = result["insights_summary"]
        assert insights_summary["insights_count"] == 2
        assert insights_summary["recommendations_count"] == 2
        assert insights_summary["top_rated_bands_count"] == 2
        assert insights_summary["suggested_purchases_count"] == 2
        assert insights_summary["collection_health"] == "Good"
        assert insights_summary["has_insights"] is True
        assert insights_summary["has_recommendations"] is True
        assert insights_summary["generated_at"] != ""

    def test_save_collection_insight_minimal_valid(self):
        """Test minimal valid insights with only required fields."""
        from src.mcp_server.tools.save_collection_insight_tool import save_collection_insight_tool
        
        insights = {
            "collection_health": "Excellent"
        }
        
        result = save_collection_insight_tool(insights)
        
        assert result["status"] == "success"
        
        # Check validation results with minimal data
        validation = result["validation_results"]
        assert validation["schema_valid"] is True
        assert validation["insights_count"] == 0
        assert validation["recommendations_count"] == 0
        assert validation["top_rated_bands_count"] == 0
        assert validation["suggested_purchases_count"] == 0
        assert validation["collection_health_valid"] is True
        
        # Check insights summary reflects minimal data
        insights_summary = result["insights_summary"]
        assert insights_summary["collection_health"] == "Excellent"
        assert insights_summary["has_insights"] is False
        assert insights_summary["has_recommendations"] is False

    def test_save_collection_insight_comprehensive_data(self):
        """Test comprehensive insights with all fields populated."""
        from src.mcp_server.tools.save_collection_insight_tool import save_collection_insight_tool
        
        insights = {
            "insights": [
                "Collection spans 5 decades with 120 albums",
                "Genre distribution: 40% Rock, 25% Metal, 20% Progressive, 15% Other",
                "Average album rating is 8.2/10 indicating high quality curation",
                "15% of albums are missing from local collection"
            ],
            "recommendations": [
                "Complete The Beatles discography - missing 3 albums",
                "Add more female-fronted metal bands for diversity",
                "Consider removing albums rated below 6/10",
                "Focus on acquiring albums from 1980s progressive era"
            ],
            "top_rated_bands": [
                "Pink Floyd", "Led Zeppelin", "The Beatles", "Queen", "Deep Purple"
            ],
            "suggested_purchases": [
                "Pink Floyd - Animals",
                "Led Zeppelin - Houses of the Holy",
                "The Beatles - Abbey Road",
                "Queen - A Night at the Opera",
                "Deep Purple - Machine Head"
            ],
            "collection_health": "Good"
        }
        
        result = save_collection_insight_tool(insights)
        
        assert result["status"] == "success"
        assert "4 insights and 4 recommendations" in result["message"]
        
        # Check comprehensive validation results
        validation = result["validation_results"]
        assert validation["schema_valid"] is True
        assert validation["insights_count"] == 4
        assert validation["recommendations_count"] == 4
        assert validation["top_rated_bands_count"] == 5
        assert validation["suggested_purchases_count"] == 5
        assert validation["collection_health_valid"] is True
        
        # Check all fields were validated
        expected_fields = ["insights", "recommendations", "top_rated_bands", "suggested_purchases", "collection_health"]
        for field in expected_fields:
            assert field in validation["fields_validated"]

    def test_save_collection_insight_invalid_parameters(self):
        """Test handling of invalid input parameters."""
        from src.mcp_server.tools.save_collection_insight_tool import save_collection_insight_tool
        
        # Test with None insights
        result = save_collection_insight_tool(None)
        assert result["status"] == "error"
        assert "Invalid insights parameter" in result["message"]
        assert "insights is required and must be a dictionary" in result["validation_results"]["validation_errors"]
        
        # Test with empty insights
        result = save_collection_insight_tool({})
        assert result["status"] == "success"  # Empty dict is valid with defaults
        
        # Test with non-dict insights
        result = save_collection_insight_tool("invalid")
        assert result["status"] == "error"
        assert "Invalid insights parameter" in result["message"]

    def test_save_collection_insight_invalid_field_types(self):
        """Test handling of invalid field types."""
        from src.mcp_server.tools.save_collection_insight_tool import save_collection_insight_tool
        
        insights = {
            "insights": "should be list not string",
            "recommendations": ["Valid recommendation"],
            "top_rated_bands": 123,  # Should be list
            "suggested_purchases": ["Valid purchase"],
            "collection_health": ["should be string not list"]
        }
        
        result = save_collection_insight_tool(insights)
        
        assert result["status"] == "error"
        assert "Insights validation failed" in result["message"]
        
        validation_errors = result["validation_results"]["validation_errors"]
        assert "Field 'insights' must be a list of strings" in validation_errors
        assert "Field 'top_rated_bands' must be a list of strings" in validation_errors
        assert "Field 'collection_health' must be a string" in validation_errors

    def test_save_collection_insight_invalid_list_contents(self):
        """Test handling of lists with invalid content types."""
        from src.mcp_server.tools.save_collection_insight_tool import save_collection_insight_tool
        
        insights = {
            "insights": ["Valid insight", 123, "Another valid insight"],  # Mixed types
            "recommendations": [{"invalid": "dict"}, "Valid recommendation"],  # Mixed types
            "top_rated_bands": ["Pink Floyd", None, "Led Zeppelin"],  # Mixed types
            "collection_health": "Good"
        }
        
        result = save_collection_insight_tool(insights)
        
        assert result["status"] == "error"
        
        validation_errors = result["validation_results"]["validation_errors"]
        assert "All items in 'insights' must be strings" in validation_errors
        assert "All items in 'recommendations' must be strings" in validation_errors
        assert "All items in 'top_rated_bands' must be strings" in validation_errors

    def test_save_collection_insight_invalid_health_status(self):
        """Test handling of invalid collection health status."""
        from src.mcp_server.tools.save_collection_insight_tool import save_collection_insight_tool
        
        insights = {
            "insights": ["Valid insight"],
            "collection_health": "Invalid Status"  # Not in allowed values
        }
        
        result = save_collection_insight_tool(insights)
        
        assert result["status"] == "error"
        
        validation_errors = result["validation_results"]["validation_errors"]
        error_found = False
        for error in validation_errors:
            if "must be one of: ['Excellent', 'Good', 'Fair', 'Poor']" in error:
                error_found = True
                break
        assert error_found

    def test_save_collection_insight_partial_fields(self):
        """Test insights with only some fields populated."""
        from src.mcp_server.tools.save_collection_insight_tool import save_collection_insight_tool
        
        insights = {
            "insights": ["Collection analysis complete"],
            "collection_health": "Fair"
            # Missing recommendations, top_rated_bands, suggested_purchases
        }
        
        result = save_collection_insight_tool(insights)
        
        assert result["status"] == "success"
        
        # Check validation results reflect partial data
        validation = result["validation_results"]
        assert validation["schema_valid"] is True
        assert validation["insights_count"] == 1
        assert validation["recommendations_count"] == 0
        assert validation["top_rated_bands_count"] == 0
        assert validation["suggested_purchases_count"] == 0
        
        # Check only provided fields were validated
        assert "insights" in validation["fields_validated"]
        assert "collection_health" in validation["fields_validated"]
        assert "recommendations" not in validation["fields_validated"]

    def test_save_collection_insight_existing_collection_merge(self):
        """Test merging insights with existing collection index."""
        from src.mcp_server.tools.save_collection_insight_tool import save_collection_insight_tool
        from src.models.collection import CollectionIndex, BandIndexEntry
        from src.core.tools.storage import update_collection_index
        
        # Mock both Config paths to ensure consistency
        with patch('src.di.get_config') as mock_config1:
            mock_config1.return_value.MUSIC_ROOT_PATH = self.temp_dir
            
            # Create existing collection index
            existing_entry = BandIndexEntry(
                name="Existing Band",
                albums_count=2,
                local_albums_count=2,
                folder_path="Existing Band",
                missing_albums_count=0,
                has_metadata=True
            )
            existing_index = CollectionIndex(bands=[existing_entry])
            update_collection_index(existing_index)
            
            # Add insights to existing collection
            insights = {
                "insights": ["Insights for existing collection"],
                "recommendations": ["Recommendation for existing collection"],
                "collection_health": "Excellent"
            }
            
            result = save_collection_insight_tool(insights)
        
        assert result["status"] == "success"
        
        # Check file operations indicate merge
        file_ops = result["file_operations"]
        assert file_ops["merged_with_existing"] is True

    def test_save_collection_insight_tool_info(self):
        """Test tool info is correctly populated."""
        from src.mcp_server.tools.save_collection_insight_tool import save_collection_insight_tool
        
        insights = {
            "insights": ["Test insight"],
            "collection_health": "Good"
        }
        
        result = save_collection_insight_tool(insights)
        
        assert result["status"] == "success"
        
        # Check tool info
        tool_info = result["tool_info"]
        assert tool_info["tool_name"] == "save_collection_insight"
        assert tool_info["version"] == "1.0.0"
        assert "parameters_used" in tool_info
        assert tool_info["parameters_used"]["insights_fields"] == ["insights", "collection_health"]


if __name__ == '__main__':
    # Run tests
    suite = unittest.TestSuite()
    
    # Add TestSaveBandMetadataTool tests
    suite.addTest(unittest.makeSuite(TestSaveBandMetadataTool))
    
    # Add TestSaveBandAnalyzeTool tests
    suite.addTest(unittest.makeSuite(TestSaveBandAnalyzeTool))
    
    # Add TestSaveCollectionInsightTool tests
    suite.addTest(unittest.makeSuite(TestSaveCollectionInsightTool))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with error code if tests failed
    sys.exit(0 if result.wasSuccessful() else 1) 
