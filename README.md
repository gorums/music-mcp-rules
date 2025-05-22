# Music Collection MCP Server

A Model Context Protocol (MCP) server that provides intelligent access to your local music collection through JSON-based metadata management, band discovery, and intelligent querying capabilities.

## Project Status

### ✅ Completed Features

#### Phase 1: Foundation (100% Complete)
- **Configuration Management**: Environment variable handling with validation
- **Core Data Models**: Pydantic v2 models for bands, albums, collections with full validation
- **Data Migration**: Schema migration tools and data validation utilities

#### Phase 2: File System Operations (66% Complete)
- **✅ Music Directory Scanner**: Full music collection scanning with album discovery and missing album detection
- **✅ Local Storage Management**: Production-ready atomic file operations, locking, and backup/recovery
- **🔄 Cache Management**: (Pending - Task 2.3)

### 🔄 In Progress
- **Phase 3: MCP Server Implementation** - Tools, Resources, and Prompts

### Key Capabilities Implemented

#### Data Models (Pydantic v2)
- `Album`: Album metadata with track counts, years, missing detection
- `BandMetadata`: Complete band information with albums array
- `CollectionIndex`: Music collection organization and statistics
- `BandAnalysis` & `AlbumAnalysis`: Review and rating system (1-10 scale)
- `CollectionInsight`: Collection-wide analytics and health metrics

#### Music Directory Scanner
- Recursive band and album folder discovery
- Music file detection (9+ formats: .mp3, .flac, .wav, .aac, .m4a, .ogg, .wma, .mp4, .m4p)
- Missing album detection by comparing metadata to folder structure
- Collection index creation and management
- UTF-8 encoding support for international characters

#### Local Storage Management
- **Atomic File Operations**: Corruption-proof writes with `AtomicFileWriter`
- **File Locking**: Concurrent access protection with `file_lock()`
- **Backup & Recovery**: Automatic timestamped backups with cleanup
- **JSON Storage**: Unicode-safe serialization with error handling
- **Metadata Operations**: `save_band_metadata()`, `save_band_analyze()`, `save_collection_insight()`
- **Band Operations**: `get_band_list()`, `load_band_metadata()`, `load_collection_index()`

### Test Coverage
- **122 tests passing (100% success rate)**
- **Test Categories**: Models (64 tests), Scanner (31 tests), Storage (30 tests), Metadata (9 tests)
- **Docker-based testing** with isolated environment
- **Comprehensive scenarios**: Normal usage, edge cases, failure scenarios

## Configuration Management

The server uses environment variables for configuration. You can set these in a `.env` file in the project root.

### Required Configuration
- `MUSIC_ROOT_PATH`: Path to the root music directory (required)

### Optional Configuration  
- `CACHE_DURATION_DAYS`: Cache expiration in days (default: 30)

Example `.env` file:
```
MUSIC_ROOT_PATH=/path/to/your/music/collection
CACHE_DURATION_DAYS=30
```

The configuration is validated at startup. See `src/config.py` for details.

## Project Architecture

### Folder Structure
```
src/
├── config.py           # Configuration management
├── models/             # Pydantic data models
│   ├── band.py        # Band and album models
│   ├── collection.py  # Collection and statistics models
└── tools/             # Core functionality
    ├── scanner.py     # Music directory scanning
    ├── storage.py     # Local storage operations
    └── metadata.py    # Metadata management

tests/                  # Comprehensive test suite
docs/                   # Project documentation
```

### Data Storage Format
```
music_root/
├── Band Name 1/
│   ├── Album 1/
│   ├── Album 2/
│   └── .band_metadata.json    # Band metadata and analysis
├── Band Name 2/
│   └── .band_metadata.json
└── .collection_index.json      # Collection overview and statistics
```

## Development Setup

### Prerequisites
- Python 3.8+
- Docker (for testing)

### Installation
```bash
# Clone repository
git clone <repo-url>
cd music-catalog-mcp

# Install dependencies
pip install -r requirements.txt

# Set up configuration
cp .env.example .env
# Edit .env with your music collection path
```

### Testing
```bash
# Build test environment
docker build -t music-mcp-tests -f Dockerfile.test .

# Run all tests
docker run --rm music-mcp-tests pytest -v

# Run specific test modules
docker run --rm music-mcp-tests pytest tests/test_storage.py -v
```

## Usage Examples

### Basic Music Collection Scanning
```python
from src.tools.scanner import scan_music_folders
from src.config import Config

config = Config()
result = scan_music_folders()
print(f"Found {result['total_bands']} bands with {result['total_albums']} albums")
```

### Band Metadata Management
```python
from src.tools.storage import save_band_metadata, load_band_metadata
from src.models import BandMetadata

# Load existing metadata
metadata = load_band_metadata("Pink Floyd")

# Save new metadata
new_metadata = BandMetadata(
    band_name="The Beatles",
    formed="1960",
    genre=["Rock", "Pop"],
    origin="Liverpool, England"
)
result = save_band_metadata("The Beatles", new_metadata)
```

## Security Features

### File System Security
- **Path Validation**: Protection against directory traversal attacks
- **Atomic Operations**: Corruption-proof file writes
- **File Locking**: Concurrent access prevention
- **Backup System**: Automatic recovery capabilities

### Data Integrity
- **Schema Validation**: Pydantic models ensure data consistency
- **Unicode Support**: Proper handling of international characters
- **Error Recovery**: Graceful handling of corrupted data

## Performance Features

### Optimization
- **Efficient Scanning**: Smart folder filtering and parallel-ready architecture
- **Memory Management**: Context managers and efficient file operations
- **Backup Cleanup**: Automatic removal of old backup files
- **Fast Validation**: Optimized schema validation and serialization

## Next Steps

### Phase 3: MCP Server Implementation
- Tool implementation for MCP integration
- Resource handlers for band information and collection summaries
- Prompt templates for AI-assisted music discovery

### Phase 4: Advanced Features
- Cache management with intelligent expiration
- Integration with external music APIs
- Collection analytics and reporting
- Missing album recommendation system

For detailed development tasks and progress, see `docs/TASKS.md`.
