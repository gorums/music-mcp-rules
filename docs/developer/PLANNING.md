# Music Collection MCP Server - Instructions

## Project Overview

This project implements a Model Context Protocol (MCP) server that provides intelligent access to your local music collection. The server exposes tools, resources, and prompts to discover, analyze, and retrieve information about bands and artists based on your folder structure.

## Scope

### Core Functionality
- **Band Discovery**: Automatically extract band names from folder structure
- **Album Type Classification**: Intelligent detection and mapping of 8 album types (Album, Compilation, EP, Live, Single, Demo, Instrumental, Split)
- **Folder Structure Analysis**: Support for multiple organization patterns with compliance scoring and recommendations
- **Metadata Management**: Store and retrieve band information in local JSON files
- **Information Enrichment**: Fetch comprehensive band data using brave search MCP
- **Intelligent Querying**: Provide context-aware prompts for music exploration

### Key Features
- **No Database Dependency**: All data stored in JSON files within music folders
- **Folder-Based Architecture**: Uses existing music directory structure with intelligent pattern recognition
- **Album Type System**: Comprehensive 8-type classification with auto-detection from folder names and metadata
- **Multiple Folder Patterns**: Support for both flat and type-based folder organization structures
- **Structure Compliance**: Scoring and validation of folder organization with improvement recommendations
- **External API Integration**: Fetches band information using brave search MCP
- **Caching Strategy**: Stores fetched data locally to minimize API calls
- **Flexible Queries**: Support for various music metadata searches with type-based filtering

## Album Type Classification System

### Supported Album Types

The system recognizes 8 distinct album types with intelligent auto-detection:

1. **Album** (Standard studio albums)
2. **Compilation** (Greatest hits, collections, anthologies)
3. **EP** (Extended plays, typically 4-7 tracks)
4. **Live** (Live recordings, concerts, unplugged sessions)
5. **Single** (Single releases)
6. **Demo** (Demo recordings, unreleased tracks)
7. **Instrumental** (Instrumental versions)
8. **Split** (Split releases with multiple artists)

### Type Detection Logic

Album types are detected using multiple strategies:

- **Folder Name Analysis**: Keywords in album folder names (e.g., "Live at Wembley", "Greatest Hits")
- **Type Folder Structure**: Enhanced organization with type-specific folders
- **Metadata Integration**: Existing metadata used for type classification
- **Pattern Recognition**: Smart parsing of naming conventions and parenthetical information

## Folder Structure Support

### Default Structure (Flat Organization)
```
Band Name/
├── 1973 - The Dark Side of the Moon/
├── 1979 - The Wall (Deluxe Edition)/
├── 1985 - Live at Wembley (Live)/
└── 1996 - Greatest Hits (Compilation)/
```

### Enhanced Structure (Type-Based Organization)
```
Band Name/
├── Album/
│   ├── 1973 - The Dark Side of the Moon/
│   └── 1979 - The Wall (Deluxe Edition)/
├── Live/
│   └── 1985 - Live at Wembley/
├── Compilation/
│   └── 1996 - Greatest Hits/
├── EP/
│   └── 1980 - Running Free EP/
└── Demo/
    └── 1978 - Early Demos/
```

### Legacy Structure (Simple Names)
```
Band Name/
├── The Dark Side of the Moon/
├── The Wall/
├── Live at Wembley/
└── Greatest Hits/
```

### Structure Analysis Features

- **Pattern Recognition**: Automatically detects which structure type is used
- **Compliance Scoring**: 0-100 score based on naming consistency and organization
- **Recommendations**: Specific suggestions for improving folder organization
- **Migration Planning**: Automated recommendations for structure upgrades
- **Health Assessment**: Overall structure health with detailed metrics

## Technical Architecture

### Technology Stack
- **Language**: Python 3.8+
- **Framework**: FastMCP (Python MCP SDK)
- **Transport**: JSON-RPC over stdio
- **Storage**: Local JSON files (no database)
- **File Operations**: Python's built-in `os`, `json`, and `pathlib` modules

### MCP Components

#### Tools (6 tools)
1. **`scan_music_folders`** - Intelligent scanning with incremental updates, album type detection, and folder structure analysis
2. **`get_band_list_tool`** - Advanced filtering by album types, compliance levels, structure types, with sorting and pagination
3. **`save_band_metadata_tool`** - Store comprehensive band and album metadata with type classification
4. **`save_band_analyze_tool`** - Store analysis data with reviews, ratings, and similar bands
5. **`save_collection_insight_tool`** - Store collection-wide insights and recommendations
6. **`validate_band_metadata_tool`** - Dry-run validation without saving data, includes structure compliance

#### Resources (2 resources)
1. **`band://info/{band_name}`** - Detailed band information with album type organization in markdown format
2. **`collection://summary`** - Collection overview with album type distribution and structure analysis

