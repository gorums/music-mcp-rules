# Music Collection MCP Server - Usage Examples with Album Type Classification

## Overview

This guide provides comprehensive examples of using all MCP tools, resources, and prompts with real-world scenarios, focusing on the new album type classification and folder structure analysis features.

## Getting Started

### Initial Setup and Collection Scan with Type Detection

Start by scanning your music collection to discover all bands, albums, and automatically detect album types:

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

**Expected Response with Album Type Classification:**
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
    "new_bands_found": 2,
    "album_type_distribution": {
      "Album": 632,
      "Live": 97,
      "Compilation": 73,
      "EP": 28,
      "Demo": 15,
      "Single": 3,
      "Instrumental": 2,
      "Split": 0
    },
    "structure_analysis": {
      "enhanced_structure_bands": 45,
      "default_structure_bands": 89,
      "legacy_structure_bands": 16,
      "average_compliance_score": 78
    }
  },
  "tool_info": {
    "tool_name": "scan_music_folders",
    "version": "1.1.0"
  }
}
```

## MCP Tools Usage Examples with Album Type Features

### Tool 1: scan_music_folders (Enhanced)

#### Basic Collection Scan with Type Detection
```json
{
  "method": "tools/call",
  "params": {
    "name": "scan_music_folders",
    "arguments": {}
  }
}
```

#### Force Full Rescan with Structure Analysis
```json
{
  "method": "tools/call",
  "params": {
    "name": "scan_music_folders",
    "arguments": {
      "force_rescan": true,
      "analyze_structure": true
    }
  }
}
```

#### Scan with Type-Specific Focus
```json
{
  "method": "tools/call",
  "params": {
    "name": "scan_music_folders",
    "arguments": {
      "force_rescan": false,
      "include_missing_albums": true,
      "detect_album_types": true
    }
  }
}
```

### Tool 2: get_band_list (Enhanced with Type Filtering)

#### Basic Band List with Album Types
```json
{
  "method": "tools/call",
  "params": {
    "name": "get_band_list",
    "arguments": {}
  }
}
```

**Response Example with Album Types:**
```json
{
  "status": "success",
  "results": {
    "bands": [
      {
        "band_name": "Pink Floyd",
        "albums_count": 15,
        "missing_albums_count": 3,
        "physical_albums_count": 12,
        "has_metadata": true,
        "has_analysis": true,
        "last_updated": "2025-01-29T10:30:00Z",
        "album_type_distribution": {
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
          },
          {
            "album_name": "Live at Pompeii",
            "type": "Live", 
            "year": "1972",
            "missing": false,
            "tracks_count": 8,
            "compliance": {
              "score": 95,
              "level": "excellent",
              "issues": []
            }
          },
          {
            "album_name": "Early Demos",
            "type": "Demo",
            "year": "1967",
            "missing": true,
            "compliance": {
              "score": 0,
              "level": "critical",
              "issues": ["Album folder missing"]
            }
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

#### Filter Bands by Album Type
```json
{
  "method": "tools/call",
  "params": {
    "name": "get_band_list",
    "arguments": {
      "filter_album_types": ["Live", "Demo"],
      "page": 1,
      "page_size": 20
    }
  }
}
```

#### Filter by Folder Structure Compliance
```json
{
  "method": "tools/call",
  "params": {
    "name": "get_band_list",
    "arguments": {
      "filter_compliance_level": ["excellent", "good"],
      "filter_structure_type": "enhanced"
    }
  }
}
```

#### Search Bands with Poor Structure Compliance
```json
{
  "method": "tools/call",
  "params": {
    "name": "get_band_list",
    "arguments": {
      "filter_compliance_level": ["poor", "critical"],
      "sort_by": "compliance_score",
      "sort_order": "asc"
    }
  }
}
```

#### Filter by Structure Type
```json
{
  "method": "tools/call",
  "params": {
    "name": "get_band_list",
    "arguments": {
      "filter_structure_type": "legacy",
      "filter_has_analysis": true
    }
  }
}
```

### Tool 3: save_band_metadata (Enhanced with Types)

#### Complete Band Metadata Save with Album Types
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
          "Roger Waters (bass, vocals)",
          "Nick Mason (drums)",
          "Richard Wright (keyboards)"
        ],
        "description": "Pioneering progressive rock band known for their philosophical lyrics and conceptual albums.",
        "albums": [
          {
            "album_name": "The Dark Side of the Moon",
            "year": "1973",
            "type": "Album",
            "edition": "",
            "genres": ["Progressive Rock", "Art Rock"],
            "tracks_count": 10,
            "duration": "43min",
            "missing": false
          },
          {
            "album_name": "Live at Pompeii",
            "year": "1972",
            "type": "Live",
            "edition": "",
            "genres": ["Progressive Rock", "Live"],
            "tracks_count": 8,
            "duration": "65min",
            "missing": false
          },
          {
            "album_name": "Greatest Hits",
            "year": "1996",
            "type": "Compilation",
            "edition": "",
            "genres": ["Progressive Rock"],
            "tracks_count": 16,
            "duration": "78min",
            "missing": true
          }
        ]
      }
    }
  }
}
```

#### Save Metadata with Folder Structure Information
```json
{
  "method": "tools/call",
  "params": {
    "name": "save_band_metadata",
    "arguments": {
      "band_name": "Queen",
      "metadata": {
        "band_name": "Queen",
        "formed": "1970",
        "genres": ["Rock", "Progressive Rock", "Art Rock"],
        "albums": [
          {
            "album_name": "A Night at the Opera",
            "year": "1975",
            "type": "Album",
            "edition": "Deluxe Edition"
          }
        ],
        "folder_structure": {
          "structure_type": "enhanced",
          "consistency": "consistent",
          "consistency_score": 95,
          "albums_analyzed": 12,
          "albums_with_type_folders": 12,
          "type_folders_found": ["Album", "Live", "Compilation"],
          "structure_score": 92,
          "recommendations": [],
          "issues": []
        }
      }
    }
  }
}
```

### Enhanced Album Type Examples

#### Save Different Album Types
```json
{
  "method": "tools/call",
  "params": {
    "name": "save_band_metadata",
    "arguments": {
      "band_name": "Iron Maiden",
      "metadata": {
        "band_name": "Iron Maiden",
        "albums": [
          {
            "album_name": "The Number of the Beast",
            "year": "1982",
            "type": "Album",
            "tracks_count": 8,
            "missing": false
          },
          {
            "album_name": "Live After Death",
            "year": "1985", 
            "type": "Live",
            "tracks_count": 15,
            "missing": false
          },
          {
            "album_name": "Running Free EP",
            "year": "1980",
            "type": "EP",
            "tracks_count": 4,
            "missing": false
          },
          {
            "album_name": "Best of the Beast",
            "year": "1996",
            "type": "Compilation",
            "tracks_count": 18,
            "missing": false
          },
          {
            "album_name": "The Soundhouse Tapes",
            "year": "1978",
            "type": "Demo",
            "tracks_count": 3,
            "missing": true
          }
        ]
      }
    }
  }
}
```

### Tool 4: Album Type Distribution Analysis

#### Get Type-Specific Collection Statistics
```json
{
  "method": "tools/call",
  "params": {
    "name": "get_band_list",
    "arguments": {
      "include_type_stats": true,
      "sort_by": "album_type_diversity",
      "sort_order": "desc"
    }
  }
}
```

**Response with Type Statistics:**
```json
{
  "status": "success",
  "results": {
    "bands": [...],
    "collection_statistics": {
      "total_albums_by_type": {
        "Album": 632,
        "Live": 97,
        "Compilation": 73,
        "EP": 28,
        "Demo": 15,
        "Single": 3,
        "Instrumental": 2,
        "Split": 0
      },
      "bands_by_type_presence": {
        "has_albums": 150,
        "has_live": 87,
        "has_compilations": 45,
        "has_eps": 23,
        "has_demos": 12,
        "has_singles": 3,
        "has_instrumentals": 2,
        "has_splits": 0
      },
      "type_diversity_analysis": {
        "most_diverse_bands": [
          {
            "band_name": "Metallica",
            "types_count": 6,
            "types": ["Album", "Live", "Demo", "EP", "Compilation", "Instrumental"]
          }
        ],
        "missing_type_recommendations": [
          {
            "band_name": "Pink Floyd",
            "missing_types": ["Single", "Split"],
            "recommendation": "Consider adding singles collection"
          }
        ]
      }
    }
  }
}
```

## Resources Usage Examples with Album Types

### Resource 1: band://info/{band_name} (Enhanced)

#### Access Band Information with Type Organization
```json
{
  "method": "resources/read",
  "params": {
    "uri": "band://info/Pink Floyd"
  }
}
```

**Enhanced Response with Album Type Organization:**
```markdown
# 🎵 Pink Floyd

