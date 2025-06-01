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

## Installation Methods

### Method 1: Docker Deployment (Recommended)

Docker provides the most reliable and consistent environment for running the MCP server.

#### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/music-catalog-mcp.git
cd music-catalog-mcp
```

#### Step 2: Build the Docker Container
```bash
docker build -t music-mcp-server .
```

#### Step 3: Prepare Your Music Collection
Ensure your music collection follows this structure:
```
/path/to/your/music/
├── Pink Floyd/
│   ├── The Wall/
│   │   ├── 01 - In The Flesh.mp3
│   │   └── 02 - The Thin Ice.mp3
│   ├── Dark Side of the Moon/
│   │   ├── 01 - Speak to Me.mp3
│   │   └── 02 - Breathe.mp3
│   └── .band_metadata.json (created automatically)
├── The Beatles/
│   ├── Abbey Road/
│   │   ├── 01 - Come Together.mp3
│   │   └── 02 - Something.mp3
│   └── .band_metadata.json (created automatically)
└── .collection_index.json (created automatically)
```

#### Step 4: Run the MCP Server
```bash
# Linux/macOS
docker run -d --name music-mcp-container \
  -v "/path/to/your/music:/music" \
  -e "MUSIC_ROOT_PATH=/music" \
  -e "CACHE_DURATION_DAYS=30" \
  music-mcp-server

# Windows
docker run -d --name music-mcp-container \
  -v "D:\Music:/music" \
  -e "MUSIC_ROOT_PATH=/music" \
  -e "CACHE_DURATION_DAYS=30" \
  music-mcp-server
```

### Method 2: Local Python Installation

For development or custom deployment scenarios.

#### Step 1: Create Virtual Environment
```bash
python -m venv music-mcp-env
source music-mcp-env/bin/activate  # Linux/macOS
# or
music-mcp-env\Scripts\activate     # Windows
```

#### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 3: Configure Environment
Create a `.env` file in the project root:
```env
MUSIC_ROOT_PATH=/path/to/your/music
CACHE_DURATION_DAYS=30
LOG_LEVEL=INFO
```

#### Step 4: Run the MCP Server
```bash
python main.py
```

### Method 3: Development Setup

For contributors and developers working on the project.

#### Step 1: Clone and Setup
```bash
git clone https://github.com/yourusername/music-catalog-mcp.git
cd music-catalog-mcp
python -m venv venv
source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

#### Step 2: Setup Test Environment
```bash
# Create test music collection
mkdir -p test_music_collection
cp -r test_data/* test_music_collection/

# Set test environment
export MUSIC_ROOT_PATH="$(pwd)/test_music_collection"
```

#### Step 3: Run Tests
```bash
# Unit tests
docker build -f Dockerfile.test -t music-mcp-tests .
docker run --rm music-mcp-tests python -m pytest . -v

# Manual testing
python main.py
```

## MCP Client Configuration

### Claude Desktop Configuration

Add the following to your Claude Desktop configuration file:

**Location:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

#### Docker Configuration
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
        "music-mcp-server"
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
        "CACHE_DURATION_DAYS": "30"
      }
    }
  }
}
```

### Cline Configuration

For VS Code with Cline extension:

```json
{
  "cline.mcpServers": {
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

### Other MCP Clients

For any MCP-compatible client, use these connection parameters:
- **Transport**: stdio
- **Command**: `docker run --rm --interactive -v "/path/to/music:/music" -e "MUSIC_ROOT_PATH=/music" music-mcp-server`
- **Working Directory**: Project root directory

## Configuration Options

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MUSIC_ROOT_PATH` | ✅ Yes | None | Path to your music collection root directory |
| `CACHE_DURATION_DAYS` | ❌ No | 30 | Number of days to cache metadata before refresh |
| `LOG_LEVEL` | ❌ No | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |

### Configuration Validation

The server validates configuration at startup:
```bash
# Check configuration
docker run --rm -v "/path/to/music:/music" -e "MUSIC_ROOT_PATH=/music" music-mcp-server --validate-config

# Expected output:
✅ Configuration valid
✅ Music directory accessible: /music
✅ Permissions verified: read/write access
✅ Directory structure: 150 bands, 850 albums detected
```

## Verification

### 1. Container Health Check
```bash
# Check if container is running
docker ps | grep music-mcp-container

# Check logs
docker logs music-mcp-container

# Expected output:
INFO: Music Collection MCP Server starting...
INFO: Configuration loaded: MUSIC_ROOT_PATH=/music
INFO: Collection found: 150 bands, 850 albums
INFO: MCP server ready on stdio
```

### 2. MCP Client Connection Test

In your MCP client, test the connection:
```
Use the scan_music_folders tool to verify the server is working
```

Expected response:
```json
{
  "status": "success",
  "results": {
    "total_bands": 150,
    "total_albums": 850,
    "music_files_found": 12500,
    "scan_duration": "15.2 seconds"
  }
}
```

### 3. Resource Access Test

Try accessing a band resource:
```
Request the resource: band://info/Pink Floyd
```

You should receive a markdown document with band information.

## Common Issues

### Permission Errors
```bash
# Fix Docker volume permissions
sudo chown -R $(id -u):$(id -g) /path/to/your/music
chmod 755 /path/to/your/music
```

### Port Conflicts
The MCP server uses stdio transport (no ports), but if using custom transport:
```bash
# Check for port conflicts
netstat -tulpn | grep :8000
```

### Memory Issues
For large collections (>10,000 albums):
```bash
# Increase Docker memory limit
docker run --memory=2g --name music-mcp-container ...
```

### Path Issues on Windows
```bash
# Use forward slashes in Docker commands
docker run -v "D:/Music:/music" ...

# Or use WSL2 paths
docker run -v "/mnt/d/Music:/music" ...
```

## Next Steps

1. **Scan Your Collection**: Use the `scan_music_folders` tool to discover your music
2. **Get Band List**: Use `get_band_list` to see all discovered bands
3. **Fetch Band Info**: Use the `fetch_band_info` prompt to gather comprehensive band data
4. **Save Metadata**: Use `save_band_metadata` to store band information locally
5. **Analyze Collection**: Use collection insights to understand your music library

## Support

- **Documentation**: See `docs/` directory for comprehensive guides
- **Issues**: Report bugs on GitHub repository
- **Testing**: Use the test suite to verify functionality
- **Logs**: Check Docker logs for troubleshooting information

For additional help, see:
- [Configuration Guide](CONFIGURATION.md)
- [Usage Examples](USAGE_EXAMPLES.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [FAQ](FAQ.md) 