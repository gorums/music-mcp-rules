# Contributing to Music Collection MCP Server

## Welcome Contributors! 🎵

Thank you for your interest in contributing to the Music Collection MCP Server! This project provides an intelligent, modular music collection management system through the Model Context Protocol, featuring advanced album type classification, separated album schemas, and dependency injection architecture. We welcome contributions of all kinds, from bug fixes to new features.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Requirements](#testing-requirements)
- [Modular Architecture Guidelines](#modular-architecture-guidelines)
- [Separated Albums Schema](#separated-albums-schema)
- [Contribution Workflow](#contribution-workflow)
- [Feature Development](#feature-development)
- [Bug Reports](#bug-reports)
- [Pull Request Process](#pull-request-process)
- [Community Guidelines](#community-guidelines)

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- **Python 3.8+** installed
- **Docker** (for testing and development)
- **Git** for version control
- A music collection for testing (optional but recommended)
- Familiarity with MCP (Model Context Protocol) concepts
- Understanding of music collection organization patterns

### Understanding the Project

1. **Read the Documentation**: Start with the [PLANNING.md](PLANNING.md) and [ARCHITECTURE.md](ARCHITECTURE.md)
2. **Review API Reference**: Check [API_REFERENCE.md](API_REFERENCE.md) for implementation details
3. **Study Album Type System**: Review [ALBUM_HANDLING.md](ALBUM_HANDLING.md) for type classification features
4. **Understand Structure Analysis**: Check [COLLECTION_ORGANIZATION.md](COLLECTION_ORGANIZATION.md) for folder structure features
5. **Check Existing Issues**: Browse GitHub issues to understand current work
6. **Test the Server**: Run the server locally to understand functionality

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/music-catalog-mcp.git
cd music-catalog-mcp

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/music-catalog-mcp.git
```

### 2. Environment Setup

#### Local Development
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env with your music collection path
```

#### Docker Development
```bash
# Build development container
docker build -f Dockerfile.test -t music-mcp-dev .

# Run development container
docker run -v $(pwd):/app -v /path/to/music:/music \
  -e "MUSIC_ROOT_PATH=/music" \
  music-mcp-dev bash
```

### 3. Verify Setup

```bash
# Run tests to verify everything works
python -m pytest tests/ -v

# Test album type detection and structure analysis
python -m pytest tests/test_models/test_album_enhancements.py -v

# Test separated albums schema
python -m pytest tests/test_separated_albums_schema.py -v

# Test modular server components
python -m pytest tests/test_mcp_server/ -v

# Test server startup
python main.py
```

## Code Style Guidelines

### Python Code Standards

We follow **PEP 8** with some project-specific additions:

#### Formatting
- **Line Length**: 100 characters maximum
- **Indentation**: 4 spaces (no tabs)
- **Imports**: Use `black` for automatic formatting
- **Type Hints**: Required for all function signatures

## Modular Architecture Guidelines

### File Size Constraints
- **Maximum file size**: 350 lines per file
- **Function size**: Maximum 50 lines per function
- **Single responsibility**: Each file should have one clear purpose
- **Separation of concerns**: Business logic separate from MCP protocol handling

### Directory Structure
```
src/
├── mcp_server/            # MCP server components (modular)
│   ├── main.py            # Server initialization (<100 lines)
│   ├── base_handlers.py   # Base handler classes
│   ├── error_handlers.py  # Error handling system
│   ├── tools/             # Individual tool files (8 tools)
│   ├── resources/         # Individual resource files (3 resources)
│   └── prompts/          # Individual prompt files (4 prompts)
├── tools/                 # Core services
├── models/               # Data models with separated schemas
├── di/                   # Dependency injection
└── exceptions.py         # Exception hierarchy
```

### Creating New Components

#### Adding New MCP Tools
1. Create individual file in `src/mcp_server/tools/`
2. Inherit from `BaseToolHandler`
3. Keep file under 350 lines
4. Export in `src/mcp_server/tools/__init__.py`

```python
# src/mcp_server/tools/my_new_tool.py
from src.mcp_server.main import app
from src.mcp_server.base_handlers import BaseToolHandler

@app.tool()
async def my_new_tool(param: str) -> dict:
    """New tool implementation."""
    # Implementation under 50 lines per function
```

## Separated Albums Schema

### Key Schema Changes
- **Local albums**: `albums` array contains only albums found in folders
- **Missing albums**: `albums_missing` array contains albums not found locally
- **No missing field**: Removed `missing: bool` from Album model
- **Computed counts**: `albums_count = len(albums) + len(albums_missing)`

### Working with Separated Schema
```python
class BandMetadata(BaseModel):
    albums: List[Album] = []           # Local albums only
    albums_missing: List[Album] = []   # Missing albums only
    
    @property
    def local_albums_count(self) -> int:
        return len(self.albums)
        
    @property
    def missing_albums_count(self) -> int:
        return len(self.albums_missing)
```

#### Code Style for Album Features
```python
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field
from pathlib import Path

# Album type enumeration  
class AlbumType(str, Enum):
    """Album type classification enumeration."""
    ALBUM = "Album"
    COMPILATION = "Compilation"
    EP = "EP"
    LIVE = "Live"
    SINGLE = "Single"
    DEMO = "Demo"
    INSTRUMENTAL = "Instrumental"
    SPLIT = "Split"

class AlbumTypeDetector:
    """
    Album type detection utility with comprehensive classification.
    
    Provides intelligent detection of album types from folder names,
    metadata, and file system structure patterns.
    
    Args:
        confidence_threshold: Minimum confidence for type assignment (0.0-1.0)
        default_type: Fallback type when detection is uncertain
        
    Returns:
        AlbumType: Detected album type with confidence scoring
        
    Raises:
        AlbumTypeError: If detection fails due to invalid input
        
    Example:
        >>> detector = AlbumTypeDetector(confidence_threshold=0.8)
        >>> album_type = detector.detect_from_folder_name("1985 - Live at Wembley")
        >>> assert album_type == AlbumType.LIVE
    """
    
    def __init__(self, confidence_threshold: float = 0.8):
        self.confidence_threshold = confidence_threshold
        self.default_type = AlbumType.ALBUM
    
    def detect_album_type_from_folder_structure(
        self, 
        folder_path: Path, 
        album_name: str
    ) -> AlbumType:
        """
        Detect album type from folder structure and naming patterns.
        
        Uses multiple detection strategies including keyword matching,
        parent directory analysis, and structure pattern recognition.
        """
        # Reason: Enhanced detection provides higher accuracy than name-only
        # by considering folder context and organization patterns
        pass

    def update_albums_count(self) -> None:
        """Update albums count based on albums list."""
        self.albums_count = len(self.albums)
        # Reason: Keep derived field in sync with source data for type statistics
```

#### Docstring Standards for New Features

Use **Google-style docstrings** for all functions, especially type-related:

```python
def analyze_folder_structure_compliance(
    band_path: Path,
    albums: List[Album],
    structure_type: StructureType = StructureType.DEFAULT
) -> FolderStructure:
    """
    Analyze folder structure compliance and generate improvement recommendations.
    
    Evaluates band folder organization against established patterns and
    calculates compliance scores for various structure types including
    default, enhanced, legacy, and mixed patterns.
    
    Args:
        band_path: Absolute path to band's root folder
        albums: List of albums with type and path information
        structure_type: Expected or detected structure type
        
    Returns:
        FolderStructure: Comprehensive analysis including compliance score,
        recommendations, detected issues, and structure metadata
        
    Raises:
        StructureAnalysisError: If band folder is inaccessible
        ValidationError: If albums list contains invalid data
        
    Example:
        >>> band_path = Path("/music/Pink Floyd")
        >>> albums = [Album(name="The Wall", type=AlbumType.ALBUM)]
        >>> analysis = analyze_folder_structure_compliance(band_path, albums)
        >>> print(f"Compliance score: {analysis.structure_score}/100")
        
    Note:
        Enhanced structure analysis requires type detection to be enabled.
        Compliance scoring considers multiple factors including naming
        consistency, type organization, and metadata completeness.
    """
```

### File Organization for Type Features

#### Module Structure
```python
# src/models/album.py - Core album models with type support
"""
Enhanced album models with type classification and compliance tracking.

Contains Album model, AlbumType enum, compliance structures, and validation
logic for the album type classification system.
"""

# src/utils/type_detector.py - Type detection algorithms
"""
Album type detection algorithms and utilities.

Provides intelligent classification of albums into 8 supported types
using keyword matching, folder structure analysis, and metadata inspection.
"""

# src/services/structure_analyzer.py - Structure analysis service
"""
Folder structure analysis and compliance validation service.

Analyzes band folder organization patterns, calculates compliance scores,
and generates recommendations for improving collection organization.
"""
```

#### File Naming Conventions for Type Features
- **Models**: `album.py`, `structure.py`, `compliance.py`
- **Services**: `type_detector.py`, `structure_analyzer.py`, `compliance_validator.py`
- **Utilities**: `album_parser.py`, `folder_utils.py`, `pattern_matcher.py`
- **Tests**: `test_album_types.py`, `test_structure_analysis.py`, `test_compliance.py`

### Error Handling for Type Features

#### Custom Exception Hierarchy
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
    """Errors during folder structure analysis and compliance validation."""
    pass

class ComplianceValidationError(MusicMCPError):
    """Errors during compliance scoring and validation."""
    pass
```

## Testing Requirements

### Test Structure for New Features

#### Album Type Detection Tests
```bash
# Run album type detection tests
python -m pytest tests/test_album_types.py -v

# Test specific detection scenarios
python -m pytest tests/test_album_types.py::test_live_album_detection -v
python -m pytest tests/test_album_types.py::test_compilation_detection -v
```

#### Structure Analysis Tests
```bash
# Run structure analysis tests
python -m pytest tests/test_structure_analysis.py -v

# Test compliance scoring
python -m pytest tests/test_compliance.py -v
```

#### Integration Tests
```bash
# Test full workflow with type features
python -m pytest tests/test_integration_types.py -v
```

### Test Requirements for New Features

When contributing type classification or structure analysis features:

1. **Unit Tests for Type Detection**: Test individual detection algorithms
2. **Structure Analysis Tests**: Validate compliance calculations and recommendations
3. **Integration Tests**: Ensure features work together correctly
4. **Edge Case Tests**: Handle unusual folder structures and naming patterns
5. **Performance Tests**: Ensure type detection doesn't significantly impact scan speed

#### Example Test Structure
```python
# tests/test_album_types.py
import pytest
from pathlib import Path
from src.models.album import Album, AlbumType
from src.utils.type_detector import AlbumTypeDetector

class TestAlbumTypeDetection:
    """Comprehensive tests for album type detection features."""
    
    def setup_method(self):
        """Set up test fixtures for type detection."""
        self.detector = AlbumTypeDetector(confidence_threshold=0.8)
    
    @pytest.mark.parametrize("folder_name,expected_type", [
        ("1985 - Live at Wembley", AlbumType.LIVE),
        ("1996 - Greatest Hits", AlbumType.COMPILATION),
        ("1980 - Love EP", AlbumType.EP),
        ("1978 - Early Demos", AlbumType.DEMO),
        ("1973 - Dark Side of the Moon", AlbumType.ALBUM),
        ("1982 - Single Release", AlbumType.SINGLE),
        ("1979 - Instrumentals", AlbumType.INSTRUMENTAL),
        ("2001 - Band A vs. Band B", AlbumType.SPLIT)
    ])
    def test_type_detection_from_folder_names(self, folder_name: str, expected_type: AlbumType):
        """Test type detection accuracy across all supported types."""
        result = self.detector.detect_from_folder_name(folder_name)
        assert result == expected_type, f"Expected {expected_type}, got {result} for '{folder_name}'"
    
    def test_enhanced_structure_detection(self):
        """Test type detection in enhanced folder structures."""
        # Test type folder detection
        test_cases = [
            (Path("/music/Pink Floyd/Live/1985 - Live at Wembley"), AlbumType.LIVE),
            (Path("/music/Queen/Album/1975 - A Night at the Opera"), AlbumType.ALBUM),
            (Path("/music/Beatles/Compilation/1996 - Anthology"), AlbumType.COMPILATION)
        ]
        
        for path, expected_type in test_cases:
            result = self.detector.detect_from_folder_structure(path, path.name)
            assert result == expected_type
    
    def test_confidence_scoring(self):
        """Test confidence scoring for type detection."""
        high_confidence_cases = [
            "1985 - Live at Wembley Stadium",  # Clear live indicators
            "1996 - The Very Best of Queen",   # Clear compilation indicators
        ]
        
        for case in high_confidence_cases:
            confidence = self.detector.get_detection_confidence(case)
            assert confidence >= 0.8, f"Expected high confidence for '{case}', got {confidence}"
    
    def test_edge_cases(self):
        """Test handling of edge cases and unusual naming patterns."""
        edge_cases = [
            ("", AlbumType.ALBUM),  # Empty string defaults to Album
            ("1985", AlbumType.ALBUM),  # Year only
            ("Live Wire", AlbumType.ALBUM),  # Contains 'live' but not live album
            ("Demo Track", AlbumType.ALBUM),  # Contains 'demo' but not demo album
        ]
        
        for folder_name, expected_type in edge_cases:
            result = self.detector.detect_from_folder_name(folder_name)
            assert result == expected_type
```

## Album Type Classification Features

### Contributing to Type Detection

When working on album type classification features:

#### 1. Understanding the Type System
- Review the 8 supported album types and their characteristics
- Understand detection keywords and patterns for each type
- Study existing detection algorithms and confidence scoring

#### 2. Adding New Detection Patterns
```python
# Example: Adding new detection keywords
class AlbumTypeDetector:
    TYPE_KEYWORDS = {
        AlbumType.LIVE: [
            'live', 'concert', 'unplugged', 'acoustic',
            'in concert', 'live at', 'live in', 'live from',
            # Add new patterns here
            'on stage', 'concert hall', 'festival'
        ]
    }
```

#### 3. Improving Detection Accuracy
- Test detection against diverse music collections
- Handle edge cases and ambiguous naming patterns
- Optimize confidence scoring algorithms
- Consider multiple detection strategies (name, path, metadata)

#### 4. Performance Considerations
- Ensure detection algorithms are efficient for large collections
- Implement caching for repeated detections
- Minimize file system operations during detection

### Type Classification Best Practices

1. **Keyword Matching**: Be specific to avoid false positives
2. **Context Awareness**: Consider folder structure and parent directories
3. **Confidence Scoring**: Provide confidence levels for uncertain detections
4. **Fallback Handling**: Default to Album type when uncertain
5. **Performance**: Keep detection fast for large collections

## Folder Structure Analysis Features

### Contributing to Structure Analysis

When working on folder structure analysis:

#### 1. Understanding Structure Types
- **Default**: Flat structure with "YYYY - Album Name" pattern
- **Enhanced**: Type-based folders with "Type/YYYY - Album Name" pattern
- **Legacy**: Simple album names without year prefixes
- **Mixed**: Combination of multiple patterns
- **Unknown**: Unable to determine structure type

#### 2. Compliance Scoring Factors
```python
# Example compliance scoring weights
COMPLIANCE_FACTORS = {
    'year_prefix_consistency': 0.30,    # Albums have consistent year prefixes
    'type_folder_organization': 0.25,   # Albums organized in type folders
    'edition_format_consistency': 0.20, # Consistent edition formatting
    'overall_consistency': 0.15,        # Pattern consistency across collection
    'naming_quality': 0.10              # Clear, descriptive naming
}
```

#### 3. Generating Recommendations
- Analyze current structure patterns
- Identify inconsistencies and improvement opportunities
- Provide specific, actionable recommendations
- Calculate estimated compliance improvements

#### 4. Migration Planning
- Assess migration complexity and risks
- Generate step-by-step migration plans
- Estimate time and effort requirements
- Validate migration feasibility

### Structure Analysis Best Practices

1. **Pattern Recognition**: Accurately identify organization patterns
2. **Comprehensive Scoring**: Consider multiple compliance factors
3. **Actionable Recommendations**: Provide specific improvement suggestions
4. **Migration Support**: Help users upgrade their organization
5. **Flexibility**: Support various organization preferences

## Contribution Workflow

### Development Process for Type Features

1. **Issue Selection**: Choose issues labeled with `album-types` or `structure-analysis`
2. **Feature Branch**: Create feature branch with descriptive name
   ```bash
   git checkout -b feature/improve-live-album-detection
   git checkout -b feature/enhanced-compliance-scoring
   ```
3. **Development**: Implement feature following code style guidelines
4. **Testing**: Add comprehensive tests for new functionality
5. **Documentation**: Update relevant documentation files
6. **Integration Testing**: Test with various music collection structures

### Testing New Type Features

#### Test Against Diverse Collections
```bash
# Test with different folder structures
export MUSIC_ROOT_PATH="/path/to/test/collection/enhanced"
python -m pytest tests/test_integration.py

export MUSIC_ROOT_PATH="/path/to/test/collection/legacy"
python -m pytest tests/test_integration.py

export MUSIC_ROOT_PATH="/path/to/test/collection/mixed"
python -m pytest tests/test_integration.py
```

#### Validate Detection Accuracy
```bash
# Run accuracy tests against known collections
python scripts/validate_type_detection.py --collection-path /test/collections
python scripts/analyze_structure_accuracy.py --collection-path /test/collections
```

## Feature Development

### Implementing New Album Types

If you want to add support for a new album type:

1. **Propose the Type**: Open an issue discussing the new type
2. **Update Enums**: Add to AlbumType enumeration
3. **Add Detection Logic**: Implement detection keywords and patterns
4. **Update Documentation**: Document the new type and its characteristics
5. **Add Tests**: Comprehensive tests for the new type
6. **Update Examples**: Add examples to documentation

### Enhancing Structure Analysis

For structure analysis improvements:

1. **Identify Patterns**: Study common folder organization patterns
2. **Improve Scoring**: Enhance compliance scoring algorithms
3. **Add Recommendations**: Implement new recommendation types
4. **Test Thoroughly**: Validate against diverse collections
5. **Document Changes**: Update analysis documentation

### Performance Optimizations

When optimizing type classification or structure analysis:

1. **Profile Performance**: Identify bottlenecks using profiling tools
2. **Implement Caching**: Cache detection results and analysis data
3. **Optimize Algorithms**: Improve efficiency of detection logic
4. **Parallel Processing**: Consider parallelization for large collections
5. **Benchmark Changes**: Measure performance improvements

## Bug Reports

### Reporting Type Classification Issues

When reporting bugs related to album type classification:

```markdown
## Album Type Classification Bug Report

**Description**: Brief description of the issue

**Expected Type**: What album type should be detected
**Actual Type**: What type was actually detected
**Folder Name**: Exact folder name causing the issue
**Collection Structure**: Describe the folder organization

**Test Collection**: 
```
Band Name/
├── Album/
│   └── 1973 - Album Name/
├── Live/
│   └── 1985 - Live at Venue/  ← Issue with this folder
```

**Environment**:
- Python Version: 3.x
- Detection Confidence Threshold: 0.8
- Structure Type: enhanced/default/legacy

**Additional Context**: Any additional information about the issue
```

### Reporting Structure Analysis Issues

```markdown
## Folder Structure Analysis Bug Report

**Description**: Brief description of the structure analysis issue

**Expected Compliance Score**: What score should be calculated
**Actual Compliance Score**: What score was actually calculated
**Structure Type**: Default/Enhanced/Legacy/Mixed
**Issues Found**: List of issues reported by analysis

**Test Collection Structure**:
```
Band Name/
├── 1973 - Album Name/
├── 1979 - Another Album/
├── Live at Venue/  ← Structure analysis issue
```

**Analysis Output**: Include relevant analysis output
**Environment**: Include system and configuration details
```

## Pull Request Process

### PR Requirements for Type Features

1. **Description**: Clearly describe the type classification or structure analysis changes
2. **Testing**: Include tests for new detection patterns or analysis features
3. **Documentation**: Update documentation for new features
4. **Performance**: Ensure changes don't significantly impact performance
5. **Backwards Compatibility**: Maintain compatibility with existing collections

### PR Template for Type Features

```markdown
## Type Classification/Structure Analysis Changes

### Description
Brief description of the changes to album type detection or structure analysis

### Type of Change
- [ ] New album type detection pattern
- [ ] Improved detection accuracy
- [ ] Enhanced structure analysis
- [ ] Performance optimization
- [ ] Bug fix
- [ ] Documentation update

### Testing
- [ ] Added tests for new detection patterns
- [ ] Tested against diverse collection structures
- [ ] Validated detection accuracy improvements
- [ ] Performance impact assessed

### Documentation
- [ ] Updated API documentation
- [ ] Updated user guides
- [ ] Added examples for new features

### Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass (including type-specific tests)
- [ ] Documentation is updated
- [ ] No performance regressions
- [ ] Backwards compatibility maintained
```

## Community Guidelines

### Collaboration on Type Features

1. **Share Test Collections**: Help others by sharing diverse test cases
2. **Document Edge Cases**: Report unusual folder structures and naming patterns
3. **Contribute Detection Patterns**: Share keywords and patterns for better detection
4. **Review Code**: Focus on accuracy and performance of type classification
5. **Provide Feedback**: Test new features with your music collection

### Best Practices for Contributors

1. **Start Small**: Begin with simple improvements to detection accuracy
2. **Test Thoroughly**: Use diverse music collections for testing
3. **Document Decisions**: Explain reasoning behind detection patterns and scoring algorithms
4. **Consider Edge Cases**: Handle unusual collection organizations gracefully
5. **Maintain Performance**: Ensure type classification remains fast

### Getting Help

- **Discord/Chat**: Join our community chat for real-time help
- **GitHub Discussions**: Use discussions for feature ideas and questions
- **Issues**: Use issues for specific bugs or feature requests
- **Documentation**: Check documentation before asking questions

We appreciate your contributions to making the Music Collection MCP Server the best tool for intelligent music collection management! 🎵 