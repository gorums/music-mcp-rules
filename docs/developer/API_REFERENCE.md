# Music Collection MCP Server - API Reference with Album Type Classification

## Overview

The Music Collection MCP Server provides a comprehensive API for managing and accessing local music collections through the Model Context Protocol (MCP). This reference documents all available tools, resources, and prompts with their schemas, parameters, and usage examples, including the new album type classification and folder structure analysis features.

## Quick Reference

### Tools (5 available)
- [`scan_music_folders`](#scan_music_folders) - Scan and index music collection with type detection
- [`get_band_list`](#get_band_list) - List bands and albums with type filtering and structure analysis
- [`save_band_metadata`](#save_band_metadata) - Store band metadata with album types
- [`save_band_analyze`](#save_band_analyze) - Store band analysis data
- [`save_collection_insight`](#save_collection_insight) - Store collection insights

### Resources (2 available)
- [`band://info/{band_name}`](#band-info-resource) - Get band information with album types
- [`collection://summary`](#collection-summary-resource) - Get collection overview with type distribution

### Prompts (4 available)
- [`fetch_band_info`](#fetch_band_info) - Template for fetching band data
- [`analyze_band`](#analyze_band) - Template for analyzing bands
- [`compare_bands`](#compare_bands) - Template for comparing bands
- [`collection_insights`](#collection_insights) - Template for collection analysis

---

## Album Type Classification System

The server supports 8 distinct album types with intelligent auto-detection:

### Album Types

| Type | Description | Detection Keywords |
|------|-------------|-------------------|
| `Album` | Standard studio albums | (default classification) |
| `Compilation` | Greatest hits, collections | "greatest hits", "best of", "collection" |
| `EP` | Extended plays | "ep", "e.p." |
| `Live` | Live recordings | "live", "concert", "unplugged" |
| `Single` | Single releases | "single" |
| `Demo` | Demo recordings | "demo", "demos", "unreleased" |
| `Instrumental` | Instrumental versions | "instrumental", "instrumentals" |
| `Split` | Split releases | "split", "vs.", "versus" |

### Folder Structure Types

| Type | Description | Example |
|------|-------------|---------|
| `default` | Flat structure | `1973 - Album Name` |
| `enhanced` | Type-based structure | `Album/1973 - Album Name` |
| `mixed` | Combination of both | Mixed patterns |
| `legacy` | No year prefix | `Album Name` |
| `unknown` | Unrecognized pattern | Various |

---

## Tools

### scan_music_folders

Scans the music collection directory to discover bands and albums with album type detection and folder structure analysis.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `force_rescan` | boolean | No | `false` | Force full rescan even if folders haven't changed |
| `force_full_scan` | boolean | No | `false` | Perform complete scan regardless of cache |
| `include_missing_albums` | boolean | No | `true` | Include missing albums in results |
| `analyze_structure` | boolean | No | `true` | Perform folder structure analysis |
| `detect_album_types` | boolean | No | `true` | Enable album type detection |

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
    "scan_duration": "5.2s",
    "album_type_distribution": {
      "Album": 1245,
      "Live": 187,
      "Compilation": 156,
      "EP": 89,
      "Demo": 67,
      "Single": 23,
      "Instrumental": 15,
      "Split": 8
    },
    "structure_analysis": {
      "enhanced_structure_bands": 45,
      "default_structure_bands": 89,
      "legacy_structure_bands": 8,
      "average_compliance_score": 78.5,
      "structure_distribution": {
        "enhanced": 32,
        "default": 63,
        "mixed": 28,
        "legacy": 15,
        "unknown": 4
      }
    }
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
      "force_rescan": true,
      "analyze_structure": true,
      "detect_album_types": true
    }
  }
}
```

---

### get_band_list

Retrieves a list of bands with optional filtering by album types, compliance levels, and structure types.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `search_term` | string | No | `""` | Search bands by name (partial match) |
| `genre_filter` | string | No | `""` | Filter by genre |
| `filter_album_types` | array | No | `[]` | Filter by album types: `["Album", "Live", "EP"]` |
| `filter_compliance_levels` | array | No | `[]` | Filter by compliance: `["excellent", "good", "fair"]` |
| `filter_structure_types` | array | No | `[]` | Filter by structure: `["enhanced", "default", "mixed"]` |
| `sort_by` | string | No | `"name"` | Sort field: `name`, `albums_count`, `compliance_score` |
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
      "local_albums": 12,
      "missing_albums": 3,
      "has_metadata": true,
      "has_analysis": true,
      "formed": "1965",
      "genres": ["Progressive Rock", "Psychedelic Rock"],
      "last_updated": "2024-01-15T10:30:00Z",
      "album_type_distribution": {
        "Album": 9,
        "Live": 3,
        "Compilation": 2,
        "Demo": 1
      },
      "structure_analysis": {
        "structure_type": "enhanced",
        "compliance_score": 95,
        "compliance_level": "excellent",
        "issues_count": 0,
        "recommendations": []
      },
      "albums": [
        {
          "album_name": "The Wall",
          "type": "Album",
          "year": "1979",
          "edition": "Deluxe Edition",
          "missing": false,
          "tracks_count": 26,
          "compliance": {
            "score": 100,
            "level": "excellent",
            "issues": []
          }
        }
      ]
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
    "genre_filter": "Rock",
    "album_types": ["Album", "Live"],
    "compliance_levels": ["excellent"],
    "structure_types": ["enhanced"]
  },
  "collection_stats": {
    "total_albums_by_type": {
      "Album": 1245,
      "Live": 187,
      "Compilation": 156,
      "EP": 89
    },
    "compliance_distribution": {
      "excellent": 45,
      "good": 67,
      "fair": 23,
      "poor": 5,
      "critical": 2
    }
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
      "filter_album_types": ["Live", "Demo"],
      "filter_compliance_levels": ["excellent", "good"],
      "sort_by": "compliance_score",
      "sort_order": "desc",
      "limit": 10
    }
  }
}
```

---

### save_band_metadata

Stores comprehensive metadata for a band including albums with type classification and compliance information.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `band_name` | string | Yes | Name of the band |
| `metadata` | object | Yes | Band metadata object with enhanced album schema |

#### Enhanced Metadata Schema

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
      "type": "Album",
      "edition": "",
      "genres": ["Progressive Rock"],
      "tracks_count": 10,
      "duration": "43min",
      "missing": false,
      "folder_path": "1973 - The Dark Side of the Moon",
      "compliance": {
        "score": 100,
        "level": "excellent",
        "issues": [],
        "recommendations": []
      }
    },
    {
      "album_name": "Live at Pompeii",
      "year": "1972",
      "type": "Live",
      "edition": "",
      "genres": ["Progressive Rock"],
      "tracks_count": 8,
      "duration": "65min",
      "missing": false,
      "folder_path": "Live/1972 - Live at Pompeii",
      "compliance": {
        "score": 95,
        "level": "excellent",
        "issues": [],
        "recommendations": []
      }
    }
  ]
}
```

#### Response Schema

```json
{
  "success": true,
  "message": "Successfully saved metadata for Pink Floyd with album type classification",
  "band_name": "Pink Floyd",
  "metadata_file": "/music/Pink Floyd/.band_metadata.json",
  "albums_processed": 15,
  "album_types_detected": {
    "Album": 9,
    "Live": 3,
    "Compilation": 2,
    "Demo": 1
  },
  "structure_analysis": {
    "structure_type": "enhanced",
    "compliance_score": 95,
    "compliance_level": "excellent"
  },
  "analyze_preserved": true,
  "analyze_action": "preserved",
  "validation": {
    "errors": [],
    "warnings": ["Album 'Ummagumma' missing year information"],
    "type_validation": {
      "auto_detected_types": 3,
      "manual_overrides": 0,
      "confidence_scores": {
        "Live at Pompeii": 0.95,
        "The Wall": 0.88
      }
    }
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
        "albums": [
          {
            "album_name": "The Wall",
            "year": "1979",
            "type": "Album",
            "tracks_count": 26
          }
        ]
      }
    }
  }
}
```

---

### save_band_analyze

Stores analysis data for bands including album-specific reviews and ratings with type-aware analysis.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `band_name` | string | Yes | Name of the band |
| `analyze_data` | object | Yes | Analysis data object |
| `analyze_missing_albums` | boolean | No | Include missing albums in analysis (default: `false`) |

#### Analysis Data Schema

```json
{
  "band_name": "Pink Floyd",
  "review": "Pioneering progressive rock band with innovative soundscapes",
  "rate": 9,
  "similar_bands": ["King Crimson", "Genesis", "Yes"],
  "album_analysis": [
    {
      "album_name": "The Wall",
      "type": "Album",
      "review": "Conceptual masterpiece exploring themes of isolation",
      "rate": 10
    },
    {
      "album_name": "Live at Pompeii",
      "type": "Live",
      "review": "Atmospheric live performance in unique setting",
      "rate": 9
    }
  ]
}
```

#### Response Schema

```json
{
  "success": true,
  "message": "Successfully saved analysis for Pink Floyd with type-aware album analysis",
  "band_name": "Pink Floyd",
  "analyze_file": "/music/Pink Floyd/.band_metadata.json",
  "albums_analyzed": 12,
  "missing_albums_analyzed": 3,
  "analysis_by_type": {
    "Album": {
      "count": 9,
      "average_rating": 8.7,
      "reviewed": 9
    },
    "Live": {
      "count": 3,
      "average_rating": 8.3,
      "reviewed": 3
    }
  },
  "validation": {
    "errors": [],
    "warnings": [],
    "rating_distribution": {
      "10": 2,
      "9": 4,
      "8": 6
    }
  }
}
```

---

### save_collection_insight

Stores collection-wide insights including album type distribution and structure analysis.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `insights` | object | Yes | Collection insights object |

#### Insights Schema

```json
{
  "collection_overview": {
    "total_bands": 142,
    "total_albums": 1847,
    "album_type_distribution": {
      "Album": 1245,
      "Live": 187,
      "Compilation": 156,
      "EP": 89,
      "Demo": 67,
      "Single": 23,
      "Instrumental": 15,
      "Split": 8
    },
    "structure_analysis": {
      "enhanced_structure_percentage": 32.4,
      "average_compliance_score": 78.5,
      "bands_needing_migration": 45
    }
  },
  "recommendations": [
    "Consider migrating 45 bands to enhanced folder structure",
    "Add missing album type classifications for 23 albums",
    "Improve compliance for 12 bands with poor scores"
  ]
}
```

---

## Resources

### band://info/{band_name}

Returns comprehensive band information in markdown format including album type distribution and structure analysis.

#### Parameters

- `band_name`: URL-encoded band name

#### Response Format

Markdown document with sections:
- **Band Overview** with formation details and genres
- **Album Type Distribution** with counts and percentages
- **Albums by Type** organized by album type
- **Structure Analysis** with compliance scores and recommendations
- **Missing Albums** if any
- **Analysis & Ratings** if available
- **Similar Bands** if available

#### Example Response

```markdown
# Pink Floyd

## Band Overview
- **Formed**: 1965
- **Origin**: London, England
- **Genres**: Progressive Rock, Psychedelic Rock
- **Members**: David Gilmour, Roger Waters, Nick Mason, Richard Wright

## Album Type Distribution
- 📀 **Albums**: 9 (60.0%)
- 🎤 **Live**: 3 (20.0%)
- 📦 **Compilation**: 2 (13.3%)
- 🎵 **Demo**: 1 (6.7%)

## Structure Analysis
- **Structure Type**: Enhanced
- **Compliance Score**: 95/100 (Excellent)
- **Organization**: Type-based folder structure

## Albums by Type

### 📀 Albums (9)
| Album | Year | Rating | Tracks | Status |
|-------|------|--------|--------|--------|
| The Wall | 1979 | ⭐ 10/10 | 26 | ✅ Local |
| Dark Side of the Moon | 1973 | ⭐ 10/10 | 10 | ✅ Local |

### 🎤 Live Albums (3)
| Album | Year | Rating | Tracks | Status |
|-------|------|--------|--------|--------|
| Live at Pompeii | 1972 | ⭐ 9/10 | 8 | ✅ Local |
```

---

### collection://summary

Returns collection overview with album type statistics and structure analysis.

#### Response Format

Markdown document with sections:
- **Collection Statistics** with totals and distributions
- **Album Type Analysis** with detailed breakdowns
- **Folder Structure Overview** with compliance metrics
- **Collection Health** with recommendations
- **Top Rated Content** by album type

#### Example Response

```markdown
# Music Collection Summary

## Collection Statistics
- **Total Bands**: 142
- **Total Albums**: 1,847 (1,623 local + 224 missing)
- **Completion Rate**: 87.9%

## Album Type Distribution
| Type | Count | Percentage | Avg Rating |
|------|-------|------------|------------|
| 📀 Album | 1,245 | 67.4% | 8.2/10 |
| 🎤 Live | 187 | 10.1% | 7.8/10 |
| 📦 Compilation | 156 | 8.4% | 7.5/10 |
| 🎵 EP | 89 | 4.8% | 8.0/10 |

## Folder Structure Analysis
- **Enhanced Structure**: 32.4% (46 bands)
- **Default Structure**: 62.7% (89 bands)
- **Average Compliance**: 78.5/100
- **Bands Needing Migration**: 45
```

---

## Prompts

### fetch_band_info

Template for fetching comprehensive band information with album type awareness.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `band_name` | string | Yes | Name of the band to fetch information for |
| `information_scope` | string | No | Scope: `basic`, `full`, `albums_only` (default: `full`) |
| `existing_albums` | array | No | List of known albums for missing album detection |

#### Template Features

- **Album Type Detection**: Instructions for identifying album types
- **Structure Analysis**: Guidelines for folder organization recommendations
- **Missing Album Detection**: Comparison with existing collection
- **Edition Recognition**: Detection of special editions and remasters

---

### analyze_band

Template for analyzing bands with type-specific analysis guidelines.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `band_name` | string | Yes | Name of the band to analyze |
| `analysis_scope` | string | No | Scope: `basic`, `full`, `albums_only` (default: `full`) |
| `albums` | array | No | List of albums to analyze |
| `analyze_missing_albums` | boolean | No | Include missing albums in analysis |

#### Template Features

- **Type-Specific Analysis**: Different criteria for different album types
- **Rating Guidelines**: Type-aware rating scales and criteria
- **Historical Context**: Analysis considering album type evolution
- **Collection Balance**: Recommendations for type diversity

---

### compare_bands

Template for comparing bands with album type distribution analysis.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `band_names` | array | Yes | List of band names to compare (minimum 2) |
| `comparison_aspects` | array | No | Aspects to compare: `style`, `discography`, `influence` |
| `comparison_scope` | string | No | Scope: `basic`, `full`, `summary` |

#### Template Features

- **Discography Comparison**: Album type distribution analysis
- **Evolution Analysis**: How album types evolved over time
- **Influence Assessment**: Impact on different album formats
- **Collection Recommendations**: Suggested album types to explore

---

### collection_insights

Template for generating collection-wide insights with type and structure analysis.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `analysis_focus` | string | No | Focus area: `types`, `structure`, `quality`, `gaps` |
| `include_recommendations` | boolean | No | Include improvement recommendations |

#### Template Features

- **Type Distribution Analysis**: Balance across album types
- **Structure Optimization**: Folder organization recommendations
- **Collection Gaps**: Missing album types and opportunities
- **Quality Assessment**: Type-specific quality metrics

---

## Error Handling

### Common Error Responses

```json
{
  "success": false,
  "error": "ValidationError",
  "message": "Invalid album type 'InvalidType'. Must be one of: Album, Compilation, EP, Live, Single, Demo, Instrumental, Split",
  "details": {
    "field": "album.type",
    "value": "InvalidType",
    "valid_values": ["Album", "Compilation", "EP", "Live", "Single", "Demo", "Instrumental", "Split"]
  }
}
```

### Album Type Validation Errors

- **Invalid Type**: When an unsupported album type is provided
- **Type Detection Failed**: When automatic type detection cannot determine type
- **Structure Mismatch**: When folder structure doesn't match declared type

### Compliance Validation Errors

- **Low Compliance Score**: When folder structure has significant issues
- **Missing Required Fields**: When album metadata lacks required type information
- **Structure Inconsistency**: When band has mixed structure patterns

---

## Version Information

- **API Version**: 1.1.0
- **Album Type System**: 1.0.0
- **Folder Structure Analysis**: 1.0.0
- **MCP Protocol**: 1.0.0
- **Last Updated**: 2025-01-30 