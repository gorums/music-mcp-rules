# Music Collection MCP Server - Installation Guide with Album Type Classification

## Prerequisites

### System Requirements
- **Python 3.8+** (for local installation)
- **Docker** (recommended for deployment)
- **MCP Client** (Claude Desktop, Cline, or other MCP-compatible client)

### Environment Preparation
- Music collection organized in folders (band/album structure)
- Minimum 1GB free disk space for metadata storage
- Network access for external band information fetching
- Understanding of supported folder organization patterns

## Installation Methods

### Method 1: Docker Deployment (Recommended)

Docker provides the most reliable and consistent environment for running the MCP server with album type classification features.

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

The server supports multiple folder organization patterns with intelligent type detection:

#### Enhanced Structure (Recommended)
```
/path/to/your/music/
├── Pink Floyd/
│   ├── Album/
│   │   ├── 1973 - The Dark Side of the Moon/
│   │   │   ├── 01 - Speak to Me.mp3
│   │   │   └── 02 - Breathe.mp3
│   │   └── 1979 - The Wall (Deluxe Edition)/
│   ├── Live/
│   │   └── 1988 - Delicate Sound of Thunder/
│   ├── Compilation/
│   │   └── 2001 - Echoes - The Best of Pink Floyd/
│   └── .band_metadata.json (created automatically)
├── The Beatles/
│   ├── Album/
│   │   ├── 1967 - Sgt. Pepper's Lonely Hearts Club Band/
│   │   └── 1969 - Abbey Road/
│   ├── Compilation/
│   │   └── 1996 - Anthology/
│   └── .band_metadata.json (created automatically)
└── .collection_index.json (created automatically)
```

#### Default Structure (Also Supported)
```
/path/to/your/music/
├── Pink Floyd/
│   ├── 1973 - The Dark Side of the Moon/
│   ├── 1979 - The Wall (Deluxe Edition)/
│   ├── 1988 - Delicate Sound of Thunder (Live)/
│   ├── 2001 - Echoes - The Best of Pink Floyd (Compilation)/
│   └── .band_metadata.json (created automatically)
├── The Beatles/
│   ├── 1967 - Sgt. Pepper's Lonely Hearts Club Band/
│   ├── 1969 - Abbey Road/
│   └── .band_metadata.json (created automatically)
└── .collection_index.json (created automatically)
```

#### Legacy Structure (Supported with Migration)
```
/path/to/your/music/
├── Pink Floyd/
│   ├── The Dark Side of the Moon/
│   ├── The Wall/
│   ├── Live at Pompeii/  # Type detected from keywords
│   └── .band_metadata.json (created automatically)
```

#### Step 4: Run the MCP Server with Album Type Features
```bash
# Linux/macOS - Enhanced Features Enabled
docker run -d --name music-mcp-container \
  -v "/path/to/your/music:/music" \
  -e "MUSIC_ROOT_PATH=/music" \
  -e "CACHE_DURATION_DAYS=30" \
  -e "ENABLE_TYPE_DETECTION=true" \
  -e "ENABLE_STRUCTURE_ANALYSIS=true" \
  -e "TYPE_DETECTION_CONFIDENCE=0.8" \
  -e "DEFAULT_ALBUM_TYPE=Album" \
  music-mcp-server

# Windows - Enhanced Features Enabled
docker run -d --name music-mcp-container \
  -v "C:\Music:/music" \
  -e "MUSIC_ROOT_PATH=/music" \
  -e "CACHE_DURATION_DAYS=30" \
  -e "ENABLE_TYPE_DETECTION=true" \
  -e "ENABLE_STRUCTURE_ANALYSIS=true" \
  -e "TYPE_DETECTION_CONFIDENCE=0.8" \
  music-mcp-server
```

### Method 2: Local Python Installation

For development or custom deployment scenarios with full album type classification features.

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

