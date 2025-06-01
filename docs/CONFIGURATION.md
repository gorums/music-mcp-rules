# Music Collection MCP Server - Configuration Guide

## Overview

This guide covers all configuration options for the Music Collection MCP Server, including environment variables, MCP client configuration, and advanced deployment scenarios.

## Environment Configuration

### Core Environment Variables

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `MUSIC_ROOT_PATH` | string | ✅ **Required** | None | Absolute path to your music collection root directory |
| `CACHE_DURATION_DAYS` | integer | ❌ Optional | `30` | Number of days to cache metadata before refresh |
| `LOG_LEVEL` | string | ❌ Optional | `INFO` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |

### Configuration Methods

#### Method 1: Environment File (.env)
Create a `.env` file in the project root:
```env
# Required Configuration
MUSIC_ROOT_PATH=/home/user/Music

# Optional Configuration
CACHE_DURATION_DAYS=30
LOG_LEVEL=INFO
```

#### Method 2: Docker Environment Variables
```bash
docker run -e "MUSIC_ROOT_PATH=/music" \
           -e "CACHE_DURATION_DAYS=30" \
           -e "LOG_LEVEL=INFO" \
           music-mcp-server
```

#### Method 3: System Environment Variables
```bash
# Linux/macOS
export MUSIC_ROOT_PATH="/home/user/Music"
export CACHE_DURATION_DAYS=30
export LOG_LEVEL=INFO

# Windows PowerShell
$env:MUSIC_ROOT_PATH = "D:\Music"
$env:CACHE_DURATION_DAYS = 30
$env:LOG_LEVEL = "INFO"

# Windows Command Prompt
set MUSIC_ROOT_PATH=D:\Music
set CACHE_DURATION_DAYS=30
set LOG_LEVEL=INFO
```

## Detailed Configuration Options

### MUSIC_ROOT_PATH Configuration

The most critical configuration setting. Points to your music collection root.

#### Valid Path Examples
```bash
# Linux/macOS
MUSIC_ROOT_PATH="/home/user/Music"
MUSIC_ROOT_PATH="/mnt/nas/music"
MUSIC_ROOT_PATH="/Volumes/MusicDrive/Collection"

# Windows
MUSIC_ROOT_PATH="D:\Music"
MUSIC_ROOT_PATH="\\NAS\Music"
MUSIC_ROOT_PATH="C:\Users\User\Music"

# Docker (always use Unix-style paths inside container)
MUSIC_ROOT_PATH="/music"
```

#### Expected Directory Structure
```
$MUSIC_ROOT_PATH/
├── Pink Floyd/                    # Band folder
│   ├── The Wall/                 # Album folder
│   │   ├── 01 - In The Flesh.mp3
│   │   ├── 02 - The Thin Ice.mp3
│   │   └── ...
│   ├── Dark Side of the Moon/    # Album folder
│   │   ├── 01 - Speak to Me.mp3
│   │   └── ...
│   └── .band_metadata.json       # Auto-generated metadata
├── The Beatles/                   # Another band
│   ├── Abbey Road/
│   │   └── ...
│   └── .band_metadata.json
└── .collection_index.json         # Auto-generated collection index
```

#### Path Validation Rules
- ✅ Must exist and be accessible
- ✅ Must have read/write permissions
- ✅ Must contain at least one band folder
- ✅ Should not be a system directory (`/`, `/usr`, etc.)
- ✅ Unicode characters in paths are supported

### CACHE_DURATION_DAYS Configuration

Controls how long metadata is cached before requiring refresh.

#### Valid Values
```env
CACHE_DURATION_DAYS=1    # Refresh daily (development)
CACHE_DURATION_DAYS=7    # Weekly refresh
CACHE_DURATION_DAYS=30   # Monthly refresh (default)
CACHE_DURATION_DAYS=90   # Quarterly refresh
CACHE_DURATION_DAYS=365  # Annual refresh
CACHE_DURATION_DAYS=0    # Disable caching (always fetch)
```

#### Cache Behavior
- **Metadata Files**: `.band_metadata.json` files older than configured days are considered stale
- **Collection Index**: `.collection_index.json` is refreshed when underlying data changes
- **External Data**: Band information fetched from external APIs respects this cache duration
- **Force Refresh**: Use `force_rescan=true` in tools to bypass cache

### LOG_LEVEL Configuration

Controls the verbosity of logging output.