## Band Information
- **Formed**: 1965
- **Origin**: London, England  
- **Genres**: Progressive Rock, Psychedelic Rock, Art Rock
- **Albums**: 15 total (12 local, 3 missing)

## 🎵 Available Albums

### 💿 Albums (9)

**1973 - The Dark Side of the Moon** ⭐ 10/10  
*Progressive Rock, Art Rock* • 10 tracks • 43min  
📁 `Album/1973 - The Dark Side of the Moon`  
✅ Excellent compliance (100/100)

**1979 - The Wall** ⭐ 9/10  
*Progressive Rock, Rock Opera* • 26 tracks • 81min  
📁 `Album/1979 - The Wall (Deluxe Edition)`  
✅ Excellent compliance (100/100)

### 🎤 Live Albums (3)

**1972 - Live at Pompeii**  
*Progressive Rock, Live* • 8 tracks • 65min  
📁 `Live/1972 - Live at Pompeii`  
✅ Excellent compliance (100/100)

**1988 - Delicate Sound of Thunder**  
*Progressive Rock, Live* • 19 tracks • 99min  
📁 `Live/1988 - Delicate Sound of Thunder`  
✅ Excellent compliance (95/100)

### 📦 Compilations (2)

**1996 - Greatest Hits** ❌ Missing  
*Progressive Rock* • 16 tracks • 78min  
📁 *Recommended: `Compilation/1996 - Greatest Hits`*  
❌ Critical compliance (0/100) - Album folder missing

