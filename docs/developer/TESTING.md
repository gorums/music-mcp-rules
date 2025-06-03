# Testing Guide

This guide covers how to run tests, write new tests, and maintain test quality for the Music Collection MCP Server.

## 🧪 Test Overview

The project uses **Pytest** with **Docker** for testing to ensure consistent environments and reliable test execution.

### Test Structure
```
tests/
├── fixtures/           # Test data and fixtures
├── test_models/        # Data model tests
├── test_tools/         # MCP tool tests
├── test_resources/     # MCP resource tests
├── test_prompts/       # MCP prompt tests
├── test_integration/   # End-to-end integration tests
└── conftest.py         # Pytest configuration and shared fixtures
```

## 🚀 Running Tests

### Quick Test Run
```bash
# Build test container
docker build -f Dockerfile.test -t music-mcp-tests .

# Run all tests
docker run --rm music-mcp-tests python -m pytest . -v
```

### Development Testing
```bash
# Run tests with coverage
docker run --rm music-mcp-tests python -m pytest . -v --cov=src --cov-report=html

# Run specific test file
docker run --rm music-mcp-tests python -m pytest tests/test_tools/test_scan_music_folders.py -v

# Run tests matching pattern
docker run --rm music-mcp-tests python -m pytest -k "test_scan" -v

# Run with detailed output
docker run --rm music-mcp-tests python -m pytest . -v -s
```

### Local Python Testing (Alternative)
```bash
# Set up environment
export MUSIC_ROOT_PATH="./test_music_collection"
export LOG_LEVEL="DEBUG"

# Install test dependencies
pip install -r requirements.txt
pip install pytest pytest-cov pytest-mock

# Run tests
python -m pytest . -v
```

## 📋 Test Categories

### 1. Unit Tests
Test individual components in isolation.

**Location**: `tests/test_models/`, `tests/test_tools/`

**Example**:
```python
def test_album_type_validation():
    """Test that album type validation works correctly."""
    album = Album(
        album_name="Test Album",
        type=AlbumType.ALBUM,
        missing=False
    )
    assert album.type == AlbumType.ALBUM
    
    # Test invalid type
    with pytest.raises(ValidationError):
        Album(
            album_name="Test Album",
            type="InvalidType",
            missing=False
        )
```

### 2. Integration Tests
Test complete workflows and component interactions.

**Location**: `tests/test_integration/`

**Example**:
```python
def test_scan_and_save_workflow(temp_music_dir):
    """Test complete scan and save workflow."""
    # Create test music structure
    create_test_band_structure(temp_music_dir, "Test Band")
    
    # Scan collection
    scan_result = scan_music_folders(incremental=False)
    assert scan_result.bands_found > 0
    
    # Save metadata
    metadata = BandMetadata(
        band_name="Test Band",
        albums=[Album(album_name="Test Album", missing=False)]
    )
    save_result = save_band_metadata_tool(metadata)
    assert save_result.success
```

### 3. File System Tests
Test file operations with mock file systems.

**Example**:
```python
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

def test_scan_with_mock_structure(mock_music_structure):
    """Test scanning with mock file structure."""
    with patch.dict(os.environ, {"MUSIC_ROOT_PATH": str(mock_music_structure)}):
        result = scan_music_folders()
        assert "Pink Floyd" in result.bands_found
```

### 4. MCP Protocol Tests
Test MCP protocol compliance and message handling.

**Example**:
```python
def test_mcp_tool_registration():
    """Test that all MCP tools are properly registered."""
    server = create_mcp_server()
    tools = server.list_tools()
    
    expected_tools = [
        "scan_music_folders",
        "get_band_list_tool",
        "save_band_metadata_tool",
        "save_band_analyze_tool",
        "save_collection_insight_tool",
        "validate_band_metadata_tool"
    ]
    
    for tool_name in expected_tools:
        assert any(tool.name == tool_name for tool in tools)
```

## 🔧 Writing New Tests

### Test Naming Convention
- Test files: `test_<component>.py`
- Test functions: `test_<functionality>_<scenario>()`
- Test classes: `Test<Component>`

### Required Test Cases
For each new feature, include:

1. **Expected Use Case**: Normal operation test
2. **Edge Case**: Boundary conditions
3. **Failure Case**: Error handling

