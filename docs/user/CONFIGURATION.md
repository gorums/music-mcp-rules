# Music Collection MCP Server - Configuration Guide with Album Type Classification

## Overview

This guide covers all configuration options for the Music Collection MCP Server, including environment variables, MCP client configuration, and advanced deployment scenarios. This includes the new album type classification and folder structure analysis features.

## Environment Configuration

### Core Environment Variables

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `MUSIC_ROOT_PATH` | string | ✅ **Required** | None | Absolute path to your music collection root directory |
| `CACHE_DURATION_DAYS` | integer | ❌ Optional | `30` | Number of days to cache metadata before refresh |
| `LOG_LEVEL` | string | ❌ Optional | `INFO` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |

### Album Type Classification Configuration

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `ENABLE_TYPE_DETECTION` | boolean | ❌ Optional | `true` | Enable automatic album type detection during scanning |
| `ENABLE_STRUCTURE_ANALYSIS` | boolean | ❌ Optional | `true` | Enable folder structure analysis and compliance scoring |
| `DEFAULT_ALBUM_TYPE` | string | ❌ Optional | `Album` | Default album type when detection fails |
| `COMPLIANCE_THRESHOLD` | integer | ❌ Optional | `70` | Minimum compliance score for "good" rating (0-100) |
| `AUTO_MIGRATE_STRUCTURE` | boolean | ❌ Optional | `false` | Automatically suggest structure migrations |
| `TYPE_DETECTION_CONFIDENCE` | float | ❌ Optional | `0.8` | Minimum confidence for automatic type detection (0.0-1.0) |

### Configuration Methods

#### Method 1: Environment File (.env)
Create a `.env` file in the project root:
```env
# Required Configuration
MUSIC_ROOT_PATH=/home/user/Music

# Optional Configuration
CACHE_DURATION_DAYS=30
LOG_LEVEL=INFO

# Album Type Classification
ENABLE_TYPE_DETECTION=true
ENABLE_STRUCTURE_ANALYSIS=true
DEFAULT_ALBUM_TYPE=Album
COMPLIANCE_THRESHOLD=75
AUTO_MIGRATE_STRUCTURE=false
TYPE_DETECTION_CONFIDENCE=0.8
```

#### Method 2: Docker Environment Variables
```bash
docker run -e "MUSIC_ROOT_PATH=/music" \
           -e "CACHE_DURATION_DAYS=30" \
           -e "LOG_LEVEL=INFO" \
           -e "ENABLE_TYPE_DETECTION=true" \
           -e "ENABLE_STRUCTURE_ANALYSIS=true" \
           -e "COMPLIANCE_THRESHOLD=75" \
           music-mcp-server
```

#### Method 3: System Environment Variables
```bash
# Linux/macOS
export MUSIC_ROOT_PATH="/home/user/Music"
export CACHE_DURATION_DAYS=30
export LOG_LEVEL=INFO
export ENABLE_TYPE_DETECTION=true
export ENABLE_STRUCTURE_ANALYSIS=true
export COMPLIANCE_THRESHOLD=75

# Windows PowerShell
$env:MUSIC_ROOT_PATH = "C:\Music"
$env:CACHE_DURATION_DAYS = 30
$env:LOG_LEVEL = "INFO"
$env:ENABLE_TYPE_DETECTION = "true"
$env:ENABLE_STRUCTURE_ANALYSIS = "true"
$env:COMPLIANCE_THRESHOLD = 75

# Windows Command Prompt
set MUSIC_ROOT_PATH=C:\Music
set CACHE_DURATION_DAYS=30
set LOG_LEVEL=INFO
set ENABLE_TYPE_DETECTION=true
set ENABLE_STRUCTURE_ANALYSIS=true
set COMPLIANCE_THRESHOLD=75
```

## Detailed Configuration Options

### MUSIC_ROOT_PATH Configuration

The most critical configuration setting. Points to your music collection root.

#### Valid Path Examples
```bash
# Linux/macOS
MUSIC_ROOT_PATH="/home/user/Music"
MUSIC_ROOT_PATH="/mnt/nas/music"
MUSIC_ROOT_PATH="/Volumes/MusicDrive/Collection"

# Windows
MUSIC_ROOT_PATH="C:\Music"
MUSIC_ROOT_PATH="\\NAS\Music"
MUSIC_ROOT_PATH="C:\Users\User\Music"

# Docker (always use Unix-style paths inside container)
MUSIC_ROOT_PATH="/music"
```

