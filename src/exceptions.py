#!/usr/bin/env python3
"""
Music Collection MCP Server - Unified Exception Hierarchy

This module defines the unified exception hierarchy for the Music Collection MCP Server,
providing standardized error handling across all components.
"""

from enum import Enum
from typing import Any, Dict, Optional, List
import traceback


class ErrorSeverity(Enum):
    """Error severity levels for categorizing exceptions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""
    VALIDATION = "validation"
    STORAGE = "storage"
    SCANNING = "scanning"
    NETWORK = "network"
    CONFIGURATION = "configuration"
    PERMISSION = "permission"
    RESOURCE = "resource"
    OPERATION = "operation"
    DATA = "data"
    SYSTEM = "system"


class MusicMCPError(Exception):
    """
    Base exception class for all Music Collection MCP Server errors.
    
    Provides standardized error information including:
    - Error message and context
    - Severity level
    - Error category
    - User-friendly message
    - Additional error details
    """
    
    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.OPERATION,
        user_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        """
        Initialize MusicMCPError.
        
        Args:
            message: Technical error message for logging
            severity: Error severity level
            category: Error category for classification
            user_message: User-friendly error message (if different from message)
            details: Additional error context and details
            original_exception: Original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.severity = severity
        self.category = category
        self.user_message = user_message or message
        self.details = details or {}
        self.original_exception = original_exception
        self.traceback_info = traceback.format_exc() if original_exception else None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary format for JSON serialization."""
        result = {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'user_message': self.user_message,
            'severity': self.severity.value,
            'category': self.category.value,
            'details': self.details
        }
        
        if self.original_exception:
            result['original_error'] = {
                'type': self.original_exception.__class__.__name__,
                'message': str(self.original_exception)
            }
        
        return result
    
    def get_client_response(self) -> Dict[str, Any]:
        """Get client-friendly error response."""
        return {
            'error': self.user_message,
            'error_type': self.__class__.__name__,
            'severity': self.severity.value,
            'category': self.category.value
        }


class ValidationError(MusicMCPError):
    """
    Exception for data validation errors.
    
    Used when input data doesn't meet required schema, format, or business rules.
    """
    
    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        field_value: Optional[Any] = None,
        validation_rules: Optional[List[str]] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if field_name:
            details['field_name'] = field_name
        if field_value is not None:
            details['field_value'] = field_value
        if validation_rules:
            details['validation_rules'] = validation_rules
        
        user_message = kwargs.get('user_message', f"Validation error: {message}")
        
        super().__init__(
            message=message,
            severity=kwargs.get('severity', ErrorSeverity.MEDIUM),
            category=ErrorCategory.VALIDATION,
            user_message=user_message,
            details=details,
            original_exception=kwargs.get('original_exception')
        )


class StorageError(MusicMCPError):
    """
    Exception for storage and file system errors.
    
    Used for file operations, JSON operations, database errors, etc.
    """
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if file_path:
            details['file_path'] = file_path
        if operation:
            details['operation'] = operation
        
        user_message = kwargs.get('user_message', f"Storage operation failed: {message}")
        
        super().__init__(
            message=message,
            severity=kwargs.get('severity', ErrorSeverity.HIGH),
            category=ErrorCategory.STORAGE,
            user_message=user_message,
            details=details,
            original_exception=kwargs.get('original_exception')
        )


class ScanningError(MusicMCPError):
    """
    Exception for music collection scanning errors.
    
    Used for folder traversal, file discovery, and album parsing errors.
    """
    
    def __init__(
        self,
        message: str,
        scan_path: Optional[str] = None,
        band_name: Optional[str] = None,
        album_name: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if scan_path:
            details['scan_path'] = scan_path
        if band_name:
            details['band_name'] = band_name
        if album_name:
            details['album_name'] = album_name
        
        user_message = kwargs.get('user_message', f"Music scanning failed: {message}")
        
        super().__init__(
            message=message,
            severity=kwargs.get('severity', ErrorSeverity.MEDIUM),
            category=ErrorCategory.SCANNING,
            user_message=user_message,
            details=details,
            original_exception=kwargs.get('original_exception')
        )


class ConfigurationError(MusicMCPError):
    """
    Exception for configuration and setup errors.
    
    Used for invalid configuration, missing environment variables, setup issues.
    """
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if config_key:
            details['config_key'] = config_key
        if config_value:
            details['config_value'] = config_value
        
        user_message = kwargs.get('user_message', f"Configuration error: {message}")
        
        super().__init__(
            message=message,
            severity=kwargs.get('severity', ErrorSeverity.HIGH),
            category=ErrorCategory.CONFIGURATION,
            user_message=user_message,
            details=details,
            original_exception=kwargs.get('original_exception')
        )


class NetworkError(MusicMCPError):
    """
    Exception for network and external service errors.
    
    Used for API calls, network timeouts, external service failures.
    """
    
    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        status_code: Optional[int] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if url:
            details['url'] = url
        if status_code:
            details['status_code'] = status_code
        
        user_message = kwargs.get('user_message', f"Network operation failed: {message}")
        
        super().__init__(
            message=message,
            severity=kwargs.get('severity', ErrorSeverity.MEDIUM),
            category=ErrorCategory.NETWORK,
            user_message=user_message,
            details=details,
            original_exception=kwargs.get('original_exception')
        )


class PermissionError(MusicMCPError):
    """
    Exception for permission and access errors.
    
    Used for file system permissions, access denied errors.
    """
    
    def __init__(
        self,
        message: str,
        resource_path: Optional[str] = None,
        required_permission: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if resource_path:
            details['resource_path'] = resource_path
        if required_permission:
            details['required_permission'] = required_permission
        
        user_message = kwargs.get('user_message', f"Permission denied: {message}")
        
        super().__init__(
            message=message,
            severity=kwargs.get('severity', ErrorSeverity.HIGH),
            category=ErrorCategory.PERMISSION,
            user_message=user_message,
            details=details,
            original_exception=kwargs.get('original_exception')
        )


class ResourceError(MusicMCPError):
    """
    Exception for resource-related errors.
    
    Used for missing resources, resource conflicts, resource exhaustion.
    """
    
    def __init__(
        self,
        message: str,
        resource_name: Optional[str] = None,
        resource_type: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if resource_name:
            details['resource_name'] = resource_name
        if resource_type:
            details['resource_type'] = resource_type
        
        user_message = kwargs.get('user_message', f"Resource error: {message}")
        
        super().__init__(
            message=message,
            severity=kwargs.get('severity', ErrorSeverity.MEDIUM),
            category=ErrorCategory.RESOURCE,
            user_message=user_message,
            details=details,
            original_exception=kwargs.get('original_exception')
        )


class DataError(MusicMCPError):
    """
    Exception for data consistency and integrity errors.
    
    Used for corrupted data, inconsistent states, data migration errors.
    """
    
    def __init__(
        self,
        message: str,
        data_type: Optional[str] = None,
        data_source: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if data_type:
            details['data_type'] = data_type
        if data_source:
            details['data_source'] = data_source
        
        user_message = kwargs.get('user_message', f"Data error: {message}")
        
        super().__init__(
            message=message,
            severity=kwargs.get('severity', ErrorSeverity.HIGH),
            category=ErrorCategory.DATA,
            user_message=user_message,
            details=details,
            original_exception=kwargs.get('original_exception')
        )


# Legacy exception compatibility
class CacheError(StorageError):
    """Legacy cache error - now inherits from StorageError."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            operation="cache",
            user_message=f"Cache operation failed: {message}",
            **kwargs
        )


