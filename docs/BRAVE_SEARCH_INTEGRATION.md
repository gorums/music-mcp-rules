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

#### Albums-Only Scope with Album Type Awareness
```
Search for complete discography of {band_name} with album type classification:
- Studio albums with release years
- Live albums and concert recordings
- Compilation albums and greatest hits
- EPs and extended plays
- Demo recordings and unreleased material
- Single releases and promotional items
- Instrumental versions and special editions
- Split releases and collaborations

For each album, include:
- Release year (YYYY format)
- Album type classification
- Edition information (Deluxe, Remastered, etc.)
- Track count and duration
- Notable information about recording/release

Focus on discography completeness and accurate type classification.
```

#### Enhanced Search with Structure Context
```
Search for {band_name} discography organized by album types:

STUDIO ALBUMS:
- Find all studio albums with release years
- Include information about deluxe/special editions

LIVE ALBUMS:
- Concert recordings and live albums
- Include venue information and recording dates

COMPILATIONS:
- Greatest hits collections
- Anthology and retrospective releases

EPs AND SINGLES:
- Extended plays and EPs
- Single releases and promotional items

RARE/SPECIAL RELEASES:
- Demo recordings and unreleased tracks
- Instrumental versions
- Split releases and collaborations

For optimal folder organization, prioritize albums that can be clearly classified by type.
```

## Integration Workflow with Album Type Classification

### Step 1: Enhanced Band Information Fetching

```json
{
  "method": "prompts/get",
  "params": {
    "name": "fetch_band_info",
    "arguments": {
      "band_name": "Pink Floyd",
      "information_scope": "full_with_types",
      "existing_albums": ["The Wall", "Animals"],
      "include_type_classification": true,
      "include_structure_recommendations": true
    }
  }
}
```

### Step 2: Type-Aware Search Execution

Execute the search with Brave Search, focusing on album type classification:

```
Search Results Analysis for Pink Floyd:

STUDIO ALBUMS:
- 1967 - The Piper at the Gates of Dawn (Album)
- 1968 - A Saucerful of Secrets (Album)
- 1969 - Ummagumma (Album)
- 1970 - Atom Heart Mother (Album)
- 1971 - Meddle (Album)
- 1973 - The Dark Side of the Moon (Album)
- 1975 - Wish You Were Here (Album)
- 1977 - Animals (Album)
- 1979 - The Wall (Album)
- 1983 - The Final Cut (Album)
- 1987 - A Momentary Lapse of Reason (Album)
- 1994 - The Division Bell (Album)

LIVE ALBUMS:
- 1969 - Ummagumma (Live) [Disc 2]
- 1988 - Delicate Sound of Thunder (Live)
- 1995 - Pulse (Live)

COMPILATION ALBUMS:
- 1971 - Relics (Compilation)
- 1981 - A Collection of Great Dance Songs (Compilation)
- 2001 - Echoes: The Best of Pink Floyd (Compilation)

SOUNDTRACKS/SPECIAL:
- 1972 - Obscured by Clouds (Soundtrack)
- 1972 - Live at Pompeii (Live Documentary)
```

### Step 3: Save Enhanced Metadata with Types

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
        "genres": ["Progressive Rock", "Psychedelic Rock", "Art Rock"],
        "origin": "London, England",
        "members": [
          "David Gilmour (guitar, vocals)",
          "Roger Waters (bass, vocals)", 
          "Nick Mason (drums)",
          "Richard Wright (keyboards)"
        ],
        "description": "English rock band formed in London in 1965. They achieved international acclaim with their progressive and psychedelic music.",
        "albums": [
          {
            "album_name": "The Dark Side of the Moon",
            "year": "1973",
            "type": "Album",
            "edition": "",
            "genres": ["Progressive Rock", "Art Rock"],
            "tracks_count": 10,
            "duration": "43min",
            "missing": false
          },
          {
            "album_name": "Live at Pompeii",
            "year": "1972",
            "type": "Live",
            "edition": "",
            "genres": ["Progressive Rock", "Live"],
            "tracks_count": 8,
            "duration": "65min",
            "missing": true
          },
          {
            "album_name": "Echoes: The Best of Pink Floyd",
            "year": "2001",
            "type": "Compilation",
            "edition": "",
            "genres": ["Progressive Rock"],
            "tracks_count": 26,
            "duration": "155min",
            "missing": true
          },
          {
            "album_name": "Early Singles",
            "year": "1967",
            "type": "Demo",
            "edition": "",
            "genres": ["Psychedelic Rock"],
            "tracks_count": 4,
            "duration": "18min",
            "missing": true
          }
        ]
      }
    }
  }
}
```

## Advanced Search Strategies with Album Types

### Type-Specific Search Queries

#### For Live Albums
```
Search for {band_name} live albums and concert recordings:
- Official live album releases
- Concert recordings with venue and date information
- Unplugged or acoustic sessions
- Festival performances and special concerts
- Bootleg information for reference (official releases only)