#### Expected Directory Structure

The server now supports multiple folder organization patterns:

##### Default Structure (Flat Organization)
```
$MUSIC_ROOT_PATH/
├── Pink Floyd/                    # Band folder
│   ├── 1973 - The Dark Side of the Moon/    # Album folder
│   │   ├── 01 - Speak to Me.mp3
│   │   ├── 02 - Breathe.mp3
│   │   └── ...
│   ├── 1979 - The Wall/          # Album folder
│   │   ├── 01 - In The Flesh.mp3
│   │   └── ...
│   └── .band_metadata.json       # Auto-generated metadata
├── The Beatles/                   # Another band
│   ├── 1967 - Sgt. Pepper's Lonely Hearts Club Band/
│   │   └── ...
│   └── .band_metadata.json
└── .collection_index.json         # Auto-generated collection index
```

##### Enhanced Structure (Type-Based Organization)
```
$MUSIC_ROOT_PATH/
├── Pink Floyd/                    # Band folder
│   ├── Album/                     # Album type folder
│   │   ├── 1973 - The Dark Side of the Moon/
│   │   │   ├── 01 - Speak to Me.mp3
│   │   │   └── ...
│   │   └── 1979 - The Wall/
│   │       ├── 01 - In The Flesh.mp3
│   │       └── ...
│   ├── Live/                      # Live album type folder
│   │   └── 1972 - Live at Pompeii/
│   │       ├── 01 - Echoes.mp3
│   │       └── ...
│   ├── Compilation/               # Compilation type folder
│   │   └── 2001 - Echoes - The Best of Pink Floyd/
│   │       └── ...
│   └── .band_metadata.json       # Auto-generated metadata
└── .collection_index.json         # Auto-generated collection index
```

##### Mixed Structure (Combination)
```
$MUSIC_ROOT_PATH/
├── Pink Floyd/                    # Band folder
│   ├── Album/                     # Some albums in type folders
│   │   └── 1973 - The Dark Side of the Moon/
│   ├── 1979 - The Wall/          # Some albums in flat structure
│   ├── Live/
│   │   └── 1972 - Live at Pompeii/
│   └── .band_metadata.json
```

#### Path Validation Rules
- ✅ Must exist and be accessible
- ✅ Must have read/write permissions
- ✅ Must contain at least one band folder
- ✅ Should not be a system directory (`/`, `/usr`, etc.)
- ✅ Unicode characters in paths are supported
- ✅ Supports multiple folder organization patterns

### Album Type Classification Configuration

#### ENABLE_TYPE_DETECTION Configuration

Controls automatic album type detection during scanning.

```env
ENABLE_TYPE_DETECTION=true   # Enable automatic type detection (default)
ENABLE_TYPE_DETECTION=false  # Disable type detection, use DEFAULT_ALBUM_TYPE
```

**When Enabled:**
- Automatically detects album types based on folder names and keywords
- Uses intelligent algorithms to classify albums as Album, Live, EP, Demo, etc.
- Provides confidence scores for detected types
- Falls back to DEFAULT_ALBUM_TYPE when detection confidence is low

**When Disabled:**
- All albums are classified as DEFAULT_ALBUM_TYPE
- No type detection algorithms are executed
- Faster scanning for large collections
- Manual type assignment required

#### ENABLE_STRUCTURE_ANALYSIS Configuration

Controls folder structure analysis and compliance scoring.

```env
ENABLE_STRUCTURE_ANALYSIS=true   # Enable structure analysis (default)
ENABLE_STRUCTURE_ANALYSIS=false  # Disable structure analysis
```

**When Enabled:**
- Analyzes folder organization patterns
- Calculates compliance scores (0-100)
- Provides structure improvement recommendations
- Detects structure types (default, enhanced, mixed, legacy)

**When Disabled:**
- No structure analysis performed
- No compliance scoring
- No organization recommendations
- Faster scanning for large collections

#### DEFAULT_ALBUM_TYPE Configuration

Sets the default album type when detection fails or is disabled.

```env
DEFAULT_ALBUM_TYPE=Album         # Standard studio albums (default)
DEFAULT_ALBUM_TYPE=Compilation   # Greatest hits/collections
DEFAULT_ALBUM_TYPE=EP           # Extended plays
DEFAULT_ALBUM_TYPE=Live         # Live recordings
DEFAULT_ALBUM_TYPE=Single       # Single releases
DEFAULT_ALBUM_TYPE=Demo         # Demo recordings
DEFAULT_ALBUM_TYPE=Instrumental # Instrumental versions
DEFAULT_ALBUM_TYPE=Split        # Split releases
```

