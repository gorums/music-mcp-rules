# Music Collection MCP Server - Usage Examples

## Overview

This guide provides comprehensive examples of using all MCP tools, resources, and prompts with real-world scenarios and album data.

## Getting Started

### Initial Setup and Collection Scan

Start by scanning your music collection to discover all bands and albums:

```json
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

**Expected Response:**
```json
{
  "status": "success",
  "results": {
    "total_bands": 150,
    "total_albums": 850,
    "music_files_found": 12500,
    "missing_albums": 25,
    "scan_duration": "15.2 seconds",
    "cache_used": false,
    "bands_updated": 5,
    "new_bands_found": 2
  },
  "tool_info": {
    "tool_name": "scan_music_folders",
    "version": "1.0.0"
  }
}
```

## MCP Tools Usage Examples

### Tool 1: scan_music_folders

#### Basic Collection Scan
```json
{
  "method": "tools/call",
  "params": {
    "name": "scan_music_folders",
    "arguments": {}
  }
}
```

#### Force Full Rescan (Bypass Cache)
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

#### Scan with Missing Album Detection
```json
{
  "method": "tools/call",
  "params": {
    "name": "scan_music_folders",
    "arguments": {
      "force_rescan": false,
      "include_missing_albums": true
    }
  }
}
```

### Tool 2: get_band_list

#### Basic Band List
```json
{
  "method": "tools/call",
  "params": {
    "name": "get_band_list",
    "arguments": {}
  }
}
```

**Response Example:**
```json
{
  "status": "success",
  "results": {
    "bands": [
      {
        "band_name": "Pink Floyd",
        "albums_count": 15,
        "missing_albums_count": 12,
        "physical_albums_count": 3,
        "has_metadata": true,
        "has_analysis": true,
        "last_updated": "2025-01-29T10:30:00Z",
        "albums": [
          {
            "album_name": "The Wall",
            "missing": false,
            "tracks_count": 26,
            "year": "1979"
          },
          {
            "album_name": "Dark Side of the Moon", 
            "missing": true,
            "year": "1973"
          }
        ]
      }
    ],
    "total_bands": 150,
    "page": 1,
    "page_size": 50,
    "total_pages": 3
  }
}
```

#### Filtered Band List by Genre
```json
{
  "method": "tools/call",
  "params": {
    "name": "get_band_list",
    "arguments": {
      "filter_genre": "Progressive Rock",
      "page": 1,
      "page_size": 20
    }
  }
}
```

#### Search Bands by Name
```json
{
  "method": "tools/call",
  "params": {
    "name": "get_band_list",
    "arguments": {
      "search": "floyd",
      "filter_has_analysis": true
    }
  }
}
```

#### Pagination Example
```json
{
  "method": "tools/call",
  "params": {
    "name": "get_band_list",
    "arguments": {
      "page": 2,
      "page_size": 25,
      "sort_by": "albums_count",
      "sort_order": "desc"
    }
  }
}
```

### Tool 3: save_band_metadata

#### Complete Band Metadata Save
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
        "genres": ["Progressive Rock", "Psychedelic Rock", "Art Rock"],
        "origin": "London, England",
        "members": [
          "David Gilmour (guitar, vocals)",
          "Nick Mason (drums)",
          "Roger Waters (bass, vocals) - former",
          "Richard Wright (keyboards) - former",
          "Syd Barrett (guitar, vocals) - former"
        ],
        "description": "English rock band formed in London in 1965. Gaining an early following as one of the first British psychedelic groups, they were distinguished for their extended compositions, sonic experimentation, philosophical lyrics and elaborate live shows.",
        "albums": [
          {
            "album_name": "The Wall",
            "missing": false,
            "tracks_count": 26,
            "duration": "81min",
            "year": "1979",
            "genres": ["Progressive Rock", "Concept Album"]
          },
          {
            "album_name": "Dark Side of the Moon",
            "missing": true,
            "tracks_count": 10,
            "duration": "43min", 
            "year": "1973",
            "genres": ["Progressive Rock", "Psychedelic Rock"]
          },
          {
            "album_name": "Wish You Were Here",
            "missing": true,
            "tracks_count": 5,
            "duration": "44min",
            "year": "1975", 
            "genres": ["Progressive Rock"]
          }
        ]
      }
    }
  }
}
```