#### Available Levels
```env
LOG_LEVEL=DEBUG    # Verbose debugging information
LOG_LEVEL=INFO     # General information (default)
LOG_LEVEL=WARNING  # Warnings and important notices
LOG_LEVEL=ERROR    # Errors only (recommended for production)
```

#### Log Output Examples
```
# DEBUG level
DEBUG: Scanning folder: /music/Pink Floyd
DEBUG: Found album: The Wall (15 tracks)
DEBUG: Loading metadata from .band_metadata.json
INFO: Collection scan completed: 150 bands, 850 albums

# INFO level (default)
INFO: Music Collection MCP Server starting...
INFO: Configuration loaded: MUSIC_ROOT_PATH=/music
INFO: Collection found: 150 bands, 850 albums
INFO: MCP server ready on stdio

# ERROR level (production)
ERROR: Failed to access music directory: Permission denied
ERROR: Invalid metadata format in Pink Floyd/.band_metadata.json
```

## MCP Client Configuration

### Claude Desktop Integration

#### Configuration File Locations
```bash
# macOS
~/Library/Application Support/Claude/claude_desktop_config.json

# Windows
%APPDATA%\Claude\claude_desktop_config.json

# Linux
~/.config/claude-desktop/config.json
```

#### Basic Docker Configuration
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

#### Advanced Docker Configuration
```json
{
  "mcpServers": {
    "music-collection": {
      "command": "docker",
      "args": [
        "run", "--rm", "--interactive",
        "--memory=2g",
        "--cpus=2",
        "-v", "/path/to/your/music:/music",
        "-v", "/tmp/music-cache:/cache",
        "-e", "MUSIC_ROOT_PATH=/music",
        "-e", "CACHE_DURATION_DAYS=30",
        "-e", "LOG_LEVEL=ERROR"
      ],
      "cwd": "/path/to/music-catalog-mcp"
    }
  }
}
```

#### Local Python Configuration
```json
{
  "mcpServers": {
    "music-collection": {
      "command": "python",
      "args": ["/path/to/music-catalog-mcp/main.py"],
      "env": {
        "MUSIC_ROOT_PATH": "/path/to/your/music",
        "CACHE_DURATION_DAYS": "30",
        "LOG_LEVEL": "INFO"
      },
      "cwd": "/path/to/music-catalog-mcp"
    }
  }
}
```

### Cline (VS Code) Integration

#### Cline Settings Configuration
```json
{
  "cline.mcpServers": {
    "music-collection": {
      "command": "docker",
      "args": [
        "run", "--rm", "--interactive",
        "-v", "/path/to/your/music:/music",
        "-e", "MUSIC_ROOT_PATH=/music",
        "-e", "LOG_LEVEL=ERROR",
        "music-mcp-server"
      ]
    }
  }
}
```

### Generic MCP Client Configuration

For any MCP-compatible client that supports stdio transport:

#### Connection Parameters
```json
{
  "transport": "stdio",
  "command": ["docker", "run", "--rm", "--interactive"],
  "args": [
    "-v", "/path/to/music:/music",
    "-e", "MUSIC_ROOT_PATH=/music",
    "music-mcp-server"
  ],
  "cwd": "/path/to/music-catalog-mcp"
}
```

## Advanced Configuration Scenarios

### Multi-Collection Setup

Configure multiple music collections for different users or genres:

```json
{
  "mcpServers": {
    "music-rock": {
      "command": "docker",
      "args": [
        "run", "--rm", "--interactive", "--name", "music-rock",
        "-v", "/music/rock:/music",
        "-e", "MUSIC_ROOT_PATH=/music",
        "music-mcp-server"
      ]
    },
    "music-classical": {
      "command": "docker",
      "args": [
        "run", "--rm", "--interactive", "--name", "music-classical",
        "-v", "/music/classical:/music",
        "-e", "MUSIC_ROOT_PATH=/music",
        "music-mcp-server"
      ]
    }
  }
}
```

### Network Storage Configuration

#### NFS/SMB Mount Configuration
```bash
# Mount network storage first
sudo mount -t nfs nas.local:/music /mnt/music-nas

# Then configure Docker
docker run -v "/mnt/music-nas:/music" \
           -e "MUSIC_ROOT_PATH=/music" \
           music-mcp-server
```

