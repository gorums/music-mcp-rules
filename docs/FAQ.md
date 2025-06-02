# Music Collection MCP Server - Frequently Asked Questions (FAQ) with Album Type Classification

## General Questions

### Q: What is the Music Collection MCP Server?

**A:** The Music Collection MCP Server is a Model Context Protocol (MCP) server that provides intelligent access to your local music collection. It scans your music folders, manages metadata, and offers tools, resources, and prompts to analyze and explore your music library through MCP-compatible clients like Claude Desktop. The server now includes advanced album type classification and folder structure analysis features.

### Q: What MCP clients are supported?

**A:** The server supports any MCP-compatible client, including:
- **Claude Desktop** (recommended)
- **Cline** (VS Code extension)
- Any client supporting MCP stdio transport
- Custom MCP client implementations

### Q: Do I need an internet connection?

**A:** The core functionality works offline, but internet access enhances the experience:
- **Required for**: Fetching band information via Brave Search integration
- **Not required for**: Local scanning, metadata storage, resource access, collection analysis, album type detection, folder structure analysis

## Album Type Classification

### Q: What album types does the server recognize?

**A:** The server supports 8 distinct album types with automatic detection:

| Type | Description | Detection Keywords | Typical Track Count |
|------|-------------|-------------------|-------------------|
| **Album** | Standard studio albums | (default classification) | 8-20 tracks |
| **Compilation** | Greatest hits, collections | "greatest hits", "best of", "collection" | 10-30 tracks |
| **EP** | Extended plays | "ep", "e.p." | 3-7 tracks |
| **Live** | Live recordings | "live", "concert", "unplugged" | 5-25 tracks |
| **Single** | Single releases | "single" | 1-3 tracks |
| **Demo** | Demo recordings | "demo", "demos", "unreleased" | 3-15 tracks |
| **Instrumental** | Instrumental versions | "instrumental", "instrumentals" | Variable |
| **Split** | Split releases | "split", "vs.", "versus" | 4-12 tracks |

### Q: How does automatic album type detection work?

**A:** The server uses multiple detection strategies:

1. **Keyword Analysis**: Scans folder names for type-specific keywords
2. **Folder Structure**: Analyzes type-based folder organization
3. **Track Count Heuristics**: Uses track count patterns for type hints
4. **Confidence Scoring**: Provides confidence levels for detected types

**Example Detection:**
```
"1972 - Live at Pompeii" → Live (confidence: 0.95)
"2001 - Greatest Hits" → Compilation (confidence: 0.90)
"1980 - Demo Sessions" → Demo (confidence: 0.85)
```

### Q: Can I override automatic type detection?

**A:** Yes! You have full control:
- **Manual Override**: Set album type in metadata manually
- **Confidence Threshold**: Configure minimum confidence for auto-detection
- **Default Type**: Set fallback type when detection fails
- **Disable Detection**: Turn off auto-detection entirely

**Configuration:**
```env
TYPE_DETECTION_CONFIDENCE=0.8  # Require high confidence
DEFAULT_ALBUM_TYPE=Album       # Fallback type
ENABLE_TYPE_DETECTION=false    # Disable auto-detection
```

### Q: How do I filter my collection by album type?

**A:** Use the enhanced `get_band_list` tool with type filtering:

```json
{
  "method": "tools/call",
  "params": {
    "name": "get_band_list",
    "arguments": {
      "filter_album_types": ["Live", "Demo"],
      "sort_by": "albums_count",
      "sort_order": "desc"
    }
  }
}
```

This returns only bands that have Live or Demo albums.

## Folder Structure Analysis

### Q: What folder structures does the server support?

**A:** The server recognizes and analyzes multiple organization patterns:

#### Default Structure (Flat Organization)
```
Band Name/
├── 1973 - Album Name/
├── 1979 - Another Album/
└── 1985 - Live Album/
```

#### Enhanced Structure (Type-Based Organization)
```
Band Name/
├── Album/
│   ├── 1973 - Album Name/
│   └── 1979 - Another Album/
├── Live/
│   └── 1985 - Live Album/
└── Compilation/
    └── 2001 - Greatest Hits/
```

