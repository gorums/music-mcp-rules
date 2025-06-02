# Music Collection MCP Server - Code Style Guide with Album Type Classification

## Overview

This document defines the coding standards and style guidelines for the Music Collection MCP Server project. Following these guidelines ensures code consistency, readability, and maintainability, especially when working with the enhanced album type classification and folder structure analysis features.

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
from typing import List, Dict, Optional, Any, Union
from enum import Enum

# Third-party imports
from pydantic import BaseModel, Field, validator
from fastmcp import FastMCP

# Local imports
from .models.band import BandMetadata
from .models.album import Album, AlbumType
from .models.structure import StructureType, FolderStructure
from .models.collection import CollectionIndex
from ..config import Config
```

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| **Modules** | `snake_case` | `music_scanner.py`, `album_classifier.py` |
| **Classes** | `PascalCase` | `BandMetadata`, `AlbumTypeDetector` |
| **Functions** | `snake_case` | `scan_music_folders()`, `detect_album_type()` |
| **Variables** | `snake_case` | `band_name`, `album_type`, `structure_score` |
| **Constants** | `UPPER_SNAKE_CASE` | `DEFAULT_CACHE_DAYS`, `ALBUM_TYPE_KEYWORDS` |
| **Private** | `_leading_underscore` | `_internal_method()`, `_parse_folder_name()` |
| **Enums** | `PascalCase` | `AlbumType`, `StructureType` |
| **Enum Values** | `UPPER_CASE` | `AlbumType.ALBUM`, `StructureType.ENHANCED` |

### Album Type and Structure Specific Conventions

#### Enum Definitions
```python
class AlbumType(str, Enum):
    """
    Album type enumeration following string enum pattern.
    
    Values should be human-readable and match expected metadata format.
    """
    ALBUM = "Album"
    COMPILATION = "Compilation"
    EP = "EP"
    LIVE = "Live"
    SINGLE = "Single"
    DEMO = "Demo"
    INSTRUMENTAL = "Instrumental"
    SPLIT = "Split"

class StructureType(str, Enum):
    """Folder structure type enumeration."""
    DEFAULT = "default"
    ENHANCED = "enhanced"
    MIXED = "mixed"
    LEGACY = "legacy"
    UNKNOWN = "unknown"
```

#### Type Detection Function Naming
```python
# Good examples
def detect_album_type_from_folder_name(folder_name: str) -> AlbumType:
def analyze_folder_structure_compliance(band_path: Path) -> FolderStructure:
def calculate_structure_compliance_score(albums: List[Album]) -> int:

# Avoid
def get_type(name: str) -> str:  # Too generic
def check_folder(path: Path) -> bool:  # Unclear return type
def score_albums(albums: List) -> int:  # Missing type hints
```

### Documentation Standards

#### Docstring Format (Google Style) with Type Examples

```python
def detect_album_type_from_folder_structure(
    folder_path: Path, 
    album_name: str,
    structure_type: StructureType = StructureType.DEFAULT
) -> AlbumType:
    """
    Detect album type from folder structure and naming patterns.
    
    Uses multiple detection strategies including keyword matching, folder structure
    analysis, and parent directory context to classify album types accurately.
    
    Args:
        folder_path: Path to the album folder
        album_name: Name of the album for keyword analysis
        structure_type: Known structure type for enhanced detection
        
    Returns:
        AlbumType: Detected album type, defaults to AlbumType.ALBUM if uncertain
        
    Raises:
        ValueError: If folder_path does not exist
        TypeError: If album_name is not a string
        
    Example:
        >>> path = Path("/music/Pink Floyd/Live/1972 - Live at Pompeii")
        >>> album_type = detect_album_type_from_folder_structure(path, "Live at Pompeii")
        >>> assert album_type == AlbumType.LIVE
        
    Note:
        Detection confidence varies by structure type. Enhanced structures
        with type folders provide higher accuracy than flat structures.
    """
