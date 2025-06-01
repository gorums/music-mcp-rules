# Music Collection MCP Server - Troubleshooting Guide

## Overview

This guide helps you diagnose and resolve common issues with the Music Collection MCP Server, including album scanning problems, Docker configuration issues, and MCP client integration challenges.

## Quick Diagnostic Commands

### Health Check
```bash
# Check if server is running
docker ps | grep music-mcp

# Check server logs
docker logs music-mcp-container

# Test configuration
docker run --rm -v "/path/to/music:/music" -e "MUSIC_ROOT_PATH=/music" music-mcp-server --validate-config
```

### Basic Functionality Test
```bash
# Test music directory scanning
docker run --rm -v "/path/to/music:/music" -e "MUSIC_ROOT_PATH=/music" music-mcp-server python -c "
from src.tools.scanner import scan_music_folders
result = scan_music_folders()
print(f'Found {result[\"total_bands\"]} bands, {result[\"total_albums\"]} albums')
"
```

## Configuration Issues

### Problem: "MUSIC_ROOT_PATH not set"

**Symptoms:**
```
ERROR: Configuration validation failed: MUSIC_ROOT_PATH is required
```

**Solutions:**
1. **Environment Variable Missing**
```bash
# Set the environment variable
export MUSIC_ROOT_PATH="/path/to/your/music"

# For Docker
docker run -e "MUSIC_ROOT_PATH=/music" ...
```

2. **Check .env File**
```bash
# Create .env file in project root
echo "MUSIC_ROOT_PATH=/path/to/your/music" > .env
```

3. **Verify Environment Loading**
```bash
# Test configuration loading
python -c "from src.config import Config; print(Config().music_root_path)"
```

### Problem: "Permission denied accessing music directory"

**Symptoms:**
```
ERROR: PermissionError: [Errno 13] Permission denied: '/music'
ERROR: Failed to scan music directory: insufficient permissions
```

**Solutions:**
1. **Fix File Permissions**
```bash
# Make directory readable/writable
sudo chown -R $(id -u):$(id -g) /path/to/your/music
chmod 755 /path/to/your/music
chmod -R 644 /path/to/your/music/*
```

2. **Docker User Mapping**
```bash
# Run Docker with current user
docker run --user $(id -u):$(id -g) \
           -v "/path/to/music:/music" \
           music-mcp-server
```

3. **SELinux Context (CentOS/RHEL)**
```bash
# Set SELinux context for Docker volumes
sudo setsebool -P container_manage_cgroup true
sudo chcon -Rt svirt_sandbox_file_t /path/to/your/music
```

### Problem: "Invalid CACHE_DURATION_DAYS value"

**Symptoms:**
```
ERROR: CACHE_DURATION_DAYS must be a positive integer
ValueError: invalid literal for int() with base 10: 'thirty'
```

**Solutions:**
1. **Use Numeric Values**
```bash
# Correct format
export CACHE_DURATION_DAYS=30

# Incorrect formats to avoid
export CACHE_DURATION_DAYS="30 days"    # Wrong
export CACHE_DURATION_DAYS="thirty"     # Wrong
```

2. **Validate Value Range**
```bash
# Valid ranges
CACHE_DURATION_DAYS=0    # Disable caching
CACHE_DURATION_DAYS=1    # Daily refresh
CACHE_DURATION_DAYS=365  # Annual refresh
```

## Docker Issues

### Problem: "Docker volume mount failed"

**Symptoms:**
```
ERROR: docker: Error response from daemon: invalid mount config
ERROR: No such file or directory
```

**Solutions:**
1. **Use Absolute Paths**
```bash
# Correct - absolute path
docker run -v "/home/user/Music:/music" music-mcp-server

# Incorrect - relative path
docker run -v "./Music:/music" music-mcp-server
```

2. **Windows Path Issues**
```bash
# Windows - use forward slashes
docker run -v "D:/Music:/music" music-mcp-server

# Windows - WSL2 paths
docker run -v "/mnt/d/Music:/music" music-mcp-server

# Windows - avoid spaces in paths
docker run -v "D:/My Music:/music" music-mcp-server  # May fail
```

3. **Path Escaping**
```bash
# Paths with spaces - use quotes
docker run -v "/home/user/My Music Collection:/music" music-mcp-server
```

### Problem: "Container exits immediately"

**Symptoms:**
```bash
$ docker ps
CONTAINER ID   IMAGE   COMMAND   CREATED   STATUS   PORTS   NAMES
# No running containers
```

