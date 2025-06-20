# Quick Start Guide

Get your Music Collection MCP Server up and running in just a few minutes!

## 🚀 Prerequisites

- Python 3.8+ with pip, OR Docker
- Music collection organized in folders (Band/Album structure)

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

## 🔄 Option 1: Automated Setup (Recommended)

### 1. Run the Setup Script
```bash
python scripts/setup.py
```

The interactive setup will:
- ✅ Check system requirements
- ✅ Guide you through installation options
- ✅ Configure your music collection path
- ✅ Generate Claude Desktop configuration
- ✅ Validate your setup

### 2. Choose Your Installation Method
The script offers several options:
1. **Local Python** - Install and run with Python
2. **Docker Container** - Containerized deployment
3. **Development** - Full development environment
4. **Configuration Only** - Just generate configs

### 3. Follow the Prompts
The setup will automatically:
- Install dependencies
- Configure environment variables
- Generate Claude Desktop config
- Test the installation

## 🐳 Option 2: Docker Quick Start

### Using the Docker Script
```bash
# Make executable (Linux/macOS)
chmod +x scripts/start-docker.sh

# Start with your music collection
./scripts/start-docker.sh -m /path/to/your/music
```

### Manual Docker
```bash
# Build the container
docker build -t music-mcp .

# Run with your music collection
docker run -d --name music-mcp \
  -v "/path/to/your/music:/music" \
  -e "MUSIC_ROOT_PATH=/music" \
  music-mcp
```

## 🐍 Option 3: Manual Python Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables
```bash
# Windows (PowerShell)
$env:MUSIC_ROOT_PATH = "C:\path\to\your\music"

# macOS/Linux
export MUSIC_ROOT_PATH="/path/to/your/music"
```

### 3. Run the Server
```bash
python main.py
```

## 🤖 Configure Claude Desktop

### Automated Configuration
If you used the setup script, it generated a configuration file. Simply:

1. Copy the contents to your Claude Desktop config file
2. Restart Claude Desktop
3. Start using the server!

### Configuration File Locations
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### Example Configuration (Python)
```json
{
  "mcpServers": {
    "music-collection": {
      "command": "python",
      "args": ["/path/to/music-mcp-server/main.py"],
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

### Analyze Your Collection
```
Analyze my collection and give me insights about its organization and completeness
```

### Find Missing Albums
```
Which bands in my collection are missing albums?
```

### Get Band Information
```
Tell me about Pink Floyd and their albums in my collection
```

## 🔧 Advanced Features

### Album Type Classification
The server automatically detects 8 album types:
- **Album** (studio albums)
- **Live** (live recordings)
- **Compilation** (greatest hits, collections)
- **EP** (extended plays)
- **Demo** (demo recordings)
- **Single** (single releases)
- **Instrumental** (instrumental versions)
- **Split** (split releases)

### Collection Analytics
Get detailed insights about your collection:
- Collection maturity assessment
- Health scoring and recommendations
- Type distribution analysis
- Missing album detection
- Organization compliance scoring

### Advanced Search
Use powerful filtering:
```
Find all live albums from the 1980s with ratings above 7
```

```
Show me all compilations and EPs in my collection
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
- Use the health check: `python scripts/health-check.py /path/to/music`
- Consider organizing music in type-based folders for better performance

### Need More Help?
- Run structure validation: `python scripts/validate-music-structure.py /path/to/music`
- Check the [FAQ](FAQ.md) for common questions
- Review the [Troubleshooting Guide](TROUBLESHOOTING.md)

## 📚 Next Steps

- Read the [Usage Examples](USAGE_EXAMPLES.md) for more advanced use cases
- Learn about [Collection Organization](COLLECTION_ORGANIZATION.md) best practices
- Explore [Album Handling](ALBUM_HANDLING.md) for understanding album types
- Check out the maintenance scripts in the `scripts/` directory

---

*Ready to explore your music collection with AI? Start chatting with Claude!* 🎶 