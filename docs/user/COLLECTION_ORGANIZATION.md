# Music Collection Organization with Album Type Classification

## Overview

This guide provides best practices for organizing your music collection to work optimally with the Music Collection MCP Server's album type classification and folder structure analysis features. Proper organization ensures accurate scanning, efficient metadata management, intelligent type detection, and the best user experience.

## Album Type Classification System

The server recognizes 8 distinct album types with automatic detection:

### Supported Album Types

| Type | Description | Auto-Detection Keywords | Typical Track Count |
|------|-------------|------------------------|-------------------|
| **Album** | Standard studio albums | (default classification) | 8-20 tracks |
| **Compilation** | Greatest hits, collections | "greatest hits", "best of", "collection", "anthology" | 10-30 tracks |
| **EP** | Extended plays | "ep", "e.p." | 3-7 tracks |
| **Live** | Live recordings | "live", "concert", "unplugged", "acoustic" | 5-25 tracks |
| **Single** | Single releases | "single" | 1-3 tracks |
| **Demo** | Demo recordings | "demo", "demos", "unreleased", "early recordings" | 3-15 tracks |
| **Instrumental** | Instrumental versions | "instrumental", "instrumentals" | Variable |
| **Split** | Split releases | "split", "vs.", "versus", "with" | 4-12 tracks |

## Folder Structure Guidelines

### Enhanced Structure (Recommended)

The enhanced structure uses type-based organization for better collection management:

```
Music Root Directory/
├── Band Name/                    # Level 1: Band folders
│   ├── Album/                   # Level 2: Type folders
│   │   ├── 1973 - Album Name/           # Level 3: Album folders
│   │   │   ├── 01 - Track Name.mp3     # Level 4: Music files
│   │   │   ├── 02 - Track Name.mp3
│   │   │   └── album_cover.jpg
│   │   └── 1979 - Another Album (Deluxe Edition)/
│   ├── Live/
│   │   ├── 1985 - Live at Venue/
│   │   └── 1992 - Unplugged Session/
│   ├── Compilation/
│   │   └── 1996 - Greatest Hits/
│   ├── EP/
│   │   └── 1980 - EP Name/
│   ├── Demo/
│   │   └── 1978 - Early Demos/
│   └── .band_metadata.json             # Auto-generated metadata
├── Another Band/
│   ├── Album/
│   ├── Live/
│   └── .band_metadata.json
└── .collection_index.json              # Auto-generated collection index
```

### Default Structure (Also Supported)

The default flat structure with intelligent type detection:

```
Music Root Directory/
├── Band Name/                    # Level 1: Band folders
│   ├── 1973 - Album Name/              # Level 2: Album folders with year
│   ├── 1979 - Another Album (Deluxe Edition)/
│   ├── 1985 - Live at Venue (Live)/    # Type detected from name
│   ├── 1996 - Greatest Hits (Compilation)/
│   ├── 1980 - EP Name (EP)/
│   ├── 1978 - Early Demos (Demo)/
│   └── .band_metadata.json
```

### Legacy Structure (Supported with Migration)

Simple album names without years (automatically detected and scored):

```
Music Root Directory/
├── Band Name/
│   ├── Album Name/                     # Simple names
│   ├── Another Album/
│   ├── Live at Venue/                  # Type detected from keywords
│   ├── Greatest Hits/
│   └── .band_metadata.json
```

## Album Type Detection Examples

### Automatic Detection from Folder Names

The system automatically detects types using intelligent keyword matching:

#### Live Albums
```
✅ Good examples:
"1985 - Live at Wembley"
"1992 - Unplugged in New York" 
"2001 - Concert at Red Rocks"
"1987 - Acoustic Sessions"
"Live/1985 - At Wembley Stadium"

❌ Avoid:
"1985 - Wembley" (unclear if live)
```

#### Demo Albums
```
✅ Good examples:
"1982 - Early Demos"
"1979 - Unreleased Tracks"
"1980 - Rough Mixes"
"Demo/1982 - Studio Sessions"

❌ Avoid:
"1982 - Sessions" (could be anything)
```

#### Compilation Albums
```
✅ Good examples:
"1996 - Greatest Hits"
"2000 - The Best of Band Name"
"1995 - The Collection"
"2005 - Anthology"
"Compilation/1996 - Greatest Hits"

❌ Avoid:
"1996 - Hits" (too generic)
```

#### EP Albums
```
✅ Good examples:
"1980 - Love EP"
"1983 - Extended Play"
"EP/1980 - Love Songs"

❌ Avoid:
"1980 - Short Album" (use track count for detection)
```

### Enhanced Type Folder Structure

