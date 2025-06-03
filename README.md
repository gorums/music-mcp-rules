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

### Using Docker (Recommended)

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

### Python Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set environment variables:**
```bash
export MUSIC_ROOT_PATH="/path/to/your/music"
```

3. **Run the server:**
```bash
python main.py
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

### Tools (6 tools)
- `scan_music_folders` - Intelligent scanning with incremental updates
- `get_band_list_tool` - Advanced filtering, sorting, and pagination
- `save_band_metadata_tool` - Store comprehensive band information
- `save_band_analyze_tool` - Store analysis with reviews and ratings
- `save_collection_insight_tool` - Store collection-wide insights
- `validate_band_metadata_tool` - Dry-run validation without saving

### Resources (2 resources)
- `band://info/{band_name}` - Detailed band information in markdown
- `collection://summary` - Collection overview and statistics

### Prompts (4 prompts)
- `fetch_band_info` - Intelligent band information fetching
- `analyze_band` - Comprehensive band analysis with ratings
- `compare_bands` - Multi-band comparison analysis
- `collection_insights` - Generate collection insights and recommendations

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