#### Prompts (4 prompts)
1. **`fetch_band_info`** - Intelligent band information fetching using brave search
2. **`analyze_band`** - Comprehensive band analysis with reviews and ratings
3. **`compare_bands`** - Multi-band comparison template
4. **`collection_insights`** - Generate collection-wide insights with type-specific recommendations

### Data Structure

#### Enhanced Album Model
Albums now include comprehensive type and structure information:

```json
{
  "album_name": "The Dark Side of the Moon",
  "year": "1973",
  "type": "Album",
  "edition": "Deluxe Edition",
  "genres": ["Progressive Rock"],
  "tracks_count": 10,
  "duration": "43min",
  "missing": false,
  "folder_path": "1973 - The Dark Side of the Moon (Deluxe Edition)",
  "compliance": {
    "score": 95,
    "level": "excellent",
    "issues": [],
    "recommended_path": "Album/1973 - The Dark Side of the Moon (Deluxe Edition)"
  }
}
```

#### Folder Structure Metadata
Each band includes detailed structure analysis:

```json
{
  "folder_structure": {
    "structure_type": "enhanced",
    "consistency": "consistent",
    "consistency_score": 92,
    "albums_analyzed": 15,
    "albums_with_type_folders": 12,
    "type_folders_found": ["Album", "Live", "Compilation", "EP"],
    "structure_score": 88,
    "recommendations": ["Move remaining albums to type folders"],
    "issues": ["3 albums not in type folders"],
    "analysis_metadata": {
      "pattern_counts": {"enhanced": 12, "default": 3},
      "compliance_distribution": {"excellent": 10, "good": 5},
      "structure_health": "good"
    }
  }
}
```

##### Validation Rules
- All year fields must be 4-digit strings (e.g., "1975", not 1975)
- Album types must be valid AlbumType enum values
- Albums array can be empty but must be present
- Members array should include all members (past and present) as flat list
- Duration format is flexible but should include time unit (min, h, etc.)
- Genres should be specific and accurate music genres
- Ratings must be integers between 0-10 (0 = unrated)
- Structure scores and consistency scores must be 0-100
- Compliance levels must be one of: excellent, good, fair, poor, critical

##### Common Mistakes to Avoid
- ❌ Using "formed_year" (should be "formed")
- ❌ Using integer for formed year (should be string "1965")
- ❌ Using nested member structure like {"current": [...], "former": [...]} (should be flat array)
- ❌ Using "notable_albums" or "discography" (should be "albums")
- ❌ Missing required album fields (album_name, year, tracks_count, missing)
- ❌ Using integer for album year (should be string "1973")
- ❌ Negative tracks_count (must be >= 0)
- ❌ Rating outside 0-10 range
- ❌ Invalid album type (must be one of: Album, Compilation, EP, Live, Single, Demo, Instrumental, Split)
- ❌ Invalid structure type or consistency level values

## Configuration

### Environment Variables
- `MUSIC_ROOT_PATH`: Path to the root music directory
- `CACHE_DURATION_DAYS`: How long to cache band metadata (default: 30)

### MCP Client Integration
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

## Album Type and Structure Features

### Type-Based Filtering
- Filter bands by specific album types (e.g., show only bands with Live albums)
- Search for bands with specific type combinations
- Get collection statistics by album type distribution

### Structure Analysis and Recommendations
- Automatic assessment of folder organization quality
- Specific recommendations for improving structure
- Migration planning for upgrading to enhanced structures
- Compliance scoring with detailed breakdown

### Enhanced Collection Insights
- Album type distribution analysis
- Structure health assessment across collection
- Recommendations for collection organization improvements
- Missing album type identification (e.g., "This band needs a live album")

## API Integration Strategy

### Fallback Strategy
1. Check local cache first (`.band_metadata.json`)
2. Query brave search MCP if cache is stale or missing
3. Store results locally for future use
4. Handle API failures gracefully with cached data

## Security Considerations

### File System Access
- Read-only access to music directories
- Write access only to `.band_metadata.json` files and `.collection_index.json`
- Input validation for all file paths
- Protection against directory traversal attacks

## Performance Optimization

### Caching Strategy
- Local JSON file caching
- Configurable cache expiration
- Incremental scanning for large collections with structure change detection
- Memory-conscious data processing

### Structure Analysis Optimization
- Efficient pattern recognition algorithms
- Cached structure analysis results
- Incremental compliance checking
- Optimized type detection using keyword matching

## Error Handling

### Graceful Degradation
- Fallback to cached data when possible
- Clear error messages for users
- Comprehensive validation with helpful suggestions for both metadata and structure
- Partial result handling for large operations
- Structure analysis error recovery with partial results