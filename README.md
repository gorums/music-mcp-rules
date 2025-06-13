# Music Collection MCP Server

A Model Context Protocol (MCP) server that provides intelligent access to your local music collection through JSON-based metadata management, band discovery, and intelligent querying capabilities.

## Features

- **Intelligent Music Scanning**: Incremental scanning with change detection for large collections
- **Advanced Metadata Management**: Store and retrieve comprehensive band and album information
- **Analysis & Reviews**: Band and album ratings, reviews, and similar artist recommendations
- **Collection Insights**: Generate collection-wide analytics and improvement suggestions
- **Smart Filtering**: Advanced search with genre, rating, and completion status filters
- **Missing Album Detection**: Identify gaps in your collection
- **MCP Integration**: Works seamlessly with Claude Desktop, Cline, and other MCP clients

## Quick Start

### Using Python (Recommended)

1. **Install dependencies:**
```bash
# Windows
py -m pip install -r requirements.txt

# Linux/macOS
pip install -r requirements.txt
```

2. **Set environment variables:**
```bash
# Windows (PowerShell)
$env:MUSIC_ROOT_PATH = "C:\Path\To\Your\Music\Collection"

# Linux/macOS
export MUSIC_ROOT_PATH="/path/to/your/music"
```

3. **Run the server:**
```bash
# Windows
py main.py

# Linux/macOS
python main.py
```

4. **Configure your MCP client:**

**For Windows:**
```json
{
  "mcpServers": {
    "music-collection": {
      "command": "py",
      "args": ["D:/Projects/music-catalog-mcp/main.py"],
      "env": {
        "MUSIC_ROOT_PATH": "D:/Path/To/Your/Music/Collection"
      }
    }
  }
}
```

**For Linux/macOS:**
```json
{
  "mcpServers": {
    "music-collection": {
      "command": "python",
      "args": ["/path/to/music-catalog-mcp/main.py"],
      "env": {
        "MUSIC_ROOT_PATH": "/path/to/your/music/collection"
      }
    }
  }
}
```

### Using Docker (Alternative)

1. **Build the container:**
```bash
docker build -t music-mcp-server .
```

2. **Run the server:**
```bash
docker run -d --name music-mcp-container \
  -v "/path/to/your/music:/music" \
  -e "MUSIC_ROOT_PATH=/music" \
  music-mcp-server
```

3. **Configure your MCP client:**
```json
{
  "mcpServers": {
    "music-collection": {
      "command": "docker",
      "args": [
        "run", "--rm", "--interactive",
        "-v", "/path/to/your/music:/music",
        "-e", "MUSIC_ROOT_PATH=/music",
        "music-mcp-server"
      ]
    }
  }
}
```

## Music Collection Structure

Organize your music like this:
```
music_root/
├── Pink Floyd/
│   ├── The Wall/
│   │   ├── 01 - In The Flesh.mp3
│   │   └── 02 - The Thin Ice.mp3
│   └── Dark Side of the Moon/
│       └── music files...
└── The Beatles/
    └── Abbey Road/
        └── music files...
```

## MCP Capabilities

Once connected to an MCP client, you'll have access to:

### Tools (8 tools)
- `scan_music_folders` - Intelligent scanning with incremental updates and album type detection
- `get_band_list_tool` - Advanced filtering, sorting, and pagination with album type support
- `save_band_metadata_tool` - Store comprehensive band information with album types and editions
- `save_band_analyze_tool` - Store analysis with reviews and ratings
- `save_collection_insight_tool` - Store collection-wide insights and recommendations
- `validate_band_metadata_tool` - Dry-run validation without saving
- **`advanced_search_albums_tool`** - Advanced search with 13 filter parameters (types, years, editions, ratings, etc.)
- **`analyze_collection_insights_tool`** - Comprehensive collection analytics with maturity assessment

### Resources (3 resources)
- `band://info/{band_name}` - Detailed band information in markdown with type organization
- `collection://summary` - Collection overview and statistics with enhanced analytics
- **`collection://analytics`** - Advanced collection analytics with health metrics and recommendations

### Prompts (4 prompts)
- `fetch_band_info` - Intelligent band information fetching using external sources
- `analyze_band` - Comprehensive band analysis with ratings and similar bands
- `compare_bands` - Multi-band comparison analysis
- `collection_insights` - Generate collection insights and recommendations

## 💬 Example Prompts for MCP Clients