**Diagnostic Steps:**
1. **Check Exit Code and Logs**
```bash
# See why container exited
docker logs music-mcp-container

# Common error patterns
"ModuleNotFoundError: No module named 'src'"
"Configuration validation failed"
"MUSIC_ROOT_PATH directory not found"
```

2. **Test Container Interactively**
```bash
# Run container with shell access
docker run -it --entrypoint /bin/bash music-mcp-server

# Inside container, test components
python -c "from src.config import Config; print('Config OK')"
python -c "from src.tools.scanner import scan_music_folders; print('Scanner OK')"
```

3. **Check Resource Limits**
```bash
# Increase memory limit for large collections
docker run --memory=2g music-mcp-server

# Check system resources
docker system df
docker system prune  # Clean up space if needed
```

### Problem: "Port already in use" (for custom transports)

**Symptoms:**
```
ERROR: bind: address already in use
```

**Solutions:**
1. **Use Standard stdio Transport**
```bash
# Default MCP uses stdio (no ports needed)
docker run music-mcp-server  # Uses stdio by default
```

2. **Find and Kill Process Using Port**
```bash
# Find process using port
netstat -tulpn | grep :8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

## Album Scanning Issues

### Problem: "No bands found in music directory"

**Symptoms:**
```json
{
  "total_bands": 0,
  "total_albums": 0,
  "message": "No music bands found in directory"
}
```

**Solutions:**
1. **Check Directory Structure**
```bash
# Verify expected structure
ls -la /path/to/your/music/
# Should show band folders like:
# Pink Floyd/
# The Beatles/
# Led Zeppelin/
```

2. **Expected Folder Organization**
```
Music/
├── Pink Floyd/           # Band folder
│   ├── The Wall/        # Album folder
│   │   ├── 01-song.mp3
│   │   └── 02-song.mp3
│   └── Animals/
│       └── *.mp3
└── The Beatles/
    ├── Abbey Road/
    └── Sgt Pepper/
```

3. **Check for Hidden or System Folders**
```bash
# Scanner ignores these patterns
ls -la /music/ | grep -E "^\.|Recycle|System|temp|cache"

# Move or rename problematic folders
mv "/music/.hidden_band" "/music/Hidden Band"
```

### Problem: "Albums not detected in band folders"

**Symptoms:**
```json
{
  "band_name": "Pink Floyd",
  "albums_count": 0,
  "albums": []
}
```

**Solutions:**
1. **Verify Album Folder Structure**
```bash
# Check band folder contents
ls -la "/path/to/music/Pink Floyd/"
# Should show album folders, not loose files
```

2. **Supported Music File Extensions**
The scanner looks for these file types:
- `.mp3`, `.flac`, `.wav`, `.aac`
- `.m4a`, `.ogg`, `.wma`, `.mp4`, `.m4p`

3. **Minimum Track Count**
```bash
# Each album folder needs at least 1 music file
find "/path/to/music/Pink Floyd/The Wall" -name "*.mp3" -o -name "*.flac" | wc -l
```

### Problem: "Missing albums not detected"

**Symptoms:**
```
Missing albums analysis shows 0 missing albums, but metadata contains more albums than physical folders
```

**Solutions:**
1. **Force Full Rescan**
```json
{
  "method": "tools/call",
  "params": {
    "name": "scan_music_folders",
    "arguments": {
      "force_rescan": true,
      "include_missing_albums": true
    }
  }
}
```

2. **Check Metadata vs Physical Albums**
```bash
# List physical albums
ls "/path/to/music/Pink Floyd/"