#### Mixed Structure (Combination)
```
Band Name/
├── Album/
│   └── 1973 - Album Name/
├── 1979 - Another Album/        # Flat structure
└── Live/
    └── 1985 - Live Album/
```

### Q: What is folder structure compliance scoring?

**A:** The server analyzes your folder organization and provides compliance scores (0-100):

- **Excellent** (90-100): Perfect organization, consistent naming
- **Good** (75-89): Minor issues, mostly well organized
- **Fair** (60-74): Some inconsistencies, acceptable organization
- **Poor** (40-59): Many issues, needs improvement
- **Critical** (0-39): Severe problems, major reorganization needed

**Factors affecting compliance:**
- Consistent naming conventions
- Proper year formatting (YYYY)
- Type folder usage (for enhanced structures)
- Special character handling
- Edition information formatting

### Q: How do I improve my collection's compliance score?

**A:** The server provides specific recommendations:

1. **Check Structure Analysis**: Use `collection://summary` resource
2. **Review Recommendations**: Server suggests specific improvements
3. **Fix Naming Issues**: Standardize album folder names
4. **Consider Migration**: Move to enhanced type-based structure
5. **Use Compliance Filtering**: Focus on low-scoring bands first

**Example recommendations:**
- "Standardize year format to YYYY in album folders"
- "Consider migrating to enhanced type-based structure"
- "Fix special characters in album names"
- "Add missing year information to 5 albums"

### Q: Should I migrate to enhanced folder structure?

**A:** Consider enhanced structure if you:
- ✅ Have many different album types (Live, EP, Demo, etc.)
- ✅ Want better organization and browsing
- ✅ Plan to expand your collection significantly
- ✅ Like type-based filtering and analysis

**Stay with default structure if you:**
- ❌ Have mostly standard studio albums
- ❌ Prefer simple flat organization
- ❌ Don't want to reorganize existing collection
- ❌ Use external music management tools

### Q: How do I filter by folder structure compliance?

**A:** Use compliance filtering in `get_band_list`:

```json
{
  "method": "tools/call",
  "params": {
    "name": "get_band_list",
    "arguments": {
      "filter_compliance_levels": ["poor", "critical"],
      "sort_by": "compliance_score",
      "sort_order": "asc"
    }
  }
}
```

This shows bands with the lowest compliance scores first.

## Installation and Setup

### Q: Should I use Docker or local Python installation?

**A:** **Docker is recommended** for most users because:
- ✅ Consistent environment across platforms
- ✅ No Python environment conflicts
- ✅ Easy updates and deployment
- ✅ Isolation from system Python
- ✅ Includes all dependencies for type detection and structure analysis

Use local Python only for development or when Docker isn't available.

### Q: What folder structure do I need for my music collection?

**A:** The server now supports multiple folder organization patterns:

#### Minimum Requirements
```
Music Root/
├── Band Name/              # Top level: band folders
│   ├── Album 1/           # Second level: album folders  
│   │   ├── track1.mp3     # Third level: music files
│   │   └── track2.mp3
│   └── Album 2/
│       └── *.mp3
└── Another Band/
    └── Album/
        └── *.mp3
```

#### Enhanced Organization (Recommended)
```
Music Root/
├── Band Name/
│   ├── Album/             # Type folders for better organization
│   │   ├── 1973 - Album Name/
│   │   └── 1979 - Another Album/
│   ├── Live/
│   │   └── 1985 - Live Album/
│   └── EP/
│       └── 1982 - EP Name/
```

**Supported**: Most common folder organizations, mixed structures
**Not supported**: Loose music files, compilation albums at root level

### Q: Which music file formats are supported?

**A:** The scanner detects these formats:
- **Common**: `.mp3`, `.flac`, `.wav`, `.aac`, `.m4a`
- **Additional**: `.ogg`, `.wma`, `.mp4`, `.m4p`

Files without these extensions are ignored during scanning.

### Q: Can I have multiple music collections?

**A:** Yes! Configure multiple MCP server instances with different type settings:
```json
{
  "mcpServers": {
    "music-rock": {
      "command": "docker",
      "args": [
        "-v", "/music/rock:/music", 
        "-e", "MUSIC_ROOT_PATH=/music",
        "-e", "COMPLIANCE_THRESHOLD=75",
        "music-mcp-server"
      ]
    },
    "music-classical": {
      "command": "docker", 
      "args": [
        "-v", "/music/classical:/music", 
        "-e", "MUSIC_ROOT_PATH=/music",
        "-e", "DEFAULT_ALBUM_TYPE=Album",
        "music-mcp-server"
      ]
    }
  }
}
```

