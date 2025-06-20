# Music Collection MCP Server - Configuration Guide

## 🚀 Quick Configuration

### Automated Setup (Recommended)
The fastest way to configure the server is using the automated setup:

```bash
python scripts/setup.py
```

This will handle all configuration automatically including:
- Environment variables
- Claude Desktop configuration
- Path validation
- Feature enablement

## ⚙️ Manual Configuration

### Environment Variables

Set these core variables for your music collection:

```bash
# Required
MUSIC_ROOT_PATH="/path/to/your/music"

# Optional (with defaults)
CACHE_DURATION_DAYS=30                    # Cache expiration in days
LOG_LEVEL=INFO                           # ERROR, WARNING, INFO, DEBUG
```

### Advanced Settings

```bash
# Album Type Detection
ENABLE_TYPE_DETECTION=true               # Enable 8-type album classification
DEFAULT_ALBUM_TYPE=Album                 # Default when detection uncertain

# Collection Analysis  
ENABLE_STRUCTURE_ANALYSIS=true          # Folder organization analysis
```

## 🤖 Claude Desktop Setup

### Configuration File Locations
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### Python Installation
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
      }
    }
  }
}
```

### Docker Installation
```json
{
  "mcpServers": {
    "music-collection": {
      "command": "docker",
      "args": [
        "run", "--rm", "--interactive",
        "-v", "/path/to/your/music:/music",
        "-e", "MUSIC_ROOT_PATH=/music",
        "-e", "CACHE_DURATION_DAYS=30",
        "music-mcp"
      ]
    }
  }
}
```

## 📁 Music Collection Organization

### Supported Folder Structures

The server works with multiple organization patterns:

#### Enhanced Structure (Best Performance)
```
Band Name/
├── Album/
│   ├── 1973 - Album Name/
│   └── 1979 - Another Album/
├── Live/
│   └── 1985 - Live Album/
├── Compilation/
│   └── 1996 - Greatest Hits/
└── .band_metadata.json (auto-created)
```

#### Simple Structure (Widely Compatible)
```
Band Name/
├── 1973 - Album Name/
├── 1979 - Another Album/
├── 1985 - Live Album (Live)/
├── 1996 - Greatest Hits (Compilation)/
└── .band_metadata.json (auto-created)
```

#### Legacy Structure (Supported)
```
Band Name/
├── Album Name/
├── Another Album/
├── Live Album/
└── .band_metadata.json (auto-created)
```

### Album Type Detection

The server automatically detects 8 album types:

| Type | Keywords | Example |
|------|----------|---------|
| **Album** | *(default)* | `1973 - Dark Side of the Moon` |
| **Live** | live, concert, unplugged | `1988 - Live at Wembley` |
| **Compilation** | greatest hits, best of, collection | `1996 - Greatest Hits` |
| **EP** | ep, e.p. | `1980 - Love EP` |
| **Demo** | demo, demos, unreleased | `1978 - Early Demos` |
| **Single** | single | `1981 - Another Brick Single` |
| **Instrumental** | instrumental | `1973 - DSOTM (Instrumental)` |
| **Split** | split, vs., versus | `2000 - Band A vs Band B` |

## 🔧 Advanced Configuration

### Multiple Collections
Configure separate instances for different music collections:

```json
{
  "mcpServers": {
    "music-rock": {
      "command": "python",
      "args": ["/path/to/music-catalog-mcp/main.py"],
      "env": {
        "MUSIC_ROOT_PATH": "/path/to/rock-music"
      }
    },
    "music-classical": {
      "command": "python",
      "args": ["/path/to/music-catalog-mcp/main.py"],
      "env": {
        "MUSIC_ROOT_PATH": "/path/to/classical-music"
      }
    }
  }
}
```

### Development Configuration
For development and testing:

```bash
# Development settings
MUSIC_ROOT_PATH=/path/to/test/music
CACHE_DURATION_DAYS=1                    # Short cache for testing
LOG_LEVEL=DEBUG                          # Detailed logging
```

### Production Configuration
For production deployment:

```bash
# Production settings  
MUSIC_ROOT_PATH=/mnt/music_collection
CACHE_DURATION_DAYS=30                   # Standard cache duration
LOG_LEVEL=WARNING                        # Minimal logging
```

## 🐳 Docker Configuration

### Basic Docker Run
```bash
docker run -d --name music-mcp \
  -v "/path/to/your/music:/music" \
  -e "MUSIC_ROOT_PATH=/music" \
  -e "CACHE_DURATION_DAYS=30" \
  music-mcp
