# Quick Start Guide

Get your Music Collection MCP Server up and running in just a few minutes!

## 🚀 Prerequisites

- Docker installed on your system, OR
- Python 3.8+ with pip

## 📁 Prepare Your Music Collection

Organize your music in a folder structure like this:

```
/path/to/your/music/
├── Pink Floyd/
│   ├── 1973 - The Dark Side of the Moon/
│   │   ├── 01 - Speak to Me.mp3
│   │   └── 02 - Breathe.mp3
│   └── 1979 - The Wall/
│       └── music files...
├── The Beatles/
│   ├── 1967 - Sgt. Pepper's Lonely Hearts Club Band/
│   └── 1969 - Abbey Road/
└── Led Zeppelin/
    └── 1971 - Led Zeppelin IV/
```

## 🐳 Option 1: Docker (Recommended)

### 1. Build the Container
```bash
docker build -t music-mcp-server .
```

### 2. Run the Server
```bash
docker run -d --name music-mcp \
  -v "/path/to/your/music:/music" \
  -e "MUSIC_ROOT_PATH=/music" \
  music-mcp-server
```

### 3. Configure Claude Desktop

Add this to your Claude Desktop configuration file:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Linux**: `~/.config/claude/claude_desktop_config.json`

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

## 🐍 Option 2: Python

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables
```bash
# Windows
set MUSIC_ROOT_PATH=C:\path\to\your\music

# macOS/Linux
export MUSIC_ROOT_PATH="/path/to/your/music"
```

### 3. Run the Server
```bash
python main.py
```

### 4. Configure Claude Desktop
```json
{
  "mcpServers": {
    "music-collection": {
      "command": "python",
      "args": ["/path/to/music-catalog-mcp/main.py"],
      "env": {
        "MUSIC_ROOT_PATH": "/path/to/your/music"
      }
    }
  }
}
```

## ✅ Test Your Setup

1. **Restart Claude Desktop** after updating the configuration
2. **Start a new conversation** in Claude
3. **Try these commands**:

```
Can you scan my music collection?
```

```
Show me a summary of my music collection
```

```
What bands do I have in my collection?
```

## 🎵 First Steps

Once connected, try these common tasks:

### Scan Your Collection
```
Please scan my music collection and show me what you found
```

### Get Collection Overview
```
Give me an overview of my music collection with statistics
```

### Find Missing Albums
```
Which bands in my collection are missing albums?
```

### Get Band Information
```
Tell me about Pink Floyd and their albums in my collection
```

## 🔧 Troubleshooting

### Server Not Connecting
- Check that the music path exists and is accessible
- Verify the Docker container is running: `docker ps`
- Check Claude Desktop logs for error messages

### No Music Found
- Ensure your music is organized in `Band Name/Album Name/` structure
- Check that the `MUSIC_ROOT_PATH` points to the correct directory
- Verify file permissions allow reading the music directory

### Performance Issues
- For large collections (>1000 albums), initial scanning may take time
- Use incremental scanning for subsequent updates
- Consider organizing music in type-based folders for better performance

## 📚 Next Steps

- Read the [Usage Examples](USAGE_EXAMPLES.md) for more advanced use cases
- Learn about [Collection Organization](COLLECTION_ORGANIZATION.md) best practices
- Check the [FAQ](FAQ.md) for common questions

## 🆘 Need Help?

- Check the [Troubleshooting Guide](TROUBLESHOOTING.md)
- Review the [FAQ](FAQ.md)
- Look at [Usage Examples](USAGE_EXAMPLES.md) for inspiration

---

*Ready to explore your music collection with AI? Start chatting with Claude!* 🎶 