"""
Shared pytest fixtures and configuration for the Music Collection MCP Server tests.

This file provides common fixtures and setup that can be used across all test modules.
"""

import os
import sys
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

# Add src directory to path for imports from all tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.models.band import Album, AlbumType, BandMetadata


@pytest.fixture
def temp_music_dir(tmp_path):
    """Create temporary music directory for testing."""
    music_dir = tmp_path / "music"
    music_dir.mkdir()
    return music_dir


@pytest.fixture
def sample_band_metadata():
    """Create sample band metadata for testing."""
    return BandMetadata(
        band_name="Test Band",
        formed="1970",
        genres=["Rock"],
        albums=[
            Album(
                album_name="Test Album",
                year="1975", 
                type=AlbumType.ALBUM
            )
        ]
    )


@pytest.fixture
def sample_album():
    """Create a sample album for testing."""
    return Album(
        album_name="Sample Album",
        year="1980",
        type=AlbumType.ALBUM
    )


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch, tmp_path):
    """Set up test environment variables."""
    test_music_path = tmp_path / "test_music"
    test_music_path.mkdir()
    monkeypatch.setenv("MUSIC_ROOT_PATH", str(test_music_path))
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")


@pytest.fixture
def mock_music_structure(tmp_path):
    """Create a mock music directory structure."""
    music_root = tmp_path / "music"
    music_root.mkdir()
    
    # Create band structure
    band_dir = music_root / "Pink Floyd"
    band_dir.mkdir()
    
    album_dir = band_dir / "1973 - The Dark Side of the Moon"
    album_dir.mkdir()
    
    # Create mock audio files
    (album_dir / "01 - Speak to Me.mp3").touch()
    (album_dir / "02 - Breathe.mp3").touch()
    
    return music_root


def create_test_band_structure(music_dir: Path, band_name: str):
    """
    Helper function to create a test band directory structure.
    
    Args:
        music_dir (Path): Root music directory
        band_name (str): Name of the band to create
    """
    band_dir = music_dir / band_name
    band_dir.mkdir(exist_ok=True)
    
    # Create sample album
    album_dir = band_dir / "1970 - Test Album"
    album_dir.mkdir(exist_ok=True)
    
    # Create sample tracks
    (album_dir / "01 - Track One.mp3").touch()
    (album_dir / "02 - Track Two.mp3").touch()
    
    return band_dir


@pytest.fixture
def test_collection_structure(tmp_path):
    """Create a complete test music collection structure."""
    music_root = tmp_path / "test_music"
    music_root.mkdir()
    
    # Create multiple bands with different structures
    bands = [
        ("The Beatles", ["1967 - Sgt. Pepper's", "1969 - Abbey Road"]),
        ("Pink Floyd", ["1973 - The Dark Side of the Moon", "1979 - The Wall"]),
        ("Led Zeppelin", ["1971 - Led Zeppelin IV", "1975 - Physical Graffiti"])
    ]
    
    for band_name, albums in bands:
        band_dir = music_root / band_name
        band_dir.mkdir()
        
        for album_name in albums:
            album_dir = band_dir / album_name
            album_dir.mkdir()
            
            # Create sample tracks
            for i in range(1, 4):
                track_file = album_dir / f"{i:02d} - Track {i}.mp3"
                track_file.touch()
    
    return music_root


@pytest.fixture
def no_music_environment(monkeypatch):
    """Set up environment with no music directory for testing error conditions."""
    monkeypatch.setenv("MUSIC_ROOT_PATH", "/nonexistent/path")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG") 