Here are example prompts you can use in your MCP client (like Claude Desktop) to interact with the Music Collection MCP Server:

### 🔍 **Collection Scanning & Management**

**Initial setup and scanning:**
```
Scan my music collection to discover all bands and albums.
```

**Get an overview of my collection:**
```
Show me a summary of my music collection with statistics.
```

**List bands with filtering:**
```
Show me all bands that have missing albums, sorted by name.
```

```
List all Heavy Metal bands in my collection that have metadata.
```

### 🔍 **Advanced Album Search (New!)**

**Important:** Use exact parameter names and values from the tool documentation. All parameters are optional. Use comma-separated strings for multiple values.

**Search by album types (exact values required):**
```
Use advanced_search_albums_tool with album_types="EP" to find all EPs.
```
```
Search using album_types="Live,Demo" for live albums and demo recordings.
```
```
Find standard albums and compilations with album_types="Album,Compilation".
```

**Search by year ranges and decades:**
```
Find 1980s albums using decades="1980s".
```
```
Search albums from 1975-1985 using year_min=1975 and year_max=1985.
```
```
Find recent albums with year_min=2000.
```

**Search by ratings (1-10 scale):**
```
Find highly rated albums using min_rating=8.
```
```
Search for unrated albums from the 90s using decades="1990s" and has_rating=false.
```
```
Find albums rated 7-9 using min_rating=7 and max_rating=9.
```

**Search by specific bands (use exact band names):**
```
Search Metallica's discography using bands="Metallica".
```
```
Find albums by classic metal bands using bands="Iron Maiden,Judas Priest,Black Sabbath".
```

**Search by genres (use exact genre names from your collection):**
```
Find heavy metal albums using genres="Heavy Metal".
```
```
Search multiple metal genres using genres="Thrash Metal,Death Metal,Black Metal".
```

**Search for special editions (use exact edition names):**
```
Find deluxe editions using editions="Deluxe Edition".
```
```
Search for special releases using editions="Limited Edition,Anniversary Edition,Remastered".
```

**Search by availability status:**
```
Find missing albums (in metadata but not found locally) using is_local=false.
```
```
Search only albums you have locally using is_local=true.
```

**Search by track count (useful for finding EPs vs albums):**
```
Find short releases (EPs/Singles) using track_count_max=6.
```
```
Find full albums using track_count_min=8 and track_count_max=15.
```

**Complex multi-parameter searches:**
```
Find metal EPs from the 1980s with good ratings using:
album_types="EP", decades="1980s", genres="Heavy Metal,Thrash Metal", min_rating=7
```
```
Search for missing deluxe editions by specific bands using:
bands="Metallica,Iron Maiden", editions="Deluxe Edition", is_local=false
```
```
Find highly rated live albums from metal bands using:
album_types="Live", genres="Heavy Metal", min_rating=8, is_local=true
```

### 📊 **Collection Analytics & Insights (New!)**

**Comprehensive collection analysis:**
```
Run the analyze_collection_insights_tool to give me a complete analysis of my music collection including health score and maturity level.
```

**Get collection recommendations:**
```
Analyze my collection and tell me what album types I'm missing and should consider adding.
```

**Check collection health:**
```
Use the collection insights tool to analyze my collection's organization health and give me improvement recommendations.
```

**View advanced analytics report:**
```
Show me the collection://analytics resource for a detailed report of my collection analytics.
```

### 📝 **Band Information & Metadata**

**Get detailed band information:**
```
Show me detailed information about Pink Floyd including their albums and any analysis.
```

**Fetch external band information:**
```
Use the fetch_band_info prompt to find comprehensive information about Led Zeppelin including their discography.
```

**Save band metadata:**
```
Save this metadata for The Beatles: formed in 1960, from Liverpool, genres include Rock and Pop, members include John Lennon, Paul McCartney, George Harrison, and Ringo Starr.
```

### 🎯 **Band Analysis & Reviews**

**Analyze a specific band:**
```
Use the analyze_band prompt to create a comprehensive analysis of Queen including ratings and similar bands.
```

**Compare multiple bands:**
```
Use the compare_bands prompt to compare The Beatles, The Rolling Stones, and Led Zeppelin in terms of musical style, influence, and commercial success.
```

**Save band analysis with ratings:**
```
Save an analysis for Iron Maiden: rate the band 9/10, rate "The Number of the Beast" album 10/10, similar bands include Judas Priest and Black Sabbath.
```

