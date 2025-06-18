#!/usr/bin/env python3
"""
Tests for Music Collection MCP Server exception handling.

This module tests the unified exception hierarchy and error handling
mechanisms across all components.
"""

import pytest
import json
from typing import Dict, Any
from unittest.mock import Mock, patch

from src.exceptions import (
    MusicMCPError, ValidationError, StorageError, ScanningError,
    ConfigurationError, NetworkError, PermissionError, ResourceError,
    DataError, CacheError, ErrorSeverity, ErrorCategory,
    wrap_exception, create_validation_error, create_storage_error
)


class TestErrorEnums:
    """Test error severity and category enums."""
    
    def test_error_severity_values(self):
        """Test that ErrorSeverity enum has correct values."""
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.CRITICAL.value == "critical"
    
    def test_error_category_values(self):
        """Test that ErrorCategory enum has all expected categories."""
        expected_categories = [
            "validation", "storage", "scanning", "network", "configuration",
            "permission", "resource", "operation", "data", "system"
        ]
        
        for category in expected_categories:
            assert any(cat.value == category for cat in ErrorCategory)


class TestMusicMCPError:
    """Test base MusicMCPError class."""
    
    def test_basic_initialization(self):
        """Test basic error initialization."""
        error = MusicMCPError("Test error message")
        
        assert error.message == "Test error message"
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.category == ErrorCategory.OPERATION
        assert error.user_message == "Test error message"
        assert error.details == {}
        assert error.original_exception is None
    
    def test_full_initialization(self):
        """Test error initialization with all parameters."""
        original_error = ValueError("Original error")
        details = {"key": "value", "count": 42}
        
        error = MusicMCPError(
            message="Technical error",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.VALIDATION,
            user_message="User-friendly error",
            details=details,
            original_exception=original_error
        )
        
        assert error.message == "Technical error"
        assert error.severity == ErrorSeverity.HIGH
        assert error.category == ErrorCategory.VALIDATION
        assert error.user_message == "User-friendly error"
        assert error.details == details
        assert error.original_exception == original_error
        assert error.traceback_info is not None
    
    def test_to_dict_conversion(self):
        """Test converting error to dictionary."""
        original_error = RuntimeError("Runtime issue")
        error = MusicMCPError(
            message="Test error",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.STORAGE,
            user_message="Storage failed",
            details={"file": "test.json"},
            original_exception=original_error
        )
        
        result = error.to_dict()
        
        expected_keys = [
            'error_type', 'message', 'user_message', 'severity', 
            'category', 'details', 'original_error'
        ]
        
        for key in expected_keys:
            assert key in result
        
        assert result['error_type'] == 'MusicMCPError'
        assert result['message'] == 'Test error'
        assert result['user_message'] == 'Storage failed'
        assert result['severity'] == 'high'
        assert result['category'] == 'storage'
        assert result['details'] == {'file': 'test.json'}
        assert result['original_error']['type'] == 'RuntimeError'
        assert result['original_error']['message'] == 'Runtime issue'
    
    def test_get_client_response(self):
        """Test getting client-friendly response."""
        error = MusicMCPError(
            message="Technical error",
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.SYSTEM,
            user_message="System error occurred"
        )
        
        response = error.get_client_response()
        
        assert response['error'] == "System error occurred"
        assert response['error_type'] == 'MusicMCPError'
        assert response['severity'] == 'critical'
        assert response['category'] == 'system'


class TestValidationError:
    """Test ValidationError class."""
    
    def test_basic_validation_error(self):
        """Test basic validation error creation."""
        error = ValidationError("Invalid data format")
        
        assert error.category == ErrorCategory.VALIDATION
        assert error.severity == ErrorSeverity.MEDIUM
        assert "Validation error:" in error.user_message
    
    def test_validation_error_with_field_info(self):
        """Test validation error with field information."""
        error = ValidationError(
            message="Invalid email format",
            field_name="email",
            field_value="invalid-email",
            validation_rules=["must contain @", "must have domain"]
        )
        
        assert error.details['field_name'] == "email"
        assert error.details['field_value'] == "invalid-email"
        assert error.details['validation_rules'] == ["must contain @", "must have domain"]
    
    def test_validation_error_custom_user_message(self):
        """Test validation error with custom user message."""
        error = ValidationError(
            message="Technical validation failure",
            user_message="Please enter a valid email address"
        )
        
        assert error.user_message == "Please enter a valid email address"


