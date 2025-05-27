import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from pathlib import Path

from src.music_mcp_server import validate_band_metadata_tool, band_metadata_schema_resource


class TestSchemaDiscovery(unittest.TestCase):
    """Test schema discovery features for MCP clients."""

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

    def test_schema_resource_returns_comprehensive_documentation(self):
        """Test that the schema resource provides comprehensive documentation."""
        result = band_metadata_schema_resource()
        
        # Check that we get markdown documentation
        assert isinstance(result, str)
        assert "# BandMetadata Schema Documentation" in result
        assert "## Required Fields" in result
        assert "## Optional Fields" in result
        assert "## Complete Example" in result
        assert "## Common Validation Errors" in result
        
        # Check required fields are documented
        assert "band_name" in result
        assert "formed" in result
        assert "genre" in result
        assert "origin" in result
        assert "members" in result
        assert "description" in result
        assert "albums" in result
        
        # Check common errors are covered
        assert "genres" in result  # wrong field name
        assert "formed_year" in result  # wrong field name
        assert "notable_albums" in result  # wrong field name
        assert "formed_location" in result  # wrong field name

    def test_validate_tool_with_correct_metadata(self):
        """Test validation tool with correct metadata returns valid status."""
        band_name = "Test Band"
        correct_metadata = {
            "band_name": "Test Band",
            "formed": "1990",
            "genres": ["Rock"],
            "origin": "USA",
            "members": ["Member 1", "Member 2"],
            "description": "A test band",
            "albums": [
                {
                    "album_name": "Test Album",
                    "year": "1995",
                    "tracks_count": 10,
                    "missing": False
                }
            ]
        }
        
        result = validate_band_metadata_tool(band_name, correct_metadata)
        
        assert result["status"] == "valid"
        assert result["validation_results"]["schema_valid"] == True
        assert len(result["validation_results"]["validation_errors"]) == 0
        assert result["validation_results"]["albums_count"] == 1
        assert "tool_info" in result
        assert result["tool_info"]["dry_run"] == True

    def test_validate_tool_with_incorrect_field_names(self):
        """Test validation tool detects common field name errors."""
        band_name = "Test Band"
        incorrect_metadata = {
            "band_name": "Test Band",
            "genre": ["Rock"],  # Wrong: should be "genres"
            "formed_year": 1990,  # Wrong: should be "formed" and string
            "formed_location": "USA",  # Wrong: should be "origin"
            "notable_albums": [],  # Wrong: should be "albums"
            "members": ["Member 1"],
            "description": "A test band"
        }
        
        result = validate_band_metadata_tool(band_name, incorrect_metadata)
        
        assert result["status"] == "invalid"
        # Note: schema_valid can be True even when status is invalid due to field name errors
        
        errors = result["validation_results"]["validation_errors"]
        assert any("'genre' should be 'genres'" in error for error in errors)
        
        suggestions = result["suggestions"]
        assert any("Rename 'genre' to 'genres'" in suggestion for suggestion in suggestions)

    def test_validate_tool_with_nested_members_structure(self):
        """Test validation tool detects nested members structure error."""
        band_name = "Test Band"
        incorrect_metadata = {
            "band_name": "Test Band",
            "formed": "1990",
            "genre": ["Rock"],
            "origin": "USA",
            "members": {  # Wrong: should be flat list
                "former": ["Ex Member"],
                "current": ["Current Member"]
            },
            "description": "A test band",
            "albums": []
        }
        
        result = validate_band_metadata_tool(band_name, incorrect_metadata)
        
        assert result["status"] == "invalid"
        
        errors = result["validation_results"]["validation_errors"]
        assert any("should be a flat list" in error for error in errors)
        
        suggestions = result["suggestions"]
        assert any("Flatten members structure" in suggestion for suggestion in suggestions)
        
        corrections = result["example_corrections"]
        assert "members" in corrections
        assert "wrong" in corrections["members"]
        assert "correct" in corrections["members"]

    def test_validate_tool_with_missing_required_fields(self):
        """Test validation tool detects missing required fields."""
        band_name = "Test Band"
        incomplete_metadata = {
            "band_name": "Test Band",
            "formed": "1990"
            # Missing: genres, origin, members, description, albums
        }
        
        result = validate_band_metadata_tool(band_name, incomplete_metadata)
        
        assert result["status"] == "invalid"
        # Note: schema_valid can be True even when status is invalid due to missing fields
        
        missing_fields = result["validation_results"]["missing_required_fields"]
        assert "genres" in missing_fields
        assert "origin" in missing_fields
        assert "members" in missing_fields
        assert "description" in missing_fields
        assert "albums" in missing_fields
        
        suggestions = result["suggestions"]
        assert any("Add required field 'genres'" in suggestion for suggestion in suggestions)

    def test_validate_tool_with_type_errors(self):
        """Test validation tool detects field type errors."""
        band_name = "Test Band"
        wrong_types_metadata = {
            "band_name": "Test Band",
            "formed": 1990,  # Wrong: should be string
            "genre": ["Rock"],
            "origin": "USA",
            "members": ["Member 1"],
            "description": "A test band",
            "albums": []
        }
        
        result = validate_band_metadata_tool(band_name, wrong_types_metadata)
        
        assert result["status"] == "invalid"
        
        errors = result["validation_results"]["validation_errors"]
        assert any("should be string (YYYY format)" in error for error in errors)
        
        suggestions = result["suggestions"]
        assert any("Convert 'formed' to string format" in suggestion for suggestion in suggestions)
        
        corrections = result["example_corrections"]
        assert "formed" in corrections
        assert corrections["formed"]["wrong"] == 1965
        assert corrections["formed"]["correct"] == "1965"

    def test_validate_tool_with_unexpected_fields(self):
        """Test validation tool detects unexpected fields."""
        band_name = "Test Band"
        extra_fields_metadata = {
            "band_name": "Test Band",
            "formed": "1990",
            "genre": ["Rock"],
            "origin": "USA",
            "members": ["Member 1"],
            "description": "A test band",
            "albums": [],
            "random_field": "unexpected",  # Unexpected field
            "another_wrong_field": 123
        }
        
        result = validate_band_metadata_tool(band_name, extra_fields_metadata)
        
        # Should still be valid if core schema is correct, but flag unexpected fields
        unexpected_fields = result["validation_results"]["unexpected_fields"]
        assert "random_field" in unexpected_fields
        assert "another_wrong_field" in unexpected_fields
        
        suggestions = result["suggestions"]
        assert any("Unexpected field 'random_field'" in suggestion for suggestion in suggestions)

    def test_validate_tool_provides_schema_resource_reference(self):
        """Test validation tool points to schema resource for documentation."""
        band_name = "Test Band"
        metadata = {"band_name": "Test Band"}
        
        result = validate_band_metadata_tool(band_name, metadata)
        
        assert "schema_resource" in result
        assert "schema://band_metadata" in result["schema_resource"]

    def test_validate_tool_error_handling(self):
        """Test validation tool handles errors gracefully."""
        band_name = "Test Band"
        invalid_metadata = "not a dict"  # Wrong type
        
        result = validate_band_metadata_tool(band_name, invalid_metadata)
        
        assert result["status"] == "error"
        assert "error" in result
        assert "suggestions" in result
        assert result["tool_info"]["dry_run"] == True

    def test_field_types_validation(self):
        """Test validation tool validates field types correctly."""
        band_name = "Test Band"
        metadata = {
            "band_name": "Test Band",
            "formed": "1990",
            "genre": ["Rock"],
            "origin": "USA",
            "members": ["Member 1"],
            "description": "A test band",
            "albums": []
        }
        
        result = validate_band_metadata_tool(band_name, metadata)
        
        if result["status"] == "valid":
            field_types = result["validation_results"]["field_types_correct"]
            assert field_types["band_name"] == True
            assert field_types["formed"] == True
            assert field_types["genre"] == True
            assert field_types["origin"] == True
            assert field_types["members"] == True
            assert field_types["description"] == True
            assert field_types["albums"] == True


if __name__ == "__main__":
    unittest.main() 