```

#### Class Documentation with Type Features
```python
class AlbumTypeDetector:
    """
    Utility class for detecting album types from various sources.
    
    Provides multiple detection strategies for classifying albums into
    8 supported types: Album, Compilation, EP, Live, Single, Demo,
    Instrumental, and Split releases.
    
    Attributes:
        type_keywords: Mapping of album types to detection keywords
        confidence_threshold: Minimum confidence required for type assignment
        default_type: Fallback type when detection is uncertain
        
    Example:
        >>> detector = AlbumTypeDetector(confidence_threshold=0.8)
        >>> album_type = detector.detect_from_folder_name("1985 - Live at Wembley")
        >>> assert album_type == AlbumType.LIVE
    """
    
    # Type detection keywords organized by album type
    TYPE_KEYWORDS: Dict[AlbumType, List[str]] = {
        AlbumType.LIVE: [
            'live', 'concert', 'unplugged', 'acoustic', 'in concert',
            'live at', 'live in', 'live from', 'concert at'
        ],
        AlbumType.COMPILATION: [
            'greatest hits', 'best of', 'collection', 'anthology', 
            'compilation', 'hits', 'complete', 'essential'
        ],
        AlbumType.EP: ['ep', 'e.p.'],
        AlbumType.SINGLE: ['single'],
        AlbumType.DEMO: [
            'demo', 'demos', 'early recordings', 'unreleased',
            'rough mixes', 'rehearsal', 'pre-production'
        ],
        AlbumType.INSTRUMENTAL: ['instrumental', 'instrumentals'],
        AlbumType.SPLIT: ['split', 'vs.', 'vs', 'versus', 'with']
    }
```

### Error Handling with Type Safety

#### Exception Hierarchy for Type Features
```python
class MusicMCPError(Exception):
    """Base exception for all Music MCP Server errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class AlbumTypeError(MusicMCPError):
    """Errors related to album type detection and classification."""
    pass

class StructureAnalysisError(MusicMCPError):
    """Errors during folder structure analysis."""
    pass

class ComplianceValidationError(MusicMCPError):
    """Errors during compliance scoring and validation."""
    pass
```

#### Error Handling Pattern with Types
```python
def analyze_band_folder_structure(band_path: Path) -> FolderStructure:
    """Analyze band folder structure with comprehensive error handling."""
    try:
        # Validate input
        if not band_path.exists():
            raise StructureAnalysisError(f"Band folder not found: {band_path}")
        
        if not band_path.is_dir():
            raise StructureAnalysisError(f"Path is not a directory: {band_path}")
        
        # Perform structure analysis
        detector = BandStructureDetector(band_path)
        structure = detector.analyze_structure()
        
        return structure
        
    except PermissionError as e:
        logger.warning(f"Permission denied accessing {band_path}: {e}")
        raise StructureAnalysisError(f"Cannot access band folder: {band_path}")
        
    except FileNotFoundError as e:
        logger.error(f"Band folder disappeared during analysis: {band_path}")
        raise StructureAnalysisError(f"Band folder not found: {band_path}")
        
    except Exception as e:
        logger.error(f"Unexpected error analyzing structure for {band_path}: {e}")
        raise StructureAnalysisError(f"Structure analysis failed: {str(e)}")
```

### Type Hints for Album Classification Features

#### Function Signatures with Enhanced Types
```python
from typing import List, Dict, Optional, Union, Tuple, Any, Set
from pathlib import Path

def scan_albums_with_type_detection(
    band_path: Path,
    force_rescan: bool = False,
    detect_types: bool = True,
    analyze_structure: bool = True
) -> Tuple[List[Album], FolderStructure]:
    """Scan albums with optional type detection and structure analysis."""
    pass

def validate_album_compliance(
    album: Album,
    structure_type: StructureType,
    band_path: Path
) -> Dict[str, Union[int, str, List[str]]]:
    """Validate album folder compliance against structure requirements."""
    pass

# Generic types for reusable functions
from typing import TypeVar, Generic, Protocol

T = TypeVar('T')
AlbumTypeT = TypeVar('AlbumTypeT', bound=AlbumType)

class TypeDetectable(Protocol):
    """Protocol for objects that support type detection."""
    def detect_type(self) -> AlbumType: ...

def batch_detect_types(items: List[TypeDetectable]) -> List[AlbumType]:
    """Generic type detection for any detectable items."""
    return [item.detect_type() for item in items]
```

#### Complex Type Annotations
```python
# Type aliases for complex structures
AlbumTypeDistribution = Dict[AlbumType, int]
StructureAnalysisResult = Dict[str, Union[str, int, List[str], Dict[str, Any]]]
ComplianceReport = Dict[str, Union[int, str, List[str], Optional[str]]]

# Function with complex return type
def analyze_collection_types(
    collection_path: Path
) -> Dict[str, Union[AlbumTypeDistribution, StructureAnalysisResult, ComplianceReport]]:
    """
    Comprehensive collection analysis with type distribution and structure compliance.
    
    Returns:
        Dictionary containing:
        - type_distribution: Count of albums by type
        - structure_analysis: Folder structure assessment
        - compliance_report: Overall compliance scoring
    """
    pass
```

### File Organization for Type Features

#### Module Structure for Classification Features
```python
# src/models/album.py
"""
Album models with type classification support.