### 🔧 Demos (1)

**1967 - Early Singles** ❌ Missing  
*Psychedelic Rock, Demo* • 4 tracks  
📁 *Recommended: `Demo/1967 - Early Singles`*  
❌ Critical compliance (0/100) - Album folder missing

## 📊 Collection Analysis

### Album Type Distribution
- **Albums**: 9/15 (60%) - Strong studio collection ✅
- **Live**: 3/15 (20%) - Good live representation ✅  
- **Compilations**: 2/15 (13%) - Reasonable ✅
- **Demos**: 1/15 (7%) - Could expand 🔶
- **Missing Types**: EP, Single, Instrumental, Split

### Folder Structure Health
- **Structure Type**: Enhanced (type-based folders)
- **Compliance Score**: 92/100 (Excellent)
- **Organization**: Consistent pattern across collection
- **Recommendations**: Collection is well-organized overall

## 🎯 Analysis & Reviews

**Overall Rating**: ⭐ 9/10

Pink Floyd revolutionized progressive rock with their atmospheric soundscapes and conceptual albums. Their ability to blend experimental music with accessible melodies created a unique sound that influenced countless artists.

**Similar Bands**: Genesis, Yes, King Crimson, Gentle Giant, Emerson Lake & Palmer
```

### Resource 2: collection://summary (Enhanced)

#### Get Collection Overview with Type Analysis
```json
{
  "method": "resources/read", 
  "params": {
    "uri": "collection://summary"
  }
}
```

**Enhanced Response with Album Type Statistics:**
```markdown
# 🎵 Music Collection Summary

## Collection Overview
- **Total Bands**: 150
- **Total Albums**: 850 (825 local, 25 missing)
- **Total Tracks**: 12,500+ 
- **Collection Completion**: 97.1%
- **Last Updated**: 2025-01-29 10:30 UTC

## 📊 Album Type Distribution

### By Type
| Type | Count | Percentage | Avg per Band |
|------|-------|------------|--------------|
| 💿 **Album** | 632 | 74.4% | 4.2 |
| 🎤 **Live** | 97 | 11.4% | 0.6 |
| 📦 **Compilation** | 73 | 8.6% | 0.5 |
| 💽 **EP** | 28 | 3.3% | 0.2 |
| 🔧 **Demo** | 15 | 1.8% | 0.1 |
| 🎵 **Single** | 3 | 0.4% | 0.02 |
| 🎼 **Instrumental** | 2 | 0.2% | 0.01 |
| 🤝 **Split** | 0 | 0.0% | 0.0 |