class TestStorageError:
    """Test StorageError class."""
    
    def test_basic_storage_error(self):
        """Test basic storage error creation."""
        error = StorageError("File not found")
        
        assert error.category == ErrorCategory.STORAGE
        assert error.severity == ErrorSeverity.HIGH
        assert "Storage operation failed:" in error.user_message
    
    def test_storage_error_with_file_info(self):
        """Test storage error with file information."""
        error = StorageError(
            message="Permission denied",
            file_path="/path/to/file.json",
            operation="write"
        )
        
        assert error.details['file_path'] == "/path/to/file.json"
        assert error.details['operation'] == "write"


class TestScanningError:
    """Test ScanningError class."""
    
    def test_basic_scanning_error(self):
        """Test basic scanning error creation."""
        error = ScanningError("Directory not accessible")
        
        assert error.category == ErrorCategory.SCANNING
        assert error.severity == ErrorSeverity.MEDIUM
        assert "Music scanning failed:" in error.user_message
    
    def test_scanning_error_with_music_info(self):
        """Test scanning error with music-specific information."""
        error = ScanningError(
            message="Invalid album structure",
            scan_path="/music/bands",
            band_name="Test Band",
            album_name="Test Album"
        )
        
        assert error.details['scan_path'] == "/music/bands"
        assert error.details['band_name'] == "Test Band"
        assert error.details['album_name'] == "Test Album"


class TestConfigurationError:
    """Test ConfigurationError class."""
    
    def test_basic_configuration_error(self):
        """Test basic configuration error creation."""
        error = ConfigurationError("Invalid configuration")
        
        assert error.category == ErrorCategory.CONFIGURATION
        assert error.severity == ErrorSeverity.HIGH
    
    def test_configuration_error_with_config_info(self):
        """Test configuration error with config information."""
        error = ConfigurationError(
            message="Invalid music root path",
            config_key="MUSIC_ROOT_PATH",
            config_value="/invalid/path"
        )
        
        assert error.details['config_key'] == "MUSIC_ROOT_PATH"
        assert error.details['config_value'] == "/invalid/path"


class TestNetworkError:
    """Test NetworkError class."""
    
    def test_basic_network_error(self):
        """Test basic network error creation."""
        error = NetworkError("Connection failed")
        
        assert error.category == ErrorCategory.NETWORK
        assert error.severity == ErrorSeverity.MEDIUM
    
    def test_network_error_with_url_info(self):
        """Test network error with URL information."""
        error = NetworkError(
            message="HTTP 404 Not Found",
            url="https://api.example.com/band/123",
            status_code=404
        )
        
        assert error.details['url'] == "https://api.example.com/band/123"
        assert error.details['status_code'] == 404


class TestPermissionError:
    """Test PermissionError class."""
    
    def test_basic_permission_error(self):
        """Test basic permission error creation."""
        error = PermissionError("Access denied")
        
        assert error.category == ErrorCategory.PERMISSION
        assert error.severity == ErrorSeverity.HIGH
    
    def test_permission_error_with_resource_info(self):
        """Test permission error with resource information."""
        error = PermissionError(
            message="Write permission denied",
            resource_path="/protected/file.json",
            required_permission="write"
        )
        
        assert error.details['resource_path'] == "/protected/file.json"
        assert error.details['required_permission'] == "write"


class TestResourceError:
    """Test ResourceError class."""
    
    def test_basic_resource_error(self):
        """Test basic resource error creation."""
        error = ResourceError("Resource not available")
        
        assert error.category == ErrorCategory.RESOURCE
        assert error.severity == ErrorSeverity.MEDIUM
    
    def test_resource_error_with_resource_info(self):
        """Test resource error with resource information."""
        error = ResourceError(
            message="Band resource not found",
            resource_name="band://info/Unknown Band",
            resource_type="band_info"
        )
        
        assert error.details['resource_name'] == "band://info/Unknown Band"
        assert error.details['resource_type'] == "band_info"


class TestDataError:
    """Test DataError class."""
    
    def test_basic_data_error(self):
        """Test basic data error creation."""
        error = DataError("Corrupted data")
        
        assert error.category == ErrorCategory.DATA
        assert error.severity == ErrorSeverity.HIGH
    
    def test_data_error_with_data_info(self):
        """Test data error with data information."""
        error = DataError(
            message="Invalid JSON structure",
            data_type="band_metadata",
            data_source="file://.band_metadata.json"
        )
        
        assert error.details['data_type'] == "band_metadata"
        assert error.details['data_source'] == "file://.band_metadata.json"


