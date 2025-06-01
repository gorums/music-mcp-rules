# Claude Desktop Configuration Examples

This directory contains ready-to-use configuration examples for integrating the Music Collection MCP Server with Claude Desktop.

## Configuration File Locations

### Windows
```
%APPDATA%\Claude\claude_desktop_config.json
```

### macOS
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

### Linux
```
~/.config/Claude/claude_desktop_config.json
```

## Configuration Examples

### 1. Local Python Setup
Use this configuration if you installed the MCP server locally with Python.

**File:** `local-python-config.json`

### 2. Docker Container Setup  
Use this configuration if you're running the MCP server in a Docker container.

**File:** `docker-config.json`

### 3. Development Setup
Use this configuration for development with debug logging enabled.

**File:** `development-config.json`

### 4. Multi-Collection Setup
Use this configuration if you have multiple music collections.

**File:** `multi-collection-config.json`

### 5. Network Storage Setup
Use this configuration if your music collection is on network storage.

**File:** `network-storage-config.json`

## Installation Instructions

1. **Locate your Claude Desktop config file** using the paths above
2. **Choose the appropriate configuration** from the examples below
3. **Update the paths** to match your music collection location
4. **Copy the configuration** to your Claude Desktop config file
5. **Restart Claude Desktop** for changes to take effect

## Troubleshooting

- **Server not appearing**: Check that the paths are correct and the server executable exists
- **Permission errors**: Ensure Claude Desktop has read access to your music folder
- **Docker issues**: Verify Docker is running and the image is built
- **Path format**: Use forward slashes (/) even on Windows, or escape backslashes (\\\\)

## Testing Configuration

After configuration, you can test the integration by asking Claude:

```
"Scan my music collection and show me the band list"
```

The server should respond with information about your music collection.

## Log Levels

- **ERROR**: Minimal output, recommended for production use
- **INFO**: Standard output with operational information  
- **DEBUG**: Verbose output for troubleshooting (development only)

## Security Considerations

- The MCP server only needs **read access** to your music folder
- Use read-only volume mounts (`-v path:/music:ro`) when using Docker
- Avoid exposing sensitive directories in the music path 