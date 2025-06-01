# Music Collection MCP Server - Frequently Asked Questions (FAQ)

## General Questions

### Q: What is the Music Collection MCP Server?

**A:** The Music Collection MCP Server is a Model Context Protocol (MCP) server that provides intelligent access to your local music collection. It scans your music folders, manages metadata, and offers tools, resources, and prompts to analyze and explore your music library through MCP-compatible clients like Claude Desktop.

### Q: What MCP clients are supported?

**A:** The server supports any MCP-compatible client, including:
- **Claude Desktop** (recommended)
- **Cline** (VS Code extension)
- Any client supporting MCP stdio transport
- Custom MCP client implementations

### Q: Do I need an internet connection?

**A:** The core functionality works offline, but internet access enhances the experience:
- **Required for**: Fetching band information via Brave Search integration
- **Not required for**: Local scanning, metadata storage, resource access, collection analysis

## Installation and Setup

### Q: Should I use Docker or local Python installation?

**A:** **Docker is recommended** for most users because:
- ✅ Consistent environment across platforms
- ✅ No Python environment conflicts
- ✅ Easy updates and deployment
- ✅ Isolation from system Python

Use local Python only for development or when Docker isn't available.

### Q: What folder structure do I need for my music collection?

**A:** The server expects this hierarchy:
```
Music Root/
├── Band Name/              # Top level: band folders
│   ├── Album 1/           # Second level: album folders  
│   │   ├── track1.mp3     # Third level: music files
│   │   └── track2.mp3
│   └── Album 2/
│       └── *.mp3
└── Another Band/
    └── Album/
        └── *.mp3
```

**Supported**: Most common folder organizations
**Not supported**: Loose music files, compilation albums at root level

### Q: Which music file formats are supported?

**A:** The scanner detects these formats:
- **Common**: `.mp3`, `.flac`, `.wav`, `.aac`, `.m4a`
- **Additional**: `.ogg`, `.wma`, `.mp4`, `.m4p`

Files without these extensions are ignored during scanning.

### Q: Can I have multiple music collections?

**A:** Yes! Configure multiple MCP server instances:
```json
{
  "mcpServers": {
    "music-rock": {
      "command": "docker",
      "args": ["-v", "/music/rock:/music", "-e", "MUSIC_ROOT_PATH=/music", "music-mcp-server"]
    },
    "music-classical": {
      "command": "docker", 
      "args": ["-v", "/music/classical:/music", "-e", "MUSIC_ROOT_PATH=/music", "music-mcp-server"]
    }
  }
}
```

## Usage Questions

### Q: How do I start using the server after installation?

**A:** Follow this workflow:
1. **Scan your collection**: Use `scan_music_folders` tool
2. **View discovered bands**: Use `get_band_list` tool or `collection://summary` resource
3. **Add band information**: Use `fetch_band_info` prompt + `save_band_metadata` tool
4. **Analyze bands**: Use `analyze_band` prompt + `save_band_analyze` tool

### Q: What's the difference between missing and physical albums?

**A:** 
- **Physical albums**: Actually exist as folders in your music directory
- **Missing albums**: Listed in band metadata but not present as physical folders
- **Purpose**: Track your collection completeness and wishlist items

Example:
```json
{
  "band_name": "Pink Floyd",
  "albums": [
    {"album_name": "The Wall", "missing": false},      // You have this
    {"album_name": "Dark Side of the Moon", "missing": true}  // You want this
  ]
}
```

### Q: How does the rating system work?

**A:** The server uses a 1-10 scale for ratings:
- **1-3**: Poor/Dislike
- **4-6**: Average/Okay  
- **7-8**: Good/Like
- **9-10**: Excellent/Love

Ratings can be applied to:
- Individual bands
- Individual albums
- Both band-level and album-level reviews

### Q: What are "similar bands" and how are they used?

**A:** Similar bands help with music discovery:
- **Stored in**: Band analysis data
- **Used for**: Collection insights, recommendations, discovery
- **Format**: Simple list of band names
- **Example**: Pink Floyd → ["King Crimson", "Genesis", "Yes"]

