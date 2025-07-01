# Music Collection MCP Server - Metadata Schema Reference

## Overview

The Music Collection MCP Server uses a comprehensive JSON-based metadata schema to store information about bands, albums, collection insights, and folder structure analysis. This document provides detailed specifications for all data structures, validation rules, and examples.

## Schema Versions

- **Current Version**: 2.0 (Separated Albums Schema)
- **Migration Support**: Automatic migration from versions 1.x and 0.9
- **Backwards Compatibility**: Full backward compatibility with automatic schema conversion
- **Breaking Changes**: Albums now separated into `albums` (local) and `albums_missing` arrays

**NEW INPUT CONTRACT (2025-06):**
- Clients should send only the full `albums` array (the complete discography, both local and missing albums).
- The server will split this into local and missing albums based on what is present in the file system.
- The client should **NOT** send `albums_missing`. If present, it will be ignored and a warning may be returned. (Deprecated as of 2025-06)

---

## Band Metadata Schema

### File Location
- **Filename**: `.band_metadata.json`
- **Location**: Inside each band's folder
- **Encoding**: UTF-8

### Complete Schema

```json
{
  "band_name": "string (required)",
  "formed": "string (YYYY format, optional)",
  "genres": ["array of strings (optional)"],
  "origin": "string (optional)",
  "members": ["array of strings (optional)"],
  "albums_count": "integer (auto-calculated)",
  "description": "string (optional)",
  "albums": [
    {
      "album_name": "string (required)",
      "year": "string (YYYY format, optional)",
      "type": "string (AlbumType enum, optional, default: 'Album')",
      "edition": "string (optional)",
      "genres": ["array of strings (optional)"],
      "track_count": "integer (optional)",
      "duration": "string (e.g., '45min', optional)",
      "folder_path": "string (relative path from band folder, optional)",
      "track_count_missing": "integer (optional, only present if local album has fewer tracks than expected)",
      "not_found" : "boolean (optional, only present if local album was not found from the imput)" 
    }
  ],
  "albums_missing": [
    // DEPRECATED: This field is now computed server-side. Do not send from client.
    "album_name": "string (required)",
      "year": "string (YYYY format, optional)",
      "type": "string (AlbumType enum, optional, default: 'Album')",
      "edition": "string (optional)",
      "genres": ["array of strings (optional)"],
      "track_count": "integer (optional)",
      "duration": "string (e.g., '45min', optional)",
      "folder_path": "string (relative path from band folder, optional)"
  ],
  "local_albums_count": "integer (auto-calculated)",
  "missing_albums_count": "integer (auto-calculated)",
  "last_updated": "string (ISO 8601 datetime, auto-generated)",
  "analyze": {
    "review": "string (optional)",
    "rate": "integer (1-10, optional)",
    "albums": [
      {
        "album_name": "string (required for matching)",
        "review": "string (optional)",
        "rate": "integer (1-10, optional)"
      }
    ],
    "similar_bands": ["array of strings (optional)"]
  },
  "folder_structure": {
    "structure_type": "string (default/enhanced/mixed/legacy/unknown)",
    "consistency": "string (consistent/mostly_consistent/inconsistent/unknown)",
    "consistency_score": "integer (0-100)",
    "albums_analyzed": "integer (≥ 0)",
    "albums_with_year_prefix": "integer (≥ 0)",
    "albums_without_year_prefix": "integer (≥ 0)",
    "albums_with_type_folders": "integer (≥ 0)",
    "detected_patterns": ["array of strings"],
    "type_folders_found": ["array of strings"],
    "structure_score": "integer (0-100)",
    "recommendations": ["array of strings"],
    "issues": ["array of strings"],
    "analysis_metadata": {
      "pattern_counts": "object",
      "compliance_distribution": "object",
      "structure_health": "string",
      "album_type_distribution": "object (optional)",
      "edition_usage": "object (optional)"
    }
  }
}
```

### Field Specifications

