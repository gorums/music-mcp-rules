#!/usr/bin/env python3
"""
Music Collection MCP Server - Base Handler Classes

This module contains abstract base classes for standardizing tool, resource, and prompt handlers.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
import traceback
from datetime import datetime, timezone

# Import standardized exception handling
import sys
import os
from pathlib import Path

# Add src directory to path if not already there
current_dir = Path(__file__).parent
src_dir = current_dir.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from exceptions import MusicMCPError, ErrorSeverity, ErrorCategory
from .error_handlers import (
    ErrorResponseManager, 
    ToolErrorHandler, 
    ResourceErrorHandler, 
    PromptErrorHandler
)

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class HandlerResponse:
    """Standardized response structure for all handlers."""
    status: str  # 'success' or 'error'
    data: Optional[Any] = None
    error: Optional[str] = None
    handler_info: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        result = {
            'status': self.status,
            'timestamp': self.timestamp or datetime.now(timezone.utc).isoformat()
        }
        
        if self.status == 'success':
            if self.data is not None:
                if isinstance(self.data, dict):
                    result.update(self.data)
                else:
                    result['data'] = self.data
        else:
            result['error'] = self.error
            
        if self.handler_info:
            result['handler_info'] = self.handler_info
            
        return result


class BaseHandler(ABC):
    """Base class for all MCP handlers with common functionality."""
    
    def __init__(self, handler_name: str, version: str = "1.0.0"):
        """
        Initialize base handler.
        
        Args:
            handler_name: Name of the handler (e.g., 'scan_music_folders')
            version: Version of the handler
        """
        self.handler_name = handler_name
        self.version = version
        self.logger = logging.getLogger(f"{__name__}.{handler_name}")
        # Initialize error response manager for standardized error handling
        self.error_manager = ErrorResponseManager(handler_name, self.logger)
    
    def _create_handler_info(self, **kwargs) -> Dict[str, Any]:
        """Create standardized handler info metadata."""
        info = {
            'handler_name': self.handler_name,
            'version': self.version,
            'handler_type': self.__class__.__name__
        }
        info.update(kwargs)
        return info
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat()
    
    def _handle_exception(self, e: Exception, context: str = "") -> HandlerResponse:
        """
        Standardized exception handling using the new error response system.
        
        Args:
            e: The exception that occurred
            context: Additional context about where the error occurred
            
        Returns:
            Standardized error response
        """
        # Use the error manager for standardized handling
        error_response = self.error_manager.handle_exception(e, context)
        
        # Convert to HandlerResponse format for backward compatibility
        return HandlerResponse(
            status=error_response['status'],
            error=error_response['error'],
            handler_info=self._create_handler_info(
                error_occurred=True,
                error_type=error_response.get('error_type'),
                severity=error_response.get('severity'),
                category=error_response.get('category')
            )
        )
    
    def _validate_required_params(self, params: Dict[str, Any], required: List[str]) -> Optional[HandlerResponse]:
        """
        Validate that required parameters are present and not None.
        
        Args:
            params: Parameters to validate
            required: List of required parameter names
            
        Returns:
            Error response if validation fails, None if validation passes
        """
        missing = []
        for param in required:
            if param not in params or params[param] is None:
                missing.append(param)
        
        if missing:
            error_msg = f"Missing required parameters: {', '.join(missing)}"
            return HandlerResponse(
                status='error',
                error=error_msg,
                handler_info=self._create_handler_info(validation_error=True)
            )
        
        return None


class BaseToolHandler(BaseHandler):
    """Base class for MCP tool handlers."""
    
    def __init__(self, tool_name: str, version: str = "1.0.0"):
        """
        Initialize tool handler.
        
        Args:
            tool_name: Name of the tool (e.g., 'scan_music_folders')
            version: Version of the tool
        """
        super().__init__(tool_name, version)
        # Initialize specialized tool error handler
        self.tool_error_handler = ToolErrorHandler(tool_name, version)
    
    @abstractmethod
    def _execute_tool(self, **kwargs) -> Any:
        """
        Execute the core tool logic. Must be implemented by subclasses.
        
        Args:
            **kwargs: Tool-specific arguments
            
        Returns:
            Tool-specific result data
        """
        pass
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute tool with standardized error handling and response formatting.
        
        Args:
            **kwargs: Tool-specific arguments
            
        Returns:
            Standardized tool response dictionary
        """
        try:
            # Execute the core tool logic
            result = self._execute_tool(**kwargs)
            
            # Create success response
            response = HandlerResponse(
                status='success',
                data=result,
                handler_info=self._create_handler_info(
                    tool_mode='execution',
                    parameters_used=kwargs
                )
            )
            
            return response.to_dict()
            
        except Exception as e:
            # Use specialized tool error handler
            return self.tool_error_handler.create_tool_error_response(
                e, "Tool execution failed", 
                tool_mode='execution',
                parameters_used=kwargs
            )
    
    def _create_tool_info(self, **kwargs) -> Dict[str, Any]:
        """Create tool-specific metadata."""
        return self._create_handler_info(
            tool_name=self.handler_name,
            **kwargs
        )