## Data and Storage

### Q: Where is my data stored?

**A:** All data is stored locally in JSON files:
- **Band metadata**: `{band_folder}/.band_metadata.json`
- **Collection index**: `{music_root}/.collection_index.json`
- **Backups**: Automatic timestamped backups of all files

**No external databases or cloud storage** - your data stays private.

### Q: Is my data backed up automatically?

**A:** Yes! The server creates automatic backups:
- **When**: Before any metadata updates
- **Format**: `.band_metadata.json.backup.YYYYMMDD-HHMMSS`
- **Retention**: Multiple backup versions kept
- **Manual restoration**: Copy backup file to replace current metadata

### Q: Can I edit metadata files manually?

**A:** Yes, but use caution:
- **Format**: Standard JSON with proper syntax
- **Validation**: Server validates on load and will reject invalid files
- **Recommendation**: Use MCP tools when possible for safety
- **Backup**: Manual edits don't create automatic backups

### Q: What happens if metadata files get corrupted?

**A:** The server handles corruption gracefully:
1. **Automatic backup restoration** if recent backup exists
2. **Error reporting** with specific validation issues
3. **Regeneration** - delete corrupted file and rescan
4. **Recovery tools** in troubleshooting guide

## Performance and Limitations

### Q: How large collections can the server handle?

**A:** Tested performance limits:
- **Small**: 1-100 bands - Instant response
- **Medium**: 100-1,000 bands - 1-5 seconds
- **Large**: 1,000-10,000 bands - 10-60 seconds  
- **Very Large**: 10,000+ bands - May need resource optimization

For very large collections, use pagination and filtering.

### Q: Why is scanning taking a long time?

**A:** Common causes and solutions:
- **Large collection**: Normal for 1000+ bands
- **Slow storage**: Use SSD for better performance
- **Limited memory**: Increase Docker memory limit
- **Network storage**: NAS/cloud mounts are slower than local storage

Optimization tips:
```bash
# Increase Docker resources
docker run --memory=4g --cpus=2 music-mcp-server

# Use incremental scanning
{"force_rescan": false}  # Only scan changed folders
```

### Q: How much disk space does the server use?

**A:** Storage requirements are minimal:
- **Metadata files**: ~1-10KB per band
- **Collection index**: ~1-100KB total
- **Backups**: 3-5x metadata size
- **Example**: 1000 bands ≈ 5-50MB total

## Advanced Features

### Q: How do I integrate with Brave Search for band information?

**A:** Brave Search integration works through MCP client configuration:
1. **Use fetch_band_info prompt** to generate search queries
2. **MCP client handles** the actual Brave Search API calls  
3. **Server provides** structured prompts for optimal results
4. **Save results** using save_band_metadata tool

The server doesn't directly call APIs - it provides intelligent prompts.

### Q: Can I export my collection data?

**A:** Yes, several export options:
1. **JSON files**: Already in standard JSON format
2. **Collection summary**: Use `collection://summary` resource for markdown export
3. **Band information**: Use `band://info/{band_name}` resource for individual bands
4. **Custom scripts**: Direct access to `.band_metadata.json` files

### Q: How do I update the server to a new version?

**A:** For Docker deployment:
```bash
# Pull latest image
docker pull music-mcp-server:latest

# Stop current container
docker stop music-mcp-container

# Start new container (data persists in volumes)
docker run -d --name music-mcp-container-new [same volume mounts] music-mcp-server:latest
```

Data persists because it's stored in mounted volumes.

## Troubleshooting

### Q: The server shows tools as errors in Claude Desktop but they work fine. Why?

**A:** This is a known FastMCP display issue:
- **Cause**: INFO-level log messages appear as errors in client UI
- **Reality**: Tools function correctly despite error appearance
- **Solution**: Set `LOG_LEVEL=ERROR` to suppress INFO messages
- **Status**: Cosmetic issue only - functionality unaffected

### Q: Resources like `band://info/Pink Floyd` return "Resource not found"