**Valid Values:**
- `Album` - Standard studio albums
- `Compilation` - Greatest hits, collections, anthologies
- `EP` - Extended plays (typically 3-7 tracks)
- `Live` - Live recordings, concerts, unplugged sessions
- `Single` - Single releases (1-3 tracks)
- `Demo` - Demo recordings, unreleased material
- `Instrumental` - Instrumental versions of albums
- `Split` - Split releases with multiple artists

#### COMPLIANCE_THRESHOLD Configuration

Sets the minimum compliance score for "good" folder organization rating.

```env
COMPLIANCE_THRESHOLD=90   # Strict compliance (excellent only)
COMPLIANCE_THRESHOLD=75   # High compliance (good and excellent)
COMPLIANCE_THRESHOLD=60   # Medium compliance (fair, good, excellent)
COMPLIANCE_THRESHOLD=40   # Low compliance (poor, fair, good, excellent)
COMPLIANCE_THRESHOLD=0    # Accept all compliance levels
```

**Compliance Levels:**
- **Excellent** (90-100): Perfect folder organization
- **Good** (75-89): Minor issues, mostly well organized
- **Fair** (60-74): Some issues, acceptable organization
- **Poor** (40-59): Many issues, needs improvement
- **Critical** (0-39): Severe issues, major reorganization needed

#### TYPE_DETECTION_CONFIDENCE Configuration

Sets the minimum confidence level for automatic type detection.

```env
TYPE_DETECTION_CONFIDENCE=0.9   # Very high confidence required
TYPE_DETECTION_CONFIDENCE=0.8   # High confidence (default)
TYPE_DETECTION_CONFIDENCE=0.6   # Medium confidence
TYPE_DETECTION_CONFIDENCE=0.4   # Low confidence
TYPE_DETECTION_CONFIDENCE=0.0   # Accept any detection result
```

**Confidence Levels:**
- **0.9-1.0**: Very high confidence - only obvious type indicators
- **0.8-0.9**: High confidence - clear type indicators
- **0.6-0.8**: Medium confidence - probable type indicators
- **0.4-0.6**: Low confidence - weak type indicators
- **0.0-0.4**: Very low confidence - uncertain type indicators

### CACHE_DURATION_DAYS Configuration

Controls how long metadata is cached before requiring refresh.

#### Valid Values
```env
CACHE_DURATION_DAYS=1    # Refresh daily (development)
CACHE_DURATION_DAYS=7    # Weekly refresh
CACHE_DURATION_DAYS=30   # Monthly refresh (default)
CACHE_DURATION_DAYS=90   # Quarterly refresh
CACHE_DURATION_DAYS=365  # Annual refresh
CACHE_DURATION_DAYS=0    # Disable caching (always fetch)
```

#### Cache Behavior with Type Classification
- **Metadata Files**: `.band_metadata.json` files older than configured days are considered stale
- **Collection Index**: `.collection_index.json` is refreshed when underlying data changes
- **Type Detection**: Album type classifications are cached with metadata
- **Structure Analysis**: Folder structure analysis results are cached
- **Compliance Scores**: Compliance scores are cached with folder modification timestamps
- **External Data**: Band information fetched from external APIs respects this cache duration
- **Force Refresh**: Use `force_rescan=true` in tools to bypass cache

### LOG_LEVEL Configuration

Controls the verbosity of logging output, including type detection and structure analysis.

#### Available Levels
```env
LOG_LEVEL=DEBUG    # Verbose debugging information
LOG_LEVEL=INFO     # General information (default)
LOG_LEVEL=WARNING  # Warnings and important notices
LOG_LEVEL=ERROR    # Errors only (recommended for production)
```

#### Log Output Examples with Type Classification
```
# DEBUG level
DEBUG: Scanning folder: /music/Pink Floyd
DEBUG: Detected structure type: enhanced
DEBUG: Found album: The Wall (26 tracks)
DEBUG: Album type detected: Album (confidence: 0.95)
DEBUG: Compliance score calculated: 95/100
DEBUG: Loading metadata from .band_metadata.json
INFO: Collection scan completed: 150 bands, 850 albums

# INFO level (default)
INFO: Music Collection MCP Server starting...
INFO: Configuration loaded: MUSIC_ROOT_PATH=/music
INFO: Type detection enabled: true
INFO: Structure analysis enabled: true
INFO: Collection found: 150 bands, 850 albums
INFO: Album type distribution: Album(632), Live(97), Compilation(73), EP(28)
INFO: Average compliance score: 78.5/100
INFO: MCP server ready on stdio

# ERROR level (production)
ERROR: Failed to access music directory: Permission denied
ERROR: Invalid metadata format in Pink Floyd/.band_metadata.json
ERROR: Album type detection failed for album: Unknown Album
ERROR: Structure analysis failed for band: Corrupted Band
```

