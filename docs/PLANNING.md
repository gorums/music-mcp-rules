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
- **Framework**: FastMCP (Python MCP SDK)
- **Transport**: JSON-RPC over stdio
- **Storage**: Local JSON files (no database)
- **File Operations**: Python's built-in `os`, `json`, and `pathlib` modules

### MCP Components

#### Tools (6 tools)
1. **`scan_music_folders`** - Intelligent scanning with incremental updates and change detection
2. **`get_band_list_tool`** - Advanced filtering, sorting, pagination, and search capabilities
3. **`save_band_metadata_tool`** - Store comprehensive band and album metadata
4. **`save_band_analyze_tool`** - Store analysis data with reviews, ratings, and similar bands
5. **`save_collection_insight_tool`** - Store collection-wide insights and recommendations
6. **`validate_band_metadata_tool`** - Dry-run validation without saving data

#### Resources (2 resources)
1. **`band://info/{band_name}`** - Detailed band information in markdown format
2. **`collection://summary`** - Collection overview and statistics in markdown format

#### Prompts (4 prompts)
1. **`fetch_band_info`** - Intelligent band information fetching using brave search
2. **`analyze_band`** - Comprehensive band analysis with reviews and ratings
3. **`compare_bands`** - Multi-band comparison template
4. **`collection_insights`** - Generate collection-wide insights and recommendations

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

The complete metadata structure for band information storage:

