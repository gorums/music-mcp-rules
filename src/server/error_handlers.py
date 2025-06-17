#!/usr/bin/env python3
"""
Music Collection MCP Server - Error Response Management

This module provides error response management and standardized error handling
across all MCP components including tools, resources, and prompts.
"""

import logging
from typing import Any, Dict, Optional, Union
from datetime import datetime, timezone
import traceback

from ..exceptions import (
    MusicMCPError, 
    ErrorSeverity, 
    ErrorCategory,
    ValidationError,
    StorageError,
    ScanningError,
    ConfigurationError,
    NetworkError,
    PermissionError,
    ResourceError,
    DataError,
    wrap_exception
)


class ErrorResponseManager:
    """
    Centralized error response management for the Music Collection MCP Server.
    
    Provides standardized error handling, logging, and response formatting
    across all components.
    """
    
    def __init__(self, component_name: str, logger: Optional[logging.Logger] = None):
        """
        Initialize error response manager.
        
        Args:
            component_name: Name of the component using this manager
            logger: Logger instance (if None, creates a new logger)
        """
        self.component_name = component_name
        self.logger = logger or logging.getLogger(f"error_handler.{component_name}")
    
    def handle_exception(
        self, 
        exception: Exception, 
        context: str = "",
        include_traceback: bool = False
    ) -> Dict[str, Any]:
        """
        Handle any exception and convert to standardized error response.
        
        Args:
            exception: The exception that occurred
            context: Additional context about where the error occurred
            include_traceback: Whether to include traceback in response
            
        Returns:
            Standardized error response dictionary
        """
        # If it's already a MusicMCPError, use it directly
        if isinstance(exception, MusicMCPError):
            error = exception
        else:
            # Wrap generic exceptions into MusicMCPError
            error = self._classify_generic_exception(exception, context)
        
        # Log the error appropriately based on severity
        self._log_error(error, context, include_traceback)
        
        # Create response
        return self._create_error_response(error, context, include_traceback)
    
    def _classify_generic_exception(self, exception: Exception, context: str) -> MusicMCPError:
        """
        Classify generic exceptions into appropriate MusicMCPError subclasses.
        
        Args:
            exception: The generic exception to classify
            context: Context where the exception occurred
            
        Returns:
            Appropriate MusicMCPError subclass instance
        """
        exc_type = type(exception).__name__
        exc_message = str(exception)
        
        # Classification rules based on exception type and message patterns
        if isinstance(exception, (FileNotFoundError, OSError, IOError)):
            return StorageError(
                message=f"File system error: {exc_message}",
                original_exception=exception,
                user_message=f"File operation failed: {exc_message}"
            )
        
        elif isinstance(exception, PermissionError):
            return PermissionError(
                message=f"Permission denied: {exc_message}",
                original_exception=exception,
                user_message=f"Access denied: {exc_message}"
            )
        
        elif isinstance(exception, ValueError):
            return ValidationError(
                message=f"Value error: {exc_message}",
                original_exception=exception,
                user_message=f"Invalid input: {exc_message}"
            )
        
        elif isinstance(exception, (KeyError, AttributeError)):
            return DataError(
                message=f"Data structure error: {exc_message}",
                original_exception=exception,
                user_message=f"Data format error: {exc_message}"
            )
        
        elif "network" in exc_message.lower() or "connection" in exc_message.lower():
            return NetworkError(
                message=f"Network error: {exc_message}",
                original_exception=exception,
                user_message=f"Network connection failed: {exc_message}"
            )
        
        elif "config" in exc_message.lower() or "environment" in exc_message.lower():
            return ConfigurationError(
                message=f"Configuration error: {exc_message}",
                original_exception=exception,
                user_message=f"Configuration problem: {exc_message}"
            )
        
        elif "scan" in context.lower() or "folder" in context.lower():
            return ScanningError(
                message=f"Scanning error: {exc_message}",
                original_exception=exception,
                user_message=f"Music scanning failed: {exc_message}"
            )
        
        else:
            # Default to generic MusicMCPError
            return MusicMCPError(
                message=f"{exc_type}: {exc_message}",
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.OPERATION,
                original_exception=exception,
                user_message=f"Operation failed: {exc_message}"
            )
    
    def _log_error(self, error: MusicMCPError, context: str, include_traceback: bool):
        """
        Log error with appropriate level based on severity.
        
        Args:
            error: The MusicMCPError to log
            context: Context information
            include_traceback: Whether to include traceback
        """
        log_message = f"[{self.component_name}] {context}: {error.message}" if context else f"[{self.component_name}] {error.message}"
        
        # Log based on severity
        if error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif error.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
        elif error.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:  # LOW
            self.logger.info(log_message)
        
        # Add detailed information in debug mode
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(f"Error details: {error.to_dict()}")
            
            if include_traceback or error.original_exception:
                if error.traceback_info:
                    self.logger.debug(f"Traceback: {error.traceback_info}")
                else:
                    self.logger.debug(f"Traceback: {traceback.format_exc()}")
    
    def _create_error_response(
        self, 
        error: MusicMCPError, 
        context: str, 
        include_traceback: bool
    ) -> Dict[str, Any]:
        """
        Create standardized error response.
        
        Args:
            error: The MusicMCPError instance
            context: Context information
            include_traceback: Whether to include traceback
            
        Returns:
            Standardized error response dictionary
        """
        response = {
            'status': 'error',
            'error': error.user_message,
            'error_type': error.__class__.__name__,
            'severity': error.severity.value,
            'category': error.category.value,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'component': self.component_name
        }
        
        # Add context if provided
        if context:
            response['context'] = context
        
        # Add error details
        if error.details:
            response['details'] = error.details
        
        # Add original error information if present
        if error.original_exception:
            response['original_error'] = {
                'type': error.original_exception.__class__.__name__,
                'message': str(error.original_exception)
            }
        
        # Add traceback if requested and available
        if include_traceback:
            if error.traceback_info:
                response['traceback'] = error.traceback_info
            else:
                response['traceback'] = traceback.format_exc()
        
        return response


