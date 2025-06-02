# Music Collection MCP Server

A Model Context Protocol (MCP) server that provides intelligent access to your local music collection through JSON-based metadata management, band discovery, and intelligent querying capabilities.

## Features

- **Music Collection Scanning**: Automatically scan and index your music directories
- **Metadata Management**: Store and retrieve comprehensive band and album information
- **Missing Album Detection**: Identify gaps in your collection
- **Intelligent Querying**: Search and filter your collection with advanced criteria
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

### Tools
- `scan_music_folders` - Scan and analyze your music collection
- `get_band_list` - List bands with filtering and search
- `save_band_metadata` - Store band information
- `save_band_analyze` - Store band analysis and ratings
- `save_collection_insight` - Store collection-wide insights

### Resources
- `band://info/{band_name}` - Detailed band information
- `collection://summary` - Collection overview and statistics

### Prompts
- `fetch_band_info` - Intelligent band information fetching
- `analyze_band` - Comprehensive band analysis
- `compare_bands` - Multi-band comparison
- `collection_insights` - Generate collection insights

## Configuration

Set these environment variables:

- `MUSIC_ROOT_PATH` - Path to your music directory (required)
- `CACHE_DURATION_DAYS` - Cache expiration in days (default: 30)
- `LOG_LEVEL` - Logging level (default: INFO)

## Documentation

### User Guides
- [Installation Guide](docs/INSTALLATION.md)
- [Configuration Guide](docs/CONFIGURATION.md)
- [Usage Examples](docs/USAGE_EXAMPLES.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [FAQ](docs/FAQ.md)

### Developer Documentation
- [API Reference](docs/API_REFERENCE.md)
- [Architecture Overview](docs/ARCHITECTURE.md)
- [Contributing Guidelines](docs/CONTRIBUTING.md)
- [Metadata Schema](docs/METADATA_SCHEMA.md)

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