#### Minimal Metadata Save
```json
{
  "method": "tools/call",
  "params": {
    "name": "save_band_metadata", 
    "arguments": {
      "band_name": "The Beatles",
      "metadata": {
        "band_name": "The Beatles",
        "formed": "1960",
        "genres": ["Rock", "Pop"],
        "origin": "Liverpool, England"
      }
    }
  }
}
```

### Tool 4: save_band_analyze

#### Complete Band Analysis with Album Reviews
```json
{
  "method": "tools/call",
  "params": {
    "name": "save_band_analyze",
    "arguments": {
      "band_name": "Pink Floyd",
      "analysis": {
        "review": "Pink Floyd stands as one of the most innovative and influential rock bands in history. Their sonic experimentation, philosophical depth, and conceptual approach to album-making set them apart from their contemporaries. From their early psychedelic explorations to their later progressive rock masterpieces, Pink Floyd consistently pushed the boundaries of what rock music could be.",
        "rate": 9,
        "albums": [
          {
            "album_name": "The Wall",
            "review": "A sprawling rock opera that explores themes of isolation, war, and mental breakdown. Roger Waters' deeply personal concept album is both Pink Floyd's most ambitious work and their most accessible. The narrative follows Pink, a rock star who builds a metaphorical wall around himself.",
            "rate": 9
          },
          {
            "album_name": "Dark Side of the Moon",
            "review": "Perhaps the greatest achievement in progressive rock history. This meditation on the human condition covers themes of conflict, greed, time, death, and mental illness. The album's seamless flow, innovative production, and universal themes make it a timeless masterpiece.",
            "rate": 10
          }
        ],
        "similar_bands": ["King Crimson", "Genesis", "Yes", "Jethro Tull", "The Moody Blues", "Radiohead"]
      },
      "analyze_missing_albums": false
    }
  }
}
```

#### Analysis with Missing Albums Included
```json
{
  "method": "tools/call",
  "params": {
    "name": "save_band_analyze",
    "arguments": {
      "band_name": "Pink Floyd",
      "analysis": {
        "review": "Comprehensive analysis covering their entire discography...",
        "rate": 9,
        "albums": [
          {
            "album_name": "The Wall",
            "review": "Physical album review...",
            "rate": 9
          },
          {
            "album_name": "Dark Side of the Moon",
            "review": "Missing album review...",
            "rate": 10
          },
          {
            "album_name": "Wish You Were Here", 
            "review": "Another missing album analysis...",
            "rate": 9
          }
        ],
        "similar_bands": ["King Crimson", "Genesis", "Yes"]
      },
      "analyze_missing_albums": true
    }
  }
}
```

#### Band-Only Analysis (No Album Reviews)
```json
{
  "method": "tools/call",
  "params": {
    "name": "save_band_analyze",
    "arguments": {
      "band_name": "Led Zeppelin",
      "analysis": {
        "review": "Led Zeppelin revolutionized hard rock and heavy metal with their powerful sound, innovative songwriting, and legendary live performances. Jimmy Page's guitar wizardry, Robert Plant's soaring vocals, John Paul Jones' versatile bass and keyboards, and John Bonham's thunderous drumming created a chemistry that has never been matched.",
        "rate": 10,
        "similar_bands": ["Black Sabbath", "Deep Purple", "The Who", "Cream", "Jimi Hendrix Experience"]
      }
    }
  }
}
```

### Tool 5: save_collection_insight