**Example**:
```python
class TestBandMetadataValidation:
    """Test band metadata validation functionality."""
    
    def test_valid_metadata_passes_validation(self):
        """Test that valid metadata passes validation."""
        metadata = BandMetadata(
            band_name="Test Band",
            formed="1970",
            genres=["Rock"],
            albums=[]
        )
        result = validate_band_metadata_tool(metadata)
        assert result.is_valid
    
    def test_empty_band_name_fails_validation(self):
        """Test that empty band name fails validation."""
        metadata = BandMetadata(
            band_name="",
            albums=[]
        )
        result = validate_band_metadata_tool(metadata)
        assert not result.is_valid
        assert "band_name" in result.errors
    
    def test_invalid_album_type_fails_validation(self):
        """Test that invalid album type fails validation."""
        with pytest.raises(ValidationError):
            Album(
                album_name="Test Album",
                type="InvalidType",
                missing=False
            )
```

### Using Fixtures

**Common Fixtures** (in `conftest.py`):
```python
@pytest.fixture
def temp_music_dir(tmp_path):
    """Create temporary music directory."""
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
                type=AlbumType.ALBUM,
                missing=False
            )
        ]
    )

@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch, tmp_path):
    """Set up test environment variables."""
    test_music_path = tmp_path / "test_music"
    test_music_path.mkdir()
    monkeypatch.setenv("MUSIC_ROOT_PATH", str(test_music_path))
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
```

## 📊 Test Coverage

### Coverage Requirements
- **Minimum**: 80% overall coverage
- **Critical Components**: 95% coverage (models, tools)
- **New Features**: 100% coverage required

### Checking Coverage
```bash
# Generate coverage report
docker run --rm music-mcp-tests python -m pytest . --cov=src --cov-report=html --cov-report=term

# View HTML report
# Coverage report will be in htmlcov/index.html
```

### Coverage Exclusions
```python
# In .coveragerc or pyproject.toml
[tool.coverage.run]
omit = [
    "*/tests/*",
    "*/venv/*",
    "setup.py",
    "*/migrations/*"
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError"
]
```

## 🐛 Debugging Tests

### Running Tests in Debug Mode
```bash
# Run with pdb on failure
docker run --rm -it music-mcp-tests python -m pytest . --pdb

# Run with detailed output
docker run --rm music-mcp-tests python -m pytest . -v -s --tb=long

# Run single test with debugging
docker run --rm -it music-mcp-tests python -m pytest tests/test_tools/test_scan.py::test_scan_empty_directory -v -s --pdb
```

### Common Debugging Techniques
```python
def test_with_debugging():
    """Example test with debugging techniques."""
    # Use print statements (with -s flag)
    print(f"Debug: variable value = {variable}")
    
    # Use pytest's built-in debugging
    import pytest
    pytest.set_trace()  # Breakpoint
    
    # Use logging
    import logging
    logging.debug("Debug message")
    
    # Assert with custom messages
    assert condition, f"Expected {expected}, got {actual}"
```

## 🔄 Continuous Integration

### GitHub Actions (Example)
```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build test container
        run: docker build -f Dockerfile.test -t music-mcp-tests .
      - name: Run tests
        run: docker run --rm music-mcp-tests python -m pytest . -v --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: tests
        name: Run tests
        entry: docker run --rm music-mcp-tests python -m pytest . -v
        language: system
        pass_filenames: false
        always_run: true
```

## 📝 Test Documentation

### Docstring Format
```python
def test_complex_functionality():
    """
    Test complex functionality with multiple scenarios.
    
    This test verifies that:
    1. Function handles normal input correctly
    2. Function raises appropriate errors for invalid input
    3. Function maintains state consistency
    
    Given:
        - A valid music collection structure
        - Proper environment configuration
    
    When:
        - The scan function is called
    
    Then:
        - All bands are discovered
        - Metadata is properly structured
        - No errors are raised
    """
    # Test implementation
```

### Test Comments
```python
def test_album_type_detection():
    """Test album type detection from folder names."""
    # Arrange: Set up test data
    test_folders = [
        "1973 - The Dark Side of the Moon",
        "1985 - Live at Wembley (Live)",
        "1996 - Greatest Hits (Compilation)"
    ]
    
    # Act: Run the detection
    results = [detect_album_type(folder) for folder in test_folders]
    
    # Assert: Verify results
    assert results[0] == AlbumType.ALBUM
    assert results[1] == AlbumType.LIVE
    assert results[2] == AlbumType.COMPILATION
```

## 🚨 Test Maintenance

### Regular Maintenance Tasks
1. **Update test data** when schema changes
2. **Review test coverage** monthly
3. **Clean up obsolete tests** when features are removed
4. **Update fixtures** when dependencies change

### Performance Testing
```python
import time
import pytest

def test_scan_performance():
    """Test that scanning completes within reasonable time."""
    start_time = time.time()
    
    result = scan_music_folders()
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Should complete within 30 seconds for test collection
    assert duration < 30, f"Scan took {duration:.2f} seconds, expected < 30"
```

---

*Remember: Good tests are the foundation of reliable software. Write tests first, keep them simple, and maintain them regularly!* 🧪 