**A:** Check these common issues:
1. **URI format**: Use `band://info/Pink Floyd` not `band/Pink Floyd`
2. **Band exists**: Verify with `get_band_list` tool
3. **Special characters**: URL-encode characters like `AC%2FDC` for "AC/DC"
4. **Metadata exists**: Band must have `.band_metadata.json` file

### Q: Why aren't my albums being detected during scanning?

**A:** Common causes:
1. **Wrong structure**: Music files must be in album folders, not loose in band folders
2. **File extensions**: Only supported formats are detected
3. **Empty folders**: Folders with no music files are ignored
4. **Hidden files**: Files starting with `.` are ignored
5. **Permissions**: Ensure read access to all folders

### Q: My collection stats don't match what I see in folders

**A:** This usually indicates:
1. **Stale cache**: Use `force_rescan=true` to refresh
2. **Missing albums**: Metadata includes albums not physically present
3. **Filtering**: Scanner ignores hidden/system folders
4. **Index not updated**: Run `scan_music_folders` to refresh collection index

## Data Privacy and Security

### Q: Is my music collection data sent anywhere?

**A:** No external data transmission:
- **Local only**: All metadata stored in your file system
- **No uploads**: Server doesn't send data to external services
- **Privacy**: Your music collection information stays private
- **Network**: Only outbound requests are from MCP client (like Brave Search)

### Q: Can other people access my MCP server?

**A:** No, by design:
- **stdio transport**: No network ports opened
- **Process isolation**: Runs as subprocess of MCP client
- **File access**: Limited to configured music directory only
- **Docker isolation**: Additional container-level security

### Q: What permissions does the server need?

**A:** Minimal required permissions:
- **Read access**: To music directory and subdirectories
- **Write access**: Only for `.band_metadata.json` and `.collection_index.json` files
- **No system access**: Doesn't access files outside music directory

## Integration and Development

### Q: Can I use this server with custom MCP clients?

**A:** Yes! The server follows standard MCP protocol:
- **Transport**: stdio (JSON-RPC)
- **Schema**: Standard MCP tool/resource/prompt definitions  
- **Documentation**: Full API documentation available
- **Testing**: Use provided test scripts to verify integration

### Q: How do I contribute to the project?

**A:** Contribution options:
1. **Bug reports**: Submit GitHub issues with detailed logs
2. **Feature requests**: Propose new functionality
3. **Code contributions**: Follow development guidelines in project docs
4. **Documentation**: Help improve guides and examples
5. **Testing**: Test with different music collections and report results

### Q: Are there API documentation and code examples?

**A:** Yes, comprehensive documentation available:
- **Installation Guide**: [INSTALLATION.md](INSTALLATION.md)
- **Configuration Guide**: [CONFIGURATION.md](CONFIGURATION.md)
- **Usage Examples**: [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md)
- **API Documentation**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **Architecture Guide**: [PLANNING.md](PLANNING.md)

## Getting More Help

### Q: Where can I get additional support?

**A:** Support resources:
1. **Documentation**: Check all guides in `docs/` directory
2. **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
3. **GitHub Issues**: Report bugs or ask questions
4. **Test Suite**: Run tests to verify your installation
5. **Log Analysis**: Enable DEBUG logging for detailed diagnostics

### Q: How do I report bugs effectively?

**A:** Include this information:
1. **System info**: OS, Docker version, Python version
2. **Configuration**: Environment variables and MCP client config
3. **Steps to reproduce**: Exact commands or actions taken
4. **Error messages**: Full error logs and stack traces
5. **Collection info**: Size and structure of music collection (without sensitive paths)

### Q: What's the best way to learn the server capabilities?

**A:** Recommended learning path:
1. **Start simple**: Install and run basic `scan_music_folders`
2. **Explore resources**: View `collection://summary` and `band://info/` 
3. **Try tools**: Use each tool with small test data
4. **Read examples**: Work through [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md)
5. **Experiment**: Try advanced features like analysis and insights

---

**Still have questions?** Check the other documentation files or submit a GitHub issue with your specific question. 