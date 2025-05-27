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
                        "review": "A solid debut that established their sound",
                        "rate": 7
                    },
                    {
                        "review": "Their masterpiece - complex yet accessible",
                        "rate": 9
                    },
                    {
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


if __name__ == '__main__':
    unittest.main() 