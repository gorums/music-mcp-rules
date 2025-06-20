#!/usr/bin/env python3
"""
Test helper utilities for the Music Collection MCP Server.

This module provides common utilities, mock factories, and helper functions
for testing various components of the server.
"""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from unittest.mock import Mock, MagicMock
import pytest

from src.models.band import BandMetadata, Album, AlbumType
from src.models.collection import CollectionIndex, BandIndexEntry


class MockFileSystem:
    """Mock file system for testing file operations."""
    
    def __init__(self, base_path: Optional[Path] = None):
        """Initialize mock file system."""
        self.base_path = base_path or Path(tempfile.mkdtemp())
        self.files: Dict[str, Any] = {}
        
    def create_band_structure(self, band_name: str, albums: List[Dict[str, Any]]) -> Path:
        """Create a mock band folder structure."""
        band_path = self.base_path / band_name
        band_path.mkdir(parents=True, exist_ok=True)
        
        for album_data in albums:
            album_name = album_data.get('folder_name', album_data['name'])
            album_path = band_path / album_name
            album_path.mkdir(exist_ok=True)
            
            # Create mock audio files
            track_count = album_data.get('track_count', 10)
            for i in range(1, track_count + 1):
                track_file = album_path / f"{i:02d} - Track {i}.mp3"
                track_file.touch()
                
        return band_path
    
    def create_json_file(self, file_path: Path, data: Dict[str, Any]) -> Path:
        """Create a JSON file with the given data."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return file_path
    
    def cleanup(self):
        """Clean up the mock file system."""
        import shutil
        if self.base_path.exists():
            shutil.rmtree(self.base_path)


class MockDataFactory:
    """Factory for creating mock test data."""
    
    @staticmethod
    def create_band_metadata(
        band_name: str = "Test Band",
        formed: str = "1970",
        albums: Optional[List[Album]] = None,
        **kwargs
    ) -> BandMetadata:
        """Create mock band metadata."""
        if albums is None:
            albums = [MockDataFactory.create_album()]
            
        return BandMetadata(
            band_name=band_name,
            formed=formed,
            albums=albums,
            genres=kwargs.get('genres', ["Rock"]),
            origin=kwargs.get('origin', "Test City"),
            members=kwargs.get('members', ["Member 1", "Member 2"]),
            description=kwargs.get('description', f"Test description for {band_name}"),
            **{k: v for k, v in kwargs.items() if k not in ['genres', 'origin', 'members', 'description']}
        )
    
    @staticmethod
    def create_album(
        album_name: str = "Test Album",
        year: str = "1975",
        album_type: AlbumType = AlbumType.ALBUM,
        missing: bool = False,
        tracks_count: int = 10,
        **kwargs
    ) -> Album:
        """Create mock album."""
        return Album(
            album_name=album_name,
            year=year,
            type=album_type,
            missing=missing,
            tracks_count=tracks_count,
            **kwargs
        )
    
    @staticmethod
    def create_collection_index(
        bands: Optional[List[BandIndexEntry]] = None,
        **kwargs
    ) -> CollectionIndex:
        """Create mock collection index."""
        if bands is None:
            bands = [MockDataFactory.create_band_index_entry()]
            
        return CollectionIndex(
            bands=bands,
            last_scan=kwargs.get('last_scan', "2025-01-01T12:00:00Z"),
            **{k: v for k, v in kwargs.items() if k not in ['last_scan']}
        )
    
    @staticmethod
    def create_band_index_entry(
        band_name: str = "Test Band",
        albums_count: int = 5,
        has_metadata: bool = True,
        **kwargs
    ) -> BandIndexEntry:
        """Create mock band index entry."""
        return BandIndexEntry(
            name=band_name,
            albums_count=albums_count,
            local_albums_count=kwargs.get('local_albums_count', albums_count),
            folder_path=kwargs.get('folder_path', band_name),
            has_metadata=has_metadata,
            **{k: v for k, v in kwargs.items() if k not in ['local_albums_count', 'folder_path']}
        )


class MockConfigFactory:
    """Factory for creating mock configurations."""
    
    @staticmethod
    def create_config(
        music_root_path: Optional[str] = None,
        cache_duration_days: int = 30,
        **kwargs
    ) -> Mock:
        """Create mock configuration object."""
        config = Mock()
        config.music_root_path = music_root_path or str(Path(tempfile.mkdtemp()))
        config.cache_duration_days = cache_duration_days
        
        # Add any additional config properties
        for key, value in kwargs.items():
            setattr(config, key, value)
            
        return config


class TestResponseValidator:
    """Utility for validating test responses."""
    
    @staticmethod
    def validate_success_response(response: Dict[str, Any], expected_keys: List[str] = None) -> bool:
        """Validate that a response indicates success and has expected structure."""
        if expected_keys is None:
            expected_keys = []
            
        # Check status
        assert response.get('status') == 'success', f"Expected success status, got: {response.get('status')}"
        
        # Check for error field not present
        assert 'error' not in response or response['error'] is None, f"Success response should not have error: {response.get('error')}"
        
        # Check expected keys
        for key in expected_keys:
            assert key in response, f"Expected key '{key}' not found in response"
            
        return True
    
    @staticmethod
    def validate_error_response(response: Dict[str, Any], expected_error_type: str = None) -> bool:
        """Validate that a response indicates error and has expected structure."""
        # Check status
        assert response.get('status') == 'error', f"Expected error status, got: {response.get('status')}"
        
        # Check for error message
        assert 'error' in response and response['error'], "Error response must have error message"
        
        # Check error type if specified
        if expected_error_type:
            assert response.get('error_type') == expected_error_type, \
                f"Expected error type '{expected_error_type}', got: {response.get('error_type')}"
                
        return True


class MockMCPServer:
    """Mock MCP server for testing."""
    
    def __init__(self):
        """Initialize mock MCP server."""
        self.tools = {}
        self.resources = {}
        self.prompts = {}
        
    def register_tool(self, name: str, handler):
        """Register a tool handler."""
        self.tools[name] = handler
        
    def register_resource(self, name: str, handler):
        """Register a resource handler."""
        self.resources[name] = handler
        
    def register_prompt(self, name: str, handler):
        """Register a prompt handler."""
        self.prompts[name] = handler
        
    def get_tool(self, name: str):
        """Get a registered tool."""
        return self.tools.get(name)
        
    def get_resource(self, name: str):
        """Get a registered resource."""
        return self.resources.get(name)
        
    def get_prompt(self, name: str):
        """Get a registered prompt."""
        return self.prompts.get(name)


# Common test fixtures and utilities
def create_temp_music_collection(bands_data: List[Dict[str, Any]]) -> Path:
    """Create a temporary music collection for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    mock_fs = MockFileSystem(temp_dir)
    
    for band_data in bands_data:
        band_name = band_data['name']
        albums = band_data.get('albums', [])
        mock_fs.create_band_structure(band_name, albums)
        
    return temp_dir


def assert_valid_json_structure(data: Any, expected_schema: Dict[str, type]) -> bool:
    """Assert that data matches expected JSON schema structure."""
    if not isinstance(data, dict):
        raise AssertionError(f"Expected dict, got {type(data)}")
        
    for key, expected_type in expected_schema.items():
        if key not in data:
            raise AssertionError(f"Missing required key: {key}")
            
        if not isinstance(data[key], expected_type):
            raise AssertionError(f"Key '{key}' should be {expected_type}, got {type(data[key])}")
            
    return True


def measure_execution_time(func, *args, **kwargs):
    """Measure execution time of a function."""
    import time
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    execution_time = end_time - start_time
    return result, execution_time 