#### Complete Collection Insights
```json
{
  "method": "tools/call",
  "params": {
    "name": "save_collection_insight",
    "arguments": {
      "insights": [
        "Your collection heavily favors classic rock from the 1970s, representing 40% of all albums",
        "Progressive rock bands like Pink Floyd, Genesis, and Yes dominate your highest-rated albums",
        "There's a notable gap in modern indie and alternative rock from the 2000s onwards",
        "Your British rock representation is excellent, but American bands from the same era are underrepresented",
        "The collection shows a preference for concept albums and long-form musical narratives"
      ],
      "recommendations": [
        "Consider adding more modern progressive rock bands like Tool, Porcupine Tree, or Steven Wilson",
        "Expand into jazz fusion with artists like Weather Report, Return to Forever, or Mahavishnu Orchestra",
        "Add more American classic rock: The Allman Brothers, Lynyrd Skynyrd, The Eagles",
        "Explore krautrock pioneers: Can, Neu!, Kraftwerk to complement your progressive collection"
      ],
      "top_rated_bands": [
        {"band_name": "Pink Floyd", "rating": 9.5, "album_count": 15},
        {"band_name": "Led Zeppelin", "rating": 9.3, "album_count": 8},
        {"band_name": "The Beatles", "rating": 9.2, "album_count": 13},
        {"band_name": "King Crimson", "rating": 9.0, "album_count": 12},
        {"band_name": "Genesis", "rating": 8.8, "album_count": 15}
      ],
      "suggested_purchases": [
        {
          "album": "Dark Side of the Moon - Pink Floyd",
          "reason": "Essential masterpiece missing from your collection",
          "priority": "High"
        },
        {
          "album": "Led Zeppelin IV - Led Zeppelin", 
          "reason": "Classic album to complete your Zeppelin collection",
          "priority": "High"
        },
        {
          "album": "The Lamb Lies Down on Broadway - Genesis",
          "reason": "Peter Gabriel-era Genesis concept album masterpiece",
          "priority": "Medium"
        }
      ],
      "collection_health": {
        "status": "Excellent",
        "metadata_coverage": 85,
        "completion_rate": 78,
        "missing_albums_count": 127,
        "analysis_coverage": 65
      }
    }
  }
}
```

#### Minimal Collection Health Update
```json
{
  "method": "tools/call",
  "params": {
    "name": "save_collection_insight",
    "arguments": {
      "collection_health": {
        "status": "Good",
        "completion_rate": 82,
        "metadata_coverage": 90
      }
    }
  }
}
```

## MCP Resources Usage Examples

### Resource 1: band://info/{band_name}

#### Accessing Band Information
```
Resource URI: band://info/Pink Floyd
```

**Expected Markdown Response:**
```markdown
# Pink Floyd 🎸

## Band Overview
- **Formed**: 1965
- **Origin**: London, England  
- **Genres**: Progressive Rock, Psychedelic Rock, Art Rock
- **Collection Status**: 3/15 albums (20% complete) 📀

## Members
- David Gilmour (guitar, vocals)
- Nick Mason (drums)
- Roger Waters (bass, vocals) - former
- Richard Wright (keyboards) - former
- Syd Barrett (guitar, vocals) - former

## Description
English rock band formed in London in 1965. Gaining an early following as one of the first British psychedelic groups, they were distinguished for their extended compositions, sonic experimentation, philosophical lyrics and elaborate live shows.

## Albums in Collection (3/15)

| Album | Year | Tracks | Status | Rating |
|-------|------|--------|--------|--------|
| The Wall | 1979 | 26 | ✅ Local | ⭐ 9/10 |
| Dark Side of the Moon | 1973 | 10 | ❌ Missing | ⭐ 10/10 |
| Wish You Were Here | 1975 | 5 | ❌ Missing | ⭐ 9/10 |

## Analysis & Reviews

### Band Review (Rating: 9/10)
Pink Floyd stands as one of the most innovative and influential rock bands in history...

### Album Reviews
**The Wall (9/10)**: A sprawling rock opera that explores themes of isolation, war, and mental breakdown...

## Similar Bands
King Crimson, Genesis, Yes, Jethro Tull, The Moody Blues, Radiohead
```

### Resource 2: collection://summary

#### Accessing Collection Summary
```
Resource URI: collection://summary
```