### 🔍 **Resource Access**

**View band details:**
```
Show me the band://info/Metallica resource with their complete information.
```

**Collection summary:**
```
Display the collection://summary resource showing my collection statistics.
```

**Advanced analytics:**
```
Show me the collection://analytics resource for comprehensive collection insights.
```

### ⚙️ **Data Validation & Management**

**Validate metadata before saving:**
```
Validate this band metadata for AC/DC before saving: formed 1973, from Australia, genre Hard Rock, members include Angus Young and Brian Johnson.
```

**Save collection insights:**
```
Save insights about my collection: 75% completion rate, strong in Rock genres, missing more Live albums, recommended to add more EPs.
```

### 🎵 **Album Type Specific Searches**

**Find missing album types:**
```
Search for bands that have Albums but are missing EPs or Live recordings.
```

**Discover rare album types:**
```
Use advanced search to find all Demo, Instrumental, and Split releases in my collection.
```

**Edition analysis:**
```
Find all standard albums that have Deluxe or Limited Edition versions available.
```

### 📈 **Collection Improvement**

**Get personalized recommendations:**
```
Based on my collection analysis, what specific albums or album types should I prioritize adding next?
```

**Organization improvement:**
```
Analyze my collection's folder structure and compliance, then suggest organization improvements.
```

**Collection goals:**
```
Help me set collection goals based on my current collection maturity level and missing album types.
```

### 🔄 **Combined Workflows**

**Complete collection assessment:**
```
Please:
1. Run collection insights analysis for overall health
2. Use advanced search to find all albums rated 9 or higher
3. Suggest missing album types based on my top-rated bands
```

**Discovery workflow:**
```
Analyze my collection, identify my favorite genres and highest-rated bands, then search for similar bands I might be missing.
```

---

**💡 Tip:** The MCP client will automatically call the appropriate tools based on your natural language requests. You can be as specific or as general as you like - the server will understand your intent and provide comprehensive results!

## Configuration

Set these environment variables:

- `MUSIC_ROOT_PATH` - Path to your music directory (required)
- `CACHE_DURATION_DAYS` - Cache expiration in days (default: 30)
- `LOG_LEVEL` - Logging level (default: INFO)

## 📚 Documentation

Our documentation is organized into three main sections:

## 📚 Documentation Sections

### Getting Started
- [Installation Guide](docs/user/INSTALLATION.md) - Step-by-step installation instructions
- [Configuration Guide](docs/user/CONFIGURATION.md) - How to configure the server for your music collection
- [Quick Start](docs/user/QUICK_START.md) - Get up and running in minutes

### Using the Server
- [Usage Examples](docs/user/USAGE_EXAMPLES.md) - Real-world examples and common use cases
- [Collection Organization](docs/user/COLLECTION_ORGANIZATION.md) - How to organize your music collection for best results
- [Album Handling](docs/user/ALBUM_HANDLING.md) - Understanding album types and metadata

### Getting Help
- [FAQ](docs/user/FAQ.md) - Frequently asked questions and answers  
- [Troubleshooting](docs/user/TROUBLESHOOTING.md) - Solutions to common problems
- [Rating System Guide](docs/user/RATING_SYSTEM.md) - Understanding the rating and analysis system


### 🛠️ Developer Documentation
For developers who want to understand, modify, or contribute to the project:
- [Architecture Overview](docs/developer/ARCHITECTURE.md) - System design and patterns
- [Metadata Schema](docs/developer/METADATA_SCHEMA.md) - The metadata schema
- [API Reference](docs/developer/API_REFERENCE.md) - Complete API documentation
- [Contributing Guidelines](docs/developer/CONTRIBUTING.md) - How to contribute
- [Code Style](docs/developer/CODE_STYLE.md) - Complete code style
- [Testing Guide](docs/developer/TESTING.md) - Running and writing tests

## Testing

Run tests using Docker:
```bash
docker build -f Dockerfile.test -t music-mcp-tests .
docker run --rm music-mcp-tests python -m pytest . -v
```

## Requirements

- Python 3.8+
- Docker (for containerized deployment)
- Music files in supported formats (MP3, FLAC, WAV, AAC, M4A, OGG, WMA, MP4, M4P)

## License

MIT License

Copyright (c) 2025 Music Collection MCP Server

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
