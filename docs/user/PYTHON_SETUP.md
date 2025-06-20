# Python Setup Guide for Music Collection MCP Server

This guide will help you set up and run the Music Collection MCP Server directly with Python instead of Docker.

## Prerequisites

- Python 3.8+ (tested with Python 3.13.4)
- Windows, macOS, or Linux

## Installation Steps

### 1. Install Python Dependencies

```bash
# Windows
py -m pip install -r requirements.txt

# Linux/macOS
pip install -r requirements.txt
```

### 2. Set Environment Variable

Set the path to your music collection:

**Windows (PowerShell):**
```powershell
$env:MUSIC_ROOT_PATH = "C:\Path\To\Your\Music\Collection"
```

**Windows (Command Prompt):**
```cmd
set MUSIC_ROOT_PATH=C:\Path\To\Your\Music\Collection
```

**macOS/Linux:**
```bash
export MUSIC_ROOT_PATH="/path/to/your/music/collection"
```

### 3. Run the Server

**Option 1: Using main.py (Recommended)**
```bash
# Windows
py main.py

# Linux/macOS  
python main.py
```

**Option 2: Direct execution**
```bash
# Windows PowerShell
cd src
py music_mcp_server.py

# Or as one line:
cd src; py music_mcp_server.py

# Linux/macOS
cd src && python music_mcp_server.py
```

### 4. Configure Claude Desktop

Add this configuration to your Claude Desktop config file:

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
      "args": ["/path/to/music-mcp-server/main.py"],
      "env": {
        "MUSIC_ROOT_PATH": "/path/to/your/music/collection"
      }
    }
  }
}
```

**Configuration Notes:**
- Use your actual path instead of `D:/Projects/music-mcp-server/main.py`
- Use your actual music collection path instead of `D:/Path/To/Your/Music/Collection`
- On Windows, use forward slashes `/` or escaped backslashes `\\\\` in paths
- The `args` field must be an array, not a string

### 5. Test the Connection

You can test the server works by running:

```bash
# Windows
py test_scan.py

# Linux/macOS
python test_scan.py
```

Run this command to test if the server starts correctly:

```bash
# Windows
py test_mcp_direct.py

# Linux/macOS
python test_mcp_direct.py
```

## Troubleshooting

### Common Issues

1. **Python not found**: Make sure Python is installed and in your PATH
2. **Import errors**: Ensure all dependencies are installed with `pip install -r requirements.txt`
3. **Permission errors**: Make sure Python has read access to your music collection
4. **Path issues**: Use absolute paths in the configuration

### Testing the Server

Run this command to test if the server starts correctly:

```bash
python test_mcp_direct.py
```

This will test the MCP communication directly without needing Claude Desktop.

## Performance Tips

- For large collections (1000+ albums), the initial scan may take several minutes
- Subsequent scans are much faster due to caching
- Consider using an SSD for better performance with large collections

## Next Steps

Once the server is running:

1. Use `scan_music_folders` tool to discover your music
2. Use `get_band_list` tool to browse your collection  
3. Use `fetch_band_info` prompt to gather band information
4. Use `save_band_metadata` tool to store band data
5. Use `analyze_band` prompt for reviews and ratings

## MCP Client Configuration

### For Claude Desktop

Add this to your Claude Desktop configuration file:

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

### For Cline (VS Code Extension)

Add this to your Cline MCP settings:

```json
{
  "mcpServers": {
    "music-collection": {
      "command": "python",
      "args": ["D:/Projects/music-catalog-mcp/main.py"],
      "env": {
        "MUSIC_ROOT_PATH": "D:/Path/To/Your/Music/Collection"
      }
    }
  }
}
```

## Testing the Setup

You can test the server using the included test client:

```bash
python test_mcp_client.py
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure all dependencies are installed with `pip install -r requirements.txt`

2. **Path Issues**: Ensure the `MUSIC_ROOT_PATH` environment variable points to a valid directory containing your music collection

3. **Windows Socket Issues**: If you encounter `[WinError 10106]` errors, try:
   - Restarting your command prompt/PowerShell as administrator
   - Checking Windows Firewall settings
   - Using Python 3.11 instead of 3.13 if the issue persists

4. **Permission Issues**: Ensure Python has read access to your music directory

### Music Collection Structure

Your music collection should be organized like this:

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

## Available Tools

Once connected, you'll have access to:

- **scan_music_folders** - Scan your music collection
- **get_band_list_tool** - List bands with filtering and pagination
- **save_band_metadata_tool** - Save band information
- **save_band_analyze_tool** - Save band analysis and ratings
- **save_collection_insight_tool** - Save collection insights
- **validate_band_metadata_tool** - Validate metadata before saving

## Resources

- **band://info/{band_name}** - Get detailed band information
- **collection://summary** - Get collection overview

## Prompts

- **fetch_band_info** - Template for fetching band information
- **analyze_band** - Template for band analysis
- **compare_bands** - Template for comparing bands
- **collection_insights** - Template for collection insights 