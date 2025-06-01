# Music Collection MCP Server - Code Style Guide

## Overview

This document defines the coding standards and style guidelines for the Music Collection MCP Server project. Following these guidelines ensures code consistency, readability, and maintainability.

## Python Standards

### Base Standards
- **PEP 8 Compliance**: Follow PEP 8 with project-specific modifications
- **Line Length**: 100 characters maximum
- **Indentation**: 4 spaces (no tabs)
- **Type Hints**: Required for all function signatures and class attributes

### Code Formatting

#### Black Configuration
```toml
# pyproject.toml
[tool.black]
line-length = 100
target-version = ['py38']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''
```

#### Import Organization
```python
# Standard library imports
import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

# Third-party imports
from pydantic import BaseModel, Field
from fastmcp import FastMCP

# Local imports
from .models.band import BandMetadata
from .models.collection import CollectionIndex
from ..config import Config
```

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| **Modules** | `snake_case` | `music_scanner.py` |
| **Classes** | `PascalCase` | `BandMetadata` |
| **Functions** | `snake_case` | `scan_music_folders()` |
| **Variables** | `snake_case` | `band_name` |
| **Constants** | `UPPER_SNAKE_CASE` | `DEFAULT_CACHE_DAYS` |
| **Private** | `_leading_underscore` | `_internal_method()` |

### Documentation Standards

#### Docstring Format (Google Style)
```python
def save_band_metadata(
    band_name: str, 
    metadata: BandMetadata,
    preserve_analyze: bool = True
) -> SaveResult:
    """
    Save band metadata to the file system with validation.
    
    Args:
        band_name: Name of the band to save metadata for
        metadata: Complete band metadata object
        preserve_analyze: Whether to preserve existing analysis data
        
    Returns:
        SaveResult: Operation result with success status and details
        
    Raises:
        ValidationError: If metadata validation fails
        StorageError: If file system operation fails
        
    Example:
        >>> metadata = BandMetadata(band_name="Pink Floyd", formed="1965")
        >>> result = save_band_metadata("Pink Floyd", metadata)
        >>> assert result.success is True
    """
```

#### Class Documentation
```python
class BandMetadata(BaseModel):
    """
    Complete metadata for a musical band including albums and analysis.
    
    This model represents all stored information about a band, including
    basic information, discography, and optional analysis data. All data
    is validated using Pydantic for type safety and data integrity.
    
    Attributes:
        band_name: Official name of the band
        formed: Year the band was formed (YYYY format)
        genres: List of musical genres the band performs
        albums: Complete list of band's albums
        analyze: Optional analysis data including ratings and reviews
        
    Example:
        >>> band = BandMetadata(
        ...     band_name="Pink Floyd",
        ...     formed="1965",
        ...     genres=["Progressive Rock"]
        ... )
    """
```

### Error Handling

#### Exception Hierarchy
```python
class MusicMCPError(Exception):
    """Base exception for all Music MCP Server errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class ValidationError(MusicMCPError):
    """Data validation errors."""
    pass

class StorageError(MusicMCPError):
    """File system and storage errors."""
    pass

class ScanError(MusicMCPError):
    """Music collection scanning errors."""
    pass
```

#### Error Handling Pattern
```python
def risky_operation(data: Dict[str, Any]) -> Result:
    """Perform operation with comprehensive error handling."""
    try:
        # Validate input
        validated_data = validate_input(data)
        
        # Perform operation
        result = perform_operation(validated_data)
        
        return Result(success=True, data=result)
        
    except ValidationError as e:
        logger.warning(f"Validation failed: {e}")
        return Result(success=False, error=str(e))
        
    except StorageError as e:
        logger.error(f"Storage operation failed: {e}")
        raise  # Re-raise storage errors
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise MusicMCPError(f"Operation failed: {str(e)}")
```

### Type Hints