## MCP Client Configuration

### Claude Desktop Integration

#### Configuration File Locations
```bash
# macOS
~/Library/Application Support/Claude/claude_desktop_config.json

# Windows
%APPDATA%\Claude\claude_desktop_config.json

# Linux
~/.config/claude-desktop/config.json
```

#### Basic Docker Configuration with Type Features
```json
{
  "mcpServers": {
    "music-collection": {
      "command": "docker",
      "args": [
        "run", "--rm", "--interactive",
        "-v", "/path/to/your/music:/music",
        "-e", "MUSIC_ROOT_PATH=/music",
        "-e", "ENABLE_TYPE_DETECTION=true",
        "-e", "ENABLE_STRUCTURE_ANALYSIS=true",
        "-e", "COMPLIANCE_THRESHOLD=75",
        "music-mcp-server"
      ]
    }
  }
}
```

#### Advanced Docker Configuration with Full Type Support
```json
{
  "mcpServers": {
    "music-collection": {
      "command": "docker",
      "args": [
        "run", "--rm", "--interactive",
        "--memory=2g",
        "--cpus=2",
        "-v", "/path/to/your/music:/music",
        "-v", "/tmp/music-cache:/cache",
        "-e", "MUSIC_ROOT_PATH=/music",
        "-e", "CACHE_DURATION_DAYS=30",
        "-e", "LOG_LEVEL=INFO",
        "-e", "ENABLE_TYPE_DETECTION=true",
        "-e", "ENABLE_STRUCTURE_ANALYSIS=true",
        "-e", "DEFAULT_ALBUM_TYPE=Album",
        "-e", "COMPLIANCE_THRESHOLD=75",
        "-e", "AUTO_MIGRATE_STRUCTURE=false",
        "-e", "TYPE_DETECTION_CONFIDENCE=0.8",
        "music-mcp-server"
      ]
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
      "args": ["/path/to/music-mcp-server/main.py"],
      "env": {
        "MUSIC_ROOT_PATH": "/path/to/your/music",
        "CACHE_DURATION_DAYS": "30",
        "LOG_LEVEL": "INFO",
        "ENABLE_TYPE_DETECTION": "true",
        "ENABLE_STRUCTURE_ANALYSIS": "true",
        "COMPLIANCE_THRESHOLD": "75"
      }
    }
  }
}
```

## Advanced Configuration Scenarios

### Development Configuration

For development and testing with enhanced type features:

```env
# Development settings
MUSIC_ROOT_PATH=/home/dev/test_music
CACHE_DURATION_DAYS=1
LOG_LEVEL=DEBUG

# Type detection settings for testing
ENABLE_TYPE_DETECTION=true
ENABLE_STRUCTURE_ANALYSIS=true
DEFAULT_ALBUM_TYPE=Album
COMPLIANCE_THRESHOLD=50
AUTO_MIGRATE_STRUCTURE=true
TYPE_DETECTION_CONFIDENCE=0.6
```

### Production Configuration

For production deployment with optimized performance:

```env
# Production settings
MUSIC_ROOT_PATH=/mnt/music_collection
CACHE_DURATION_DAYS=30
LOG_LEVEL=WARNING

# Type detection settings for production
ENABLE_TYPE_DETECTION=true
ENABLE_STRUCTURE_ANALYSIS=true
DEFAULT_ALBUM_TYPE=Album
COMPLIANCE_THRESHOLD=75
AUTO_MIGRATE_STRUCTURE=false
TYPE_DETECTION_CONFIDENCE=0.8
```

### Large Collection Configuration

For very large music collections (10,000+ albums):

```env
# Large collection settings
MUSIC_ROOT_PATH=/nas/massive_music_collection
CACHE_DURATION_DAYS=90
LOG_LEVEL=ERROR

# Optimized type detection for large collections
ENABLE_TYPE_DETECTION=true
ENABLE_STRUCTURE_ANALYSIS=false  # Disable for performance
DEFAULT_ALBUM_TYPE=Album
COMPLIANCE_THRESHOLD=60
AUTO_MIGRATE_STRUCTURE=false
TYPE_DETECTION_CONFIDENCE=0.9    # High confidence only
```

