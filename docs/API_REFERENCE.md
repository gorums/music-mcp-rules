# Music Collection MCP Server - API Reference

## Overview

The Music Collection MCP Server provides a comprehensive API for managing and accessing local music collections through the Model Context Protocol (MCP). This reference documents all available tools, resources, and prompts with their schemas, parameters, and usage examples.

## Quick Reference

### Tools (5 available)
- [`scan_music_folders`](#scan_music_folders) - Scan and index music collection
- [`get_band_list`](#get_band_list) - List bands and albums with filtering
- [`save_band_metadata`](#save_band_metadata) - Store band metadata
- [`save_band_analyze`](#save_band_analyze) - Store band analysis data
- [`save_collection_insight`](#save_collection_insight) - Store collection insights

### Resources (2 available)
- [`band://info/{band_name}`](#band-info-resource) - Get band information in markdown
- [`collection://summary`](#collection-summary-resource) - Get collection overview

### Prompts (4 available)
- [`fetch_band_info`](#fetch_band_info) - Template for fetching band data
- [`analyze_band`](#analyze_band) - Template for analyzing bands
- [`compare_bands`](#compare_bands) - Template for comparing bands
- [`collection_insights`](#collection_insights) - Template for collection analysis

---

## Tools

### scan_music_folders

Scans the music collection directory to discover bands and albums, creating or updating the collection index.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `force_rescan` | boolean | No | `false` | Force full rescan even if folders haven't changed |
| `force_full_scan` | boolean | No | `false` | Perform complete scan regardless of cache |

#### Response Schema

```json
{
  "success": true,
  "message": "Scanned 142 band folders, found 1,847 albums (1,623 local + 224 missing)",
  "stats": {
    "bands_scanned": 142,
    "albums_found": 1847,
    "local_albums": 1623,
    "missing_albums": 224,
    "scan_duration": "5.2s"
  },
  "collection_path": "/music/collection",
  "index_updated": true
}
```

#### Usage Example

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

---

### get_band_list

Retrieves a list of bands with optional filtering, sorting, and pagination.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `search_term` | string | No | `""` | Search bands by name (partial match) |
| `genre_filter` | string | No | `""` | Filter by genre |
| `sort_by` | string | No | `"name"` | Sort field: `name`, `albums_count`, `year_formed` |
| `sort_order` | string | No | `"asc"` | Sort order: `asc`, `desc` |
| `limit` | integer | No | `50` | Maximum results to return |
| `offset` | integer | No | `0` | Number of results to skip |
| `include_missing` | boolean | No | `true` | Include bands with missing albums |

#### Response Schema

```json
{
  "success": true,
  "bands": [
    {
      "band_name": "Pink Floyd",
      "albums_count": 15,
      "local_albums": 8,
      "missing_albums": 7,
      "has_metadata": true,
      "has_analysis": true,
      "formed": "1965",
      "genres": ["Progressive Rock", "Psychedelic Rock"],
      "last_updated": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "total": 142,
    "offset": 0,
    "limit": 50,
    "has_more": true
  },
  "filters_applied": {
    "search_term": "",
    "genre_filter": "Rock"
  }
}
```

#### Usage Example

```json
{
  "method": "tools/call",
  "params": {
    "name": "get_band_list",
    "arguments": {
      "genre_filter": "Rock",
      "sort_by": "albums_count",
      "sort_order": "desc",
      "limit": 10
    }
  }
}
```

---

### save_band_metadata

Stores comprehensive metadata for a band including albums, members, and basic information.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `band_name` | string | Yes | Name of the band |
| `metadata` | object | Yes | Band metadata object (see schema below) |
| `preserve_analyze` | boolean | No | Preserve existing analysis data (default: `true`) |
| `clear_analyze` | boolean | No | Clear existing analysis data (default: `false`) |

#### Metadata Schema

```json
{
  "band_name": "Pink Floyd",
  "formed": "1965",
  "genres": ["Progressive Rock", "Psychedelic Rock"],
  "origin": "London, England",
  "members": ["David Gilmour", "Roger Waters", "Nick Mason", "Richard Wright"],
  "description": "Pioneering progressive rock band known for conceptual albums and elaborate live shows",
  "albums": [
    {
      "album_name": "The Dark Side of the Moon",
      "year": "1973",
      "genres": ["Progressive Rock"],
      "tracks_count": 10,
      "duration": "43min",
      "missing": false
    }
  ]
}
```

#### Response Schema

```json
{
  "success": true,
  "message": "Successfully saved metadata for Pink Floyd",
  "band_name": "Pink Floyd",
  "metadata_file": "/music/Pink Floyd/.band_metadata.json",
  "albums_processed": 15,
  "analyze_preserved": true,
  "analyze_action": "preserved_existing",
  "validation": {
    "errors": [],
    "warnings": ["Album 'Ummagumma' missing year information"]
  },
  "backup_created": "/music/Pink Floyd/.band_metadata_backup_20240115103000.json"
}
```

#### Usage Example

```json
{
  "method": "tools/call",
  "params": {
    "name": "save_band_metadata",
    "arguments": {
      "band_name": "Pink Floyd",
      "metadata": {
        "band_name": "Pink Floyd",
        "formed": "1965",
        "genres": ["Progressive Rock", "Psychedelic Rock"],
        "origin": "London, England",
        "members": ["David Gilmour", "Roger Waters", "Nick Mason", "Richard Wright"],
        "description": "Pioneering progressive rock band",
        "albums": [
          {
            "album_name": "The Dark Side of the Moon",
            "year": "1973",
            "genres": ["Progressive Rock"],
            "tracks_count": 10,
            "missing": false
          }
        ]
      }
    }
  }
}
```

---

### save_band_analyze

Stores analysis data including reviews, ratings, and similar bands information.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `band_name` | string | Yes | Name of the band |
| `analysis` | object | Yes | Analysis data object (see schema below) |
| `analyze_missing_albums` | boolean | No | Include missing albums in analysis (default: `false`) |

#### Analysis Schema

```json
{
  "review": "Pink Floyd revolutionized progressive rock with their atmospheric soundscapes and conceptual albums. Their ability to blend experimental music with accessible melodies created a unique sound that influenced countless artists.",
  "rate": 9,
  "albums": [
    {
      "album_name": "The Dark Side of the Moon",
      "review": "A masterpiece of progressive rock that explores themes of conflict, greed, and mental illness through innovative use of sound effects and seamless song transitions.",
      "rate": 10
    }
  ],
  "similar_bands": ["Genesis", "Yes", "King Crimson", "Gentle Giant"]
}
```

#### Response Schema

```json
{
  "success": true,
  "message": "Successfully saved analysis for Pink Floyd",
  "band_name": "Pink Floyd",
  "analysis_file": "/music/Pink Floyd/.band_metadata.json",
  "albums_analyzed": 8,
  "missing_albums_included": false,
  "ratings": {
    "band_rating": 9,
    "average_album_rating": 8.5,
    "album_count": 8
  },
  "similar_bands_count": 4,
  "validation": {
    "errors": [],
    "warnings": []
  }
}
```

#### Usage Example

```json
{
  "method": "tools/call",
  "params": {
    "name": "save_band_analyze",
    "arguments": {
      "band_name": "Pink Floyd",
      "analysis": {
        "review": "Pink Floyd revolutionized progressive rock...",
        "rate": 9,
        "albums": [
          {
            "album_name": "The Dark Side of the Moon",
            "review": "A masterpiece of progressive rock...",
            "rate": 10
          }
        ],
        "similar_bands": ["Genesis", "Yes", "King Crimson"]
      }
    }
  }
}
```

---

### save_collection_insight

Stores insights and analytics about the entire music collection.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `insights` | array | No | Collection insights and observations |
| `recommendations` | array | No | Recommendations for collection improvement |
| `top_rated_bands` | array | No | List of highest-rated bands |
| `suggested_purchases` | array | No | Suggested albums to purchase |
| `collection_health` | object | No | Collection health metrics |

#### Collection Health Schema

```json
{
  "completion_percentage": 75.5,
  "metadata_coverage": 89.2,
  "analysis_coverage": 67.8,
  "total_bands": 142,
  "analyzed_bands": 96,
  "missing_albums_count": 224,
  "health_score": 8.2
}
```

#### Response Schema

```json
{
  "success": true,
  "message": "Successfully saved collection insights",
  "insights_file": "/music/.collection_index.json",
  "insights_count": 5,
  "recommendations_count": 8,
  "top_rated_bands_count": 10,
  "suggested_purchases_count": 15,
  "collection_health_updated": true,
  "files_modified": [".collection_index.json"],
  "backup_created": "/music/.collection_index_backup_20240115103000.json"
}
```

#### Usage Example

```json
{
  "method": "tools/call",
  "params": {
    "name": "save_collection_insight",
    "arguments": {
      "insights": [
        "Progressive rock is heavily represented with 35 bands",
        "Most albums are from the 1970s golden era"
      ],
      "recommendations": [
        "Consider adding more contemporary progressive bands",
        "Fill gaps in classic album collections"
      ],
      "collection_health": {
        "completion_percentage": 75.5,
        "metadata_coverage": 89.2,
        "health_score": 8.2
      }
    }
  }
}
```

---

## Resources

### Band Info Resource

**URI**: `band://info/{band_name}`

Provides comprehensive information about a specific band in markdown format.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `band_name` | string | Name of the band (URL encoded) |

#### Response Format

Returns markdown-formatted band information including:
- Band overview (formation, genre, origin, members)
- Complete albums listing with availability status
- Missing albums section
- Analysis and ratings (if available)
- Similar bands
- Collection statistics
- Metadata information

#### Example Request

```
GET band://info/Pink%20Floyd
```

#### Example Response

```markdown
# Pink Floyd

## Band Overview
🎵 **Genre**: Progressive Rock, Psychedelic Rock  
📅 **Formed**: 1965  
🌍 **Origin**: London, England  
👥 **Members**: David Gilmour, Roger Waters, Nick Mason, Richard Wright

## Albums (15 total: 8 local + 7 missing)

### Local Albums (8)
| Album | Year | Tracks | Rating | Genres |
|-------|------|--------|--------|--------|
| The Dark Side of the Moon | 1973 | 10 | ⭐ 10/10 | Progressive Rock |
| The Wall | 1979 | 26 | ⭐ 9/10 | Progressive Rock, Rock Opera |

### Missing Albums (7)
- Ummagumma (1969)
- Atom Heart Mother (1970)
...

## Analysis
**Band Rating**: ⭐ 9/10

Pink Floyd revolutionized progressive rock with their atmospheric soundscapes...

**Similar Bands**: Genesis, Yes, King Crimson, Gentle Giant
```

---

### Collection Summary Resource

**URI**: `collection://summary`

Provides a comprehensive overview of the entire music collection.

#### Response Format

Returns markdown-formatted collection summary including:
- Collection overview with statistics
- Band distribution analysis
- Missing albums analysis
- Collection insights and recommendations
- Health assessment
- Metadata information

#### Example Request

```
GET collection://summary
```

#### Example Response

```markdown
# Music Collection Summary

## Collection Overview
🎵 **Total Bands**: 142  
💿 **Total Albums**: 1,847 (1,623 local + 224 missing)  
📊 **Completion**: 87.9%  
📈 **Health Score**: 8.5/10

## Band Distribution
| Size | Count | Percentage |
|------|-------|------------|
| Large Collections (≥10 albums) | 45 | 31.7% |
| Medium Collections (4-9 albums) | 67 | 47.2% |
| Small Collections (1-3 albums) | 30 | 21.1% |

## Missing Albums Analysis
**Total Missing**: 224 albums (12.1% of collection)
- 15 bands missing 50%+ of their albums
- 67 bands missing 1-3 albums each
```

---

## Prompts

### fetch_band_info

Generates prompts for fetching band information using external sources like Brave Search.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `band_name` | string | No | `""` | Specific band to fetch info for |
| `information_scope` | string | No | `"full"` | Scope: `basic`, `full`, `albums_only` |
| `existing_albums` | array | No | `[]` | Known albums for missing detection |

#### Response

Returns a structured prompt template for fetching band information with specific instructions and output format requirements.

#### Usage Example

```json
{
  "method": "prompts/get",
  "params": {
    "name": "fetch_band_info",
    "arguments": {
      "band_name": "Pink Floyd",
      "information_scope": "full"
    }
  }
}
```

---

### analyze_band

Generates prompts for comprehensive band analysis including reviews and ratings.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `band_name` | string | No | `""` | Specific band to analyze |
| `analysis_scope` | string | No | `"full"` | Scope: `basic`, `full`, `albums_only` |
| `albums` | array | No | `[]` | Albums to include in analysis |
| `analyze_missing_albums` | boolean | No | `false` | Include missing albums |

#### Response

Returns a structured prompt template for band analysis with rating guidelines and output format.

#### Usage Example

```json
{
  "method": "prompts/get",
  "params": {
    "name": "analyze_band",
    "arguments": {
      "band_name": "Pink Floyd",
      "analysis_scope": "full",
      "analyze_missing_albums": true
    }
  }
}
```

---

### compare_bands

Generates prompts for comparing multiple bands across various dimensions.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `band_names` | array | No | `[]` | Bands to compare (minimum 2) |
| `comparison_scope` | string | No | `"full"` | Scope: `basic`, `full`, `summary` |
| `comparison_aspects` | array | No | `["all"]` | Aspects: `style`, `discography`, `influence`, etc. |

#### Response

Returns a structured prompt template for band comparison with specific analysis dimensions.

#### Usage Example

```json
{
  "method": "prompts/get",
  "params": {
    "name": "compare_bands",
    "arguments": {
      "band_names": ["Pink Floyd", "Genesis", "Yes"],
      "comparison_scope": "full",
      "comparison_aspects": ["style", "influence", "discography"]
    }
  }
}
```

---

### collection_insights

Generates prompts for analyzing the entire music collection and providing insights.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `collection_data` | object | No | `{}` | Collection statistics |
| `insights_scope` | string | No | `"comprehensive"` | Scope: `basic`, `comprehensive`, `health_only` |
| `focus_areas` | array | No | `["all"]` | Areas: `statistics`, `recommendations`, `health`, etc. |

#### Response

Returns a structured prompt template for collection analysis with data-driven insights.

#### Usage Example

```json
{
  "method": "prompts/get",
  "params": {
    "name": "collection_insights",
    "arguments": {
      "insights_scope": "comprehensive",
      "focus_areas": ["statistics", "recommendations", "health"]
    }
  }
}
```

---

## Error Handling

### Standard Error Response

All API endpoints return standardized error responses:

```json
{
  "success": false,
  "error": {
    "code": "BAND_NOT_FOUND",
    "message": "Band 'Unknown Band' not found in collection",
    "details": {
      "band_name": "Unknown Band",
      "suggestion": "Use scan_music_folders to refresh the collection index"
    }
  }
}
```

### Common Error Codes

| Code | Description | Typical Resolution |
|------|-------------|-------------------|
| `BAND_NOT_FOUND` | Band not found in collection | Scan collection or check band name |
| `METADATA_VALIDATION_ERROR` | Invalid metadata format | Check schema and fix validation errors |
| `FILE_PERMISSION_ERROR` | Cannot write to metadata file | Check file permissions |
| `COLLECTION_INDEX_CORRUPTED` | Collection index file is corrupted | Rescan collection to rebuild index |
| `INVALID_RATING` | Rating outside 1-10 range | Provide rating between 1 and 10 |

---

## Rate Limits and Performance

### Performance Characteristics

| Operation | Typical Response Time | Memory Usage |
|-----------|----------------------|--------------|
| `scan_music_folders` (1000 bands) | < 60 seconds | < 500 MB |
| `get_band_list` (500 bands) | < 5 seconds | < 100 MB |
| `save_band_metadata` | < 1 second | < 50 MB |
| Resource access | < 500ms | < 10 MB |

### Best Practices

1. **Scanning**: Use `force_rescan=false` for regular operations
2. **Listing**: Use pagination for large collections (limit ≤ 100)
3. **Metadata**: Validate data before saving to avoid rollbacks
4. **Resources**: Cache results when possible for better performance
5. **Concurrent Access**: The server handles file locking automatically

---

## Versioning

Current API Version: **1.1.0**

### Version History

- **1.1.0**: Added analyze preservation in `save_band_metadata`
- **1.0.0**: Initial stable release with all core features
- **0.9.x**: Beta releases with incremental feature additions

### Backwards Compatibility

The API maintains backwards compatibility within major versions. Deprecated features are marked with `@deprecated` and will be removed in the next major version. 