#### Core Band Information

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `band_name` | string | Yes | Non-empty, max 200 chars | Official band name |
| `formed` | string | No | YYYY format (1800-2100) | Year band was formed |
| `genres` | array | No | Each string max 50 chars | Musical genres |
| `origin` | string | No | Max 100 chars | Geographic origin |
| `members` | array | No | Each string max 100 chars | Band members |
| `albums_count` | integer | Auto | ≥ 0 | Total albums (auto-calculated) |
| `description` | string | No | Max 2000 chars | Band description |
| `last_updated` | string | Auto | ISO 8601 format | Last modification timestamp |

#### Enhanced Album Information

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `album_name` | string | Yes | Non-empty, max 200 chars | Album title |
| `year` | string | No | YYYY format (1800-2100) | Release year |
| `type` | string | No | AlbumType enum | Album type classification |
| `edition` | string | No | Max 100 chars | Special edition information |
| `genres` | array | No | Each string max 50 chars | Album-specific genres |
| `track_count` | integer | No | 0-999 | Alias for tracks_count |
| `duration` | string | No | Format: "\d+min" | Album duration |
| `missing` | boolean | No | true/false | Whether album is missing locally |
| `folder_path` | string | No | Valid path | Relative path from band folder |
| `track_count_missing` | integer | No | 1-999 | Number of missing tracks (only present if local album has fewer tracks than expected) |
| `not_found` | boolena| No | true/false | Whether album is found locally |

#### Album Compliance Information

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `score` | integer | No | 0-100 inclusive | Compliance score |
| `level` | string | No | Enum values | Compliance level |
| `issues` | array | No | String array | List of compliance issues |
| `recommended_path` | string | No | Valid path | Recommended folder path |

#### Album Type Enumeration

The system supports 8 distinct album types:

| Type | Value | Description | Detection Keywords |
|------|-------|-------------|-------------------|
| **Album** | "Album" | Standard studio album | Default fallback |
| **Compilation** | "Compilation" | Greatest hits, collections | "greatest hits", "best of", "collection", "anthology", "compilation" |
| `EP` | "EP" | Extended Play | "ep", "e.p." |
| **Live** | "Live" | Live recordings | "live", "concert", "unplugged", "acoustic", "live at" |
| **Single** | "Single" | Single releases | "single" |
| **Demo** | "Demo" | Demo recordings | "demo", "demos", "early recordings", "unreleased" |
| **Instrumental** | "Instrumental" | Instrumental versions | "instrumental", "instrumentals" |
| **Split** | "Split" | Split releases | "split", "vs.", "vs", "versus", "with" |

#### Analysis Information

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `review` | string | No | Max 5000 chars | Band review |
| `rate` | integer | No | 1-10 inclusive | Band rating |
| `similar_bands` | array | No | Each string max 100 chars | Similar bands list |

#### Album Analysis

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `album_name` | string | Yes | Must match existing album | Album identifier |
| `review` | string | No | Max 5000 chars | Album review |
| `rate` | integer | No | 1-10 inclusive | Album rating |

#### Folder Structure Information

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `structure_type` | string | No | Enum values | Primary structure type |
| `consistency` | string | No | Enum values | Consistency level assessment |
| `consistency_score` | integer | No | 0-100 inclusive | Numerical consistency score |
| `albums_analyzed` | integer | No | ≥ 0 | Number of albums analyzed |
| `albums_with_year_prefix` | integer | No | ≥ 0 | Albums following year prefix pattern |
| `albums_without_year_prefix` | integer | No | ≥ 0 | Albums missing year prefix |
| `albums_with_type_folders` | integer | No | ≥ 0 | Albums in type-based folders |
| `detected_patterns` | array | No | String array | List of detected folder patterns |
| `type_folders_found` | array | No | String array | List of type folders found |
| `structure_score` | integer | No | 0-100 inclusive | Overall structure organization score |
| `recommendations` | array | No | String array | Improvement recommendations |
| `issues` | array | No | String array | Identified structure issues |
| `analysis_metadata` | object | No | Object | Additional analysis data |

#### Structure Type Values
- **default**: Standard flat structure with "YYYY - Album Name (Edition?)" pattern
- **enhanced**: Type-based structure with "Type/YYYY - Album Name (Edition?)" pattern  
- **mixed**: Combination of both default and enhanced structures
- **legacy**: Albums without year prefix, just "Album Name" pattern
- **unknown**: Unable to determine structure type