#### Function Signatures
```python
from typing import List, Dict, Optional, Union, Tuple, Any

def process_band_data(
    band_name: str,
    albums: List[Dict[str, Any]],
    metadata: Optional[BandMetadata] = None
) -> Tuple[bool, Optional[str]]:
    """Process band data with full type annotations."""
    pass

# Generic types for reusable functions
from typing import TypeVar, Generic

T = TypeVar('T')

def cache_operation(operation: Callable[[], T]) -> T:
    """Generic cache wrapper with type preservation."""
    pass
```

#### Complex Types
```python
from typing import Protocol, Union, Literal

# Protocol for type-safe interfaces
class Scannable(Protocol):
    def scan(self) -> ScanResult:
        """Scan implementation required."""
        ...

# Union types for multiple possibilities
ScanMode = Union[Literal["full"], Literal["incremental"]]

# Type aliases for clarity
BandName = str
AlbumCount = int
CollectionStats = Dict[str, Union[int, float]]
```

### Code Organization

#### Module Structure
```python
"""
Module for music collection scanning operations.

This module provides comprehensive scanning functionality including:
- File system traversal for band and album discovery
- Incremental scanning for performance optimization
- Error recovery and validation
- Collection index management

Classes:
    MusicScanner: Main scanning class
    ScanResult: Scan operation results
    
Functions:
    scan_music_folders: High-level scanning interface
    
Constants:
    SUPPORTED_FORMATS: Supported music file formats
"""

# Module-level constants
SUPPORTED_FORMATS = ['.mp3', '.flac', '.wav', '.aac', '.m4a']
DEFAULT_SCAN_DEPTH = 3

# Module-level functions
def scan_music_folders(path: str) -> ScanResult:
    """Public API for music folder scanning."""
    pass

# Classes
class MusicScanner:
    """Main music collection scanner."""
    pass
```

#### File Layout
```
src/
├── __init__.py                 # Package initialization
├── config.py                  # Configuration management
├── music_mcp_server.py        # Main server implementation
├── models/                    # Data models
│   ├── __init__.py           # Model exports
│   ├── band.py               # Band-related models
│   ├── collection.py         # Collection models
│   └── migration.py          # Data migration utilities
├── tools/                     # Core business logic
│   ├── __init__.py           # Tool exports
│   ├── scanner.py            # Collection scanning
│   ├── storage.py            # Data persistence
│   ├── cache.py              # Caching layer
│   └── metadata.py           # Metadata operations
├── resources/                 # MCP resources
│   ├── __init__.py
│   ├── band_info.py          # Band information resource
│   └── collection_summary.py # Collection summary resource
└── prompts/                   # MCP prompts
    ├── __init__.py
    ├── fetch_band_info.py     # Band info prompt
    ├── analyze_band.py        # Band analysis prompt
    ├── compare_bands.py       # Band comparison prompt
    └── collection_insights.py  # Collection insights prompt
```

### Performance Guidelines

#### Efficient Data Structures
```python
# Use appropriate data structures
from collections import defaultdict, deque
from typing import Set, Dict

# For unique collections
band_names: Set[str] = set()

# For counting operations
album_counts: defaultdict[str, int] = defaultdict(int)

# For FIFO operations
scan_queue: deque[str] = deque()
```

#### Memory Management
```python
def process_large_collection(bands: List[str]) -> None:
    """Process large collections efficiently."""
    # Process in chunks to manage memory
    chunk_size = 100
    
    for i in range(0, len(bands), chunk_size):
        chunk = bands[i:i + chunk_size]
        process_band_chunk(chunk)
        
        # Explicit cleanup for large objects
        del chunk
```

#### Async Operations
```python
import asyncio
from typing import List

async def scan_multiple_bands(band_paths: List[str]) -> List[ScanResult]:
    """Scan multiple bands concurrently."""
    tasks = [scan_single_band(path) for path in band_paths]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle exceptions in results
    return [r for r in results if not isinstance(r, Exception)]
```

### Testing Standards