class TestCacheError:
    """Test CacheError class."""
    
    def test_cache_error_inherits_storage(self):
        """Test that CacheError inherits from StorageError."""
        error = CacheError("Cache write failed")
        
        assert isinstance(error, StorageError)
        assert error.category == ErrorCategory.STORAGE
    
    def test_cache_error_custom_severity(self):
        """Test cache error with custom severity."""
        error = CacheError("Critical cache failure", severity=ErrorSeverity.CRITICAL)
        
        assert error.severity == ErrorSeverity.CRITICAL


class TestExceptionUtilities:
    """Test exception utility functions."""
    
    def test_wrap_exception_basic(self):
        """Test basic exception wrapping."""
        original = ValueError("Original error")
        
        wrapped = wrap_exception(original)
        
        assert isinstance(wrapped, MusicMCPError)
        assert wrapped.original_exception == original
        assert "Original error" in wrapped.message
    
    def test_wrap_exception_custom_class(self):
        """Test exception wrapping with custom class."""
        original = FileNotFoundError("File not found")
        
        wrapped = wrap_exception(original, StorageError, file_path="/test/file.json")
        
        assert isinstance(wrapped, StorageError)
        assert wrapped.original_exception == original
        assert wrapped.details.get('file_path') == "/test/file.json"
    
    def test_create_validation_error(self):
        """Test validation error creation utility."""
        error = create_validation_error(
            field_name="band_name",
            field_value="",
            message="Band name cannot be empty"
        )
        
        assert isinstance(error, ValidationError)
        assert error.details['field_name'] == "band_name"
        assert error.details['field_value'] == ""
        assert "Band name cannot be empty" in error.message
    
    def test_create_storage_error(self):
        """Test storage error creation utility."""
        original = IOError("Disk full")
        
        error = create_storage_error(
            operation="save_metadata",
            file_path="/music/band/.band_metadata.json",
            original_error=original
        )
        
        assert isinstance(error, StorageError)
        assert error.details['operation'] == "save_metadata"
        assert error.details['file_path'] == "/music/band/.band_metadata.json"
        assert error.original_exception == original


class TestExceptionSerialization:
    """Test exception serialization and JSON handling."""
    
    def test_error_to_json(self):
        """Test converting error to JSON."""
        error = ValidationError(
            message="Test error",
            field_name="test_field",
            severity=ErrorSeverity.HIGH
        )
        
        error_dict = error.to_dict()
        json_str = json.dumps(error_dict)
        
        # Should not raise exception
        assert isinstance(json_str, str)
        
        # Should be able to parse back
        parsed = json.loads(json_str)
        assert parsed['error_type'] == 'ValidationError'
        assert parsed['severity'] == 'high'
    
    def test_nested_error_serialization(self):
        """Test serialization of errors with nested original exceptions."""
        try:
            raise ValueError("Original problem")
        except ValueError as e:
            wrapped = wrap_exception(e, StorageError, operation="test")
            
        error_dict = wrapped.to_dict()
        
        assert 'original_error' in error_dict
        assert error_dict['original_error']['type'] == 'ValueError'
        assert error_dict['original_error']['message'] == 'Original problem'


class TestExceptionIntegration:
    """Test exception integration with other components."""
    
    def test_exception_in_handler_context(self):
        """Test exception handling in handler context."""
        from tests.utils.test_helpers import TestResponseValidator
        
        error = ValidationError("Invalid input", field_name="test")
        response = error.get_client_response()
        
        # Should have expected structure
        assert response['error'] == "Validation error: Invalid input"
        assert response['error_type'] == 'ValidationError'
        assert response['severity'] == 'medium'
        assert response['category'] == 'validation'
    
    def test_exception_chaining(self):
        """Test exception chaining and context preservation."""
        original = FileNotFoundError("File not found")
        storage_error = create_storage_error("read", "/test/file.json", original)
        wrapped_again = wrap_exception(storage_error, DataError, data_type="metadata")
        
        # Should preserve original exception chain
        assert wrapped_again.original_exception == storage_error
        assert storage_error.original_exception == original
    
    @pytest.mark.parametrize("severity", [
        ErrorSeverity.LOW,
        ErrorSeverity.MEDIUM, 
        ErrorSeverity.HIGH,
        ErrorSeverity.CRITICAL
    ])
    def test_all_severity_levels(self, severity):
        """Test all severity levels work correctly."""
        error = MusicMCPError("Test error", severity=severity)
        
        assert error.severity == severity
        assert error.to_dict()['severity'] == severity.value
    
    @pytest.mark.parametrize("category", list(ErrorCategory))
    def test_all_error_categories(self, category):
        """Test all error categories work correctly."""
        error = MusicMCPError("Test error", category=category)
        
        assert error.category == category
        assert error.to_dict()['category'] == category.value 