Organize albums by type for optimal organization:

```
Pink Floyd/
├── Album/                      # Standard studio albums
│   ├── 1973 - The Dark Side of the Moon/
│   ├── 1975 - Wish You Were Here/
│   └── 1979 - The Wall (Deluxe Edition)/
├── Live/                       # Live recordings
│   ├── 1988 - Delicate Sound of Thunder/
│   └── 1994 - Pulse/
├── Compilation/                # Greatest hits, collections
│   ├── 1981 - A Collection of Great Dance Songs/
│   └── 2001 - Echoes - The Best of Pink Floyd/
└── Demo/                       # Early recordings, demos
    └── 1967 - Early Singles/
```

## Naming Conventions with Type Support

### Enhanced Structure Naming

#### Type Folder Names
```
✅ Recommended:
Album/          (or Albums/)
Live/           (or Lives/)
Compilation/    (or Compilations/)
EP/             (or EPs/)
Demo/           (or Demos/)
Single/         (or Singles/)
Instrumental/   (or Instrumentals/)
Split/          (or Splits/)

❌ Avoid:
Studio/         (use Album/)
Concert/        (use Live/)
Collections/    (use Compilation/)
```

#### Album Folder Names Within Type Folders
```
✅ Enhanced structure examples:
Album/1973 - The Dark Side of the Moon/
Album/1979 - The Wall (Deluxe Edition)/
Live/1985 - Live at Wembley/
Compilation/1996 - Greatest Hits/
EP/1980 - Running Free EP/
Demo/1978 - Early Demos/

❌ Avoid in enhanced structure:
Album/1973 - The Dark Side of the Moon (Album)/  # Redundant type
Live/1985 - Live at Wembley (Live)/              # Redundant type
```

### Default Structure Naming

For flat organization, include type hints in parentheses:

```
✅ Default structure examples:
1973 - The Dark Side of the Moon/               # Standard album
1979 - The Wall (Deluxe Edition)/              # Edition specified
1985 - Live at Wembley (Live)/                 # Type specified
1996 - Greatest Hits (Compilation)/            # Type specified
1980 - Running Free EP (EP)/                   # Type specified
1978 - Early Demos (Demo)/                     # Type specified

❌ Avoid:
Live at Wembley (1985)/                        # Year should be prefix
The Wall - Deluxe Edition/                     # Use parentheses for edition
```

### Edition and Type Handling

#### Edition Format
```
✅ Good edition examples:
(Deluxe Edition)
(Limited Edition)
(Remastered)
(Anniversary Edition)
(Expanded Edition)

❌ Avoid:
[Deluxe Edition]                               # Use parentheses
- Deluxe Edition                               # Use parentheses
(Deluxe)                                       # Be specific
```

#### Combining Type and Edition
```
✅ Enhanced structure (type folder + edition):
Live/1985 - Live at Wembley (Deluxe Edition)/

✅ Default structure (type + edition):
1985 - Live at Wembley (Live) (Deluxe Edition)/
1985 - Live at Wembley (Live, Deluxe Edition)/

❌ Avoid:
1985 - Live at Wembley (Deluxe Live Edition)/  # Confusing order
```

## Folder Structure Compliance and Scoring

### Compliance Levels

The system scores album folder compliance on a 0-100 scale:

| Score Range | Level | Description | Example Issues |
|-------------|-------|-------------|----------------|
| 90-100 | **Excellent** | Perfect organization | None |
| 70-89 | **Good** | Minor improvements possible | Missing type folders |
| 50-69 | **Fair** | Some organization issues | Inconsistent naming |
| 25-49 | **Poor** | Significant problems | Missing years, poor naming |
| 0-24 | **Critical** | Major organizational issues | No structure, missing albums |

### Compliance Factors

#### Year Prefix (Weight: 30%)
```
✅ Excellent: 1973 - Album Name
✅ Good: 1973 Album Name
❌ Poor: Album Name (1973)
❌ Critical: Album Name
```

#### Type Organization (Weight: 25%)
```
✅ Excellent: Album/1973 - Album Name/
✅ Good: 1973 - Album Name (Album)/
❌ Fair: 1973 - Album Name/  (type unclear)
```

#### Edition Formatting (Weight: 20%)
```
✅ Excellent: Album Name (Deluxe Edition)
✅ Good: Album Name (Deluxe)
❌ Poor: Album Name - Deluxe Edition
```

#### Consistency (Weight: 15%)
```
✅ Excellent: All albums follow same pattern
❌ Poor: Mixed patterns throughout collection
```

#### Naming Quality (Weight: 10%)
```
✅ Excellent: Descriptive, clear names
❌ Poor: Abbreviated, unclear names
```