class BaseResourceHandler(BaseHandler):
    """Base class for MCP resource handlers."""
    
    def __init__(self, resource_name: str, version: str = "1.0.0"):
        """
        Initialize resource handler.
        
        Args:
            resource_name: Name of the resource (e.g., 'band_info')
            version: Version of the resource
        """
        super().__init__(resource_name, version)
        # Initialize specialized resource error handler
        self.resource_error_handler = ResourceErrorHandler(resource_name, version)
    
    @abstractmethod
    def _get_resource_content(self, **kwargs) -> str:
        """
        Get the resource content. Must be implemented by subclasses.
        
        Args:
            **kwargs: Resource-specific arguments
            
        Returns:
            Resource content (typically markdown)
        """
        pass
    
    def get_content(self, **kwargs) -> str:
        """
        Get resource content with standardized error handling.
        
        Args:
            **kwargs: Resource-specific arguments
            
        Returns:
            Resource content or error message
        """
        try:
            return self._get_resource_content(**kwargs)
            
        except Exception as e:
            # Use specialized resource error handler
            return self.resource_error_handler.create_resource_error_content(
                e, "Resource content generation failed", **kwargs
            )
    
    def _format_error_content(self, error_message: str, **kwargs) -> str:
        """
        Format error message as markdown content.
        
        Args:
            error_message: The error message
            **kwargs: Context parameters for error formatting
            
        Returns:
            Markdown-formatted error message
        """
        return f"""# Error Retrieving {self.handler_name.title()} Information

**Resource:** {self.handler_name}
**Error:** {error_message}

Please check your request parameters and try again. If the problem persists, 
check the server logs for more detailed error information.

**Timestamp:** {datetime.now(timezone.utc).isoformat()}
"""


class BasePromptHandler(BaseHandler):
    """Base class for MCP prompt handlers."""
    
    def __init__(self, prompt_name: str, version: str = "1.0.0"):
        """
        Initialize prompt handler.
        
        Args:
            prompt_name: Name of the prompt (e.g., 'fetch_band_info')
            version: Version of the prompt
        """
        super().__init__(prompt_name, version)
        # Initialize specialized prompt error handler
        self.prompt_error_handler = PromptErrorHandler(prompt_name, version)
    
    @abstractmethod
    def _generate_prompt(self, **kwargs) -> Dict[str, Any]:
        """
        Generate the prompt template. Must be implemented by subclasses.
        
        Args:
            **kwargs: Prompt-specific arguments
            
        Returns:
            Prompt template dictionary
        """
        pass
    
    def generate(self, **kwargs) -> Dict[str, Any]:
        """
        Generate prompt with standardized error handling.
        
        Args:
            **kwargs: Prompt-specific arguments
            
        Returns:
            Prompt template dictionary or error response
        """
        try:
            return self._generate_prompt(**kwargs)
            
        except Exception as e:
            # Use specialized prompt error handler
            return self.prompt_error_handler.create_prompt_error_template(
                e, "Prompt generation failed", **kwargs
            )


# Utility functions for common response patterns

def create_success_response(data: Any, handler_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a standardized success response."""
    response = HandlerResponse(
        status='success',
        data=data,
        handler_info=handler_info
    )
    return response.to_dict()


def create_error_response(error_message: str, handler_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a standardized error response."""
    response = HandlerResponse(
        status='error',
        error=error_message,
        handler_info=handler_info
    )
    return response.to_dict()


def validate_pagination_params(page: int, page_size: int, max_page_size: int = 100) -> Optional[str]:
    """
    Validate pagination parameters.
    
    Args:
        page: Page number (should be >= 1)
        page_size: Items per page (should be 1-max_page_size)
        max_page_size: Maximum allowed page size
        
    Returns:
        Error message if validation fails, None if valid
    """
    if page < 1:
        return "Page number must be >= 1"
    
    if page_size < 1 or page_size > max_page_size:
        return f"Page size must be between 1 and {max_page_size}"
    
    return None


def validate_sort_params(sort_by: str, sort_order: str, allowed_fields: List[str]) -> Optional[str]:
    """
    Validate sorting parameters.
    
    Args:
        sort_by: Field to sort by
        sort_order: Sort order ('asc' or 'desc')
        allowed_fields: List of allowed sort fields
        
    Returns:
        Error message if validation fails, None if valid
    """
    if sort_by not in allowed_fields:
        return f"sort_by must be one of: {', '.join(allowed_fields)}"
    
    if sort_order not in ['asc', 'desc']:
        return "sort_order must be 'asc' or 'desc'"
    
    return None 