#### Step 3: Configure Environment with Type Features
Create a `.env` file in the project root:
```env
# Basic Configuration
MUSIC_ROOT_PATH=/path/to/your/music
CACHE_DURATION_DAYS=30
LOG_LEVEL=INFO

# Album Type Classification Features
ENABLE_TYPE_DETECTION=true
TYPE_DETECTION_CONFIDENCE=0.8
DEFAULT_ALBUM_TYPE=Album

# Folder Structure Analysis Features
ENABLE_STRUCTURE_ANALYSIS=true
STRUCTURE_ANALYSIS_DEPTH=2
AUTO_MIGRATION_SUGGESTIONS=true

# Performance Settings
TYPE_DETECTION_CACHE_SIZE=1000
STRUCTURE_ANALYSIS_CACHE_TTL=3600
```

#### Step 4: Run the MCP Server
```bash
python main.py
```

### Method 3: Development Setup

For contributors and developers working on album type classification and structure analysis features.

#### Step 1: Clone and Setup
```bash
git clone https://github.com/yourusername/music-catalog-mcp.git
cd music-catalog-mcp
python -m venv venv
source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

#### Step 2: Setup Test Environment with Type Features
```bash
# Create test music collection with various structures
mkdir -p test_music_collection
cp -r test_data/* test_music_collection/

# Set test environment with type detection enabled
export MUSIC_ROOT_PATH="$(pwd)/test_music_collection"
export ENABLE_TYPE_DETECTION=true
export ENABLE_STRUCTURE_ANALYSIS=true
export LOG_LEVEL=DEBUG
```

#### Step 3: Run Tests Including Type Features
```bash
# Unit tests for album type classification
docker build -f Dockerfile.test -t music-mcp-tests .
docker run --rm music-mcp-tests python -m pytest tests/test_album_types.py -v

# Structure analysis tests
docker run --rm music-mcp-tests python -m pytest tests/test_structure_analysis.py -v

# Full test suite
docker run --rm music-mcp-tests python -m pytest . -v

# Manual testing with type features
python main.py
```

## Configuration Options for Album Type Classification

### Environment Variables

#### Core Album Type Settings
```bash
# Enable/disable album type detection
ENABLE_TYPE_DETECTION=true  # Default: true

# Confidence threshold for type detection (0.0-1.0)
TYPE_DETECTION_CONFIDENCE=0.8  # Default: 0.8

# Default type when detection is uncertain
DEFAULT_ALBUM_TYPE=Album  # Default: Album

# Enable multiple detection strategies
ENABLE_KEYWORD_DETECTION=true  # Default: true
ENABLE_FOLDER_STRUCTURE_DETECTION=true  # Default: true
ENABLE_METADATA_TYPE_DETECTION=true  # Default: true
```

#### Folder Structure Analysis Settings
```bash
# Enable/disable structure analysis
ENABLE_STRUCTURE_ANALYSIS=true  # Default: true

# Analysis depth (how deep to scan subfolders)
STRUCTURE_ANALYSIS_DEPTH=2  # Default: 2

# Enable automatic migration suggestions
AUTO_MIGRATION_SUGGESTIONS=true  # Default: true

# Compliance scoring thresholds
COMPLIANCE_EXCELLENT_THRESHOLD=90  # Default: 90
COMPLIANCE_GOOD_THRESHOLD=70      # Default: 70
COMPLIANCE_FAIR_THRESHOLD=50      # Default: 50
```

#### Performance Tuning
```bash
# Cache settings for type detection
TYPE_DETECTION_CACHE_SIZE=1000  # Default: 1000
TYPE_DETECTION_CACHE_TTL=3600   # Default: 3600 (1 hour)

# Structure analysis caching
STRUCTURE_ANALYSIS_CACHE_SIZE=500  # Default: 500
STRUCTURE_ANALYSIS_CACHE_TTL=3600  # Default: 3600

# Batch processing settings
MAX_ALBUMS_PER_BATCH=100  # Default: 100
PARALLEL_PROCESSING=true  # Default: true
MAX_WORKER_THREADS=4      # Default: 4
```

### Supported Album Types

The system automatically detects and classifies the following album types:

| Type | Description | Detection Keywords |
|------|-------------|-------------------|
| **Album** | Standard studio albums | Default classification |
| **Compilation** | Greatest hits, collections | "greatest hits", "best of", "collection", "anthology" |
| **EP** | Extended plays | "ep", "e.p." |
| **Live** | Live recordings | "live", "concert", "unplugged", "acoustic" |
| **Single** | Single releases | "single" |
| **Demo** | Demo recordings | "demo", "demos", "unreleased", "early recordings" |
| **Instrumental** | Instrumental versions | "instrumental", "instrumentals" |
| **Split** | Split releases | "split", "vs.", "versus", "with" |

### Folder Structure Types

The system recognizes and analyzes these organization patterns:

| Structure Type | Description | Example |
|----------------|-------------|---------|
| **Enhanced** | Type-based folders | `Album/1973 - Album Name/` |
| **Default** | Flat with year prefix | `1973 - Album Name/` |
| **Legacy** | Simple names | `Album Name/` |
| **Mixed** | Combination of patterns | Various patterns mixed |
| **Unknown** | Unrecognized pattern | Non-standard organization |

## MCP Client Configuration

### Claude Desktop Configuration with Type Features

Add the following to your Claude Desktop configuration file:

**Location:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

#### Docker Configuration with Album Type Features
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
        "-e", "ENABLE_TYPE_DETECTION=true",
        "-e", "ENABLE_STRUCTURE_ANALYSIS=true",
        "-e", "TYPE_DETECTION_CONFIDENCE=0.8",
        "-e", "AUTO_MIGRATION_SUGGESTIONS=true",
        "music-mcp-server"
      ],
      "cwd": "/path/to/music-catalog-mcp"
    }
  }
}
```

#### Local Python Configuration with Type Features
```json
{
  "mcpServers": {
    "music-collection": {
      "command": "python",
      "args": ["/path/to/music-catalog-mcp/main.py"],
      "env": {
        "MUSIC_ROOT_PATH": "/path/to/your/music",
        "CACHE_DURATION_DAYS": "30",
        "ENABLE_TYPE_DETECTION": "true",
        "ENABLE_STRUCTURE_ANALYSIS": "true",
        "TYPE_DETECTION_CONFIDENCE": "0.8",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Cline Configuration with Album Type Features

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
        "-e", "ENABLE_TYPE_DETECTION=true",
        "-e", "ENABLE_STRUCTURE_ANALYSIS=true",
        "music-mcp-server"
      ]
    }
  }
}
```

### Other MCP Clients with Type Features

For any MCP-compatible client, use these connection parameters:
- **Transport**: stdio
- **Environment Variables**: Include type detection and structure analysis settings
- **Capabilities**: Support for enhanced metadata with album types and compliance scoring

## Verification and Testing

### Verify Installation with Type Features

#### Test Basic Functionality
```bash
# Test connection and basic scanning
docker run --rm -v "/path/to/music:/music" \
  -e "MUSIC_ROOT_PATH=/music" \
  -e "ENABLE_TYPE_DETECTION=true" \
  music-mcp-server python -c "
from src.tools.scanner import scan_music_folders
result = scan_music_folders()
print(f'Scan completed. Found {result.get(\"total_albums\", 0)} albums')
print(f'Type distribution: {result.get(\"album_type_distribution\", {})}')
"
```

#### Test Album Type Detection
```bash
# Test type detection on specific folders
docker run --rm -v "/path/to/music:/music" \
  -e "MUSIC_ROOT_PATH=/music" \
  -e "ENABLE_TYPE_DETECTION=true" \
  -e "LOG_LEVEL=DEBUG" \
  music-mcp-server python -c "
from src.utils.type_detector import AlbumTypeDetector
detector = AlbumTypeDetector()
test_cases = [
    '1985 - Live at Wembley',
    '1996 - Greatest Hits', 
    '1980 - Love EP',
    '1978 - Early Demos'
]
for case in test_cases:
    result = detector.detect_from_folder_name(case)
    print(f'{case} → {result}')
"
```

#### Test Structure Analysis
```bash
# Test folder structure analysis
docker run --rm -v "/path/to/music:/music" \
  -e "MUSIC_ROOT_PATH=/music" \
  -e "ENABLE_STRUCTURE_ANALYSIS=true" \
  music-mcp-server python -c "
from src.services.structure_analyzer import analyze_collection_structure
result = analyze_collection_structure()
print(f'Structure analysis completed')
print(f'Average compliance: {result.get(\"average_compliance\", 0)}')
print(f'Structure types: {result.get(\"structure_distribution\", {})}')
"
```

### Common Configuration Issues

#### Type Detection Not Working
```bash
# Check if type detection is enabled
echo $ENABLE_TYPE_DETECTION  # Should output 'true'

# Verify confidence threshold
echo $TYPE_DETECTION_CONFIDENCE  # Should be 0.0-1.0

# Check logs for detection attempts
docker logs music-mcp-container | grep "type.*detect"
```

#### Structure Analysis Issues
```bash
# Verify structure analysis is enabled
echo $ENABLE_STRUCTURE_ANALYSIS  # Should output 'true'

# Check analysis depth setting
echo $STRUCTURE_ANALYSIS_DEPTH  # Should be 1-3

# Review structure analysis logs
docker logs music-mcp-container | grep "structure.*analysis"
```

### Performance Optimization

#### For Large Collections (>1000 albums)
```bash
# Optimize cache settings
export TYPE_DETECTION_CACHE_SIZE=2000
export STRUCTURE_ANALYSIS_CACHE_SIZE=1000

# Enable parallel processing
export PARALLEL_PROCESSING=true
export MAX_WORKER_THREADS=6

# Increase batch size
export MAX_ALBUMS_PER_BATCH=200
```

#### For Slower Systems
```bash
# Reduce cache sizes
export TYPE_DETECTION_CACHE_SIZE=500
export STRUCTURE_ANALYSIS_CACHE_SIZE=250

# Disable some features if needed
export ENABLE_STRUCTURE_ANALYSIS=false
export AUTO_MIGRATION_SUGGESTIONS=false

# Reduce concurrency
export MAX_WORKER_THREADS=2
export MAX_ALBUMS_PER_BATCH=50
```

## Troubleshooting

### Album Type Detection Issues

#### Types Not Being Detected
1. **Check Configuration**: Ensure `ENABLE_TYPE_DETECTION=true`
2. **Verify Confidence**: Lower `TYPE_DETECTION_CONFIDENCE` if needed
3. **Review Folder Names**: Ensure they contain recognizable keywords
4. **Check Logs**: Look for detection attempts in debug logs

#### Incorrect Type Detection
1. **Increase Confidence**: Raise `TYPE_DETECTION_CONFIDENCE` threshold
2. **Manual Override**: Use metadata to manually specify types
3. **Review Keywords**: Check if folder names contain misleading terms

### Structure Analysis Issues

#### Low Compliance Scores
1. **Review Organization**: Check folder naming consistency
2. **Add Year Prefixes**: Ensure albums have year prefixes
3. **Consider Type Folders**: Upgrade to enhanced structure
4. **Check Recommendations**: Review system suggestions

#### Analysis Not Running
1. **Enable Feature**: Ensure `ENABLE_STRUCTURE_ANALYSIS=true`
2. **Check Permissions**: Verify read access to music folders
3. **Review Logs**: Look for analysis errors in logs

For additional troubleshooting, see the [Troubleshooting Guide](TROUBLESHOOTING.md).

This enhanced installation process provides full access to the album type classification and folder structure analysis features, enabling intelligent music collection management with automated organization assessment and recommendations. 