### Collection Balance Assessment
- ✅ **Strong**: Studio albums (74.4%) - Excellent foundation
- ✅ **Good**: Live albums (11.4%) - Well represented  
- ✅ **Adequate**: Compilations (8.6%) - Reasonable coverage
- 🔶 **Could Improve**: EPs (3.3%) - Consider expanding
- 🔶 **Limited**: Demos (1.8%) - Opportunity for rare material
- ⚠️ **Missing**: Singles, Instrumentals, Splits - Consider adding

## 🏗️ Folder Structure Analysis

### Structure Type Distribution
| Structure Type | Bands | Percentage | Avg Compliance |
|----------------|-------|------------|---------------|
| **Enhanced** | 45 | 30.0% | 94.2 |
| **Default** | 89 | 59.3% | 82.1 |
| **Legacy** | 16 | 10.7% | 45.8 |

### Compliance Level Distribution
| Level | Albums | Percentage | Score Range |
|-------|--------|------------|-------------|
| ✅ **Excellent** | 623 | 73.3% | 90-100 |
| ✅ **Good** | 156 | 18.4% | 70-89 |
| 🔶 **Fair** | 46 | 5.4% | 50-69 |
| ⚠️ **Poor** | 20 | 2.4% | 25-49 |
| ❌ **Critical** | 5 | 0.6% | 0-24 |

### Overall Structure Health: **Excellent** (87.3/100)

## 🎯 Collection Insights

### Most Diverse Collections (by album types)
1. **Metallica** - 6 types (Album, Live, Demo, EP, Compilation, Instrumental)
2. **Iron Maiden** - 5 types (Album, Live, EP, Compilation, Demo)
3. **Pink Floyd** - 4 types (Album, Live, Compilation, Demo)

### Bands Missing Key Album Types
- **48 bands** lack live albums - Consider live recordings
- **105 bands** lack compilations - Opportunity for best-of collections  
- **127 bands** lack EPs - Short-form releases missing
- **138 bands** lack demo material - Rare/unreleased content opportunity

### Structure Improvement Opportunities
- **16 legacy bands** could benefit from year prefixes
- **89 default structure bands** could upgrade to type-based organization
- **25 albums** need compliance improvements

## 📈 Recommendations

### Collection Enhancement
1. **Add Missing Types**: Focus on live albums for 48 bands
2. **Expand EP Collections**: Only 28 EPs across 150 bands
3. **Acquire Demo Material**: Limited demo representation (1.8%)
4. **Consider Instrumental Versions**: Only 2 instrumental albums

### Organization Improvements  
1. **Upgrade to Enhanced Structure**: 89 bands could benefit from type folders
2. **Fix Compliance Issues**: 25 albums need naming/organization fixes
3. **Add Missing Years**: 16 legacy structure bands need year prefixes

### Metadata Enhancement
1. **25 bands** lack metadata files
2. **67 bands** could benefit from analysis/reviews
3. **15 bands** have incomplete album information
```

## Advanced Usage Examples

### Type-Based Collection Analysis

#### Find Bands with Specific Type Combinations
```json
{
  "method": "tools/call",
  "params": {
    "name": "get_band_list",
    "arguments": {
      "filter_album_types": ["Album", "Live", "Demo"],
      "require_all_types": true,
      "sort_by": "type_diversity",
      "sort_order": "desc"
    }
  }
}
```

#### Identify Collection Gaps
```json
{
  "method": "tools/call",
  "params": {
    "name": "get_band_list",
    "arguments": {
      "missing_album_types": ["EP", "Single"],
      "filter_has_metadata": true
    }
  }
}
```

### Structure Migration Examples

#### Find Bands Needing Structure Upgrades
```json
{
  "method": "tools/call",
  "params": {
    "name": "get_band_list",
    "arguments": {
      "filter_structure_type": "legacy",
      "sort_by": "albums_count",
      "sort_order": "desc"
    }
  }
}
```

#### Get Migration Recommendations
```json
{
  "method": "resources/read",
  "params": {
    "uri": "band://info/Led Zeppelin"
  }
}
```

*Response includes specific migration suggestions for improving folder structure and organization.*

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