Include venue names, recording dates, and performance context.
```

#### For Compilation Albums
```
Search for {band_name} compilation albums and greatest hits:
- Official greatest hits collections
- Anthology and retrospective releases
- Record label compilations
- Career-spanning collections
- Rarities and B-sides collections

Include track selection criteria and coverage period.
```

#### For Demo and Rare Material
```
Search for {band_name} demo recordings and unreleased material:
- Official demo releases
- Early recordings and sessions
- Unreleased tracks and outtakes
- Promotional releases
- Special edition bonus material

Focus on officially released material, note historical significance.
```

### Structure-Aware Search Templates

#### Enhanced Structure Search
```
Search for {band_name} complete discography organized by type:

Request information structured as:
STUDIO ALBUMS (Album/):
- Year - Album Name (Edition if applicable)

LIVE RECORDINGS (Live/):
- Year - Live Album Name (Venue/Context)

COMPILATIONS (Compilation/):
- Year - Compilation Name (Scope/Period)

EPs AND SINGLES (EP/ or Single/):
- Year - Release Name (Format)

SPECIAL RELEASES (Demo/ or Split/):
- Year - Release Name (Context)

This structure supports enhanced folder organization.
```

#### Legacy Structure Search
```
Search for {band_name} discography with type indicators:

Format results as:
- Year - Album Name (Album Type in parentheses)
- Include edition information where applicable
- Note any special characteristics or contexts

Example format:
- 1973 - The Dark Side of the Moon
- 1988 - Delicate Sound of Thunder (Live)
- 2001 - Echoes (Compilation)
- 1967 - Early Singles (Demo)

This format supports legacy folder naming with type hints.
```

## Error Handling and Data Validation

### Type Classification Validation

When processing search results, validate album types:

```python
def validate_album_type_from_search(album_data: Dict[str, Any]) -> AlbumType:
    """
    Validate and determine album type from search results.
    
    Args:
        album_data: Album information from search results
        
    Returns:
        Validated AlbumType enum value
    """
    album_name = album_data.get('name', '').lower()
    description = album_data.get('description', '').lower()
    
    # Check for explicit type indicators
    type_indicators = {
        AlbumType.LIVE: ['live', 'concert', 'unplugged', 'acoustic'],
        AlbumType.COMPILATION: ['greatest hits', 'best of', 'collection', 'anthology'],
        AlbumType.EP: ['ep', 'extended play'],
        AlbumType.DEMO: ['demo', 'demos', 'unreleased', 'early recordings'],
        AlbumType.SINGLE: ['single'],
        AlbumType.INSTRUMENTAL: ['instrumental'],
        AlbumType.SPLIT: ['split', 'vs.', 'versus']
    }
    
    for album_type, keywords in type_indicators.items():
        if any(keyword in album_name or keyword in description for keyword in keywords):
            return album_type
    
    return AlbumType.ALBUM  # Default to Album type