**Expected Markdown Response:**
```markdown
# Music Collection Summary 🎵

## Collection Overview
- **Total Bands**: 150 🎸
- **Total Albums**: 850 💿
- **Physical Albums**: 723 📀
- **Missing Albums**: 127 ❌
- **Collection Status**: Large Collection 🏆

## Key Statistics
- **Completion Rate**: 85.1% ✅
- **Metadata Coverage**: 89.3% 📝
- **Analysis Coverage**: 67.3% 🔍
- **Health Status**: Excellent 💚

## Band Distribution Analysis

| Collection Size | Count | Percentage |
|----------------|-------|------------|
| Large (10+ albums) | 25 | 16.7% |
| Medium (5-9 albums) | 45 | 30.0% |
| Small (1-4 albums) | 80 | 53.3% |

## Missing Albums Analysis
- **Total Missing**: 127 albums
- **Completion Rate**: 85.1%
- **Top Missing Band**: Pink Floyd (12 missing albums)

## Collection Insights
- Your collection heavily favors classic rock from the 1970s
- Progressive rock dominates your highest-rated albums
- Strong British rock representation

## Top Rated Bands
1. Pink Floyd (9.5/10) - 15 albums
2. Led Zeppelin (9.3/10) - 8 albums  
3. The Beatles (9.2/10) - 13 albums

## Metadata Information
- **Last Collection Scan**: 2025-01-29 15:30:00
- **Index Version**: 1.2.0
- **Resource URI**: collection://summary
```

## MCP Prompts Usage Examples

### Prompt 1: fetch_band_info

#### Basic Band Information Prompt
```json
{
  "method": "prompts/get",
  "params": {
    "name": "fetch_band_info",
    "arguments": {
      "band_name": "Pink Floyd",
      "information_scope": "basic"
    }
  }
}
```

#### Full Band Information with Album Detection
```json
{
  "method": "prompts/get",
  "params": {
    "name": "fetch_band_info", 
    "arguments": {
      "band_name": "Pink Floyd",
      "information_scope": "full",
      "existing_albums": ["The Wall", "Animals", "Meddle"]
    }
  }
}
```

#### Albums-Only Information Scope
```json
{
  "method": "prompts/get",
  "params": {
    "name": "fetch_band_info",
    "arguments": {
      "band_name": "King Crimson",
      "information_scope": "albums_only",
      "existing_albums": ["In the Court of the Crimson King", "Red"]
    }
  }
}
```

### Prompt 2: analyze_band

#### Comprehensive Band Analysis
```json
{
  "method": "prompts/get",
  "params": {
    "name": "analyze_band",
    "arguments": {
      "band_name": "Pink Floyd",
      "analysis_scope": "full",
      "albums": ["The Wall", "Dark Side of the Moon", "Wish You Were Here"],
      "analyze_missing_albums": true
    }
  }
}
```

#### Album-Only Analysis
```json
{
  "method": "prompts/get",
  "params": {
    "name": "analyze_band",
    "arguments": {
      "band_name": "The Beatles",
      "analysis_scope": "albums_only", 
      "albums": ["Abbey Road", "Sgt. Pepper's", "Revolver", "White Album"]
    }
  }
}
```

### Prompt 3: compare_bands

#### Multi-Band Comparison
```json
{
  "method": "prompts/get",
  "params": {
    "name": "compare_bands",
    "arguments": {
      "band_names": ["Pink Floyd", "Genesis", "King Crimson", "Yes"],
      "comparison_scope": "full",
      "comparison_aspects": ["style", "discography", "influence", "innovation"]
    }
  }
}
```

#### Style-Focused Comparison
```json
{
  "method": "prompts/get",
  "params": {
    "name": "compare_bands",
    "arguments": {
      "band_names": ["Led Zeppelin", "Black Sabbath", "Deep Purple"],
      "comparison_scope": "basic",
      "comparison_aspects": ["style", "influence"]
    }
  }
}
```

### Prompt 4: collection_insights

