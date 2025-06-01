# Contributing to Music Collection MCP Server

## Welcome Contributors! 🎵

Thank you for your interest in contributing to the Music Collection MCP Server! This project aims to provide an intelligent, file-system-based music collection management system through the Model Context Protocol. We welcome contributions of all kinds, from bug fixes to new features.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Requirements](#testing-requirements)
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

### Understanding the Project

1. **Read the Documentation**: Start with the [PLANNING.md](PLANNING.md) and [ARCHITECTURE.md](ARCHITECTURE.md)
2. **Review API Reference**: Check [API_REFERENCE.md](API_REFERENCE.md) for implementation details
3. **Check Existing Issues**: Browse GitHub issues to understand current work
4. **Test the Server**: Run the server locally to understand functionality

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
docker run -v $(pwd):/app -v /path/to/music:/music music-mcp-dev bash
```

### 3. Verify Setup

```bash
# Run tests to verify everything works
python -m pytest tests/ -v

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

#### Example Code Style
```python
from typing import List, Optional, Dict, Any
from datetime import datetime

from pydantic import BaseModel, Field

class BandMetadata(BaseModel):
    """
    Represents complete metadata for a musical band.
    
    Args:
        band_name: Official name of the band
        formed: Year the band was formed (YYYY format)
        genres: List of musical genres
        
    Returns:
        BandMetadata: Validated band metadata instance
        
    Raises:
        ValidationError: If required fields are missing or invalid
    """
    band_name: str = Field(..., min_length=1, max_length=200)
    formed: Optional[str] = Field(None, regex=r"^\d{4}$")
    genres: List[str] = Field(default_factory=list)
    albums_count: int = Field(0, ge=0)
    
    def update_albums_count(self) -> None:
        """Update albums count based on albums list."""
        self.albums_count = len(self.albums)
        # Reason: Keep derived field in sync with source data
```

#### Docstring Standards

Use **Google-style docstrings** for all functions:

```python
def scan_music_folders(
    music_path: str, 
    force_rescan: bool = False
) -> ScanResult:
    """
    Scan music collection directory for bands and albums.
    
    Discovers band folders and their albums, creating a collection index
    for fast access. Supports incremental scanning for performance.
    
    Args:
        music_path: Absolute path to music collection root
        force_rescan: Force full rescan even if no changes detected
        
    Returns:
        ScanResult: Object containing scan statistics and discovered bands
        
    Raises:
        ScanError: If music directory is inaccessible
        ValidationError: If music_path is invalid
        
    Example:
        >>> result = scan_music_folders("/music", force_rescan=True)
        >>> print(f"Found {result.bands_count} bands")
    """
```

### File Organization

#### Module Structure
```python
# src/tools/scanner.py
"""
Music collection scanner for band and album discovery.

This module provides comprehensive scanning functionality for music collections,
including incremental updates, error recovery, and performance optimization.
"""

# Standard library imports
import os
import json
from pathlib import Path
from typing import List, Dict, Optional

# Third-party imports
from pydantic import BaseModel, Field

# Local imports
from ..models.band import BandMetadata
from ..models.collection import CollectionIndex
from ..config import Config
```

#### File Naming Conventions
- **Modules**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private members**: `_leading_underscore`

### Error Handling

#### Custom Exception Hierarchy
```python
class MusicMCPError(Exception):
    """Base exception for Music MCP Server."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class ScanError(MusicMCPError):
    """Errors during collection scanning."""
    pass

class StorageError(MusicMCPError):
    """Errors during data storage operations."""
    pass
```

#### Error Handling Patterns
```python
def save_band_metadata(band_name: str, metadata: BandMetadata) -> SaveResult:
    """Save band metadata with comprehensive error handling."""
    try:
        # Validate input
        if not band_name.strip():
            raise ValidationError("Band name cannot be empty")
            
        # Attempt operation
        result = _perform_save(band_name, metadata)
        
        return SaveResult(success=True, band_name=band_name)
        
    except ValidationError as e:
        # Handle validation errors
        return SaveResult(
            success=False, 
            error={"code": "VALIDATION_ERROR", "message": str(e)}
        )
    except PermissionError as e:
        # Handle file permission errors  
        raise StorageError(
            f"Cannot write metadata for {band_name}",
            details={"band_name": band_name, "original_error": str(e)}
        )
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error saving {band_name}: {e}")
        raise StorageError(f"Failed to save metadata for {band_name}")
```

## Testing Requirements

### Test Structure

Our testing follows a comprehensive strategy:

#### Unit Tests
- **Location**: `tests/test_*.py`
- **Coverage**: Minimum 85% line coverage
- **Scope**: Individual functions and classes

#### Integration Tests
- **Location**: `tests/integration/`
- **Scope**: Component interactions and workflows
- **Requirements**: Docker environment for isolation

#### Performance Tests
- **Location**: `tests/performance/`
- **Scope**: Large collection handling and benchmarks
- **Thresholds**: Defined performance requirements

### Writing Tests

#### Unit Test Example
```python
import pytest
from unittest.mock import Mock, patch

from src.models.band import BandMetadata, Album
from src.tools.storage import save_band_metadata

class TestBandMetadata:
    """Test band metadata model validation and behavior."""
    
    def test_valid_band_metadata_creation(self):
        """Test creating valid band metadata."""
        # Arrange
        band_data = {
            "band_name": "Pink Floyd",
            "formed": "1965",
            "genres": ["Progressive Rock"],
            "albums": [
                {
                    "album_name": "The Dark Side of the Moon",
                    "year": "1973",
                    "tracks_count": 10
                }
            ]
        }
        
        # Act
        band = BandMetadata(**band_data)
        
        # Assert
        assert band.band_name == "Pink Floyd"
        assert band.formed == "1965"
        assert len(band.albums) == 1
        assert band.albums[0].album_name == "The Dark Side of the Moon"
    
    def test_invalid_year_format_raises_validation_error(self):
        """Test that invalid year format raises ValidationError."""
        # Arrange
        band_data = {
            "band_name": "Test Band",
            "formed": "invalid_year"  # Invalid format
        }
        
        # Act & Assert
        with pytest.raises(ValidationError):
            BandMetadata(**band_data)
    
    @pytest.mark.parametrize("rating,expected_valid", [
        (1, True),
        (5, True), 
        (10, True),
        (0, False),
        (11, False),
        ("8", False)
    ])
    def test_rating_validation(self, rating, expected_valid):
        """Test rating validation with various inputs."""
        if expected_valid:
            # Should not raise exception
            album = AlbumAnalysis(album_name="Test", rate=rating)
            assert album.rate == rating
        else:
            # Should raise ValidationError
            with pytest.raises(ValidationError):
                AlbumAnalysis(album_name="Test", rate=rating)
```

#### Integration Test Example
```python
@pytest.mark.integration
class TestScannerIntegration:
    """Integration tests for music scanner."""
    
    @pytest.fixture
    def temp_music_collection(self, tmp_path):
        """Create temporary music collection for testing."""
        music_root = tmp_path / "music"
        
        # Create band folders
        pink_floyd = music_root / "Pink Floyd"
        pink_floyd.mkdir(parents=True)
        
        # Create album folders
        album = pink_floyd / "The Dark Side of the Moon"
        album.mkdir()
        
        # Create music files
        (album / "track1.mp3").touch()
        (album / "track2.mp3").touch()
        
        return music_root
    
    def test_full_collection_scan(self, temp_music_collection):
        """Test complete collection scanning workflow."""
        # Arrange
        scanner = MusicScanner(Config(music_root_path=str(temp_music_collection)))
        
        # Act
        result = scanner.scan_music_folders(force_rescan=True)
        
        # Assert
        assert result.success is True
        assert result.bands_scanned == 1
        assert result.albums_found == 1
        assert "Pink Floyd" in [band.band_name for band in result.bands]
```

### Running Tests

#### Local Testing
```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run specific test file
python -m pytest tests/test_models_band.py -v

# Run performance tests
python -m pytest tests/performance/ -v --disable-warnings
```

#### Docker Testing
```bash
# Build test container
docker build -f Dockerfile.test -t music-mcp-tests .

# Run all tests in container
docker run --rm music-mcp-tests python -m pytest . -v

# Run with coverage
docker run --rm music-mcp-tests python -m pytest . -v --cov=src
```

## Contribution Workflow

### 1. Issue Selection

#### Finding Issues
- **Good First Issues**: Look for `good-first-issue` label
- **Help Wanted**: Check `help-wanted` for needed contributions
- **Bugs**: `bug` label for confirmed bugs
- **Features**: `enhancement` label for new features

#### Before Starting
1. **Comment on Issue**: Let others know you're working on it
2. **Understand Requirements**: Ask questions if unclear
3. **Check Dependencies**: Ensure no blocking issues
4. **Estimate Scope**: Consider time commitment

### 2. Branch Strategy

```bash
# Create feature branch from main
git checkout main
git pull upstream main
git checkout -b feature/your-feature-name

# Create bug fix branch
git checkout -b bugfix/issue-number-description

# Create documentation branch
git checkout -b docs/documentation-topic
```

#### Branch Naming Conventions
- **Features**: `feature/descriptive-name`
- **Bug Fixes**: `bugfix/issue-number-description`
- **Documentation**: `docs/topic-name`
- **Performance**: `perf/optimization-area`
- **Tests**: `test/test-area`

### 3. Development Process

#### Regular Commits
```bash
# Make small, focused commits
git add .
git commit -m "feat: add album missing detection to scanner

- Implement missing album detection in _scan_band_folder
- Add missing flag to Album model
- Update collection index with missing album counts
- Add tests for missing album scenarios

Resolves #123"
```

#### Commit Message Format
```
type(scope): brief description

Detailed explanation of changes made, why they were necessary,
and how they address the issue.

- Bullet point for major change 1
- Bullet point for major change 2
- Bullet point for major change 3

Resolves #issue-number
```

**Commit Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions/changes
- `refactor`: Code restructuring
- `perf`: Performance improvements
- `style`: Formatting changes

### 4. Testing Before Submission

```bash
# Run full test suite
python -m pytest tests/ -v

# Check code style
black src/ tests/
flake8 src/ tests/

# Type checking
mypy src/

# Test documentation generation
python -c "import src.models.band; help(src.models.band.BandMetadata)"
```

## Feature Development

### Planning New Features

#### 1. Create Feature Proposal
Before implementing large features, create an issue with:

```markdown
## Feature Proposal: [Feature Name]

### Problem Statement
Describe the problem this feature solves.

### Proposed Solution
Explain your proposed approach.

### Implementation Plan
- [ ] Task 1: Specific implementation step
- [ ] Task 2: Another implementation step
- [ ] Task 3: Testing and documentation

### API Changes
Describe any API modifications needed.

### Breaking Changes
List any breaking changes (avoid if possible).

### Testing Strategy
Explain how the feature will be tested.
```

#### 2. Design Review
- **Architecture**: Ensure alignment with existing design
- **Performance**: Consider impact on large collections
- **Backwards Compatibility**: Minimize breaking changes
- **Testing**: Plan comprehensive test coverage

### Implementation Guidelines

#### 1. Start with Tests
```python
# Write tests first (TDD approach)
def test_new_feature_basic_functionality():
    """Test basic functionality of new feature."""
    # Arrange
    setup_test_data()
    
    # Act
    result = new_feature_function(test_input)
    
    # Assert
    assert result.success is True
    assert result.data == expected_data
```

#### 2. Implement Incrementally
- **Small Changes**: Make incremental, testable changes
- **Frequent Commits**: Commit working code frequently
- **Test Coverage**: Maintain test coverage throughout
- **Documentation**: Update documentation as you go

#### 3. Integration Points
Consider how your feature integrates with:
- **MCP Protocol**: Ensure MCP compliance
- **Data Models**: Use existing Pydantic models
- **Storage Layer**: Follow atomic operation patterns
- **Error Handling**: Use established error patterns

### Feature Documentation

Update relevant documentation:
- **API Reference**: Add new tools/resources/prompts
- **Usage Examples**: Provide real-world examples
- **Architecture**: Update if architectural changes made
- **CHANGELOG**: Document user-facing changes

## Bug Reports

### Creating Bug Reports

Use the following template for bug reports:

```markdown
## Bug Report

### Description
Brief description of the bug.

### Steps to Reproduce
1. Step one
2. Step two
3. Step three

### Expected Behavior
What should happen.

### Actual Behavior
What actually happens.

### Environment
- OS: [e.g., Windows 10, Ubuntu 20.04]
- Python Version: [e.g., 3.9.7]
- MCP Server Version: [e.g., 1.1.0]
- Collection Size: [e.g., 100 bands, 1000 albums]

### Error Logs
```
Paste relevant error logs here
```

### Additional Context
Any other relevant information.
```

### Investigating Bugs

#### 1. Reproduce Locally
```bash
# Create minimal reproduction case
python -c "
from src.tools.scanner import scan_music_folders
result = scan_music_folders('/test/path')
print(result)
"
```

#### 2. Debug Information
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable debug mode for investigation
from src.config import Config
config = Config(debug_mode=True)
```

#### 3. Fix with Tests
```python
def test_bug_fix_regression():
    """Test that ensures bug doesn't happen again."""
    # Arrange - recreate conditions that caused bug
    problematic_input = create_bug_scenario()
    
    # Act - perform operation that previously failed
    result = fixed_function(problematic_input)
    
    # Assert - verify bug is fixed
    assert result.success is True
    assert result.error is None
```

## Pull Request Process

### 1. Pre-submission Checklist

Before submitting a pull request:

- [ ] **Tests Pass**: All tests pass locally
- [ ] **Code Style**: Code follows style guidelines
- [ ] **Documentation**: Updated relevant documentation
- [ ] **Type Hints**: Added type hints to new functions
- [ ] **Error Handling**: Proper error handling implemented
- [ ] **Performance**: Considered performance impact
- [ ] **Backwards Compatibility**: No unnecessary breaking changes

### 2. Pull Request Template

```markdown
## Pull Request: [Brief Description]

### Changes Made
- Bullet point of change 1
- Bullet point of change 2
- Bullet point of change 3

### Issue Reference
Resolves #issue-number

### Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

### Documentation
- [ ] API documentation updated
- [ ] Usage examples added
- [ ] Code comments added

### Breaking Changes
- [ ] No breaking changes
- [ ] Breaking changes documented

### Review Checklist
- [ ] Code follows style guidelines
- [ ] Tests provide adequate coverage
- [ ] Documentation is clear and complete
- [ ] Performance impact considered
```

### 3. Review Process

#### Reviewer Guidelines
- **Constructive Feedback**: Provide helpful, specific feedback
- **Code Quality**: Check for maintainability and readability
- **Test Coverage**: Ensure adequate testing
- **Documentation**: Verify documentation completeness
- **Performance**: Consider performance implications

#### Addressing Feedback
```bash
# Make requested changes
git add .
git commit -m "address review feedback: improve error handling"

# Push updates
git push origin feature/your-feature-name
```

### 4. Merge Requirements

Pull requests must meet these requirements:
- **Two Approvals**: At least two maintainer approvals
- **CI Passing**: All continuous integration checks pass
- **Conflicts Resolved**: No merge conflicts with main branch
- **Documentation Updated**: All documentation current

## Community Guidelines

### Code of Conduct

We are committed to providing a welcoming and inclusive environment:

#### Our Standards
- **Respectful Communication**: Treat all contributors with respect
- **Inclusive Language**: Use inclusive language in code and communication
- **Constructive Feedback**: Provide helpful, actionable feedback
- **Professional Behavior**: Maintain professional standards

#### Unacceptable Behavior
- **Harassment**: Any form of harassment is not tolerated
- **Discrimination**: Discrimination based on any personal characteristic
- **Trolling**: Deliberate provocation or disruptive behavior
- **Spam**: Unsolicited or irrelevant contributions

### Getting Help

#### Communication Channels
- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Documentation**: Check existing documentation first
- **Code Comments**: Read inline documentation

#### Mentorship Program
We offer mentorship for new contributors:
- **Pairing Sessions**: Code with experienced contributors
- **Issue Guidance**: Help selecting appropriate issues
- **Code Review**: Detailed feedback on contributions
- **Best Practices**: Learn project conventions and patterns

### Recognition

We recognize contributors through:
- **Contributor List**: Recognition in project documentation
- **Release Notes**: Mention in release announcements
- **GitHub Recognition**: Appropriate labels and mentions
- **Community Highlights**: Feature outstanding contributions

## Development Tools

### Recommended IDE Setup

#### VS Code Configuration
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "100"],
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests/"]
}
```

#### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Configuration in .pre-commit-config.yaml
repos:
- repo: https://github.com/psf/black
  rev: 22.3.0
  hooks:
  - id: black
    args: [--line-length=100]
- repo: https://github.com/pycqa/flake8
  rev: 4.0.1
  hooks:
  - id: flake8
```

### Debugging Tools

#### Debug Configuration
```python
# debug_config.py
import logging

# Enable detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Enable MCP debug mode
from src.config import Config
debug_config = Config(
    debug_mode=True,
    log_level="DEBUG",
    performance_monitoring=True
)
```

## Thank You! 🎵

Thank you for contributing to the Music Collection MCP Server! Your contributions help make music collection management more intelligent and accessible for everyone.

For questions or additional help, please create an issue or start a discussion on GitHub. We're here to help and excited to see what you'll build! 