```

### Docker Compose
Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  music-mcp:
    build: .
    container_name: music-mcp
    environment:
      - MUSIC_ROOT_PATH=/music
      - CACHE_DURATION_DAYS=30
      - LOG_LEVEL=INFO
    volumes:
      - "/path/to/your/music:/music:ro"
    restart: unless-stopped
```

Run with:
```bash
docker-compose up -d music-mcp
```

### Using Setup Scripts
Automated Docker startup:

```bash
# Make executable
chmod +x scripts/start-docker.sh

# Start with options
./scripts/start-docker.sh -m /path/to/music -c 30 -l INFO
```

## 🔍 Configuration Validation

### Check Your Setup
Use the built-in validation tools:

```bash
# Validate collection structure
python scripts/validate-music-structure.py /path/to/your/music

# Run health check
python scripts/health-check.py /path/to/your/music

# Test configuration
python main.py
```

### Verify Claude Desktop Connection
1. Restart Claude Desktop after configuration changes
2. Start a new conversation
3. Test with: "Can you scan my music collection?"

## 🛠️ Maintenance Configuration

### Backup Settings
Configure automated backups:

```bash
# Backup your collection metadata
python scripts/backup-recovery.py backup /path/to/your/music

# Create regular backups
python scripts/backup-recovery.py backup /path/to/music --incremental
```

### Monitoring Setup
Enable comprehensive monitoring:

```python
# In your scripts or automation
from scripts.monitoring.logging_config import setup_monitoring

monitoring = setup_monitoring(environment="production")
logger = monitoring['main_logger']
```

## 🆘 Troubleshooting Configuration

### Common Issues

**Environment variables not working:**
```bash
# Check if variables are set
echo $MUSIC_ROOT_PATH
env | grep MUSIC_

# Set them properly
export MUSIC_ROOT_PATH="/path/to/your/music"
```

**Claude Desktop not connecting:**
```json
// Check JSON syntax is valid
// Verify paths exist
// Ensure no trailing commas
{
  "mcpServers": {
    "music-collection": {
      "command": "python",
      "args": ["/absolute/path/to/main.py"],
      "env": {
        "MUSIC_ROOT_PATH": "/absolute/path/to/music"
      }
    }
  }
}
```

**Docker container issues:**
```bash
# Check container logs
docker logs music-mcp

# Verify volume mounts
docker inspect music-mcp

# Test manually
docker run --rm -it \
  -v "/path/to/music:/music" \
  -e "MUSIC_ROOT_PATH=/music" \
  music-mcp python main.py
```

### Getting Help
1. **Use automated health check**: `python scripts/health-check.py`
2. **Validate structure**: `python scripts/validate-music-structure.py`
3. **Check the [FAQ](FAQ.md)** for common questions
4. **Review [Troubleshooting Guide](TROUBLESHOOTING.md)**

## 📚 Next Steps

After configuration:
1. **Test your setup** with basic commands
2. **Scan your collection** for the first time
3. **Explore advanced features** with [Usage Examples](USAGE_EXAMPLES.md)
4. **Optimize organization** with [Collection Organization](COLLECTION_ORGANIZATION.md)

---

*Your music collection is now ready for intelligent AI-powered management!* 🎶 