#### Comprehensive Collection Analysis
```json
{
  "method": "prompts/get",
  "params": {
    "name": "collection_insights",
    "arguments": {
      "insights_scope": "comprehensive",
      "collection_data": {
        "total_bands": 150,
        "total_albums": 850,
        "genres": {"Progressive Rock": 45, "Classic Rock": 38, "Hard Rock": 32},
        "missing_albums": 127,
        "completion_rate": 85.1
      },
      "focus_areas": ["statistics", "recommendations", "health"]
    }
  }
}
```

## Real-World Workflow Examples

### Workflow 1: New Collection Setup

1. **Initial Scan**
```json
{"method": "tools/call", "params": {"name": "scan_music_folders", "arguments": {"force_rescan": true}}}
```

2. **Review Collection** 
```json
{"method": "tools/call", "params": {"name": "get_band_list", "arguments": {"page_size": 100}}}
```

3. **Check Collection Summary**
```
Resource: collection://summary
```

### Workflow 2: Band Research and Analysis

1. **Fetch Band Information**
```json
{"method": "prompts/get", "params": {"name": "fetch_band_info", "arguments": {"band_name": "Pink Floyd", "information_scope": "full"}}}
```

2. **Save Fetched Metadata**
```json
{"method": "tools/call", "params": {"name": "save_band_metadata", "arguments": {"band_name": "Pink Floyd", "metadata": {...}}}}
```

3. **Generate Analysis**
```json
{"method": "prompts/get", "params": {"name": "analyze_band", "arguments": {"band_name": "Pink Floyd", "analysis_scope": "full"}}}
```

4. **Save Analysis**
```json
{"method": "tools/call", "params": {"name": "save_band_analyze", "arguments": {"band_name": "Pink Floyd", "analysis": {...}}}}
```

5. **View Band Information**
```
Resource: band://info/Pink Floyd
```

### Workflow 3: Collection Analysis and Insights

1. **Compare Top Bands**
```json
{"method": "prompts/get", "params": {"name": "compare_bands", "arguments": {"band_names": ["Pink Floyd", "Genesis", "King Crimson"]}}}
```

2. **Generate Collection Insights**
```json
{"method": "prompts/get", "params": {"name": "collection_insights", "arguments": {"insights_scope": "comprehensive"}}}
```

3. **Save Insights**
```json
{"method": "tools/call", "params": {"name": "save_collection_insight", "arguments": {"insights": [...], "recommendations": [...]}}}
```

4. **Review Updated Summary**
```
Resource: collection://summary
```

## Error Handling Examples

### Invalid Band Name
```json
{
  "method": "tools/call",
  "params": {
    "name": "save_band_metadata",
    "arguments": {
      "band_name": "",
      "metadata": {...}
    }
  }
}
```

**Error Response:**
```json
{
  "status": "error",
  "error": "Band name cannot be empty",
  "validation_results": {
    "schema_valid": false,
    "validation_errors": ["band_name: Field required"]
  }
}
```

### Invalid Rating Value
```json
{
  "method": "tools/call", 
  "params": {
    "name": "save_band_analyze",
    "arguments": {
      "band_name": "Pink Floyd",
      "analysis": {
        "rate": 15,
        "review": "Great band"
      }
    }
  }
}
```

**Error Response:**
```json
{
  "status": "error",
  "error": "Analysis validation failed",
  "validation_results": {
    "schema_valid": false,
    "validation_errors": ["rate: Rating must be between 0 and 10"]
  }
}
```

## Performance Examples

### Large Collection Handling
```json
{
  "method": "tools/call",
  "params": {
    "name": "get_band_list",
    "arguments": {
      "page": 1,
      "page_size": 20,
      "filter_has_analysis": true,
      "sort_by": "albums_count", 
      "sort_order": "desc"
    }
  }
}
```

This approach handles large collections efficiently by using pagination and filtering.

For more examples and troubleshooting, see:
- [Configuration Guide](CONFIGURATION.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [API Documentation](API_DOCUMENTATION.md) 