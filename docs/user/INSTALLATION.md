# Music Collection MCP Server - Installation Guide

## Prerequisites

### System Requirements
- **Python 3.8+** (for local installation)
- **Docker** (recommended for deployment)
- **MCP Client** (Claude Desktop, Cline, or other MCP-compatible client)

### Environment Preparation
- Music collection organized in folders (band/album structure)
- Minimum 1GB free disk space for metadata storage
- Network access for external band information fetching

## 🚀 Automated Installation (Recommended)

### Quick Setup
The easiest way to get started is with the automated setup script:

```bash
python scripts/setup.py
```

This interactive script will:
- ✅ Check system requirements
- ✅ Guide you through installation options
- ✅ Install dependencies automatically
- ✅ Configure your music collection path
- ✅ Generate Claude Desktop configuration
- ✅ Validate your setup

### Installation Options
The setup script offers several methods:

1. **Local Python Installation** - Install and run with system Python
2. **Docker Container** - Containerized deployment (recommended for production)
3. **Development Environment** - Full development setup with testing tools
4. **Configuration Only** - Generate configurations without installing

### What You'll Need
- Path to your music collection
- Preferred installation method (Python or Docker)
- Claude Desktop installed (for MCP integration)

## 📁 Music Collection Organization

The server supports multiple folder organization patterns with intelligent type detection:

### Enhanced Structure (Recommended)
```
/path/to/your/music/
├── Pink Floyd/
│   ├── Album/
│   │   ├── 1973 - The Dark Side of the Moon/
│   │   │   ├── 01 - Speak to Me.mp3
│   │   │   └── 02 - Breathe.mp3
│   │   └── 1979 - The Wall (Deluxe Edition)/
│   ├── Live/
│   │   └── 1988 - Delicate Sound of Thunder/
│   ├── Compilation/
│   │   └── 2001 - Echoes - The Best of Pink Floyd/
│   └── .band_metadata.json (created automatically)
├── The Beatles/
│   ├── Album/
│   │   ├── 1967 - Sgt. Pepper's Lonely Hearts Club Band/
│   │   └── 1969 - Abbey Road/
│   ├── Compilation/
│   │   └── 1996 - Anthology/
│   └── .band_metadata.json (created automatically)
└── .collection_index.json (created automatically)
```

### Default Structure (Also Supported)
```
/path/to/your/music/
├── Pink Floyd/
│   ├── 1973 - The Dark Side of the Moon/
│   ├── 1979 - The Wall (Deluxe Edition)/
│   ├── 1988 - Delicate Sound of Thunder (Live)/
│   ├── 2001 - Echoes - The Best of Pink Floyd (Compilation)/
│   └── .band_metadata.json (created automatically)
├── The Beatles/
│   ├── 1967 - Sgt. Pepper's Lonely Hearts Club Band/
│   ├── 1969 - Abbey Road/
│   └── .band_metadata.json (created automatically)
└── .collection_index.json (created automatically)
```

### Legacy Structure (Supported with Migration)
```
/path/to/your/music/
├── Pink Floyd/
│   ├── The Dark Side of the Moon/
│   ├── The Wall/
│   ├── Live at Pompeii/  # Type detected from keywords
│   └── .band_metadata.json (created automatically)
```

## 🐳 Docker Installation

### Using the Docker Script
```bash
# Make executable (Linux/macOS)
chmod +x scripts/start-docker.sh

# Start with your music collection
./scripts/start-docker.sh -m /path/to/your/music
```

### Manual Docker Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/music-catalog-mcp.git
cd music-catalog-mcp

# Build the container
docker build -t music-mcp .

# Run the server
docker run -d --name music-mcp \
  -v "/path/to/your/music:/music" \
  -e "MUSIC_ROOT_PATH=/music" \
  -e "CACHE_DURATION_DAYS=30" \
  music-mcp
```

### Docker Compose (Production)
```bash
# Update docker-compose.yml with your music path
# Then start the service
docker-compose up music-mcp
```

## 🐍 Local Python Installation

### Step-by-Step Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/music-mcp-server.git
cd music-mcp-server

# Create virtual environment (recommended)
python -m venv music-mcp-env
source music-mcp-env/bin/activate  # Linux/macOS
# or
music-mcp-env\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
export MUSIC_ROOT_PATH="/path/to/your/music"  # Linux/macOS
# or
set MUSIC_ROOT_PATH=C:\path\to\your\music     # Windows

# Run the server
python main.py
```