```

### Search Result Processing with Types

```python
def process_search_results_with_types(search_results: List[Dict]) -> List[Album]:
    """
    Process Brave Search results and extract album information with type classification.
    
    Args:
        search_results: Raw search results from Brave Search
        
    Returns:
        List of Album objects with type classification
    """
    albums = []
    
    for result in search_results:
        try:
            # Extract album information
            album_info = extract_album_info(result)
            
            # Classify album type
            album_type = validate_album_type_from_search(album_info)
            
            # Create Album object
            album = Album(
                album_name=album_info['name'],
                year=album_info.get('year'),
                type=album_type,
                edition=album_info.get('edition', ''),
                genres=album_info.get('genres', []),
                tracks_count=album_info.get('tracks_count'),
                duration=album_info.get('duration'),
                missing=True  # From search, not in local collection
            )
            
            albums.append(album)
            
        except Exception as e:
            logger.warning(f"Error processing search result: {e}")
            continue
    
    return albums
```

## Integration Best Practices with Album Types

### Search Query Optimization

1. **Type-Specific Keywords**: Include album type keywords in search queries
2. **Year Range Filtering**: Search by decades for better organization
3. **Format Specification**: Distinguish between different release formats
4. **Edition Awareness**: Include information about special editions

### Data Quality Assurance

1. **Type Validation**: Verify album types against known patterns
2. **Duplicate Detection**: Identify and merge duplicate albums across types
3. **Edition Handling**: Properly classify different editions of same album
4. **Missing Album Identification**: Compare search results with local collection

### Collection Organization Integration

1. **Structure Recommendations**: Suggest folder organization based on retrieved types
2. **Migration Planning**: Help users upgrade to enhanced structures
3. **Compliance Assessment**: Evaluate how search results align with current structure
4. **Type Distribution Analysis**: Provide insights on collection balance

## Automated Collection Enhancement

### Smart Collection Building

```python
def enhance_collection_with_brave_search(band_name: str) -> Dict[str, Any]:
    """
    Automatically enhance collection using Brave Search with type awareness.
    
    Args:
        band_name: Name of band to enhance
        
    Returns:
        Enhancement results with type statistics and recommendations
    """
    # Get current collection state
    current_metadata = load_band_metadata(band_name)
    current_albums = current_metadata.albums if current_metadata else []
    
    # Search for complete discography
    search_results = brave_search_band_discography(band_name)
    discovered_albums = process_search_results_with_types(search_results)
    
    # Identify missing albums by type
    missing_by_type = identify_missing_albums_by_type(current_albums, discovered_albums)
    
    # Generate type-aware recommendations
    recommendations = generate_type_recommendations(missing_by_type)
    
    # Suggest structure improvements
    structure_suggestions = analyze_structure_for_types(current_albums, discovered_albums)
    
    return {
        "band_name": band_name,
        "discovered_albums": len(discovered_albums),
        "missing_by_type": missing_by_type,
        "recommendations": recommendations,
        "structure_suggestions": structure_suggestions,
        "type_distribution": calculate_type_distribution(discovered_albums)
    }
```

### Collection Gap Analysis

```python
def analyze_collection_gaps_with_types(collection_data: Dict) -> Dict[str, Any]:
    """
    Analyze collection gaps using album type classification.
    
    Identifies missing album types and suggests acquisition priorities.
    """
    gap_analysis = {
        "missing_types_by_band": {},
        "priority_acquisitions": [],
        "structure_improvements": [],
        "type_balance_assessment": {}
    }
    
    for band_name, band_data in collection_data.items():
        current_types = set(album.type for album in band_data.albums)
        all_types = set(AlbumType)
        missing_types = all_types - current_types
        
        if missing_types:
            gap_analysis["missing_types_by_band"][band_name] = list(missing_types)
            
            # Prioritize based on band importance and type significance
            priority_score = calculate_acquisition_priority(band_data, missing_types)
            if priority_score > 0.7:
                gap_analysis["priority_acquisitions"].append({
                    "band_name": band_name,
                    "missing_types": list(missing_types),
                    "priority_score": priority_score
                })
    
    return gap_analysis
```

This enhanced Brave Search integration provides comprehensive support for album type classification and intelligent collection organization, enabling users to build well-structured, complete music collections with proper type classification and folder organization.

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