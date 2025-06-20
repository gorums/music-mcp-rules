# Music Collection MCP Server

A powerful Model Context Protocol (MCP) server that provides intelligent access to your local music collection through advanced metadata management, album type classification, and comprehensive analytics.

## ✨ Key Features

- **🎵 Smart Music Discovery**: Intelligent scanning with 8-type album classification (Album, EP, Live, Demo, Compilation, Single, Instrumental, Split)
- **📊 Advanced Analytics**: Collection maturity assessment, health scoring, and personalized recommendations
- **🏗️ Flexible Organization**: Support for multiple folder structures with automated compliance scoring
- **⚡ High Performance**: Optimized scanning (20-30% faster), batch operations, and intelligent caching
- **🤖 AI Integration**: Works seamlessly with Claude Desktop and other MCP clients
- **🔄 Automated Setup**: One-command installation with configuration generation

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

```bash
python scripts/setup.py
```

This guided setup will:
- Check system requirements
- Install dependencies
- Configure your music collection path
- Generate Claude Desktop configuration
- Validate your setup

### Option 2: Manual Installation

#### Using Python
```bash
# Install dependencies
pip install -r requirements.txt

# Set your music path
export MUSIC_ROOT_PATH="/path/to/your/music"

# Run the server
python main.py
```

#### Using Docker
```bash
# Build and run
docker build -t music-mcp .
docker run -v "/path/to/your/music:/music" -e MUSIC_ROOT_PATH=/music music-mcp
```

## 📁 Music Organization

The server supports multiple organization patterns:

### Enhanced Structure (Recommended)
```
Band Name/
├── Album/
│   ├── 1973 - Dark Side of the Moon/
│   └── 1979 - The Wall (Deluxe)/
├── Live/
│   └── 1988 - Delicate Sound of Thunder/
├── Compilation/
│   └── 2001 - Echoes - Best Of/
└── .band_metadata.json (auto-generated)
```

### Simple Structure (Also Supported)
```
Band Name/
├── 1973 - Dark Side of the Moon/
├── 1988 - Delicate Sound of Thunder (Live)/
└── 2001 - Echoes - Best Of (Compilation)/
```

## 🛠️ MCP Capabilities

### Tools (8 total)
- **Music Discovery**: `scan_music_folders` - Smart scanning with type detection
- **Collection Management**: `get_band_list` - Advanced filtering and search
- **Metadata Storage**: `save_band_metadata`, `save_band_analyze`, `save_collection_insight`
- **Validation**: `validate_band_metadata` - Dry-run validation
- **Advanced Search**: `advanced_search_albums` - 13-parameter filtering system
- **Analytics**: `analyze_collection_insights` - Comprehensive collection analysis

### Resources (3 total)
- **Band Info**: `band://info/{band_name}` - Detailed band information
- **Collection Summary**: `collection://summary` - Overview and statistics  
- **Advanced Analytics**: `collection://analytics` - Deep collection analysis

### Prompts (4 total)
- **Information Gathering**: `fetch_band_info`, `analyze_band`
- **Analysis**: `compare_bands`, `collection_insights`

## ⚙️ Configuration

Configure via environment variables or the automated setup:

```bash
MUSIC_ROOT_PATH="/path/to/your/music"     # Required: Your music directory
CACHE_DURATION_DAYS=30                    # Optional: Cache expiration (default: 30)
LOG_LEVEL=INFO                           # Optional: Logging level (default: INFO)
```

## 📚 Documentation

### Get Started Quickly
- [Quick Start Guide](docs/user/QUICK_START.md) - Get running in minutes
- [Installation Guide](docs/user/INSTALLATION.md) - Detailed setup instructions
- [Configuration Guide](docs/user/CONFIGURATION.md) - Advanced configuration options

### Learn More
- [Usage Examples](docs/user/USAGE_EXAMPLES.md) - Real-world examples
- [Collection Organization](docs/user/COLLECTION_ORGANIZATION.md) - Best practices
- [Album Handling](docs/user/ALBUM_HANDLING.md) - Understanding album types

### Get Help
- [FAQ](docs/user/FAQ.md) - Common questions
- [Troubleshooting](docs/user/TROUBLESHOOTING.md) - Problem solving
- [Rating System](docs/user/RATING_SYSTEM.md) - Understanding ratings and analysis

## 🔧 Maintenance & Scripts

The `scripts/` directory provides powerful maintenance tools:

- **Setup**: `setup.py` - Automated installation and configuration
- **Docker**: `start-docker.sh` - Container management with options
- **Validation**: `validate-music-structure.py` - Collection health checking
- **Backup**: `backup-recovery.py` - Complete backup and recovery system
- **Monitoring**: `health-check.py` - Comprehensive health monitoring

## 🧪 Testing

```bash
# Using Docker (recommended)
docker build -f Dockerfile.test -t music-mcp-tests .
docker run --rm music-mcp-tests python -m pytest . -v

# Using Python
python -m pytest tests/ -v
```

## 📊 What's New

### Recent Improvements
- **Advanced Analytics**: Collection maturity assessment and health scoring
- **Performance**: 20-30% faster scanning with optimized file operations
- **Separated Schema**: Local vs missing albums for better management
- **Automated Setup**: One-command installation and configuration
- **Album Types**: Intelligent 8-type classification system
- **Flexible Structure**: Support for multiple organization patterns

## 🆘 Need Help?

1. **Check the [FAQ](docs/user/FAQ.md)** for common questions
2. **Run health check**: `python scripts/health-check.py /path/to/music`
3. **Validate structure**: `python scripts/validate-music-structure.py /path/to/music`
4. **Review [Troubleshooting](docs/user/TROUBLESHOOTING.md)** guide

## 🔗 Links

- **Setup Scripts**: Complete automation in `scripts/` directory
- **Claude Desktop Configs**: Ready-to-use examples in `scripts/claude-desktop-configs/`
- **Developer Docs**: Architecture and API reference in `docs/developer/`

---

*Transform your music collection into an intelligent, searchable library with AI-powered insights!* 🎶

## Requirements

- Python 3.8+
- Docker (for containerized deployment)

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