#### Consistency Level Values
- **consistent**: All albums follow the same pattern (90-100% consistency)
- **mostly_consistent**: Most albums follow the same pattern (70-89% consistency)
- **inconsistent**: Albums use multiple different patterns (below 70% consistency)
- **unknown**: Unable to determine consistency

#### Compliance Level Values
- **excellent**: 90-100 compliance score
- **good**: 70-89 compliance score
- **fair**: 50-69 compliance score
- **poor**: 25-49 compliance score
- **critical**: 0-24 compliance score

### Validation Rules

#### Album Type Validation
- **Format**: String enum value
- **Valid Values**: "Album", "Compilation", "EP", "Live", "Single", "Demo", "Instrumental", "Split"
- **Case Sensitivity**: Must match exact casing
- **Default**: "Album" if not specified
- **Auto-Detection**: System can automatically detect types from folder names

#### Edition Validation
- **Format**: String
- **Common Values**: "Deluxe Edition", "Limited Edition", "Remastered", "Anniversary Edition"
- **Max Length**: 100 characters
- **Normalization**: System removes wrapping parentheses if present

#### Compliance Validation
- **Score Range**: 0-100 (inclusive)
- **Level Values**: Must be one of: excellent, good, fair, poor, critical
- **Issues**: Array of descriptive strings
- **Recommended Path**: Must be valid folder path format

#### Genre Validation
- **Format**: String array
- **Valid Examples**: `["Progressive Rock", "Jazz Fusion", "Electronic"]`
- **Case Sensitivity**: Preserved as entered
- **Maximum Length**: 50 characters per genre
- **Maximum Count**: 10 genres per band/album

#### Year Validation
- **Format**: String in YYYY format
- **Range**: 1800-2100
- **Examples**: `"1973"`, `"2024"`
- **Invalid**: `"73"`, `"1973-1975"`, `"Unknown"`

#### Rating Validation
- **Range**: 1-10 (inclusive)
- **Type**: Integer only
- **Examples**: `8`, `10`
- **Invalid**: `0`, `11`, `8.5`, `"8"`

#### Duration Format
- **Pattern**: `\d+min`
- **Examples**: `"45min"`, `"67min"`, `"128min"`
- **Invalid**: `"45m"`, `"1h 5min"`, `"45 minutes"`

#### Folder Structure Validation
- **Structure Type**: Must be one of: default, enhanced, mixed, legacy, unknown
- **Consistency**: Must be one of: consistent, mostly_consistent, inconsistent, unknown
- **Scores**: All score fields must be integers between 0-100
- **Counts**: All count fields must be non-negative integers
- **Arrays**: Pattern and folder arrays contain strings
- **Health Values**: excellent, good, fair, poor, critical

### Example: Complete Band Metadata with Album Types

