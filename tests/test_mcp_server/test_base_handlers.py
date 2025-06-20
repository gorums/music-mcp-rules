#!/usr/bin/env python3
"""
Tests for Music Collection MCP Server base handler classes.

This module tests the abstract base classes for standardizing tool, resource, 
and prompt handlers including error handling and response formatting.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Any, Dict
from datetime import datetime, timezone

from src.mcp_server.base_handlers import (
    HandlerResponse, BaseHandler, BaseToolHandler, 
    BaseResourceHandler, BasePromptHandler,
    create_success_response, create_error_response,
    validate_pagination_params, validate_sort_params
)
from src.exceptions import (
    MusicMCPError, ValidationError, StorageError, 
    ErrorSeverity, ErrorCategory
)


class TestHandlerResponse:
    """Test HandlerResponse data class."""
    
    def test_success_response_creation(self):
        """Test creating a success response."""
        response = HandlerResponse(
            status='success',
            data={'result': 'test'}
        )
        
        assert response.status == 'success'
        assert response.data == {'result': 'test'}
        assert response.error is None
    
    def test_error_response_creation(self):
        """Test creating an error response."""
        response = HandlerResponse(
            status='error',
            error='Test error message',
            handler_info={'handler': 'test_handler'}
        )
        
        assert response.status == 'error'
        assert response.error == 'Test error message'
        assert response.data is None
    
    def test_to_dict_success(self):
        """Test converting success response to dictionary."""
        response = HandlerResponse(
            status='success',
            data={'bands': ['Band1', 'Band2']}
        )
        
        result = response.to_dict()
        
        assert result['status'] == 'success'
        assert result['bands'] == ['Band1', 'Band2']
        assert 'timestamp' in result
    
    def test_to_dict_error(self):
        """Test converting error response to dictionary."""
        response = HandlerResponse(
            status='error',
            error='Something went wrong',
            handler_info={'handler': 'test'}
        )
        
        result = response.to_dict()
        
        assert result['status'] == 'error'
        assert result['error'] == 'Something went wrong'
        assert result['handler_info'] == {'handler': 'test'}
        assert 'timestamp' in result
    
    def test_to_dict_with_non_dict_data(self):
        """Test converting response with non-dict data."""
        response = HandlerResponse(
            status='success',
            data='simple string result'
        )
        
        result = response.to_dict()
        
        assert result['status'] == 'success'
        assert result['data'] == 'simple string result'
    
    def test_automatic_timestamp(self):
        """Test that timestamp is automatically added."""
        response = HandlerResponse(status='success')
        result = response.to_dict()
        
        assert 'timestamp' in result
        # Should be valid ISO format
        datetime.fromisoformat(result['timestamp'].replace('Z', '+00:00'))


class ConcreteHandler(BaseHandler):
    """Concrete implementation of BaseHandler for testing."""
    
    def test_method(self):
        """Test method for validation."""
        return "test result"


class TestBaseHandler:
    """Test BaseHandler abstract base class."""
    
    def test_initialization(self):
        """Test basic handler initialization."""
        handler = ConcreteHandler("test_handler", "2.0.0")
        
        assert handler.handler_name == "test_handler"
        assert handler.version == "2.0.0"
        assert handler.logger.name.endswith("test_handler")
        assert handler.error_manager is not None
    
    def test_create_handler_info(self):
        """Test handler info creation."""
        handler = ConcreteHandler("test_handler")
        
        info = handler._create_handler_info(custom_field="custom_value")
        
        assert info['handler_name'] == "test_handler"
        assert info['version'] == "1.0.0"
        assert info['handler_type'] == "ConcreteHandler"
        assert info['custom_field'] == "custom_value"
    
    def test_get_timestamp(self):
        """Test timestamp generation."""
        handler = ConcreteHandler("test_handler")
        
        timestamp = handler._get_timestamp()
        
        # Should be valid ISO format
        parsed = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        assert isinstance(parsed, datetime)
    
    def test_handle_exception_basic(self):
        """Test basic exception handling."""
        handler = ConcreteHandler("test_handler")
        error = ValueError("Test error")
        
        response = handler._handle_exception(error, "test context")
        
        assert response.status == 'error'
        assert response.error is not None
        assert response.handler_info is not None
        assert response.handler_info['error_occurred'] is True
    
    def test_handle_exception_music_mcp_error(self):
        """Test handling of MusicMCPError exceptions."""
        handler = ConcreteHandler("test_handler")
        error = ValidationError("Validation failed", field_name="test_field")
        
        response = handler._handle_exception(error, "validation context")
        
        assert response.status == 'error'
        assert "Validation failed" in response.error
        # Error manager reports generic type for MusicMCPError subclasses
        assert response.handler_info['error_type'] == 'MusicMCPError'
    
    def test_validate_required_params_success(self):
        """Test successful parameter validation."""
        handler = ConcreteHandler("test_handler")
        params = {"required1": "value1", "required2": "value2"}
        required = ["required1", "required2"]
        
        result = handler._validate_required_params(params, required)
        
        assert result is None
    
    def test_validate_required_params_missing(self):
        """Test parameter validation with missing parameters."""
        handler = ConcreteHandler("test_handler")
        params = {"required1": "value1"}
        required = ["required1", "required2"]
        
        result = handler._validate_required_params(params, required)
        
        assert result is not None
        assert result.status == 'error'
        assert "Missing required parameters" in result.error


class ConcreteTool(BaseToolHandler):
    """Concrete implementation of BaseToolHandler for testing."""
    
    def __init__(self, tool_name: str, version: str = "1.0.0", return_value: Any = None, raise_exception: Exception = None):
        super().__init__(tool_name, version)
        self.return_value = return_value or {"result": "success"}
        self.raise_exception = raise_exception
        self.execution_count = 0
    
    def _execute_tool(self, **kwargs) -> Any:
        """Test implementation of tool execution."""
        self.execution_count += 1
        if self.raise_exception:
            raise self.raise_exception
        return self.return_value


class TestBaseToolHandler:
    """Test BaseToolHandler abstract base class."""
    
    def test_initialization(self):
        """Test tool handler initialization."""
        tool = ConcreteTool("test_tool", "3.0.0")
        
        assert tool.handler_name == "test_tool"
        # Version gets set in constructor 
        assert tool.version == "3.0.0"
        assert tool.tool_error_handler is not None
    
    def test_execute_success(self):
        """Test successful tool execution."""
        tool = ConcreteTool("test_tool", return_value={"bands": ["Band1", "Band2"]})
        
        result = tool.execute(param1="value1")
        
        assert result['status'] == 'success'
        assert result['bands'] == ["Band1", "Band2"]
        assert tool.execution_count == 1
    
    def test_execute_with_exception(self):
        """Test tool execution with exception."""
        error = ValidationError("Invalid input")
        tool = ConcreteTool("test_tool", raise_exception=error)
        
        result = tool.execute(param1="value1")
        
        assert result['status'] == 'error'
        assert 'error' in result
        assert tool.execution_count == 1
    
    def test_execute_with_runtime_exception(self):
        """Test tool execution with runtime exception."""
        error = RuntimeError("Runtime error")
        tool = ConcreteTool("test_tool", raise_exception=error)
        
        result = tool.execute()
        
        assert result['status'] == 'error'
        assert 'error' in result
    
    def test_tool_info_creation(self):
        """Test tool-specific info creation."""
        tool = ConcreteTool("test_tool")
        
        info = tool._create_tool_info(execution_mode="test", custom="value")
        
        assert info['handler_name'] == "test_tool"
        assert info['handler_type'] == "ConcreteTool"
        assert info['execution_mode'] == "test"
        assert info['custom'] == "value"


class ConcreteResource(BaseResourceHandler):
    """Concrete implementation of BaseResourceHandler for testing."""
    
    def __init__(self, resource_name: str, version: str = "1.0.0", content: str = None, raise_exception: Exception = None):
        super().__init__(resource_name, version)
        self.content = content or "Test resource content"
        self.raise_exception = raise_exception
        self.access_count = 0
    
    def _get_resource_content(self, **kwargs) -> str:
        """Test implementation of resource content generation."""
        self.access_count += 1
        if self.raise_exception:
            raise self.raise_exception
        return self.content


class TestBaseResourceHandler:
    """Test BaseResourceHandler abstract base class."""
    
    def test_initialization(self):
        """Test resource handler initialization."""
        resource = ConcreteResource("test_resource", "4.0.0")
        
        assert resource.handler_name == "test_resource"
        assert resource.version == "4.0.0"
    
    def test_get_content_success(self):
        """Test successful resource content retrieval."""
        content = "# Test Resource\n\nThis is test content."
        resource = ConcreteResource("test_resource", content=content)
        
        result = resource.get_content(param1="value1")
        
        assert result == content
        assert resource.access_count == 1
    
    def test_get_content_with_exception(self):
        """Test resource content retrieval with exception."""
        error = StorageError("Storage failed")
        resource = ConcreteResource("test_resource", raise_exception=error)
        
        result = resource.get_content()
        
        # Should return formatted error content (uses resource error handler)
        assert "Error Retrieving" in result
        assert "Storage failed" in result
        assert resource.access_count == 1
    
    def test_format_error_content(self):
        """Test error content formatting."""
        resource = ConcreteResource("test_resource")
        
        error_content = resource._format_error_content(
            "Test error message",
            resource_name="test://resource",
            additional_info="Extra details"
        )
        
        assert "Error Retrieving" in error_content
        assert "Test error message" in error_content
        assert "test_resource" in error_content  # Uses handler name, not passed resource_name
        assert "Timestamp:" in error_content


class ConcretePrompt(BasePromptHandler):
    """Concrete implementation of BasePromptHandler for testing."""
    
    def __init__(self, prompt_name: str, version: str = "1.0.0", prompt_data: Dict[str, Any] = None, raise_exception: Exception = None):
        super().__init__(prompt_name, version)
        self.prompt_data = prompt_data or {"template": "Test template", "parameters": []}
        self.raise_exception = raise_exception
        self.generation_count = 0
    
    def _generate_prompt(self, **kwargs) -> Dict[str, Any]:
        """Test implementation of prompt generation."""
        self.generation_count += 1
        if self.raise_exception:
            raise self.raise_exception
        return self.prompt_data


class TestBasePromptHandler:
    """Test BasePromptHandler abstract base class."""
    
    def test_initialization(self):
        """Test prompt handler initialization."""
        prompt = ConcretePrompt("test_prompt", "5.0.0")
        
        assert prompt.handler_name == "test_prompt"
        assert prompt.version == "5.0.0"
    
    def test_generate_success(self):
        """Test successful prompt generation."""
        prompt_data = {
            "template": "Analyze {band_name}",
            "parameters": ["band_name"],
            "description": "Band analysis prompt"
        }
        prompt = ConcretePrompt("test_prompt", prompt_data=prompt_data)
        
        result = prompt.generate(band_name="Test Band")
        
        # Successful prompt generation returns the prompt_data directly
        assert result['template'] == "Analyze {band_name}"
        assert result['parameters'] == ["band_name"]
        assert prompt.generation_count == 1
    
    def test_generate_with_exception(self):
        """Test prompt generation with exception."""
        error = ValidationError("Invalid prompt parameters")
        prompt = ConcretePrompt("test_prompt", raise_exception=error)
        
        result = prompt.generate(invalid_param="value")
        
        # Prompt errors return a template structure with error info
        assert result['name'] == 'test_prompt'
        assert "Invalid prompt parameters" in result['description']
        assert 'messages' in result
        assert prompt.generation_count == 1
    
    def test_generate_with_runtime_exception(self):
        """Test prompt generation with runtime exception."""
        error = RuntimeError("Template error")
        prompt = ConcretePrompt("test_prompt", raise_exception=error)
        
        result = prompt.generate()
        
        # Prompt errors return a template structure with error info
        assert result['name'] == 'test_prompt'
        assert "Template error" in result['description']
        assert 'messages' in result


class TestUtilityFunctions:
    """Test utility functions in base_handlers module."""
    
    def test_create_success_response_basic(self):
        """Test basic success response creation."""
        result = create_success_response({"result": "success"})
        
        assert result['status'] == 'success'
        assert result['result'] == 'success'
        assert 'timestamp' in result
    
    def test_create_success_response_with_handler_info(self):
        """Test success response with handler info."""
        handler_info = {"handler": "test", "version": "1.0"}
        result = create_success_response({"data": "test"}, handler_info)
        
        assert result['status'] == 'success'
        assert result['data'] == 'test'
        assert result['handler_info'] == handler_info
    
    def test_create_error_response_basic(self):
        """Test basic error response creation."""
        result = create_error_response("Something went wrong")
        
        assert result['status'] == 'error'
        assert result['error'] == 'Something went wrong'
        assert 'timestamp' in result
    
    def test_create_error_response_with_handler_info(self):
        """Test error response with handler info."""
        handler_info = {"handler": "test", "error_code": "E001"}
        result = create_error_response("Test error", handler_info)
        
        assert result['status'] == 'error'
        assert result['error'] == 'Test error'
        assert result['handler_info'] == handler_info
    
    def test_validate_pagination_params_valid(self):
        """Test pagination parameter validation with valid values."""
        result = validate_pagination_params(1, 20, 100)
        
        assert result is None  # No error
    
    def test_validate_pagination_params_invalid_page(self):
        """Test pagination validation with invalid page number."""
        result = validate_pagination_params(0, 20, 100)
        
        assert result is not None
        assert "Page number" in result
    
    def test_validate_pagination_params_invalid_page_size(self):
        """Test pagination validation with invalid page size."""
        result = validate_pagination_params(1, 0, 100)
        
        assert result is not None
        assert "Page size" in result
    
    def test_validate_pagination_params_exceeds_max(self):
        """Test pagination validation with page size exceeding maximum."""
        result = validate_pagination_params(1, 150, 100)
        
        assert result is not None
        assert "Page size must be between 1 and" in result
    
    def test_validate_sort_params_valid(self):
        """Test sort parameter validation with valid values."""
        allowed_fields = ["name", "date", "rating"]
        result = validate_sort_params("name", "asc", allowed_fields)
        
        assert result is None  # No error
    
    def test_validate_sort_params_invalid_field(self):
        """Test sort validation with invalid field."""
        allowed_fields = ["name", "date", "rating"]
        result = validate_sort_params("invalid_field", "asc", allowed_fields)
        
        assert result is not None
        assert "sort_by must be one of:" in result
    
    def test_validate_sort_params_invalid_order(self):
        """Test sort validation with invalid order."""
        allowed_fields = ["name", "date", "rating"]
        result = validate_sort_params("name", "invalid", allowed_fields)
        
        assert result is not None
        assert "sort_order must be 'asc' or 'desc'" in result


class TestHandlerIntegration:
    """Test integration between different handler types."""
    
    def test_error_consistency_across_handlers(self):
        """Test that error handling is consistent across handler types."""
        error = ValidationError("Test validation error")
        
        tool = ConcreteTool("test_tool", raise_exception=error)
        resource = ConcreteResource("test_resource", raise_exception=error)
        prompt = ConcretePrompt("test_prompt", raise_exception=error)
        
        tool_result = tool.execute()
        resource_result = resource.get_content()
        prompt_result = prompt.generate()
        
        # All should handle errors gracefully
        assert tool_result['status'] == 'error'
        assert "Error Retrieving" in resource_result  # Resources return formatted markdown
        assert prompt_result['name'] == 'test_prompt'  # Prompts return template structure
    
    def test_timestamp_consistency(self):
        """Test that timestamps are consistent across responses."""
        tool = ConcreteTool("test_tool")
        
        # Execute multiple times rapidly
        result1 = tool.execute()
        result2 = tool.execute()
        
        assert 'timestamp' in result1
        assert 'timestamp' in result2
        # Timestamps should be different (execution takes some time)
        assert result1['timestamp'] != result2['timestamp']
    
    def test_handler_info_structure(self):
        """Test that handler info has consistent structure."""
        tool = ConcreteTool("test_tool", "1.0.0")
        resource = ConcreteResource("test_resource", "2.0.0")
        prompt = ConcretePrompt("test_prompt", "3.0.0")
        
        tool_result = tool.execute()
        resource_result = resource.get_content()
        prompt_result = prompt.generate()
        
        # Tool results should have handler_info
        assert 'handler_info' in tool_result
        assert tool_result['handler_info']['handler_name'] == "test_tool"
        assert tool_result['handler_info']['version'] == "1.0.0"
        
        # Prompt results are just the prompt data for successful generation
        assert prompt_result['template'] == "Test template"  # Returns prompt_data directly 