#### Test Structure
```python
import pytest
from unittest.mock import Mock, patch, MagicMock

class TestBandMetadata:
    """Test suite for BandMetadata model."""
    
    def test_valid_creation(self):
        """Test creating valid band metadata."""
        # Arrange
        data = {"band_name": "Test Band", "formed": "1970"}
        
        # Act
        band = BandMetadata(**data)
        
        # Assert
        assert band.band_name == "Test Band"
        assert band.formed == "1970"
    
    @pytest.mark.parametrize("invalid_year", ["70", "nineteen seventy", ""])
    def test_invalid_year_validation(self, invalid_year: str):
        """Test that invalid years raise ValidationError."""
        with pytest.raises(ValidationError):
            BandMetadata(band_name="Test", formed=invalid_year)
    
    @patch('src.tools.storage.Path.exists')
    def test_metadata_saving_with_mocks(self, mock_exists):
        """Test metadata saving with file system mocks."""
        # Arrange
        mock_exists.return_value = True
        
        # Act & Assert
        # Test implementation
```

#### Test Naming
- **Test files**: `test_module_name.py`
- **Test classes**: `TestClassName`
- **Test methods**: `test_method_description`
- **Fixtures**: `descriptive_fixture_name`

### Configuration and Environment

#### Environment Variables
```python
from pydantic import BaseSettings, Field

class Config(BaseSettings):
    """Application configuration from environment variables."""
    
    # Required settings
    music_root_path: str = Field(..., env="MUSIC_ROOT_PATH")
    
    # Optional settings with defaults
    cache_duration_days: int = Field(30, env="CACHE_DURATION_DAYS")
    max_scan_threads: int = Field(4, env="MAX_SCAN_THREADS")
    
    # Boolean settings
    debug_mode: bool = Field(False, env="DEBUG_MODE")
    enable_performance_monitoring: bool = Field(False, env="ENABLE_PERF_MON")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

### Logging Standards

#### Logging Configuration
```python
import logging
from typing import Any

# Module-level logger
logger = logging.getLogger(__name__)

def setup_logging(debug: bool = False) -> None:
    """Configure application logging."""
    level = logging.DEBUG if debug else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('music_mcp.log')
        ]
    )

# Usage in functions
def scan_band_folder(path: str) -> ScanResult:
    """Scan individual band folder."""
    logger.info(f"Scanning band folder: {path}")
    
    try:
        result = perform_scan(path)
        logger.debug(f"Scan completed: {result.albums_found} albums found")
        return result
        
    except Exception as e:
        logger.error(f"Scan failed for {path}: {e}")
        raise
```

### Security Guidelines

#### Input Validation
```python
from pathlib import Path

def validate_music_path(path: str) -> Path:
    """Validate and sanitize music collection path."""
    # Convert to Path object
    music_path = Path(path).resolve()
    
    # Security checks
    if not music_path.exists():
        raise ValidationError(f"Path does not exist: {path}")
    
    if not music_path.is_dir():
        raise ValidationError(f"Path is not a directory: {path}")
    
    # Prevent directory traversal
    if '..' in str(music_path):
        raise ValidationError(f"Invalid path contains '..': {path}")
    
    return music_path
```

## Tools and Automation

### Pre-commit Configuration
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
        args: [--line-length=100]
  
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: [--profile=black]
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=100, --extend-ignore=E203,W503]
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.0.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### Development Scripts
```bash
#!/bin/bash
# scripts/format.sh - Code formatting script

echo "Running code formatters..."

# Black formatting
black src/ tests/ --line-length=100

# Import sorting
isort src/ tests/ --profile=black

# Linting
flake8 src/ tests/ --max-line-length=100

# Type checking
mypy src/

echo "Code formatting complete!"
```

## Summary

This style guide ensures:
- **Consistency**: Uniform code style across the project
- **Readability**: Clear, well-documented code
- **Maintainability**: Easy to understand and modify
- **Quality**: High code quality through validation and testing
- **Automation**: Automated formatting and validation

Follow these guidelines for all contributions to maintain code quality and project consistency. 