### Environment Configuration
Create a `.env` file in the project root:
```env
# Basic Configuration
MUSIC_ROOT_PATH=/path/to/your/music
CACHE_DURATION_DAYS=30
LOG_LEVEL=INFO

# Advanced Features
ENABLE_TYPE_DETECTION=true
ENABLE_STRUCTURE_ANALYSIS=true
DEFAULT_ALBUM_TYPE=Album
```

## 🤖 Claude Desktop Configuration

### Automated Configuration
If you used the setup script, it generated a configuration file. Copy the contents to your Claude Desktop config file.

### Configuration File Locations
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### Example Configurations

#### Local Python
```json
{
  "mcpServers": {
    "music-collection": {
      "command": "python",
      "args": ["/path/to/music-mcp-server/main.py"],
      "env": {
        "MUSIC_ROOT_PATH": "/path/to/your/music",
        "CACHE_DURATION_DAYS": "30",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

#### Docker Container
```json
{
  "mcpServers": {
    "music-collection": {
      "command": "docker",
      "args": [
        "run", "--rm", "--interactive",
        "-v", "/path/to/your/music:/music",
        "-e", "MUSIC_ROOT_PATH=/music",
        "music-mcp"
      ]
    }
  }
}
```

## 🔧 Development Setup

For contributors and developers:

```bash
# Clone and setup
git clone https://github.com/yourusername/music-mcp-server.git
cd music-mcp-server

# Use the setup script for development
python scripts/setup.py
# Choose option 3: Development environment

# Or manually:
python -m venv venv
source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt

# Install test dependencies
pip install pytest pytest-asyncio psutil pre-commit

# Run tests
docker build -f Dockerfile.test -t music-mcp-tests .
docker run --rm music-mcp-tests python -m pytest . -v
```

## ✅ Validation and Testing

### Validate Your Installation
```bash
# Check collection structure
python scripts/validate-music-structure.py /path/to/your/music

# Run health check
python scripts/health-check.py /path/to/your/music

# Test the server
python main.py
```

### Test with Claude Desktop
1. Restart Claude Desktop after configuration
2. Start a new conversation
3. Try: "Can you scan my music collection?"

## 🔧 Advanced Configuration

### Environment Variables
```bash
# Core Settings
MUSIC_ROOT_PATH="/path/to/your/music"     # Required
CACHE_DURATION_DAYS=30                    # Cache expiration (default: 30)
LOG_LEVEL=INFO                           # Logging level (default: INFO)

# Performance Settings
ENABLE_TYPE_DETECTION=true               # Album type detection (default: true)
ENABLE_STRUCTURE_ANALYSIS=true          # Structure analysis (default: true)
DEFAULT_ALBUM_TYPE=Album                 # Default album type (default: Album)

# Cache Settings
TYPE_DETECTION_CACHE_SIZE=1000          # Type detection cache size
STRUCTURE_ANALYSIS_CACHE_TTL=3600       # Structure cache TTL in seconds
```

### Multiple Collections
```json
{
  "mcpServers": {
    "music-rock": {
      "command": "python",
      "args": ["/path/to/music-mcp-server/main.py"],
      "env": {
        "MUSIC_ROOT_PATH": "/path/to/rock-music"
      }
    },
    "music-classical": {
      "command": "python", 
      "args": ["/path/to/music-mcp-server/main.py"],
      "env": {
        "MUSIC_ROOT_PATH": "/path/to/classical-music"
      }
    }
  }
}
```

## 🆘 Troubleshooting

### Common Issues

**Installation fails:**
```bash
# Check Python version
python --version  # Should be 3.8+

# Check pip
pip --version

# Try with explicit Python version
python3 -m pip install -r requirements.txt
```

**Docker issues:**
```bash
# Check Docker status
docker --version
docker info

# Rebuild if needed
docker build --no-cache -t music-mcp .
```

**Permission errors:**
```bash
# Check music path permissions
ls -la /path/to/music

# Fix permissions if needed (Linux/macOS)
chmod -R 755 /path/to/music
```

**Configuration not working:**
- Validate JSON syntax in Claude Desktop config
- Check path formatting and existence
- Verify environment variables
- Restart Claude Desktop after changes

### Getting Help
1. Run the automated health check: `python scripts/health-check.py`
2. Validate collection structure: `python scripts/validate-music-structure.py`
3. Check the [FAQ](FAQ.md) for common questions
4. Review [Troubleshooting Guide](TROUBLESHOOTING.md)

## 📚 Next Steps

After installation:
1. **Test the setup** with Claude Desktop
2. **Scan your collection** for the first time
3. **Explore the features** with the [Usage Examples](USAGE_EXAMPLES.md)
4. **Optimize your organization** with [Collection Organization](COLLECTION_ORGANIZATION.md)

---

*Ready to transform your music collection into an intelligent, searchable library!* 🎶 