#!/usr/bin/env python3
"""
Music Collection MCP Server - Validate Band Metadata Tool

This module contains the validate_band_metadata_tool implementation.
"""

import logging
from typing import Any, Dict

from ..core import mcp

# Configure logging
logger = logging.getLogger(__name__)

@mcp.tool()
def validate_band_metadata_tool(
    band_name: str,
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate band metadata structure without saving it.
    
    This tool performs dry-run validation to help clients test their metadata format:
    - Validates metadata against the BandMetadata schema
    - Returns detailed validation results and errors
    - Does NOT save any data or modify files
    - Useful for testing metadata structure before calling save_band_metadata_tool
    
    Args:
        band_name: The name of the band
        metadata: Metadata dictionary to validate (same format as save_band_metadata_tool)
    
    Returns:
        Dict containing validation results:
        - status: 'valid' or 'invalid'
        - validation_results: Detailed schema validation information
        - suggestions: Helpful suggestions to fix validation errors
        - example_corrections: Examples of how to fix common errors
    """
    try:
        # Import required models
        from src.models.band import BandMetadata
        
        # Prepare validation results
        validation_results = {
            "schema_valid": False,
            "validation_errors": [],
            "fields_validated": [],
            "albums_count": 0,
            "missing_albums_count": 0,
            "field_types_correct": {},
            "missing_required_fields": [],
            "unexpected_fields": []
        }
        
        suggestions = []
        example_corrections = {}
        
        # Check for common field name errors
        common_field_errors = {
            "genre": "genres",
            "formed_year": "formed", 
            "formed_location": "origin",
            "notable_albums": "albums"
        }
        
        for wrong_field, correct_field in common_field_errors.items():
            if wrong_field in metadata:
                validation_results["validation_errors"].append(
                    f"Field '{wrong_field}' should be '{correct_field}'"
                )
                suggestions.append(f"Rename '{wrong_field}' to '{correct_field}'")
                example_corrections[wrong_field] = correct_field
        
        # Check for nested members structure
        if isinstance(metadata.get("members"), dict):
            validation_results["validation_errors"].append(
                "Field 'members' should be a flat list, not nested object with 'former'/'current'"
            )
            suggestions.append("Flatten members structure: combine all members into single array")
            example_corrections["members"] = {
                "wrong": {"former": ["..."], "current": ["..."]},
                "correct": ["member1", "member2", "member3"]
            }
        
        # Check required fields
        required_fields = ["band_name", "formed", "genres", "origin", "members", "description", "albums"]
        for field in required_fields:
            if field not in metadata:
                validation_results["missing_required_fields"].append(field)
                suggestions.append(f"Add required field '{field}'")
        
        # Check field types
        if "formed" in metadata and not isinstance(metadata["formed"], str):
            validation_results["validation_errors"].append(
                f"Field 'formed' should be string (YYYY format), got {type(metadata['formed']).__name__}"
            )
            suggestions.append("Convert 'formed' to string format: '1965' not 1965")
            example_corrections["formed"] = {
                "wrong": 1965,
                "correct": "1965"
            }
        
        # Ensure band_name consistency
        if 'band_name' not in metadata:
            metadata['band_name'] = band_name
        elif metadata['band_name'] != band_name:
            metadata['band_name'] = band_name
            validation_results["validation_errors"].append(
                f"band_name updated to match parameter: '{band_name}'"
            )
        
        # Try to create BandMetadata object for full validation
        try:
            band_metadata = BandMetadata(**metadata)
            validation_results["schema_valid"] = True
            validation_results["fields_validated"] = list(metadata.keys())
            validation_results["albums_count"] = len(band_metadata.albums) + len(band_metadata.albums_missing)
            validation_results["missing_albums_count"] = len(band_metadata.albums_missing)
            
            # Validate each field type
            validation_results["field_types_correct"] = {
                "band_name": isinstance(metadata.get("band_name"), str),
                "formed": isinstance(metadata.get("formed"), str),
                "genres": isinstance(metadata.get("genres"), list),
                "origin": isinstance(metadata.get("origin"), str),
                "members": isinstance(metadata.get("members"), list),
                "description": isinstance(metadata.get("description"), str),
                "albums": isinstance(metadata.get("albums"), list)
            }
            
        except Exception as e:
            validation_error = str(e)
            validation_results["validation_errors"].append(f"Schema validation failed: {validation_error}")
            
            # Add specific suggestions based on error message
            if "String should match pattern" in validation_error and "formed" in validation_error:
                suggestions.append("'formed' field must be 4-digit year as string (e.g., '1965')")
            if "ensure this value is greater than or equal to 0" in validation_error:
                suggestions.append("'tracks_count' must be 0 or positive integer")
            if "ensure this value is less than or equal to 10" in validation_error:
                suggestions.append("'rate' fields must be between 0-10")
        
        # Check for unexpected fields
        expected_fields = ["band_name", "formed", "genres", "origin", "members", "description", "albums", "albums_missing", "analyze", "last_updated", "albums_count"]
        for field in metadata.keys():
            if field not in expected_fields:
                validation_results["unexpected_fields"].append(field)
                suggestions.append(f"Unexpected field '{field}' - check field name spelling")
        
        # Determine overall status
        has_validation_errors = len(validation_results["validation_errors"]) > 0
        has_missing_required = len(validation_results["missing_required_fields"]) > 0
        schema_invalid = not validation_results["schema_valid"]
        
        status = "valid" if (validation_results["schema_valid"] and not has_validation_errors and not has_missing_required) else "invalid"
        
        return {
            "status": status,
            "message": f"Metadata validation {'successful' if status == 'valid' else 'failed'} for {band_name}",
            "validation_results": validation_results,
            "suggestions": suggestions,
            "example_corrections": example_corrections,
            "schema_resource": "Use resource 'schema://band_metadata' for complete documentation",
            "tool_info": {
                "tool_name": "validate_band_metadata",
                "version": "1.0.0",
                "dry_run": True
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": f"Validation tool failed: {str(e)}",
            "suggestions": ["Check that metadata is a valid JSON object"],
            "schema_resource": "Use resource 'schema://band_metadata' for complete documentation",
            "tool_info": {
                "tool_name": "validate_band_metadata",
                "version": "1.0.0",
                "dry_run": True
            }
        } 