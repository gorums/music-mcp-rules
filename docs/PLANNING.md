# Music Collection MCP Server - Instructions

## Project Overview

This project implements a Model Context Protocol (MCP) server that provides intelligent access to your local music collection. The server exposes tools, resources, and prompts to discover, analyze, and retrieve information about bands and artists based on your folder structure.

## Scope

### Core Functionality
- **Band Discovery**: Automatically extract band names from folder structure
- **Metadata Management**: Store and retrieve band information in local JSON files
- **Information Enrichment**: Fetch comprehensive band data using brave search MCP
- **Intelligent Querying**: Provide context-aware prompts for music exploration

### Key Features
- **No Database Dependency**: All data stored in JSON files within music folders
- **Folder-Based Architecture**: Uses existing music directory structure
- **External API Integration**: Fetches band information using brave search MCP
- **Caching Strategy**: Stores fetched data locally to minimize API calls
- **Flexible Queries**: Support for various music metadata searches

## Technical Architecture

### Technology Stack
- **Language**: Python 3.8+
- **Framework**: MCP Python SDK
- **Transport**: JSON-RPC over stdio
- **Storage**: Local JSON files (no database)
- **File Operations**: Python's built-in `os`, `json`, and `pathlib` modules

### MCP Components

#### Tools (4 tools)
1. **`scan_music_folders`** - Discovers all band folders in the music directory including the albums inside the band folder
2. **`get_band_list`** - Returns list of all discovered bands and albums that we have for each band. 
3. **`save_band_metadata`** - Stores band information in local JSON files
3. **`save_band_analyze`** - Stores band information in local JSON files
4. **`save_collection_insight`** - Stores insights about the entire collection

#### Resources (2 resources)
1. **`band_info/{band_name}`** - Provides detailed information for a specific band in a markdown format using the .band_metadata.json
2. **`collection_summary`** - Overview of entire music collection statistics using the .collection_index.json

#### Prompts (3 prompts)
1. **`fetch_band_info`** - Prompt template to retrieves band information using brave search MCP
2. **`analyze_band`** - Comprehensive band analysis prompt template, including similar bands, review about the band and each album using brave search MCP
3. **`compare_bands`** - Template for comparing multiple bands
4. **`collection_insights`** - Generate insights about the entire collection

### Data Structure

#### Folder Organization
```
music_root/
├── Band Name 1/
│   ├── Album 1/
│   ├── Album 2/
│   └── .band_metadata.json
├── Band Name 2/
│   ├── Album 1/
│   └── .band_metadata.json
└── .collection_index.json
```

#### Metadata Schema
```json
{
  "band_name": "string",
  "formed": "YYYY",
  "genres": ["string"],
  "origin": "string",
  "members": ["string"],
  "albums_count": number,
  "description": "string",
  "albums": [
              "album": {
                     "album_name": "string",
                     "missing": boolean, // true if the album is not in the local folder
                     "tracks_count": number,
                     "duration": "string", // "67min"
                     "year": "YYYY",
                     "genres": ["string"],
              }
       ],
  "last_updated": "ISO datetime", 
  "analyze":  {       
       "review": "string",
       "rate": number // from 1 to 10
       "albums": [
              "album": {
                     "review": "string",
                     "rate": number // from 1 to 10
              }
       ],
       "similar_bands": ["string"],
  }
}
```

## Configuration

### Environment Variables
- `MUSIC_ROOT_PATH`: Path to the root music directory
- `CACHE_DURATION_DAYS`: How long to cache band metadata (default: 30)

### MCP Client Integration
The server will be configured as a local MCP server in Claude Desktop or other MCP clients:

```json
{
  "mcpServers": {
    "music-collection": {
      "command": "python",
      "args": ["/path/to/main.py"],
      "env": {
        "MUSIC_ROOT_PATH": "/path/to/your/music"
      }
    }
  }
}
```

## API Integration Strategy

### Fallback Strategy
1. Check local cache first (`.band_metadata.json`)
2. Query brave search MCP if cache is stale or missing
3. Store results locally for future use
4. Handle API failures gracefully with cached data

## Security Considerations

### File System Access
- Read-only access to music directories
- Write access only to `.band_metadata.json` files and .collection_index.json
- Input validation for all file paths
- Protection against directory traversal attacks

## Performance Optimization

### Caching Strategy
- Local JSON file caching
- Configurable cache expiration
- Batch processing for large collections

### Resource Management
- Efficient file system traversal
- Memory-conscious data processing
- Error recovery mechanisms

## Extensibility

### Future Enhancements
- Album-level metadata storage
- Music file tag integration
- Advanced search capabilities
- Collection statistics and analytics
- Export functionality (CSV, JSON)

### Plugin Architecture
- Modular design for easy extension
- Abstract base classes for different metadata sources
- Event-driven architecture for real-time updates
- Custom prompt template support

## Error Handling

### Graceful Degradation
- Fallback to cached data when possible
- Clear error messages for users
- Logging for debugging and monitoring

### Recovery Mechanisms
- Automatic retry for transient failures
- Cache corruption detection and recovery
- Partial result handling
- User notification for persistent issues