```json
{
  "band_name": "Pink Floyd",
  "formed": "1965",
  "genres": ["Progressive Rock", "Psychedelic Rock", "Art Rock"],
  "origin": "London, England",
  "members": [
    "David Gilmour (guitar, vocals)",
    "Roger Waters (bass, vocals)",
    "Nick Mason (drums)",
    "Richard Wright (keyboards)"
  ],
  "albums_count": 15,
  "description": "Pioneering progressive rock band known for their philosophical lyrics, sonic experimentation, elaborate live shows, and conceptual albums. One of the most commercially successful and influential groups in popular music history.",
  "albums": [
    {
      "album_name": "The Dark Side of the Moon",
      "year": "1973",
      "type": "Album",
      "edition": "",
      "genres": ["Progressive Rock", "Art Rock"],
      "track_count": 10,
      "track_count_missing": 2,
      "duration": "43min",
      "folder_path": "Album/1973 - The Dark Side of the Moon"
    },
    {
      "album_name": "The Wall",
      "year": "1979",
      "type": "Album",
      "edition": "Deluxe Edition",
      "genres": ["Progressive Rock", "Rock Opera"],
      "track_count": 26,
      "track_count_missing": 0,
      "duration": "81min",
      "folder_path": "Album/1979 - The Wall (Deluxe Edition)"
    },
    {
      "album_name": "Live at Pompeii",
      "year": "1972",
      "type": "Live",
      "edition": "",
      "genres": ["Progressive Rock", "Live"],
      "track_count": 8,
      "track_count_missing": 0,
      "duration": "65min",
      "folder_path": "Live/1972 - Live at Pompeii"
    },
    {
      "album_name": "Greatest Hits",
      "year": "1996",
      "type": "Compilation",
      "edition": "",
      "genres": ["Progressive Rock"],
      "track_count": 16,
      "track_count_missing": 0,
      "duration": "78min"
    }
  ],  
  "last_updated": "2024-01-15T10:30:00Z",
  "analyze": {
    "review": "Pink Floyd revolutionized progressive rock with their atmospheric soundscapes and conceptual albums. Their ability to blend experimental music with accessible melodies created a unique sound that influenced countless artists. The band's exploration of philosophical themes, combined with innovative use of studio effects and extended compositions, set new standards for rock music.",
    "rate": 9,
    "albums": [
      {
        "album_name": "The Dark Side of the Moon",
        "review": "A masterpiece of progressive rock that explores themes of conflict, greed, time, and mental illness. The album's seamless flow, innovative sound effects, and philosophical depth make it one of the greatest albums ever recorded.",
        "rate": 10
      },
      {
        "album_name": "The Wall",
        "review": "An ambitious rock opera that tells the story of Pink's psychological isolation. The album combines powerful storytelling with complex musical arrangements, creating an immersive experience that works both as music and narrative.",
        "rate": 9
      }
    ],
    "similar_bands": ["Genesis", "Yes", "King Crimson", "Gentle Giant", "Emerson Lake & Palmer"]
  },
  "folder_structure": {
    "structure_type": "enhanced",
    "consistency": "consistent",
    "consistency_score": 95,
    "albums_analyzed": 14,
    "albums_with_year_prefix": 14,
    "albums_without_year_prefix": 0,
    "albums_with_type_folders": 14,
    "detected_patterns": ["enhanced_with_edition", "enhanced_no_edition"],
    "type_folders_found": ["Album", "Live", "Compilation"],
    "structure_score": 92,
    "recommendations": [],
    "issues": [],
    "analysis_metadata": {
      "pattern_counts": {
        "enhanced_with_edition": 8,
        "enhanced_no_edition": 6
      },
      "compliance_distribution": {
        "excellent": 13,
        "good": 1,
        "fair": 0,
        "poor": 0,
        "critical": 1
      },
      "structure_health": "excellent",
      "album_type_distribution": {
        "Album": 11,
        "Live": 2,
        "Compilation": 2
      },
      "edition_usage": {
        "Deluxe Edition": 3,
        "Remastered": 2,
        "": 10
      }
    }
  }
}
```

## Album Type Detection Examples

### Automatic Type Detection from Folder Names

The system automatically detects album types using intelligent keyword matching:

```json
// Live albums
"1985 - Live at Wembley" → type: "Live"
"Unplugged in New York" → type: "Live"
"Acoustic Sessions" → type: "Live"

// Demo albums  
"1982 - Early Demos" → type: "Demo"
"Unreleased Tracks" → type: "Demo"
"Rough Mixes" → type: "Demo"

// Compilation albums
"Greatest Hits" → type: "Compilation"
"Best of Queen" → type: "Compilation"
"The Collection" → type: "Compilation"

// EP albums
"Love EP" → type: "EP"
"Extended Play" → type: "EP"

// Instrumental albums
"Album (Instrumental)" → type: "Instrumental"
"Instrumentals Collection" → type: "Instrumental"

// Split albums
"Band A vs. Band B" → type: "Split"
"Split Series Vol. 1" → type: "Split"

// Standard albums (default)
"1980 - Back in Black" → type: "Album"
"Dark Side of the Moon" → type: "Album"
```

### Enhanced Folder Structure Detection

The system recognizes type-based folder structures:

```
Pink Floyd/
├── Album/                  ← Type folder detected
│   ├── 1973 - The Dark Side of the Moon/
│   └── 1979 - The Wall/
├── Live/                   ← Type folder detected
│   └── 1985 - Live at Wembley/
└── Compilation/            ← Type folder detected
    └── 1996 - Greatest Hits/
```

