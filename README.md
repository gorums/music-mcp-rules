# Music Collection MCP Server

A Model Context Protocol (MCP) server that provides intelligent access to your local music collection through JSON-based metadata management, band discovery, and intelligent querying capabilities.

## Project Status

### ✅ Completed Features

#### Phase 1: Foundation (100% Complete)
- **Configuration Management**: Environment variable handling with validation
- **Core Data Models**: Pydantic v2 models for bands, albums, collections with full validation
- **Data Migration**: Schema migration tools and data validation utilities

#### Phase 2: File System Operations (100% Complete)
- **✅ Music Directory Scanner**: Full music collection scanning with album discovery and missing album detection
- **✅ Local Storage Management**: Production-ready atomic file operations, locking, and backup/recovery
- **✅ Cache Management**: Production-ready cache management with intelligent expiration

#### Phase 3: MCP Server Implementation (20% Complete)
- **✅ Tool 1 - scan_music_folders**: MCP tool for music collection scanning with FastMCP integration
- **🔄 Tool 2-5**: Remaining MCP tools (in progress)
- **🔄 Resources**: MCP resource handlers (in progress)
- **🔄 Prompts**: MCP prompt templates (in progress)

### Key Capabilities Implemented

#### MCP Server Implementation
- **FastMCP Framework**: Production MCP server using FastMCP library
- **Tool 1 - scan_music_folders**: Comprehensive music scanning tool with:
  - `force_rescan` option to bypass cache
  - `include_missing_albums` for missing album detection
  - Structured JSON responses with status, results, and tool info
- **Proper Entrypoint**: `main.py` provides Python path setup, import resolution, and graceful error handling
- **Docker Integration**: Full containerized MCP server deployment

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
- **143 tests passing (100% success rate)**
- **Test Categories**: Models (64 tests), Scanner (31 tests), Storage (30 tests), Cache (19 tests), MCP Server (17 tests)
- **Docker-based testing** with isolated environment
- **Comprehensive scenarios**: Normal usage, edge cases, failure scenarios
- **Zero pytest warnings** - all tests use proper assertion patterns

## Configuration Management

The server uses environment variables for configuration. You can set these in a `.env` file in the project root.

### Required Configuration
- `MUSIC_ROOT_PATH`: Path to the root music directory (required)

### Optional Configuration  
- `CACHE_DURATION_DAYS`: Cache expiration in days (default: 30)
- `LOG_LEVEL`: Logging level (default: INFO)


The configuration is validated at startup. See `src/config.py` for details.

## Project Architecture

### Folder Structure
```
├── main.py                     # MCP server entrypoint (proper Python path setup)
├── src/
│   ├── music_mcp_server.py    # FastMCP server implementation
│   ├── config.py              # Configuration management
│   ├── models/                # Pydantic data models
│   │   ├── band.py           # Band and album models
│   │   ├── collection.py     # Collection and statistics models
│   └── tools/                # Core functionality
│       ├── scanner.py        # Music directory scanning
│       ├── storage.py        # Local storage operations
│       ├── cache.py          # Cache management
│       └── metadata.py       # Metadata management
├── tests/                     # Comprehensive test suite
├── docs/                      # Project documentation
└── Dockerfile                 # Production container setup
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
- Docker (for testing and deployment)

### Running the MCP Server

#### Docker Deployment
```bash
# Build the container
docker build -t music-mcp-server .

# Run the MCP server
docker run -d --name music-mcp-container -v "D:\Projects\music-catalog-mcp\test_music_collection:/music" -e "MUSIC_ROOT_PATH=/music" -it music-mcp-server  
```

## Schema Discovery and Validation

### How MCP Clients Can Discover Correct Metadata Structure

The server provides multiple ways for MCP clients to discover and validate the correct metadata structure:

#### 1. Schema Documentation Resource
```
schema://band_metadata
```
**Purpose**: Get complete BandMetadata schema documentation in markdown format
**Contains**: 
- Required and optional fields with types and examples
- Complete JSON example with proper structure
- Common validation errors table
- Field name corrections guide

#### 2. Validation Tool (Dry-Run)
```json
{
  "tool": "validate_band_metadata_tool",
  "arguments": {
    "band_name": "Pink Floyd",
    "metadata": { ... }
  }
}
```
**Purpose**: Validate metadata structure WITHOUT saving anything
**Returns**:
- Validation status (valid/invalid)
- Detailed error descriptions
- Actionable suggestions to fix issues
- Example corrections for common errors
- Points to schema documentation resource

#### 3. Enhanced Error Messages
The `save_band_metadata_tool` provides comprehensive error reporting when validation fails:
```json
{
  "status": "error",
  "error": "Metadata validation failed: ...",
  "validation_results": {
    "schema_valid": false,
    "validation_errors": ["Specific field errors"],
    "suggestions": ["How to fix each error"]
  }
}
```

### Common Schema Issues and Solutions

| ❌ Incorrect | ✅ Correct | Issue |
|-------------|-----------|--------|
| `"genres": [...]` | `"genre": [...]` | Wrong field name |
| `formed_year: 1965` | `"formed": "1965"` | Integer vs string, wrong name |
| `members: {former: [...], current: [...]}` | `members: [...]` | Nested vs flat structure |
| `"notable_albums": [...]` | `"albums": [...]` | Wrong field name |
| `year: 1973` | `"year": "1973"` | Integer vs string in albums |
| `tracks_count: -1` | `tracks_count: 8` | Negative numbers not allowed |
| `rate: 11` | `rate: 10` | Rating must be 0-10 |

### Client Workflow for Schema Discovery

1. **Test Structure**: Use `validate_band_metadata_tool` to test your metadata structure
2. **Fix Errors**: Follow the suggestions and example corrections provided
3. **Verify**: Re-validate until status is "valid"
4. **Save**: Use `save_band_metadata_tool` when validation passes
5. **Reference**: Access `schema://band_metadata` resource for complete documentation