Contains Album model, AlbumType enum, and related validation logic.
Focused on core album representation and type classification.
"""

# Standard library imports
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime

# Third-party imports
from pydantic import BaseModel, Field, validator

# Local imports
from .base import BaseModel
from ..utils.validation import validate_year_format

# src/utils/album_classifier.py
"""
Album type detection and classification utilities.

Provides algorithms for detecting album types from folder names,
metadata, and file system structure patterns.
"""

# src/services/structure_analyzer.py
"""
Folder structure analysis and compliance validation.

Analyzes band folder organization patterns and calculates
compliance scores for various structure types.
"""
```

#### File Naming Conventions for Type Features
- **Models**: `album.py`, `structure.py`, `compliance.py`
- **Services**: `type_detector.py`, `structure_analyzer.py`, `compliance_validator.py`
- **Utilities**: `album_parser.py`, `folder_utils.py`, `type_keywords.py`
- **Tests**: `test_album_types.py`, `test_structure_analysis.py`, `test_compliance.py`

### Validation and Type Safety

#### Pydantic Models with Type Validation
```python
class Album(BaseModel):
    """Enhanced album model with type classification and compliance."""
    
    album_name: str = Field(..., min_length=1, max_length=200)
    year: Optional[str] = Field(None, regex=r'^\d{4}$')
    type: AlbumType = Field(default=AlbumType.ALBUM)
    edition: Optional[str] = Field(default="", max_length=100)
    
    # Compliance information
    compliance: Optional[AlbumCompliance] = Field(default_factory=AlbumCompliance)
    
    @validator('type')
    def validate_album_type(cls, v):
        """Ensure album type is valid AlbumType enum value."""
        if isinstance(v, str):
            try:
                return AlbumType(v)
            except ValueError:
                raise ValueError(f'Invalid album type: {v}')
        return v
    
    @validator('compliance')
    def validate_compliance_structure(cls, v):
        """Validate compliance object structure."""
        if v is not None and not isinstance(v, AlbumCompliance):
            # Try to create from dict
            if isinstance(v, dict):
                return AlbumCompliance(**v)
            raise ValueError('Compliance must be AlbumCompliance object or dict')
        return v
    
    def auto_detect_type(self, folder_path: Optional[Path] = None) -> AlbumType:
        """Auto-detect album type from available information."""
        detector = AlbumTypeDetector()
        
        if folder_path:
            return detector.detect_from_folder_structure(folder_path, self.album_name)
        else:
            return detector.detect_from_name(self.album_name)
```

#### Type-Safe Helper Functions
```python
def ensure_album_type(value: Union[str, AlbumType]) -> AlbumType:
    """
    Ensure value is a valid AlbumType instance.
    
    Args:
        value: String or AlbumType to validate
        
    Returns:
        Valid AlbumType instance
        
    Raises:
        ValueError: If value cannot be converted to AlbumType
    """
    if isinstance(value, AlbumType):
        return value
    elif isinstance(value, str):
        try:
            return AlbumType(value)
        except ValueError:
            raise ValueError(f"Invalid album type: {value}")
    else:
        raise TypeError(f"Expected str or AlbumType, got {type(value)}")

def ensure_structure_type(value: Union[str, StructureType]) -> StructureType:
    """Ensure value is a valid StructureType instance."""
    if isinstance(value, StructureType):
        return value
    elif isinstance(value, str):
        try:
            return StructureType(value)
        except ValueError:
            raise ValueError(f"Invalid structure type: {value}")
    else:
        raise TypeError(f"Expected str or StructureType, got {type(value)}")
```

### Testing Standards for Type Features

#### Unit Test Structure
```python
# tests/test_album_type_detection.py
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from src.models.album import Album, AlbumType
from src.utils.album_classifier import AlbumTypeDetector
from src.services.structure_analyzer import BandStructureDetector

class TestAlbumTypeDetection:
    """Test suite for album type detection functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.detector = AlbumTypeDetector()
        self.test_cases = [
            ("1985 - Live at Wembley", AlbumType.LIVE),
            ("1996 - Greatest Hits", AlbumType.COMPILATION),
            ("1980 - Love EP", AlbumType.EP),
            ("1978 - Early Demos", AlbumType.DEMO),
            ("1973 - Dark Side of the Moon", AlbumType.ALBUM)
        ]
    
    @pytest.mark.parametrize("folder_name,expected_type", [
        ("1985 - Live at Wembley", AlbumType.LIVE),
        ("1996 - Greatest Hits", AlbumType.COMPILATION),
        ("1980 - Love EP", AlbumType.EP),
        ("1978 - Early Demos", AlbumType.DEMO),
        ("1973 - Dark Side of the Moon", AlbumType.ALBUM)
    ])
    def test_type_detection_from_folder_name(self, folder_name: str, expected_type: AlbumType):
        """Test type detection from folder names."""
        result = self.detector.detect_from_folder_name(folder_name)
        assert result == expected_type
    
    def test_enhanced_structure_detection(self):
        """Test type detection in enhanced folder structures."""
        test_path = Path("/music/Pink Floyd/Live/1985 - Live at Wembley")
        
        with patch('pathlib.Path.exists', return_value=True):
            result = self.detector.detect_from_folder_structure(test_path, "Live at Wembley")
            assert result == AlbumType.LIVE
    
    def test_invalid_input_handling(self):
        """Test handling of invalid inputs."""
        with pytest.raises(ValueError):
            self.detector.detect_from_folder_name("")
        
        with pytest.raises(TypeError):
            self.detector.detect_from_folder_name(None)
