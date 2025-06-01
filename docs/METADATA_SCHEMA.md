# Music Collection MCP Server - Metadata Schema Reference

## Overview

The Music Collection MCP Server uses a comprehensive JSON-based metadata schema to store information about bands, albums, and collection insights. This document provides detailed specifications for all data structures, validation rules, and examples.

## Schema Versions

- **Current Version**: 1.0
- **Migration Support**: From version 0.9 (automatic migration available)
- **Backwards Compatibility**: Maintained within major versions

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
      "genres": ["array of strings (optional)"],
      "tracks_count": "integer (optional)",
      "duration": "string (e.g., '45min', optional)",
      "missing": "boolean (default: false)"
    }
  ],
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

#### Album Information

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `album_name` | string | Yes | Non-empty, max 200 chars | Album title |
| `year` | string | No | YYYY format (1800-2100) | Release year |
| `genres` | array | No | Each string max 50 chars | Album-specific genres |
| `tracks_count` | integer | No | 1-999 | Number of tracks |
| `duration` | string | No | Format: "\d+min" | Album duration |
| `missing` | boolean | No | true/false | Whether album is missing locally |

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

### Validation Rules

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

### Example: Complete Band Metadata

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
      "genres": ["Progressive Rock", "Art Rock"],
      "tracks_count": 10,
      "duration": "43min",
      "missing": false
    },
    {
      "album_name": "The Wall",
      "year": "1979",
      "genres": ["Progressive Rock", "Rock Opera"],
      "tracks_count": 26,
      "duration": "81min",
      "missing": false
    },
    {
      "album_name": "Ummagumma",
      "year": "1969",
      "genres": ["Psychedelic Rock", "Experimental"],
      "tracks_count": 8,
      "duration": "86min",
      "missing": true
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
  }
}
```

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

## Data Migration

### Migration from Version 0.9 to 1.0

The server automatically handles migration from older schema versions:

#### Changes in Version 1.0
- Changed `genre` field to `genres` (array)
- Added `albums_count` auto-calculation
- Enhanced validation rules
- Added `analyze.albums` structure
- Improved error handling

#### Migration Process
1. **Backup**: Original files backed up with timestamp
2. **Transform**: Convert single `genre` to `genres` array
3. **Validate**: Apply new validation rules
4. **Update**: Save migrated data with new version

#### Migration Example

**Before (v0.9)**:
```json
{
  "band_name": "Pink Floyd",
  "genre": "Progressive Rock",
  "albums": [...]
}
```

**After (v1.0)**:
```json
{
  "band_name": "Pink Floyd",
  "genres": ["Progressive Rock"],
  "albums_count": 15,
  "albums": [...]
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