## Migration Strategies

### From Legacy to Default Structure

```bash
# Before (Legacy)
Pink Floyd/
├── Dark Side of the Moon/
├── The Wall/
└── Live at Pompeii/

# After (Default)
Pink Floyd/
├── 1973 - The Dark Side of the Moon/
├── 1979 - The Wall/
└── 1972 - Live at Pompeii (Live)/
```

### From Default to Enhanced Structure

```bash
# Before (Default)
Pink Floyd/
├── 1973 - The Dark Side of the Moon/
├── 1979 - The Wall/
├── 1972 - Live at Pompeii (Live)/
└── 1996 - Greatest Hits (Compilation)/

# After (Enhanced)
Pink Floyd/
├── Album/
│   ├── 1973 - The Dark Side of the Moon/
│   └── 1979 - The Wall/
├── Live/
│   └── 1972 - Live at Pompeii/
└── Compilation/
    └── 1996 - Greatest Hits/
```

### Automated Migration Recommendations

The system provides specific migration suggestions:

```json
{
  "recommendations": [
    "Create Album/ folder and move 8 standard albums",
    "Create Live/ folder and move 2 live albums", 
    "Add year prefix to 3 albums missing dates",
    "Standardize edition format for 2 albums"
  ],
  "migration_plan": {
    "create_folders": ["Album", "Live", "Compilation"],
    "move_operations": [
      {
        "from": "Dark Side of the Moon",
        "to": "Album/1973 - The Dark Side of the Moon",
        "reason": "Add year prefix and move to type folder"
      }
    ]
  }
}
```

## Advanced Organization Features

### Type-Based Statistics

Track collection balance across album types:

```json
{
  "album_type_distribution": {
    "Album": 15,      // 60% - Good balance
    "Live": 4,        // 16% - Good variety  
    "Compilation": 3, // 12% - Reasonable
    "EP": 2,          // 8%  - Could use more
    "Demo": 1,        // 4%  - Consider adding
    "Single": 0,      // 0%  - Missing type
    "Instrumental": 0,
    "Split": 0
  }
}
```

### Missing Type Recommendations

The system suggests missing album types:

```
Recommendations for Pink Floyd:
- ✅ Strong studio album collection (15 albums)
- ✅ Good live representation (4 albums)
- ⚠️  Consider adding: Singles collection
- ⚠️  Consider adding: Instrumental versions
- ⚠️  Consider adding: More EPs
```

### Collection Health Assessment

Overall collection organization health:

```json
{
  "structure_health": "excellent",
  "compliance_summary": {
    "excellent": 18,  // 72%
    "good": 5,        // 20%  
    "fair": 2,        // 8%
    "poor": 0,        // 0%
    "critical": 0     // 0%
  },
  "recommendations": [
    "Collection is well-organized overall",
    "Consider upgrading 2 fair-rated albums to enhanced structure"
  ]
}
```

## File Format Recommendations

### Album Type Considerations

Different album types may benefit from different file formats:

#### Studio Albums (Album type)
- **Recommended**: FLAC for archival quality
- **Alternative**: MP3 320kbps or AAC 256kbps
- **Avoid**: Low bitrate formats for primary collection

#### Live Albums (Live type)
- **Recommended**: FLAC for full dynamic range
- **Note**: Live recordings benefit from lossless preservation
- **Organization**: Consider separate folders for different venues/dates

#### Demos (Demo type)
- **Acceptable**: MP3 192kbps+ (often sourced from lower quality)
- **Note**: Preserve original quality, even if limited
- **Organization**: Group by recording session/period

#### Compilations (Compilation type)
- **Recommended**: Match source album quality
- **Note**: May mix different eras and quality levels
- **Organization**: Maintain consistent format within compilation

## Integration with Metadata Management

### Automatic Type Detection

The system automatically:
- Detects album types from folder names and structure
- Updates metadata with detected types
- Validates type assignments against folder organization
- Suggests corrections for misclassified albums

### Manual Type Override

You can manually specify types in metadata:

```json
{
  "albums": [
    {
      "album_name": "Dark Side of the Moon",
      "type": "Album",
      "year": "1973"
    },
    {
      "album_name": "Live at Pompeii", 
      "type": "Live",
      "year": "1972"
    }
  ]
}
```

### Type-Based Filtering and Search

Use album types for enhanced collection management:
- Filter bands by album types ("Show me bands with Live albums")
- Search for specific type combinations
- Generate type-specific recommendations
- Track collection balance across types

This enhanced organization system provides intelligent classification while maintaining flexibility for different collection styles and migration paths. 