## Usage Questions

### Q: How do I start using the server after installation?

**A:** Follow this enhanced workflow:
1. **Scan your collection**: Use `scan_music_folders` tool with type detection
2. **Review type distribution**: Check album type statistics in scan results
3. **Analyze structure**: Review compliance scores and recommendations
4. **View discovered bands**: Use `get_band_list` tool with type filtering
5. **Add band information**: Use `fetch_band_info` prompt + `save_band_metadata` tool
6. **Analyze bands**: Use `analyze_band` prompt + `save_band_analyze` tool

### Q: What's the difference between missing and physical albums?

**A:** 
- **Physical albums**: Actually exist as folders in your music directory
- **Missing albums**: Listed in band metadata but not present as physical folders
- **Purpose**: Track your collection completeness and wishlist items

Example with album types:
```json
{
  "band_name": "Pink Floyd",
  "albums": [
    {"album_name": "The Wall", "type": "Album", "missing": false},
    {"album_name": "Live at Pompeii", "type": "Live", "missing": false},
    {"album_name": "Early Demos", "type": "Demo", "missing": true}
  ]
}
```

### Q: How does the rating system work?

**A:** The server uses a 1-10 scale for ratings with type-aware analysis:
- **1-3**: Poor/Dislike
- **4-6**: Average/Okay  
- **7-8**: Good/Like
- **9-10**: Excellent/Love

Ratings can be applied to:
- Individual bands (overall rating)
- Individual albums (with type consideration)
- Type-specific analysis (e.g., "Best Live Albums")

### Q: What are "similar bands" and how are they used?

**A:** Similar bands help with music discovery and type analysis:
- **Stored in**: Band analysis data
- **Used for**: Collection insights, recommendations, discovery, type-based suggestions
- **Format**: Simple list of band names
- **Example**: Pink Floyd → ["King Crimson", "Genesis", "Yes"]
- **Type Context**: Consider album type distribution when suggesting similar bands

## Data and Storage

### Q: Where is my data stored?

**A:** All data is stored locally in JSON files with enhanced schema:
- **Band metadata**: `{band_folder}/.band_metadata.json` (includes album types and compliance)
- **Collection index**: `{music_root}/.collection_index.json` (includes type distribution)
- **Backups**: Automatic timestamped backups of all files

**No external databases or cloud storage** - your data stays private.

### Q: Is my data backed up automatically?

**A:** Yes! The server creates automatic backups:
- **When**: Before any metadata updates
- **Format**: `.band_metadata.json.backup.YYYYMMDD-HHMMSS`
- **Retention**: Multiple backup versions kept
- **Manual restoration**: Copy backup file to replace current metadata
- **Type preservation**: Album types and compliance data included in backups

### Q: Can I edit metadata files manually?

**A:** Yes, but use caution with the enhanced schema:
- **Format**: Standard JSON with proper syntax including album type fields
- **Validation**: Server validates album types and compliance data
- **Recommendation**: Use MCP tools when possible for safety and type detection
- **Backup**: Manual edits don't create automatic backups

### Q: What happens if metadata files get corrupted?

**A:** The server handles corruption gracefully:
1. **Automatic backup restoration** if recent backup exists
2. **Error reporting** with specific validation issues (including type validation)
3. **Regeneration** - delete corrupted file and rescan with type detection
4. **Recovery tools** in troubleshooting guide

## Performance and Limitations

### Q: How large collections can the server handle?

**A:** Tested performance limits with type detection and structure analysis:
- **Small**: 1-100 bands - Instant response
- **Medium**: 100-1,000 bands - 1-5 seconds
- **Large**: 1,000-10,000 bands - 10-60 seconds  
- **Very Large**: 10,000+ bands - May need optimization

**Performance optimization for large collections:**
```env
ENABLE_STRUCTURE_ANALYSIS=false  # Disable for speed
TYPE_DETECTION_CONFIDENCE=0.9    # Higher confidence = faster
COMPLIANCE_THRESHOLD=60          # Lower threshold = less processing
```