### Example: Converting Incorrect to Correct Structure

**❌ Original (Incorrect):**
```json
{
  "genres": ["Progressive Rock"],
  "formed_year": 1965,
  "members": {
    "former": ["David Gilmour", "Roger Waters"],
    "current": []
  },
  "notable_albums": [
    {
      "type": "studio",
      "year": 1973,
      "title": "The Dark Side of the Moon"
    }
  ],
  "formed_location": "London, England"
}
```

**✅ Corrected:**
```json
{
  "band_name": "Pink Floyd",
  "formed": "1965",
  "genre": ["Progressive Rock"],
  "origin": "London, England",
  "members": ["David Gilmour", "Roger Waters"],
  "description": "Legendary progressive rock band...",
  "albums": [
    {
      "album_name": "The Dark Side of the Moon",
      "year": "1973",
      "tracks_count": 10,
      "missing": false
    }
  ]
}
```

## MCP Client Integration

**MCP Client Configuration:**
```json
{
  "mcpServers": {
    "music-collection": {
      "command": "docker",
      "args": [
        "run", "--rm", "--interactive",
        "-v", "/path/to/your/music:/music",
        "-e", "MUSIC_ROOT_PATH=/music",
        "-e", "CACHE_DURATION_DAYS=30"
        "music-mcp-server"
      ],
      "cwd": "/path/to/music-catalog-mcp"
    }
  }
}
```

### MCP Server Capabilities

Once connected, your MCP client will have access to:

**Tools:**
- `scan_music_folders`: Scan and analyze your music collection

**Resources:** (Coming in Tool 2-5)
- `collection/summary`: Overview of your music collection
- `band/{band_name}`: Detailed band information
- `album/{band_name}/{album_name}`: Specific album details

**Prompts:** (Coming in Tool 2-5)
- Music discovery assistance
- Collection analysis guidance
- Missing album recommendations

### Example MCP Tool Call
```json
{
  "method": "tools/call",
  "params": {
    "name": "scan_music_folders",
    "arguments": {
      "force_rescan": true
    }
  }
}
```

## MCP Tools

### Tool 1: scan_music_folders
Comprehensive music collection scanning tool.

**Parameters:**
- `force_rescan` (bool): Bypass cache and force fresh scan
- `include_missing_albums` (bool): Include missing album detection

**Returns:**
```json
{
  "status": "success",
  "results": {
    "total_bands": 150,
    "total_albums": 850,
    "music_files_found": 12500,
    "missing_albums": 25,
    "scan_duration": "15.2 seconds",
    "cache_used": true
  },
  "tool_info": {
    "tool_name": "scan_music_folders",
    "version": "1.0.0"
  }
}
```

## Usage Examples

### MCP Tool Usage
```python
# Via MCP client
{
  "method": "tools/call",
  "params": {
    "name": "scan_music_folders",
    "arguments": {
      "force_rescan": true,
      "include_missing_albums": true
    }
  }
}
```

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
- **Cache Management**: Intelligent cache expiration and refresh strategies

## Next Steps

### Phase 3: Complete MCP Server Implementation
- Tool 2-5 implementation for remaining MCP functionality
- Resource handlers for band information and collection summaries
- Prompt templates for AI-assisted music discovery

### Phase 4: Advanced Features
- Integration with external music APIs
- Collection analytics and reporting
- Missing album recommendation system
- Advanced search and filtering capabilities

For detailed development tasks and progress, see `docs/TASKS.md`.
