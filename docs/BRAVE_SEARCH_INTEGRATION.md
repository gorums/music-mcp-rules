# Brave Search MCP Integration Guide

## Overview

The Music Collection MCP Server integrates with Brave Search through MCP client configuration to fetch comprehensive band information. This guide explains how to set up and use Brave Search integration for enriching your music collection metadata.

## How Integration Works

### Architecture
```
MCP Client (Claude Desktop) 
    ↓
Brave Search MCP Server ← fetch_band_info prompt → Music Collection MCP Server
    ↓                                                       ↓
Brave Search API                                    save_band_metadata tool
```

### Workflow
1. **Music server provides prompts** with structured search queries
2. **MCP client connects** to both servers simultaneously  
3. **Brave Search server** executes web searches using provided prompts
4. **Music server receives** and processes search results
5. **Metadata is saved** locally using music server tools

## Setup Requirements

### Prerequisites
- **Brave Search API Key** (required for Brave Search MCP server)
- **MCP Client** supporting multiple server connections (Claude Desktop recommended)
- **Music Collection MCP Server** already configured and running

### Brave Search MCP Server Setup

#### 1. Install Brave Search MCP Server
```bash
# Install the official Brave Search MCP server
npm install -g @brave/mcp-server-search
```

#### 2. Get Brave Search API Key
1. Visit [Brave Search API](https://api.search.brave.com/)
2. Sign up for API access
3. Generate API key
4. Note usage limits and pricing

#### 3. Configure Environment
```bash
# Set API key environment variable
export BRAVE_SEARCH_API_KEY="your_api_key_here"
```

## MCP Client Configuration

### Claude Desktop Configuration

Configure both servers in your Claude Desktop config:

```json
{
  "mcpServers": {
    "brave-search": {
      "command": "npx",
      "args": ["@brave/mcp-server-search"],
      "env": {
        "BRAVE_SEARCH_API_KEY": "your_api_key_here"
      }
    },
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

### Alternative: Local Brave Search Server
```json
{
  "mcpServers": {
    "brave-search": {
      "command": "python",
      "args": ["/path/to/brave-search-mcp/main.py"],
      "env": {
        "BRAVE_SEARCH_API_KEY": "your_api_key_here"
      }
    },
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

## Usage Workflow

### Step 1: Generate Search Prompt

Use the music server's `fetch_band_info` prompt to create optimized search queries:

```json
{
  "method": "prompts/get",
  "params": {
    "name": "fetch_band_info",
    "arguments": {
      "band_name": "Pink Floyd",
      "information_scope": "full",
      "existing_albums": ["The Wall", "Animals"]
    }
  }
}
```

### Step 2: Execute Search with Brave Search

The prompt output provides structured guidance for the Brave Search server:

```
Search for comprehensive information about Pink Floyd including:
- Formation year and origin
- Band members and their roles  
- Musical genres and style
- Complete discography
- Missing albums: Dark Side of the Moon, Wish You Were Here, Meddle...

Use reliable sources like Wikipedia, AllMusic, official band websites.
```

### Step 3: Save Retrieved Information

Use the music server's `save_band_metadata` tool to store the fetched data:

```json
{
  "method": "tools/call",
  "params": {
    "name": "save_band_metadata",
    "arguments": {
      "band_name": "Pink Floyd",
      "metadata": {
        "band_name": "Pink Floyd",
        "formed": "1965",
        "genres": ["Progressive Rock", "Psychedelic Rock"],
        "origin": "London, England",
        "members": ["David Gilmour", "Nick Mason", "Roger Waters", "Richard Wright"],
        "description": "English rock band formed in London...",
        "albums": [
          {
            "album_name": "Dark Side of the Moon",
            "missing": true,
            "year": "1973",
            "genres": ["Progressive Rock"]
          }
        ]
      }
    }
  }
}
```

## Prompt Templates and Search Strategies

### Information Scopes

#### Basic Information Scope
```
Search for basic information about {band_name}:
- Formation year (YYYY format)
- Origin city/country  
- Primary genres (2-3 main genres)
- Current/former members

Focus on verified, factual information from reliable sources.
```

#### Full Information Scope  
```
Search for comprehensive information about {band_name}:
- Formation year and origin
- Complete member history with roles
- Musical genres and evolution
- Complete discography with years
- Band history and notable achievements
- Influence and legacy

Prioritize official sources, Wikipedia, AllMusic, and music databases.
```

#### Albums-Only Scope
```
Search specifically for {band_name} discography:
- Studio albums with release years
- Album genres and styles
- Missing albums from existing collection: {existing_albums}
- Album reception and significance

Focus on reliable music databases and official discographies.
```

### Search Quality Guidelines

#### Recommended Sources
1. **Primary**: Wikipedia, AllMusic, official band websites
2. **Secondary**: Rolling Stone, Pitchfork, music databases
3. **Avoid**: User-generated content, unreliable blogs, speculation

#### Data Validation Rules
- **Years**: Must be in YYYY format (e.g., "1973" not "early 70s")
- **Genres**: Use standard genre names (e.g., "Progressive Rock" not "prog")
- **Members**: Include roles (e.g., "David Gilmour (guitar, vocals)")
- **Origins**: City, Country format (e.g., "London, England")

## Advanced Integration Patterns

### Batch Band Processing

Process multiple bands efficiently:

```python
# Pseudo-workflow for multiple bands
bands_to_process = ["Pink Floyd", "Led Zeppelin", "The Beatles"]

for band in bands_to_process:
    # 1. Generate prompt
    prompt = get_fetch_band_info_prompt(band_name=band, scope="full")
    
    # 2. Use Brave Search (via MCP client)
    search_results = brave_search(prompt)
    
    # 3. Parse and save results
    metadata = parse_search_results(search_results)
    save_band_metadata(band, metadata)
```

### Missing Album Detection

Enhance searches with existing collection data:

```json
{
  "method": "prompts/get",
  "params": {
    "name": "fetch_band_info",
    "arguments": {
      "band_name": "Pink Floyd",
      "information_scope": "albums_only",
      "existing_albums": ["The Wall", "Animals", "Meddle"]
    }
  }
}
```

This generates targeted searches for missing albums:
```
Search for Pink Floyd albums NOT in this list: The Wall, Animals, Meddle
Focus on finding: Dark Side of the Moon, Wish You Were Here, Saucerful of Secrets...
```

### Collection Analysis Integration

Combine with collection insights:

```json
{
  "method": "prompts/get",
  "params": {
    "name": "collection_insights",
    "arguments": {
      "insights_scope": "comprehensive",
      "focus_areas": ["recommendations"]
    }
  }
}
```

Use insights to guide band research:
```
Based on your collection preferences for Progressive Rock,
search for information about recommended bands: King Crimson, Genesis, Yes
```

## Error Handling and Troubleshooting

### Common Issues

#### 1. API Rate Limits
```
Error: Brave Search API rate limit exceeded
```

**Solutions:**
- Implement delays between searches
- Use batch processing during off-peak hours
- Upgrade to higher API tier if needed

#### 2. Invalid API Key
```
Error: Authentication failed - invalid API key
```

**Solutions:**
- Verify API key in environment variables
- Check key expiration date
- Regenerate key if necessary

#### 3. Network Connectivity
```
Error: Failed to connect to Brave Search API
```

**Solutions:**
- Check internet connectivity
- Verify API endpoint accessibility
- Test with simple search first

### Search Quality Issues

#### 1. Inconsistent Data Format
**Problem**: Search results in non-standard format
**Solution**: Use more specific prompts with format examples

#### 2. Incomplete Information
**Problem**: Missing key metadata fields
**Solution**: Use "full" scope prompts with comprehensive requirements

#### 3. Inaccurate Information
**Problem**: Conflicting or wrong data
**Solution**: Emphasize reliable sources in prompts, manual verification

## Best Practices

### Efficient Search Strategies

1. **Start with basic scope** for quick information gathering
2. **Use full scope** for comprehensive band research
3. **Focus on missing albums** when expanding collection
4. **Batch similar searches** to optimize API usage

### Data Quality Assurance

1. **Validate formats** before saving (years, genres, etc.)
2. **Cross-reference** information from multiple sources
3. **Manual review** for important or questionable data
4. **Use structured prompts** for consistent results

### API Usage Optimization

1. **Cache results locally** using music server storage
2. **Avoid duplicate searches** for same band/album
3. **Respect rate limits** with appropriate delays
4. **Monitor API usage** and costs

## Security Considerations

### API Key Protection

1. **Environment variables**: Never commit API keys to code
2. **Access control**: Limit key permissions to search only
3. **Rotation**: Regularly rotate API keys
4. **Monitoring**: Watch for unusual API usage

### Data Privacy

1. **Local storage**: All metadata stays on your system
2. **Search queries**: Only band names sent to API
3. **No personal data**: Music file paths not transmitted
4. **Audit logs**: Monitor search activity if needed

## Testing and Validation

### Test Search Integration

```bash
# Test Brave Search server connectivity
curl -H "X-Api-Key: your_key" "https://api.search.brave.com/res/v1/web/search?q=Pink+Floyd"

# Test MCP client with both servers
echo '{"method": "prompts/list"}' | claude-desktop
```

### Validate Search Results

```json
{
  "method": "tools/call",
  "params": {
    "name": "get_band_list",
    "arguments": {
      "search": "Pink Floyd",
      "filter_has_metadata": true
    }
  }
}
```

## Example Complete Workflow

### Real-World Band Research Example

1. **Discover missing band information**:
```json
{"method": "tools/call", "params": {"name": "get_band_list", "arguments": {"filter_has_metadata": false}}}
```

2. **Generate targeted search prompt**:
```json
{"method": "prompts/get", "params": {"name": "fetch_band_info", "arguments": {"band_name": "King Crimson", "information_scope": "full"}}}
```

3. **Execute search using Brave Search MCP** (via MCP client)

4. **Save comprehensive metadata**:
```json
{"method": "tools/call", "params": {"name": "save_band_metadata", "arguments": {"band_name": "King Crimson", "metadata": {...}}}}
```

5. **Verify results**:
```
Resource: band://info/King Crimson
```

## Support and Resources

### Documentation References
- [Brave Search API Documentation](https://api.search.brave.com/app/documentation)
- [MCP Protocol Specification](https://github.com/modelcontextprotocol/mcp)
- [Usage Examples](USAGE_EXAMPLES.md)
- [Configuration Guide](CONFIGURATION.md)

### Troubleshooting
- [Troubleshooting Guide](TROUBLESHOOTING.md) for integration issues
- [FAQ](FAQ.md) for common questions about Brave Search integration

For additional help with Brave Search integration, check the troubleshooting guide or submit a GitHub issue with integration-specific details. 