# Check metadata file
cat "/path/to/music/Pink Floyd/.band_metadata.json" | jq '.albums[].album_name'
```

3. **Manual Missing Album Detection**
```python
# Check missing album logic
from src.tools.scanner import _detect_missing_albums
missing = _detect_missing_albums("Pink Floyd", physical_albums, metadata_albums)
print(f"Missing: {missing}")
```

## MCP Client Integration Issues

### Problem: "MCP client cannot connect to server"

**Symptoms:**
- Claude Desktop shows connection error
- Tools/resources not visible in MCP client
- "Server not responding" messages

**Solutions:**
1. **Verify Client Configuration**
```json
{
  "mcpServers": {
    "music-collection": {
      "command": "docker",
      "args": [
        "run", "--rm", "--interactive",
        "-v", "/absolute/path/to/music:/music",
        "-e", "MUSIC_ROOT_PATH=/music",
        "music-mcp-server"
      ]
    }
  }
}
```

2. **Test Manual Connection**
```bash
# Test if server responds to stdio
echo '{"jsonrpc": "2.0", "method": "initialize", "id": 1, "params": {}}' | \
docker run --rm -i -v "/path/to/music:/music" -e "MUSIC_ROOT_PATH=/music" music-mcp-server
```

3. **Check Server Logs in Client Context**
```bash
# For Claude Desktop, check logs at:
# macOS: ~/Library/Logs/Claude/
# Windows: %APPDATA%\Claude\logs\
```

### Problem: "Tools appear as errors in MCP client"

**Symptoms:**
- Tools are listed but show error icons
- Error messages in client interface
- Functions work but appear broken

**Solutions:**
1. **Lower Log Level**
```bash
# Set ERROR log level to suppress INFO messages
docker run -e "LOG_LEVEL=ERROR" music-mcp-server
```

2. **Update FastMCP Configuration**
This is a known FastMCP display issue. Tools work correctly despite error appearance.

3. **Verify Tool Functionality**
```bash
# Test tool execution directly
echo '{"jsonrpc": "2.0", "method": "tools/call", "id": 1, "params": {"name": "scan_music_folders", "arguments": {}}}' | \
docker run --rm -i music-mcp-server
```

### Problem: "Resources not loading in client"

**Symptoms:**
- `band://info/Pink Floyd` shows "Resource not found"
- `collection://summary` returns empty response

**Solutions:**
1. **Verify Resource URIs**
```bash
# Correct URI format
band://info/Pink Floyd           # Correct
collection://summary             # Correct

# Incorrect formats
band/Pink Floyd                  # Wrong
band://Pink Floyd                # Wrong
collection/summary               # Wrong
```

2. **Check Band Name Encoding**
```bash
# URL encode special characters
band://info/AC%2FDC              # For "AC/DC"
band://info/Guns%20N%27%20Roses  # For "Guns N' Roses"
```

3. **Verify Band Exists**
```json
{
  "method": "tools/call",
  "params": {
    "name": "get_band_list",
    "arguments": {"search": "Pink Floyd"}
  }
}
```

## Performance Issues

### Problem: "Scanning takes very long time"

**Symptoms:**
```
Scan duration: 300+ seconds for moderate collections
Memory usage continuously increasing
```

**Solutions:**
1. **Optimize Docker Resources**
```bash
# Increase memory and CPU limits
docker run --memory=4g --cpus=2 music-mcp-server
```

2. **Use SSD Storage**
```bash
# Mount music directory from SSD
docker run -v "/ssd/path/to/music:/music" music-mcp-server
```

3. **Enable Incremental Scanning**
```json
{
  "method": "tools/call",
  "params": {
    "name": "scan_music_folders",
    "arguments": {
      "force_rescan": false  // Use cache when possible
    }
  }
}
```

### Problem: "Memory usage too high"

**Symptoms:**
```
Docker container using >2GB RAM
System becomes slow during scanning
```

**Solutions:**
1. **Implement Pagination**
```json
{
  "method": "tools/call",
  "params": {
    "name": "get_band_list",
    "arguments": {
      "page_size": 20,  // Smaller page sizes
      "page": 1
    }
  }
}
```

2. **Clear Caches Periodically**
```bash
# Clean up container caches
docker run --rm music-mcp-server python -c "
from src.tools.cache import clear_expired_cache
clear_expired_cache()
"
```

## Data Issues

### Problem: "Corrupted metadata files"

**Symptoms:**
```
JSONDecodeError: Expecting ',' delimiter
Invalid metadata format in .band_metadata.json
```

**Solutions:**
1. **Backup and Restore**
```bash
# Check for backup files
ls /path/to/music/Pink\ Floyd/.band_metadata.json.backup.*

# Restore from backup
cp "/path/to/music/Pink Floyd/.band_metadata.json.backup.20250129" \
   "/path/to/music/Pink Floyd/.band_metadata.json"
```

2. **Validate JSON Format**
```bash
# Check JSON syntax
python -m json.tool "/path/to/music/Pink Floyd/.band_metadata.json"

# Fix common issues
sed -i 's/,\s*}/}/g' "/path/to/music/Pink Floyd/.band_metadata.json"  # Remove trailing commas
```