### Legacy Collection Configuration

For older collections with inconsistent organization:

```env
# Legacy collection settings
MUSIC_ROOT_PATH=/old_music_archive
CACHE_DURATION_DAYS=7
LOG_LEVEL=INFO

# Lenient type detection for legacy collections
ENABLE_TYPE_DETECTION=true
ENABLE_STRUCTURE_ANALYSIS=true
DEFAULT_ALBUM_TYPE=Album
COMPLIANCE_THRESHOLD=30          # Very lenient
AUTO_MIGRATE_STRUCTURE=true      # Suggest improvements
TYPE_DETECTION_CONFIDENCE=0.5    # Lower confidence threshold
```

## Configuration Validation

### Startup Validation

The server validates configuration on startup:

```
INFO: Validating configuration...
INFO: ✅ MUSIC_ROOT_PATH exists and is accessible
INFO: ✅ Type detection configuration valid
INFO: ✅ Structure analysis configuration valid
INFO: ✅ Compliance threshold in valid range (0-100)
INFO: ✅ Type detection confidence in valid range (0.0-1.0)
INFO: ✅ Default album type is valid
INFO: Configuration validation completed successfully
```

### Common Configuration Errors

#### Invalid Album Type
```
ERROR: Invalid DEFAULT_ALBUM_TYPE 'InvalidType'
Valid types: Album, Compilation, EP, Live, Single, Demo, Instrumental, Split
```

#### Invalid Compliance Threshold
```
ERROR: COMPLIANCE_THRESHOLD must be between 0 and 100, got: 150
```

#### Invalid Type Detection Confidence
```
ERROR: TYPE_DETECTION_CONFIDENCE must be between 0.0 and 1.0, got: 1.5
```

### Configuration Testing

Test your configuration with the scan tool:

```bash
# Test basic scanning with type detection
docker run --rm -it \
  -v "/path/to/music:/music" \
  -e "MUSIC_ROOT_PATH=/music" \
  -e "ENABLE_TYPE_DETECTION=true" \
  -e "LOG_LEVEL=DEBUG" \
  music-mcp-server \
  python -c "
from src.tools.scanner import MusicScanner
from src.config import Config
config = Config()
scanner = MusicScanner(config)
result = scanner.scan_music_folders(force_rescan=True)
print(f'Scanned {result.stats.bands_scanned} bands')
print(f'Found {result.stats.albums_found} albums')
print(f'Type distribution: {result.stats.album_type_distribution}')
"
```

## Performance Tuning

### Type Detection Performance

- **Large Collections**: Set `TYPE_DETECTION_CONFIDENCE=0.9` for faster scanning
- **Accuracy vs Speed**: Lower confidence = faster scanning, higher confidence = more accurate
- **Disable for Speed**: Set `ENABLE_TYPE_DETECTION=false` for maximum speed

### Structure Analysis Performance

- **Large Collections**: Set `ENABLE_STRUCTURE_ANALYSIS=false` for faster scanning
- **Periodic Analysis**: Enable only during maintenance windows
- **Selective Analysis**: Use compliance threshold to focus on problematic bands

### Memory Optimization

- **Cache Duration**: Longer cache duration = less memory usage
- **Log Level**: Higher log level = less memory for log buffers
- **Batch Processing**: Process large collections in smaller batches

## Troubleshooting Configuration

### Common Issues

#### Type Detection Not Working
1. Check `ENABLE_TYPE_DETECTION=true`
2. Verify `TYPE_DETECTION_CONFIDENCE` is not too high
3. Check folder names contain recognizable keywords
4. Review debug logs for detection attempts

#### Structure Analysis Failing
1. Check `ENABLE_STRUCTURE_ANALYSIS=true`
2. Verify folder permissions are correct
3. Check for special characters in folder names
4. Review compliance threshold settings

#### Poor Performance
1. Increase `CACHE_DURATION_DAYS`
2. Set `LOG_LEVEL=ERROR`
3. Consider disabling structure analysis for large collections
4. Increase `TYPE_DETECTION_CONFIDENCE` to reduce processing

---

## Version Information

- **Configuration Version**: 2.0.0
- **Album Type System**: 1.0.0
- **Folder Structure Analysis**: 1.0.0
- **Last Updated**: 2025-01-30 