#### Cloud Storage Integration
```bash
# Mount cloud storage (example with rclone)
rclone mount gdrive:Music /mnt/cloud-music &

# Configure with cloud path
docker run -v "/mnt/cloud-music:/music" \
           -e "MUSIC_ROOT_PATH=/music" \
           -e "CACHE_DURATION_DAYS=1" \
           music-mcp-server
```

### Performance Optimization Configuration

#### Large Collection Configuration (>10,000 albums)
```bash
docker run --memory=4g \
           --cpus=4 \
           --shm-size=1g \
           -v "/path/to/huge/collection:/music" \
           -e "MUSIC_ROOT_PATH=/music" \
           -e "CACHE_DURATION_DAYS=90" \
           -e "LOG_LEVEL=ERROR" \
           music-mcp-server
```

#### SSD Cache Configuration
```bash
# Use SSD for cache storage
docker run -v "/path/to/music:/music" \
           -v "/ssd/cache:/app/cache" \
           -e "MUSIC_ROOT_PATH=/music" \
           -e "CACHE_DURATION_DAYS=30" \
           music-mcp-server
```

## Configuration Validation

### Automatic Validation

The server validates configuration at startup:

```bash
# Run validation check
docker run --rm \
           -v "/path/to/music:/music" \
           -e "MUSIC_ROOT_PATH=/music" \
           music-mcp-server --validate-config
```

### Validation Checklist

#### Environment Variables
- ✅ `MUSIC_ROOT_PATH` is set and accessible
- ✅ `CACHE_DURATION_DAYS` is a valid positive integer
- ✅ `LOG_LEVEL` is one of: DEBUG, INFO, WARNING, ERROR

#### File System
- ✅ Music directory exists and is readable
- ✅ Music directory is writable (for metadata files)
- ✅ At least one band folder is present
- ✅ Sufficient disk space for metadata storage

#### Permissions
- ✅ Docker has access to mounted volumes
- ✅ User has read/write permissions on music directory
- ✅ No SELinux or other security restrictions blocking access

### Troubleshooting Configuration Issues

#### Common Configuration Problems

**Problem**: `MUSIC_ROOT_PATH not set`
```bash
# Solution: Set the environment variable
export MUSIC_ROOT_PATH="/path/to/music"
```

**Problem**: `Permission denied accessing music directory`
```bash
# Solution: Fix permissions
sudo chown -R $(id -u):$(id -g) /path/to/music
chmod 755 /path/to/music
```

**Problem**: `Invalid CACHE_DURATION_DAYS value`
```bash
# Solution: Use valid integer
export CACHE_DURATION_DAYS=30  # Not "30 days" or "thirty"
```

**Problem**: `Docker volume mount failed`
```bash
# Solution: Use absolute paths
docker run -v "/absolute/path/to/music:/music"  # Not ./music
```

#### Configuration Testing Commands

```bash
# Test environment loading
docker run --rm music-mcp-server python -c "from src.config import Config; print(Config())"

# Test music directory access
docker run --rm -v "/path/to/music:/music" music-mcp-server ls -la /music

# Test full configuration
docker run --rm \
           -v "/path/to/music:/music" \
           -e "MUSIC_ROOT_PATH=/music" \
           music-mcp-server python -c "
from src.tools.scanner import scan_music_folders
result = scan_music_folders()
print(f'Found {result[\"total_bands\"]} bands')
"
```

## Security Configuration

### File System Security
```bash
# Restrict container permissions
docker run --read-only \
           --tmpfs /tmp \
           --tmpfs /app/cache \
           -v "/path/to/music:/music:ro" \
           -v "/path/to/metadata:/metadata:rw" \
           music-mcp-server
```

### Network Security
```bash
# Disable networking if not needed
docker run --network=none \
           -v "/path/to/music:/music" \
           music-mcp-server
```

## Environment-Specific Examples

### Development Environment
```env
MUSIC_ROOT_PATH=./test_music_collection
CACHE_DURATION_DAYS=1
LOG_LEVEL=DEBUG
```

### Production Environment
```env
MUSIC_ROOT_PATH=/srv/music
CACHE_DURATION_DAYS=90
LOG_LEVEL=ERROR
```

### Testing Environment
```env
MUSIC_ROOT_PATH=/tmp/test_music
CACHE_DURATION_DAYS=0
LOG_LEVEL=DEBUG
```

For more configuration examples and troubleshooting, see:
- [Installation Guide](INSTALLATION.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Usage Examples](USAGE_EXAMPLES.md) 