3. **Regenerate Metadata**
```bash
# Delete corrupted file and rescan
rm "/path/to/music/Pink Floyd/.band_metadata.json"

# Force rescan to regenerate
docker run music-mcp-server python -c "
from src.tools.scanner import scan_music_folders
scan_music_folders(force_rescan=True)
"
```

### Problem: "Analysis data lost after metadata update"

**Symptoms:**
```
Band metadata updated successfully, but analyze section is now empty
Previous ratings and reviews are missing
```

**Solutions:**
1. **Check Analysis Preservation Settings**
```json
{
  "method": "tools/call",
  "params": {
    "name": "save_band_metadata",
    "arguments": {
      "band_name": "Pink Floyd",
      "metadata": {...},
      "preserve_analyze": true  // Ensure this is true
    }
  }
}
```

2. **Restore from Backup**
```bash
# Check for analyze backup
grep -l "analyze" /path/to/music/Pink\ Floyd/.band_metadata.json.backup.*

# Copy analyze section from backup
python -c "
import json
with open('backup.json') as f: backup = json.load(f)
with open('current.json') as f: current = json.load(f)
current['analyze'] = backup.get('analyze', {})
with open('current.json', 'w') as f: json.dump(current, f, indent=2)
"
```

## Network and API Issues

### Problem: "Brave search integration not working"

**Symptoms:**
```
Error: Unable to fetch band information from external sources
Brave search API timeout or connection error
```

**Solutions:**
1. **Check Network Connectivity**
```bash
# Test from container
docker run --rm music-mcp-server python -c "
import requests
response = requests.get('https://api.search.brave.com/res/v1/web/search')
print(f'Status: {response.status_code}')
"
```

2. **Verify API Configuration**
```bash
# Check if Brave search MCP is available
# This depends on your MCP client configuration
```

3. **Use Offline Mode**
```json
{
  "method": "tools/call",
  "params": {
    "name": "save_band_metadata",
    "arguments": {
      "band_name": "Pink Floyd",
      "metadata": {
        // Manually entered metadata
      }
    }
  }
}
```

## Advanced Troubleshooting

### Debug Mode

Enable detailed logging for troubleshooting:

```bash
# Run with debug logging
docker run -e "LOG_LEVEL=DEBUG" music-mcp-server

# Save debug logs
docker logs music-mcp-container > debug.log 2>&1
```

### Container Inspection

```bash
# Inspect running container
docker exec -it music-mcp-container /bin/bash

# Check mounted volumes
df -h
ls -la /music

# Check Python environment
python --version
pip list | grep -E "mcp|pydantic|fastapi"
```

### Manual Testing Scripts

Create test script for component validation:

```python
#!/usr/bin/env python3
# test_components.py

def test_config():
    try:
        from src.config import Config
        config = Config()
        print(f"✅ Config loaded: {config.music_root_path}")
        return True
    except Exception as e:
        print(f"❌ Config failed: {e}")
        return False

def test_scanner():
    try:
        from src.tools.scanner import scan_music_folders
        result = scan_music_folders()
        print(f"✅ Scanner: {result['total_bands']} bands found")
        return True
    except Exception as e:
        print(f"❌ Scanner failed: {e}")
        return False

def test_storage():
    try:
        from src.tools.storage import load_collection_index
        index = load_collection_index()
        print(f"✅ Storage: {len(index.bands)} bands in index")
        return True
    except Exception as e:
        print(f"❌ Storage failed: {e}")
        return False

if __name__ == "__main__":
    tests = [test_config, test_scanner, test_storage]
    results = [test() for test in tests]
    success_rate = sum(results) / len(results) * 100
    print(f"\nOverall: {success_rate:.1f}% tests passed")
```

Run the test script:
```bash
docker run --rm -v "$(pwd)/test_components.py:/app/test_components.py" music-mcp-server python test_components.py
```

## Getting Help

### Log Collection
When reporting issues, collect these logs:

```bash
# System information
uname -a
docker --version
python --version

# Container logs
docker logs music-mcp-container

# Configuration
docker run --rm music-mcp-server python -c "from src.config import Config; print(Config())"

# File permissions
ls -la /path/to/your/music/
```

### Support Channels
- **GitHub Issues**: Report bugs with full logs
- **Documentation**: Check other documentation files
- **Test Suite**: Run the test suite to verify functionality

For additional help, see:
- [Installation Guide](INSTALLATION.md)
- [Configuration Guide](CONFIGURATION.md)
- [Usage Examples](USAGE_EXAMPLES.md)
- [FAQ](FAQ.md) 