# Utility functions for exception handling
def wrap_exception(original_exception: Exception, error_class: type = MusicMCPError, **kwargs) -> MusicMCPError:
    """
    Wrap a generic exception into a MusicMCPError subclass.
    
    Args:
        original_exception: The original exception to wrap
        error_class: The MusicMCPError subclass to use
        **kwargs: Additional arguments for the error class
        
    Returns:
        MusicMCPError instance with wrapped exception
    """
    message = kwargs.get('message', str(original_exception))
    kwargs['original_exception'] = original_exception
    
    return error_class(message, **kwargs)


def create_validation_error(field_name: str, field_value: Any, message: str, **kwargs) -> ValidationError:
    """
    Create a validation error with standardized formatting.
    
    Args:
        field_name: Name of the field that failed validation
        field_value: Value that failed validation
        message: Validation error message
        **kwargs: Additional error arguments
        
    Returns:
        ValidationError instance
    """
    return ValidationError(
        message=f"Validation failed for field '{field_name}': {message}",
        field_name=field_name,
        field_value=field_value,
        user_message=f"Invalid {field_name}: {message}",
        **kwargs
    )


def create_storage_error(operation: str, file_path: str, original_error: Exception, **kwargs) -> StorageError:
    """
    Create a storage error with standardized formatting.
    
    Args:
        operation: The storage operation that failed
        file_path: Path to the file involved in the operation
        original_error: The original exception that occurred
        **kwargs: Additional error arguments
        
    Returns:
        StorageError instance
    """
    return StorageError(
        message=f"Storage {operation} failed for {file_path}: {str(original_error)}",
        operation=operation,
        file_path=file_path,
        original_exception=original_error,
        user_message=f"Failed to {operation} data. Please check file permissions and disk space.",
        **kwargs
    ) 