### Q: Why is scanning taking a long time?

**A:** Common causes and solutions with type features:
- **Large collection**: Normal for 1000+ bands
- **Type detection**: Adds processing time but can be optimized
- **Structure analysis**: Can be disabled for faster scanning
- **Slow storage**: Use SSD for better performance
- **Limited memory**: Increase Docker memory limit

Optimization tips:
```bash
# Increase Docker resources
docker run --memory=4g --cpus=2 music-mcp-server

# Optimize type detection
-e "TYPE_DETECTION_CONFIDENCE=0.9"
-e "ENABLE_STRUCTURE_ANALYSIS=false"

# Use incremental scanning
{"force_rescan": false}  # Only scan changed folders
```

### Q: How much disk space does the server use?

**A:** Storage requirements with enhanced features:
- **Metadata files**: ~2-15KB per band (increased for type data)
- **Collection index**: ~2-200KB total (includes type distribution)
- **Backups**: 3-5x metadata size
- **Example**: 1000 bands ≈ 10-75MB total

## Configuration Questions

### Q: How do I configure album type detection?

**A:** Use these environment variables:

```env
# Enable/disable type detection
ENABLE_TYPE_DETECTION=true

# Set confidence threshold (0.0-1.0)
TYPE_DETECTION_CONFIDENCE=0.8

# Set default type when detection fails
DEFAULT_ALBUM_TYPE=Album

# Enable structure analysis
ENABLE_STRUCTURE_ANALYSIS=true

# Set compliance threshold
COMPLIANCE_THRESHOLD=75
```

### Q: What's the difference between confidence levels?

**A:** Type detection confidence levels:

- **0.9-1.0**: Very high confidence - only obvious indicators
- **0.8-0.9**: High confidence - clear indicators (recommended)
- **0.6-0.8**: Medium confidence - probable indicators
- **0.4-0.6**: Low confidence - weak indicators
- **0.0-0.4**: Very low confidence - uncertain indicators

**Higher confidence = more accurate but fewer detections**
**Lower confidence = more detections but potentially less accurate**

### Q: How do I disable type detection for better performance?

**A:** For maximum scanning speed:

```env
ENABLE_TYPE_DETECTION=false      # Disable type detection
ENABLE_STRUCTURE_ANALYSIS=false  # Disable structure analysis
DEFAULT_ALBUM_TYPE=Album         # All albums will be "Album" type
LOG_LEVEL=ERROR                  # Reduce logging overhead
```

This provides the fastest scanning but loses type classification benefits.

## Troubleshooting

### Q: Why aren't album types being detected correctly?

**A:** Common issues and solutions:

1. **Confidence too high**: Lower `TYPE_DETECTION_CONFIDENCE`
2. **Keywords not recognized**: Check folder names for standard keywords
3. **Detection disabled**: Verify `ENABLE_TYPE_DETECTION=true`
4. **Folder structure**: Some types need specific folder patterns

**Debug steps:**
```env
LOG_LEVEL=DEBUG  # Enable detailed logging
```
Check logs for type detection attempts and confidence scores.

### Q: Why is my compliance score low?

**A:** Common compliance issues:

1. **Inconsistent naming**: Mix of formats like "Album Name" vs "1973 - Album Name"
2. **Missing years**: Albums without year prefixes
3. **Special characters**: Unusual characters in folder names
4. **Mixed structures**: Combination of flat and type-based organization

**Check specific issues**: Use `collection://summary` resource for detailed recommendations.

### Q: How do I migrate to enhanced folder structure?

**A:** Migration is currently manual, but the server provides guidance:

1. **Enable migration suggestions**: Set `AUTO_MIGRATE_STRUCTURE=true`
2. **Review recommendations**: Check compliance analysis
3. **Plan migration**: Start with bands that have multiple album types
4. **Test first**: Try with a few bands before full migration
5. **Update gradually**: No need to migrate everything at once

**Future versions** may include automated migration tools.

---

## Version Information

- **FAQ Version**: 2.0.0
- **Album Type System**: 1.0.0
- **Folder Structure Analysis**: 1.0.0
- **Last Updated**: 2025-01-30 