##### Band Metadata Structure

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
    {
      "album_name": "string",
      "missing": boolean,
      "tracks_count": number,
      "duration": "string",
      "year": "YYYY",
      "genres": ["string"]
    }
  ],
  "last_updated": "ISO datetime",
  "analyze": {
    "review": "string",
    "rate": number,
    "albums": [
      {
        "album_name": "string",
        "review": "string", 
        "rate": number
      }
    ],
    "similar_bands": ["string"]
  },
  "folder_structure": {
    "structure_type": "string",
    "consistency": "string",
    "consistency_score": number,
    "albums_analyzed": number,
    "albums_with_year_prefix": number,
    "albums_without_year_prefix": number,
    "albums_with_type_folders": number,
    "detected_patterns": ["string"],
    "type_folders_found": ["string"],
    "structure_score": number,
    "recommendations": ["string"],
    "issues": ["string"],
    "analysis_metadata": {
      "pattern_counts": {
        "string": number
      },
      "compliance_distribution": {
        "excellent": number,
        "good": number,
        "fair": number,
        "poor": number
      },
      "structure_health": "string"
    }
  }
}
```

##### Required Fields (Band Metadata)
- **formed** (string): Formation year in "YYYY" format
- **genres** (array of strings): List of music genres
- **origin** (string): Country/city of origin
- **members** (array of strings): List of all band member names (past and present)
- **description** (string): Band biography or description
- **albums** (array): List of album objects

##### Album Schema (Required Fields)
- **album_name** (string): Name of the album
- **year** (string): Release year in "YYYY" format
- **tracks_count** (integer): Number of tracks (must be >= 0)
- **missing** (boolean): true if album not found in local folders, false if present

##### Album Schema (Optional Fields)
- **duration** (string): Album length (format: "43min", "1h 23min", etc.)
- **genres** (array of strings): Album-specific genres (can differ from band genres)

##### Analysis Schema (Optional Section)
- **review** (string): Overall band review text
- **rate** (integer): Overall band rating from 0-10 (0 = unrated)
- **albums** (array): Per-album analysis objects:
  - **album_name** (string, REQUIRED): Name of the album
  - **review** (string): Album review text
  - **rate** (integer): Album rating 0-10 (0 = unrated)
- **similar_bands** (array of strings): Names of similar/related bands

##### Folder Structure Schema (Optional Section)
- **structure_type** (string): Primary structure type ("default", "enhanced", "mixed", "legacy", "unknown")
- **consistency** (string): Consistency level ("consistent", "mostly_consistent", "inconsistent", "unknown")
- **consistency_score** (integer): Numerical consistency score (0-100)
- **albums_analyzed** (integer): Number of albums analyzed for structure detection
- **albums_with_year_prefix** (integer): Count of albums following year prefix pattern
- **albums_without_year_prefix** (integer): Count of albums missing year prefix
- **albums_with_type_folders** (integer): Count of albums organized in type folders
- **detected_patterns** (array of strings): List of folder patterns found in band
- **type_folders_found** (array of strings): List of type folders found (Album, Live, Demo, etc.)
- **structure_score** (integer): Overall structure organization score (0-100)
- **recommendations** (array of strings): List of specific improvement recommendations
- **issues** (array of strings): List of identified structure issues
- **analysis_metadata** (object): Additional analysis information including pattern counts and health indicators

##### Structure Types
- **default**: Standard flat structure with "YYYY - Album Name (Edition?)" pattern
- **enhanced**: Type-based structure with "Type/YYYY - Album Name (Edition?)" pattern
- **mixed**: Combination of both default and enhanced structures
- **legacy**: Albums without year prefix, just "Album Name" pattern
- **unknown**: Unable to determine structure type

##### Complete Example

```json
{
  "band_name": "Pink Floyd",
  "formed": "1965",
  "genres": ["Progressive Rock", "Psychedelic Rock", "Art Rock"],
  "origin": "London, England",
  "members": ["David Gilmour", "Roger Waters", "Nick Mason", "Richard Wright", "Syd Barrett"],
  "albums_count": 3,
  "description": "English rock band formed in London in 1965. Achieved international acclaim with their progressive and psychedelic music.",
  "albums": [
    {
      "album_name": "The Dark Side of the Moon",
      "year": "1973",
      "tracks_count": 10,
      "missing": false,
      "duration": "43min",
      "genres": ["Progressive Rock", "Art Rock"]
    },
    {
      "album_name": "The Wall",
      "year": "1979", 
      "tracks_count": 26,
      "missing": false,
      "duration": "81min",
      "genres": ["Progressive Rock", "Rock Opera"]
    },
    {
      "album_name": "Wish You Were Here",
      "year": "1975",
      "tracks_count": 5,
      "missing": true,
      "duration": "44min",
      "genres": ["Progressive Rock"]
    }
  ],
  "last_updated": "2025-01-11T10:30:00Z",
  "analyze": {
    "review": "Legendary progressive rock band known for conceptual albums and innovative sound design.",
    "rate": 9,
    "albums": [
      {
        "album_name": "The Dark Side of the Moon",
        "review": "Masterpiece of progressive rock with innovative sound design and philosophical themes.",
        "rate": 10
      },
      {
        "album_name": "The Wall",
        "review": "Epic rock opera exploring themes of isolation and psychological breakdown.",
        "rate": 9
      }
    ],
    "similar_bands": ["King Crimson", "Genesis", "Yes", "Led Zeppelin"]
  },
  "folder_structure": {
    "structure_type": "default",
    "consistency": "consistent",
    "consistency_score": 85,
    "albums_analyzed": 2,
    "albums_with_year_prefix": 2,
    "albums_without_year_prefix": 0,
    "albums_with_type_folders": 0,
    "detected_patterns": ["YYYY - Album Name"],
    "type_folders_found": [],
    "structure_score": 82,
    "recommendations": [
      "Consider adding missing album 'Wish You Were Here' to complete collection",
      "Folder organization is consistent, good structure maintenance"
    ],
    "issues": [],
    "analysis_metadata": {
      "pattern_counts": {
        "YYYY - Album Name": 2
      },
      "compliance_distribution": {
        "excellent": 2,
        "good": 0,
        "fair": 0,
        "poor": 0
      },
      "structure_health": "good"
    }
  }
}
```

##### Validation Rules
- All year fields must be 4-digit strings (e.g., "1975", not 1975)
- Albums array can be empty but must be present
- Members array should include all members (past and present) as flat list
- Duration format is flexible but should include time unit (min, h, etc.)
- Genres should be specific and accurate music genres
- Ratings must be integers between 0-10 (0 = unrated)

##### Common Mistakes to Avoid
- ❌ Using "formed_year" (should be "formed")
- ❌ Using integer for formed year (should be string "1965")
- ❌ Using nested member structure like {"current": [...], "former": [...]} (should be flat array)
- ❌ Using "notable_albums" or "discography" (should be "albums")
- ❌ Missing required album fields (album_name, year, tracks_count, missing)
- ❌ Using integer for album year (should be string "1973")
- ❌ Negative tracks_count (must be >= 0)
- ❌ Rating outside 0-10 range

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
- Incremental scanning for large collections
- Memory-conscious data processing

## Error Handling

### Graceful Degradation
- Fallback to cached data when possible
- Clear error messages for users
- Comprehensive validation with helpful suggestions
- Partial result handling for large operations