## Migration and Compatibility

### Schema Version Migration

The system automatically migrates older schema versions:

- **From 1.0 to 1.1**: Adds album type and compliance fields with defaults
- **From 0.9 to 1.1**: Comprehensive migration including structure analysis
- **Backwards Compatibility**: Existing metadata remains functional

### Default Values for New Fields

When migrating existing metadata:
- `type`: Defaults to "Album", then auto-detection runs
- `edition`: Defaults to empty string
- `compliance`: Generated during next scan
- `folder_structure`: Analyzed during next scan

This comprehensive schema supports the full range of album type classification and folder structure analysis features while maintaining backwards compatibility with existing collections.

---

## Collection Index Schema

### File Location
- **Filename**: `.collection_index.json`
- **Location**: Music collection root directory
- **Purpose**: Fast access to collection overview

### Complete Schema

```json
{
  "version": "string (schema version)",
  "last_updated": "string (ISO 8601 datetime)",
  "last_scan": "string (ISO 8601 datetime)",
  "collection_path": "string (absolute path)",
  "stats": {
    "total_bands": "integer",
    "total_albums": "integer",
    "total_missing_albums": "integer",
    "bands_with_metadata": "integer",
    "bands_with_analysis": "integer",
    "completion_percentage": "number (0-100)"
  },
  "bands": [
    {
      "band_name": "string",
      "folder_path": "string (relative path)",
      "albums_count": "integer",
      "local_albums": "integer",
      "missing_albums": "integer",
      "has_metadata": "boolean",
      "has_analysis": "boolean",
      "last_updated": "string (ISO 8601 datetime)"
    }
  ],
  "insights": {
    "insights": ["array of strings (optional)"],
    "recommendations": ["array of strings (optional)"],
    "top_rated_bands": [
      {
        "band_name": "string",
        "rating": "integer (1-10)"
      }
    ],
    "suggested_purchases": ["array of strings (optional)"],
    "collection_health": {
      "completion_percentage": "number (0-100)",
      "metadata_coverage": "number (0-100)",
      "analysis_coverage": "number (0-100)",
      "total_bands": "integer",
      "analyzed_bands": "integer",
      "missing_albums_count": "integer",
      "health_score": "number (0-10)"
    }
  }
}
```

### Example: Collection Index

```json
{
  "version": "1.0",
  "last_updated": "2024-01-15T10:30:00Z",
  "last_scan": "2024-01-15T09:15:00Z",
  "collection_path": "/music/collection",
  "stats": {
    "total_bands": 142,
    "total_albums": 1847,
    "total_missing_albums": 224,
    "bands_with_metadata": 127,
    "bands_with_analysis": 89,
    "completion_percentage": 87.9
  },
  "bands": [
    {
      "band_name": "Pink Floyd",
      "folder_path": "Pink Floyd",
      "albums_count": 15,
      "local_albums": 13,
      "missing_albums": 2,
      "has_metadata": true,
      "has_analysis": true,
      "last_updated": "2024-01-15T10:30:00Z"
    },
    {
      "band_name": "Genesis",
      "folder_path": "Genesis",
      "albums_count": 18,
      "local_albums": 12,
      "missing_albums": 6,
      "has_metadata": true,
      "has_analysis": false,
      "last_updated": "2024-01-10T14:20:00Z"
    }
  ],
  "insights": {
    "insights": [
      "Progressive rock is heavily represented with 35 bands (24.6% of collection)",
      "Most albums are from the 1970s golden era (42% of collection)",
      "Average band rating is 7.8/10 across analyzed bands"
    ],
    "recommendations": [
      "Consider adding more contemporary progressive bands",
      "Fill gaps in classic album collections for Genesis and Yes",
      "Focus on acquiring missing albums from highly-rated bands"
    ],
    "top_rated_bands": [
      {"band_name": "Pink Floyd", "rating": 9},
      {"band_name": "King Crimson", "rating": 9},
      {"band_name": "Yes", "rating": 8}
    ],
    "collection_health": {
      "completion_percentage": 87.9,
      "metadata_coverage": 89.4,
      "analysis_coverage": 62.7,
      "total_bands": 142,
      "analyzed_bands": 89,
      "missing_albums_count": 224,
      "health_score": 8.2
    }
  }
}
```

