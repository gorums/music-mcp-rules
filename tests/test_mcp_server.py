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

from src.music_mcp_server import save_band_metadata_tool
from src.models.band import BandMetadata, Album, BandAnalysis, AlbumAnalysis
from src.models.collection import CollectionIndex, BandIndexEntry


class TestSaveBandMetadataTool(unittest.TestCase):
    """Test the enhanced save_band_metadata_tool with comprehensive validation and sync."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_patch = patch('src.tools.storage.Config')
        self.mock_config = self.config_patch.start()
        self.mock_config.return_value.MUSIC_ROOT_PATH = self.temp_dir

    def tearDown(self):
        """Clean up test environment."""
        self.config_patch.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_band_metadata_simple_success(self):
        """Test successful metadata save with basic schema."""
        band_name = "Test Band"
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
                    "tracks_count": 10,
                    "missing": False
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
        assert str(Path(self.temp_dir) / band_name / ".band_metadata.json") in file_ops["metadata_file"]
        
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
        band_name = "Test Band"
        metadata = {
            "formed": "1985",
            "genres": ["Metal"],
            "albums": [
                {
                    "album_name": "Heavy Album",
                    "year": "1990",
                    "tracks_count": 8,
                    "missing": False
                },
                {
                    "album_name": "Missing Album",
                    "year": "1995",
                    "tracks_count": 12,
                    "missing": True
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
        """Test updating metadata for existing band in collection index."""
        band_name = "Existing Band"
        
        # First, create an existing collection index with the band
        existing_entry = BandIndexEntry(
            name=band_name,
            albums_count=1,
            folder_path=band_name,
            missing_albums_count=0,
            has_metadata=False
        )
        existing_index = CollectionIndex(bands=[existing_entry])
        
        # Save the existing index
        from src.tools.storage import update_collection_index
        update_collection_index(existing_index)
        
        # Now update the band metadata
        metadata = {
            "formed": "1995",
            "genres": ["Alternative"],
            "albums": [
                {
                    "album_name": "First Album",
                    "year": "1995",
                    "tracks_count": 8
                },
                {
                    "album_name": "Second Album",
                    "year": "1998",
                    "tracks_count": 10
                }
            ]
        }
        
        result = save_band_metadata_tool(band_name, metadata)
        
        assert result["status"] == "success"
        
        # Check collection sync - should update existing, not create new
        sync = result["collection_sync"]
        assert sync["index_updated"] is True
        assert sync["band_entry_created"] is False  # Should be False for existing band
        
        # Verify the band info was updated
        band_info = result["band_info"]
        assert band_info["albums_count"] == 2

    def test_save_band_metadata_collection_sync_error(self):
        """Test handling of collection sync errors."""
        band_name = "Sync Error Band"
        metadata = {
            "band_name": band_name,
            "albums": []
        }
        
        # Mock update_collection_index to fail - patch it in the storage module where it's imported
        with patch('src.tools.storage.update_collection_index') as mock_update:
            mock_update.return_value = {"status": "error", "error": "Mock error"}
            
            result = save_band_metadata_tool(band_name, metadata)
        
        # Should still succeed in saving metadata
        assert result["status"] == "success"
        
        # But collection sync should have errors
        sync = result["collection_sync"]
        assert sync["index_updated"] is False
        assert len(sync["index_errors"]) > 0

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
                    "missing": False,
                    "tracks_count": 8,
                    "duration": "45min",
                    "year": "1982",
                    "genres": ["Progressive Rock"]
                },
                {
                    "album_name": "Sophomore Effort",
                    "missing": False,
                    "tracks_count": 10,
                    "duration": "52min",
                    "year": "1984",
                    "genres": ["Art Rock"]
                },
                {
                    "album_name": "Lost Album",
                    "missing": True,
                    "tracks_count": 6,
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
        assert tool_info["version"] == "1.0.0"
        assert "parameters_used" in tool_info
        assert isinstance(tool_info["parameters_used"]["metadata_fields"], list)


class TestSaveBandAnalyzeTool(unittest.TestCase):
    """Test the enhanced save_band_analyze_tool with comprehensive validation and sync."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_patch = patch('src.tools.storage.Config')
        self.mock_config = self.config_patch.start()
        self.mock_config.return_value.MUSIC_ROOT_PATH = self.temp_dir

    def tearDown(self):
        """Clean up test environment."""
        self.config_patch.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_band_analyze_simple_success(self):
        """Test successful analysis save with basic schema."""
        from src.music_mcp_server import save_band_analyze_tool
        
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
        from src.music_mcp_server import save_band_analyze_tool
        
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
        from src.music_mcp_server import save_band_analyze_tool
        
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
        from src.music_mcp_server import save_band_analyze_tool
        
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
        from src.music_mcp_server import save_band_analyze_tool
        
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
        from src.music_mcp_server import save_band_analyze_tool
        
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
        from src.music_mcp_server import save_band_analyze_tool
        
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
        from src.music_mcp_server import save_band_analyze_tool
        
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
        from src.music_mcp_server import save_band_analyze_tool
        from src.tools.storage import update_collection_index
        from src.models.collection import CollectionIndex, BandIndexEntry
        
        band_name = "Sync Test Band"
        
        # Create existing collection index with the band
        existing_entry = BandIndexEntry(
            name=band_name,
            albums_count=2,
            folder_path=band_name,
            missing_albums_count=0,
            has_metadata=True,
            has_analysis=False  # Initially no analysis
        )
        existing_index = CollectionIndex(bands=[existing_entry])
        update_collection_index(existing_index)
        
        # Save analysis
        analysis = {
            "review": "Great band for sync testing",
            "rate": 8
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
        from src.music_mcp_server import save_band_analyze_tool
        
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


if __name__ == '__main__':
    # Run tests
    suite = unittest.TestSuite()
    
    # Add TestSaveBandMetadataTool tests
    suite.addTest(unittest.makeSuite(TestSaveBandMetadataTool))
    
    # Add TestSaveBandAnalyzeTool tests
    suite.addTest(unittest.makeSuite(TestSaveBandAnalyzeTool))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with error code if tests failed
    sys.exit(0 if result.wasSuccessful() else 1) 