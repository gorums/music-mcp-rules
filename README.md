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

#### Phase 3: MCP Server Implementation (80% Complete)
- **✅ Tool 1 - scan_music_folders**: MCP tool for music collection scanning with FastMCP integration
- **✅ Tool 2 - get_band_list**: Enhanced band listing with filtering, pagination, and search capabilities
- **✅ Tool 3 - save_band_metadata**: Complete metadata storage with validation and schema documentation support
- **✅ Tool 4 - save_band_analyze**: Analysis data storage with album reviews, ratings, and similar bands
- **✅ Tool 5 - save_collection_insight**: Collection-wide insights and analytics storage
- **✅ Resource 1 - band://info/{band_name}**: Comprehensive band information in markdown format
- **✅ Resource 2 - collection://summary**: Complete collection overview with statistics and health metrics
- **✅ Prompt 1 - fetch_band_info**: Intelligent band information fetching with brave search integration
- **🔄 Prompts 2-4**: Remaining prompt templates (analyze_band, compare_bands, collection_insights)

### Key Capabilities Implemented

#### Complete MCP Server Implementation
- **FastMCP Framework**: Production MCP server using FastMCP library with error-level logging
- **5 Production Tools**: All core MCP tools implemented with comprehensive validation and error handling
- **2 Resource Handlers**: Dynamic band information and collection summary resources with markdown formatting
- **1 Prompt Template**: Intelligent band information fetching with configurable scopes and existing album integration
- **Proper Entrypoint**: `main.py` provides Python path setup, import resolution, and graceful error handling
- **Docker Integration**: Full containerized MCP server deployment

#### Enhanced Data Models (Pydantic v2)
- `Album`: Album metadata with track counts, years, missing detection
- `AlbumAnalysis`: Album-specific reviews and ratings (1-10 scale)
- `BandMetadata`: Complete band information with albums array and analysis integration
- `BandAnalysis`: Band reviews, ratings, and similar bands recommendations
- `CollectionIndex`: Music collection organization and statistics with health metrics
- `CollectionInsight`: Collection-wide analytics, recommendations, and health assessment
- `CollectionStats`: Automated statistics calculation with completion percentages

#### Advanced Music Directory Scanner
- Recursive band and album folder discovery with incremental update support
- Music file detection (9+ formats: .mp3, .flac, .wav, .aac, .m4a, .ogg, .wma, .mp4, .m4p)
- Missing album detection by comparing metadata to folder structure
- Collection index preservation during scanning (maintains metadata and analysis data)
- Smart update detection based on folder timestamps
- UTF-8 encoding support for international characters
- Optimized scanning for large collections with caching

#### Production-Ready Storage Management
- **Atomic File Operations**: Corruption-proof writes with `AtomicFileWriter`
- **File Locking**: Concurrent access protection with `file_lock()`
- **Backup & Recovery**: Automatic timestamped backups with cleanup
- **JSON Storage**: Unicode-safe serialization with error handling
- **Metadata Operations**: Complete CRUD operations for all data types
- **Analysis Preservation**: Smart analyze data preservation during metadata updates
- **Collection Synchronization**: Automatic stats updates and index maintenance

#### Comprehensive Resource System
- **Band Information**: Dynamic markdown generation with complete band details, album listings, analysis sections, and missing album tracking
- **Collection Summary**: Rich collection overview with statistics, band distribution analysis, health assessment, and recommendations
- **Status Indicators**: Smart badges and status indicators for collection health, completion percentage, and metadata coverage
- **Error Handling**: Graceful handling of missing data with helpful error messages and getting started guidance

#### Advanced Prompt System
- **fetch_band_info**: Configurable prompt with three information scopes (basic, full, albums_only)
- **Existing Albums Integration**: Smart missing album detection using existing collection data
- **Search Strategy Guidelines**: Optimized for Wikipedia, AllMusic, and official sources
- **JSON Schema Examples**: Complete output format documentation for AI agents
- **Validation Rules**: Built-in data quality validation and formatting guidelines

### Test Coverage
- **285 tests passing (100% success rate)**
- **Test Categories**: 
  - Models (64 tests): Complete Pydantic model validation
  - Scanner (31 tests): Music directory scanning and indexing
  - Storage (46 tests): File operations and metadata management
  - Cache (19 tests): Cache validation and management
  - MCP Server (75 tests): All tools, resources, and validation
  - Resources (66 tests): Markdown generation and error handling
  - Prompts (17 tests): Template generation and parameter handling
- **Docker-based testing** with isolated environment
- **Comprehensive scenarios**: Normal usage, edge cases, failure scenarios, integration tests
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

### Tool 2: get_band_list
Enhanced band listing with filtering, searching, and pagination capabilities.

**Parameters:**
- `page` (int): Page number for pagination (default: 1)
- `page_size` (int): Number of results per page (default: 50, max: 100)
- `search` (str): Search by band or album name
- `filter_genre` (str): Filter by specific genre
- `filter_has_metadata` (bool): Filter bands with/without metadata
- `filter_missing_albums` (bool): Filter bands with missing albums
- `sort_by` (str): Sort by "name", "albums_count", "completion_percentage"
- `include_albums` (bool): Include detailed album information

**Returns:**
```json
{
  "status": "success",
  "results": {
    "bands": [
      {
        "band_name": "Pink Floyd",
        "albums_count": 15,
        "missing_albums_count": 14,
        "completion_percentage": 6.67,
        "has_metadata": true,
        "has_analysis": false,
        "genres": ["Progressive Rock"],
        "albums": [...]
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 3,
      "total_bands": 150,
      "page_size": 50
    }
  }
}
```

### Tool 3: save_band_metadata
Store comprehensive band metadata with validation and analyze preservation.