---

## Performance Considerations

### File Size Guidelines
- **Band Metadata**: Typically 2-50 KB per file
- **Collection Index**: Scales with collection size (1-10 MB for large collections)
- **Maximum Recommended**: 100 MB per band metadata file

### Optimization Tips
1. **Limit Review Length**: Keep reviews under 5000 characters
2. **Reasonable Album Count**: No hard limit, but performance degrades beyond 1000 albums per band
3. **Genre Limits**: Maximum 10 genres per band/album for better categorization
4. **Member Lists**: Consider abbreviated member lists for bands with many members

### Indexing Strategy
- Collection index provides fast access without parsing individual files
- Band-specific data loaded on-demand
- Automatic cache invalidation based on file timestamps

---

## Validation and Error Handling

### Validation Levels

#### Strict Validation (Default)
- All required fields must be present
- All fields must pass type and format validation
- Referenced albums in analysis must exist

#### Lenient Validation (Migration Mode)
- Missing optional fields are filled with defaults
- Invalid values are converted when possible
- Warnings generated for data quality issues

### Common Validation Errors

| Error | Cause | Resolution |
|-------|-------|------------|
| `INVALID_YEAR_FORMAT` | Year not in YYYY format | Use 4-digit year: `"1973"` |
| `RATING_OUT_OF_RANGE` | Rating not 1-10 | Use integer 1-10: `8` |
| `MISSING_REQUIRED_FIELD` | Required field absent | Add required field |
| `ALBUM_NOT_FOUND` | Album in analysis not in albums array | Add album or remove analysis |
| `INVALID_DURATION_FORMAT` | Duration format wrong | Use format: `"45min"` |

### Data Quality Warnings

| Warning | Cause | Impact |
|---------|-------|--------|
| `MISSING_GENRE` | No genres specified | Reduced filtering capability |
| `LONG_REVIEW` | Review over 5000 chars | Performance impact |
| `DUPLICATE_ALBUM` | Album name appears twice | Data inconsistency |
| `MISSING_YEAR` | Album without year | Limited chronological analysis |

---

## Best Practices

### Data Entry Guidelines

1. **Consistent Naming**: Use official band and album names
2. **Genre Standardization**: Use established genre names
3. **Complete Information**: Fill all relevant fields
4. **Review Quality**: Write informative, concise reviews
5. **Rating Consistency**: Use consistent rating criteria

### File Management

1. **Backup Strategy**: Regular backups of metadata files
2. **Version Control**: Consider versioning for large collections
3. **Access Control**: Proper file permissions for concurrent access
4. **Storage Location**: Keep metadata files with music files

### Performance Optimization

1. **Incremental Updates**: Use partial scans when possible
2. **Batch Operations**: Group multiple metadata updates
3. **Index Maintenance**: Regular collection index updates
4. **Cache Strategy**: Leverage built-in caching mechanisms

### Data Integrity

1. **Validation**: Always validate before saving
2. **Atomic Operations**: Use atomic file writes
3. **Backup Creation**: Automatic backups before modifications
4. **Recovery Procedures**: Test data recovery processes

---

## Schema Extensions

### Custom Fields

The schema supports custom fields for specialized use cases:

```json
{
  "band_name": "Pink Floyd",
  "custom_fields": {
    "record_label": "EMI",
    "producer": "Various",
    "personal_notes": "Saw them live in 1975"
  }
}
```

### Plugin Integration

Future schema versions will support:
- Plugin-specific metadata sections
- Extended validation rules
- Custom field types
- External data source integration

### Version Compatibility

- **Forward Compatibility**: Newer versions ignore unknown fields
- **Backward Compatibility**: Older versions work with core fields
- **Migration Path**: Automatic migration between versions
- **Validation Modes**: Strict and lenient modes for different use cases 

**Deprecation Note:**
- `albums_missing` is now computed server-side. Clients should send only the full `albums` array. Sending `albums_missing` is deprecated and will be ignored. 