```

### Performance Considerations for Type Features

#### Efficient Type Detection
```python
class CachedAlbumTypeDetector:
    """Type detector with caching for performance."""
    
    def __init__(self, cache_size: int = 1000):
        self._cache: Dict[str, AlbumType] = {}
        self._cache_size = cache_size
    
    def detect_from_folder_name(self, folder_name: str) -> AlbumType:
        """Detect type with caching."""
        # Normalize cache key
        cache_key = folder_name.lower().strip()
        
        # Check cache first
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Perform detection
        result = self._perform_detection(folder_name)
        
        # Cache result (with size limit)
        if len(self._cache) < self._cache_size:
            self._cache[cache_key] = result
        
        return result
```

### Configuration and Constants

#### Type-Related Configuration
```python
# src/config/type_detection.py
"""Configuration constants for album type detection."""

# Detection confidence thresholds
TYPE_DETECTION_CONFIDENCE_THRESHOLD = 0.8
STRUCTURE_ANALYSIS_CONFIDENCE_THRESHOLD = 0.7

# Performance settings
MAX_ALBUMS_PER_BATCH = 100
TYPE_DETECTION_CACHE_SIZE = 1000
STRUCTURE_ANALYSIS_CACHE_TTL = 3600  # 1 hour

# Default values
DEFAULT_ALBUM_TYPE = AlbumType.ALBUM
DEFAULT_STRUCTURE_TYPE = StructureType.DEFAULT

# Compliance scoring weights
COMPLIANCE_WEIGHTS = {
    'year_prefix': 0.30,
    'type_organization': 0.25,
    'edition_format': 0.20,
    'consistency': 0.15,
    'naming_quality': 0.10
}
```

This enhanced code style guide ensures consistent, maintainable code while leveraging the full capabilities of Python's type system for the album classification and structure analysis features. 