**Parameters:**
- `band_name` (str): Name of the band (required)
- `metadata` (dict): Complete band metadata following BandMetadata schema
- `clear_analyze` (bool): Whether to clear existing analysis data (default: false)

**Returns:**
```json
{
  "status": "success",
  "message": "Band metadata saved successfully for Pink Floyd",
  "band_name": "Pink Floyd",
  "analyze_preserved": true,
  "analyze_action": "preserved_existing_analyze_data",
  "files_created": [".band_metadata.json"],
  "collection_updated": true,
  "tool_info": {
    "tool_name": "save_band_metadata",
    "version": "1.1.0"
  }
}
```

### Tool 4: save_band_analyze
Store band and album analysis with reviews, ratings, and similar bands.

**Parameters:**
- `band_name` (str): Name of the band (required)
- `analysis` (dict): Analysis data following BandAnalysis schema
- `analyze_missing_albums` (bool): Include missing albums in analysis (default: false)

**Returns:**
```json
{
  "status": "success",
  "message": "Band analysis saved successfully for Pink Floyd",
  "band_name": "Pink Floyd",
  "albums_analyzed": 3,
  "missing_albums_included": false,
  "files_updated": [".band_metadata.json"],
  "collection_updated": true,
  "tool_info": {
    "tool_name": "save_band_analyze",
    "version": "1.0.0"
  }
}
```

### Tool 5: save_collection_insight
Store collection-wide insights, recommendations, and health metrics.

**Parameters:**
- `insights` (list): Collection insights and observations
- `recommendations` (list): Recommendations for collection improvement
- `top_rated_bands` (list): List of top-rated bands
- `suggested_purchases` (list): Suggested albums to purchase
- `collection_health` (dict): Health metrics (status, metadata_coverage, completion_rate)

**Returns:**
```json
{
  "status": "success",
  "message": "Collection insights saved successfully",
  "insights_count": 5,
  "recommendations_count": 3,
  "files_updated": [".collection_index.json"],
  "collection_updated": true,
  "tool_info": {
    "tool_name": "save_collection_insight",
    "version": "1.0.0"
  }
}
```

## MCP Resources

### Resource 1: band://info/{band_name}
Provides comprehensive band information in markdown format.

**Example URI:** `band://info/Pink Floyd`

**Returns:** Rich markdown document with:
- Band overview with formation details and completion status
- Complete album listing with track counts and availability
- Missing albums section with clear indicators
- Analysis section with reviews and ratings
- Collection statistics and metadata information

### Resource 2: collection://summary
Provides complete collection overview with statistics and health assessment.

**Returns:** Comprehensive markdown document with:
- Collection overview with key statistics and status badges
- Band distribution analysis (large/medium/small collections)
- Missing albums analysis with completion percentages
- Collection insights and health recommendations
- Metadata information with scan timestamps

## MCP Prompts

### Prompt 1: fetch_band_info
Intelligent band information fetching with brave search integration.

**Parameters:**
- `band_name` (str): Name of the band to fetch information for
- `information_scope` (str): Scope of information ("basic", "full", "albums_only")
- `existing_albums` (list): Current albums in collection for missing detection

**Features:**
- Three configurable information scopes for different use cases
- Integration with existing album data for missing album detection
- Search strategy guidelines for reliable sources
- Complete JSON schema examples for output format
- Built-in validation rules and data quality guidelines

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

## Troubleshooting

### MCP Client Cannot See Resources/Tools

**Issue**: MCP clients (Cline, Claude Desktop) show connection errors or cannot see resources like `band://info/{band_name}`, tools, or prompts.

**Solution**: This is a common issue with FastMCP-based servers. The problem is that FastMCP outputs INFO-level logs during initialization, which MCP clients interpret as errors.

**Fix Applied**: The server is already configured with `log_level="ERROR"` to suppress these initialization logs. If you still see issues:

1. **Check Client Logs**: Look for actual errors vs. initialization messages
2. **Test Functionality**: Often tools work correctly despite appearing as "errors" in the UI
3. **Retry Connection**: Sometimes reconnecting resolves UI display issues

**Technical Details**: MCP clients expect clean output but FastMCP logs protocol messages like:
```
INFO Processing request of type ListToolsRequest
INFO Processing request of type ListResourcesRequest  
INFO Processing request of type ListResourceTemplatesRequest
```

These are normal initialization messages, not actual errors.

## Next Steps

### Phase 3: Complete MCP Server Implementation (20% Remaining)
- **Prompt 2: analyze_band** - Comprehensive band analysis prompt template with brave search integration
- **Prompt 3: compare_bands** - Template for comparing multiple bands with analysis
- **Prompt 4: collection_insights** - Generate insights about the entire collection

### Phase 4: Advanced Features & Optimization
- **Enhanced Testing**: Integration testing with real MCP clients and large collections
- **Performance Optimization**: Parallel processing for large collections and memory optimization
- **External API Integration**: Integration with music databases (MusicBrainz, Last.fm)
- **Advanced Analytics**: Collection trend analysis and recommendation engine
- **Export Functionality**: CSV, JSON export with comprehensive filtering
- **Missing Album Recommendations**: Smart suggestions based on band discography

### Phase 5: User Experience & Documentation
- **Interactive Setup**: Guided configuration and collection validation
- **Advanced Filtering**: Genre-based analytics and year-based collection insights
- **Client Integration Examples**: Complete examples for Claude Desktop, Cline, and other MCP clients
- **Performance Benchmarks**: Documentation for large collection handling (10,000+ bands)
- **Troubleshooting Guide**: Common issues and solutions for MCP client integration

For detailed development tasks and progress, see `docs/TASKS.md`.