class ToolErrorHandler(ErrorResponseManager):
    """Specialized error handler for MCP tools."""
    
    def __init__(self, tool_name: str, tool_version: str = "1.0.0"):
        super().__init__(f"tool.{tool_name}")
        self.tool_name = tool_name
        self.tool_version = tool_version
    
    def create_tool_error_response(
        self, 
        exception: Exception, 
        context: str = "",
        **tool_info
    ) -> Dict[str, Any]:
        """
        Create tool-specific error response.
        
        Args:
            exception: The exception that occurred
            context: Context about the error
            **tool_info: Additional tool metadata
            
        Returns:
            Tool error response with standardized format
        """
        response = self.handle_exception(exception, context)
        
        # Add tool-specific information
        response['tool_info'] = {
            'tool_name': self.tool_name,
            'version': self.tool_version,
            'error_occurred': True,
            **tool_info
        }
        
        return response


class ResourceErrorHandler(ErrorResponseManager):
    """Specialized error handler for MCP resources."""
    
    def __init__(self, resource_name: str, resource_version: str = "1.0.0"):
        super().__init__(f"resource.{resource_name}")
        self.resource_name = resource_name
        self.resource_version = resource_version
    
    def create_resource_error_content(
        self, 
        exception: Exception, 
        context: str = "",
        **resource_info
    ) -> str:
        """
        Create resource error content in markdown format.
        
        Args:
            exception: The exception that occurred
            context: Context about the error
            **resource_info: Additional resource metadata
            
        Returns:
            Markdown-formatted error content
        """
        # Handle the exception to get standardized error info
        error_info = self.handle_exception(exception, context)
        
        # Format as markdown
        return f"""# Error Retrieving {self.resource_name.title()} Information

**Resource:** `{self.resource_name}`  
**Error Type:** `{error_info['error_type']}`  
**Severity:** `{error_info['severity']}`  
**Category:** `{error_info['category']}`

## Error Message
{error_info['error']}

## Context
{context if context else 'No additional context available'}

## What You Can Do
1. Check the input parameters and try again
2. Verify that required data files exist and are accessible
3. Check the server logs for more detailed error information
4. If the problem persists, contact support

**Timestamp:** {error_info['timestamp']}  
**Component:** {error_info['component']}
"""


class PromptErrorHandler(ErrorResponseManager):
    """Specialized error handler for MCP prompts."""
    
    def __init__(self, prompt_name: str, prompt_version: str = "1.0.0"):
        super().__init__(f"prompt.{prompt_name}")
        self.prompt_name = prompt_name
        self.prompt_version = prompt_version
    
    def create_prompt_error_template(
        self, 
        exception: Exception, 
        context: str = "",
        **prompt_info
    ) -> Dict[str, Any]:
        """
        Create prompt error template.
        
        Args:
            exception: The exception that occurred
            context: Context about the error
            **prompt_info: Additional prompt metadata
            
        Returns:
            Prompt error template dictionary
        """
        error_info = self.handle_exception(exception, context)
        
        return {
            'name': self.prompt_name,
            'description': f'Error loading {self.prompt_name} prompt template - {error_info["error"]}',
            'messages': [
                {
                    'role': 'user',
                    'content': f"""Error generating {self.prompt_name} prompt: {error_info['error']}

Context: {context if context else 'No additional context'}

Please check your parameters and try again. If the problem persists, check the server logs for more detailed error information.

Error Details:
- Error Type: {error_info['error_type']}
- Severity: {error_info['severity']}
- Category: {error_info['category']}
- Timestamp: {error_info['timestamp']}"""
                }
            ],
            'arguments': [],
            'error_info': error_info
        }


# Utility functions for creating error handlers
def create_tool_error_handler(tool_name: str, version: str = "1.0.0") -> ToolErrorHandler:
    """Create a tool error handler instance."""
    return ToolErrorHandler(tool_name, version)


def create_resource_error_handler(resource_name: str, version: str = "1.0.0") -> ResourceErrorHandler:
    """Create a resource error handler instance."""
    return ResourceErrorHandler(resource_name, version)


def create_prompt_error_handler(prompt_name: str, version: str = "1.0.0") -> PromptErrorHandler:
    """Create a prompt error handler instance."""
    return PromptErrorHandler(prompt_name, version)


# Global error handler functions for backward compatibility
def handle_tool_error(tool_name: str, exception: Exception, context: str = "", **kwargs) -> Dict[str, Any]:
    """Handle tool error with standardized response."""
    handler = ToolErrorHandler(tool_name)
    return handler.create_tool_error_response(exception, context, **kwargs)


def handle_resource_error(resource_name: str, exception: Exception, context: str = "", **kwargs) -> str:
    """Handle resource error with markdown response."""
    handler = ResourceErrorHandler(resource_name)
    return handler.create_resource_error_content(exception, context, **kwargs)


def handle_prompt_error(prompt_name: str, exception: Exception, context: str = "", **kwargs) -> Dict[str, Any]:
    """Handle prompt error with template response."""
    handler = PromptErrorHandler(prompt_name)
    return handler.create_prompt_error_template(exception, context, **kwargs) 