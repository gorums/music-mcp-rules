# Music Collection MCP Server - Troubleshooting Guide with Album Type Classification

## Overview

This guide helps you diagnose and resolve common issues with the Music Collection MCP Server, including album scanning problems, Docker configuration issues, MCP client integration challenges, and the new album type classification and folder structure analysis features.

## Quick Diagnostic Commands

### Health Check
```bash
# Check if server is running
docker ps | grep music-mcp

# Check server logs
docker logs music-mcp-container

# Test configuration with type detection
docker run --rm -v "/path/to/music:/music" \
  -e "MUSIC_ROOT_PATH=/music" \
  -e "ENABLE_TYPE_DETECTION=true" \
  -e "LOG_LEVEL=DEBUG" \
  music-mcp-server --validate-config
```

### Basic Functionality Test
```bash
# Test music directory scanning with type detection
docker run --rm -v "/path/to/music:/music" \
  -e "MUSIC_ROOT_PATH=/music" \
  -e "ENABLE_TYPE_DETECTION=true" \
  -e "ENABLE_STRUCTURE_ANALYSIS=true" \
  music-mcp-server python -c "
from src.tools.scanner import MusicScanner
from src.config import Config
config = Config()
scanner = MusicScanner(config)
result = scanner.scan_music_folders(force_rescan=True)
print(f'Found {result.stats.bands_scanned} bands, {result.stats.albums_found} albums')
print(f'Type distribution: {result.stats.album_type_distribution}')
print(f'Average compliance: {result.stats.structure_analysis.average_compliance_score}')
"
```

## Album Type Classification Issues

### Problem: "Album types not being detected"

**Symptoms:**
```
All albums showing as type "Album"
No type distribution in scan results
Type detection confidence scores are 0.0
```

**Diagnostic Steps:**
1. **Check Type Detection Configuration**
```bash
# Verify type detection is enabled
docker run --rm music-mcp-server python -c "
from src.config import Config
config = Config()
print(f'Type detection enabled: {config.enable_type_detection}')
print(f'Confidence threshold: {config.type_detection_confidence}')
print(f'Default type: {config.default_album_type}')
"
```

2. **Enable Debug Logging**
```bash
# Run with debug logging to see detection attempts
docker run -e "LOG_LEVEL=DEBUG" -e "ENABLE_TYPE_DETECTION=true" music-mcp-server
```

**Solutions:**
1. **Enable Type Detection**
```bash
# Ensure type detection is enabled
export ENABLE_TYPE_DETECTION=true
```

2. **Lower Confidence Threshold**
```bash
# Reduce confidence requirement for more detections
export TYPE_DETECTION_CONFIDENCE=0.6  # Default is 0.8
```

3. **Check Folder Names**
```bash
# Ensure folder names contain recognizable keywords
# Good examples:
"1972 - Live at Pompeii"          # → Live
"2001 - Greatest Hits"            # → Compilation  
"1980 - Demo Sessions"            # → Demo
"1985 - Instrumentals"            # → Instrumental

# Poor examples (won't be detected):
"1973 - DSOTM"                    # → Album (no keywords)
"1979 - Wall"                     # → Album (no keywords)
```

### Problem: "Incorrect album types detected"

**Symptoms:**
```
Studio albums detected as "Live"
Compilations detected as "Album"
High confidence scores for wrong types
```

**Diagnostic Steps:**
1. **Review Detection Keywords**
```bash
# Check what keywords triggered detection
grep "Album type detected" /var/log/music-mcp.log
grep "confidence:" /var/log/music-mcp.log
```

2. **Test Specific Albums**
```bash
# Test type detection for specific album
docker run --rm music-mcp-server python -c "
from src.models.validation import AlbumTypeDetector
result = AlbumTypeDetector.detect_type_from_folder_name('1972 - Live at Pompeii')
print(f'Detected type: {result}')
"
```

**Solutions:**
1. **Increase Confidence Threshold**
```bash
# Require higher confidence for detection
export TYPE_DETECTION_CONFIDENCE=0.9
```

2. **Manual Override in Metadata**
```json
{
  "albums": [
    {
      "album_name": "The Wall",
      "type": "Album",  // Manual override
      "year": "1979"
    }
  ]
}
```

3. **Review Folder Naming**
```bash
# Avoid misleading keywords in studio album names
"1973 - Live Wire"        # May be detected as Live
"1979 - The Wall Live"    # May be detected as Live

# Better naming:
"1973 - Live Wire (Album)"
"1979 - The Wall"
```

### Problem: "Type detection confidence too low"

**Symptoms:**
```
Many albums falling back to DEFAULT_ALBUM_TYPE
Low confidence scores in debug logs
Type detection working but not confident enough
```

**Solutions:**
1. **Lower Confidence Threshold**
```bash
# Accept lower confidence detections
export TYPE_DETECTION_CONFIDENCE=0.5  # From default 0.8
```

2. **Improve Folder Naming**
```bash
# Add clear type indicators to folder names
"Live/1972 - Live at Pompeii"         # Enhanced structure
"1972 - Live at Pompeii (Live)"       # Edition indicator
"1972 - Live at Pompeii - Live Album" # Clear descriptor
```

3. **Use Enhanced Folder Structure**
```bash
# Organize albums by type for better detection
Band Name/
├── Album/
│   └── 1973 - Album Name/
├── Live/
│   └── 1972 - Live Album/
└── Compilation/
    └── 2001 - Greatest Hits/
```

## Folder Structure Analysis Issues

### Problem: "Low compliance scores"

**Symptoms:**
```
Compliance scores below 70
Many "poor" or "critical" compliance levels
Structure analysis showing many issues
```

**Diagnostic Steps:**
1. **Check Structure Analysis Results**
```bash
# Get detailed compliance information
docker run --rm music-mcp-server python -c "
from src.resources.collection_summary import get_collection_summary
summary = get_collection_summary()
print(summary)  # Look for compliance section
"
```

2. **Review Specific Band Issues**
```bash
# Check individual band compliance
docker run --rm music-mcp-server python -c "
from src.models.band_structure import FolderStructureAnalyzer
from pathlib import Path
analyzer = FolderStructureAnalyzer()
result = analyzer.analyze_band_structure(Path('/music/Pink Floyd'))
print(f'Compliance: {result.compliance_score}')
print(f'Issues: {result.issues}')
print(f'Recommendations: {result.recommendations}')
"
```

**Solutions:**
1. **Standardize Naming Conventions**
```bash
# Fix inconsistent year formats
"Album Name"              # → "1973 - Album Name"
"73 - Album Name"         # → "1973 - Album Name"  
"Album Name (1973)"       # → "1973 - Album Name"
```

2. **Fix Special Characters**
```bash
# Replace problematic characters
"AC/DC - Album"           # → "AC-DC - Album"
"Album: Subtitle"         # → "Album - Subtitle"
"Album [Remaster]"        # → "Album (Remaster)"
```

3. **Consistent Structure**
```bash
# Choose one structure and stick to it
# Either flat:
Band/1973 - Album/
Band/1979 - Another Album/

# Or enhanced:
Band/Album/1973 - Album/
Band/Album/1979 - Another Album/

# Avoid mixing:
Band/1973 - Album/           # Flat
Band/Album/1979 - Another/   # Enhanced - inconsistent!
```

### Problem: "Structure analysis disabled or failing"

**Symptoms:**
```
No compliance scores in results
Structure analysis section missing
Error messages about structure analysis
```

**Diagnostic Steps:**
1. **Check Configuration**
```bash
# Verify structure analysis is enabled
docker run --rm music-mcp-server python -c "
from src.config import Config
config = Config()
print(f'Structure analysis enabled: {config.enable_structure_analysis}')
"
```

2. **Test Structure Analysis**
```bash
# Test on specific band folder
docker run --rm music-mcp-server python -c "
from src.models.band_structure import FolderStructureAnalyzer
from pathlib import Path
analyzer = FolderStructureAnalyzer()
try:
    result = analyzer.analyze_band_structure(Path('/music/Test Band'))
    print(f'Analysis successful: {result.structure_type}')
except Exception as e:
    print(f'Analysis failed: {e}')
"
```

**Solutions:**
1. **Enable Structure Analysis**
```bash
export ENABLE_STRUCTURE_ANALYSIS=true
```

2. **Check Folder Permissions**
```bash
# Ensure read access to all folders
chmod -R 755 /path/to/music
```

3. **Fix Corrupted Folder Names**
```bash
# Remove or fix folders with invalid characters
find /path/to/music -name "*[<>:\"|?*]*" -type d
```

### Problem: "Mixed structure type detected"

**Symptoms:**
```
Structure type showing as "mixed"
Inconsistent compliance scores
Recommendations to standardize structure
```

**Understanding:**
- Mixed structure means some albums use flat organization while others use type-based folders
- This isn't necessarily an error, but may indicate inconsistent organization

**Solutions:**
1. **Accept Mixed Structure**
```bash
# Mixed structures are valid, just set appropriate threshold
export COMPLIANCE_THRESHOLD=60  # Lower threshold for mixed collections
```

2. **Migrate to Consistent Structure**
```bash
# Choose target structure and migrate gradually
# Option 1: Migrate to flat structure
Band/Album/1973 - Album Name/  →  Band/1973 - Album Name/

# Option 2: Migrate to enhanced structure  
Band/1973 - Album Name/        →  Band/Album/1973 - Album Name/
```

3. **Use Structure Filtering**
```bash
# Filter by structure type in get_band_list
{
  "filter_structure_types": ["enhanced"],  # Only enhanced structures
  "sort_by": "compliance_score"
}
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
cat > .env << EOF
MUSIC_ROOT_PATH=/path/to/your/music
ENABLE_TYPE_DETECTION=true
ENABLE_STRUCTURE_ANALYSIS=true
COMPLIANCE_THRESHOLD=75
EOF
```

3. **Verify Environment Loading**
```bash
# Test configuration loading
python -c "from src.config import Config; print(Config().music_root_path)"
```

### Problem: "Invalid album type configuration"

**Symptoms:**
```
ERROR: Invalid DEFAULT_ALBUM_TYPE 'InvalidType'
ERROR: TYPE_DETECTION_CONFIDENCE must be between 0.0 and 1.0
ERROR: COMPLIANCE_THRESHOLD must be between 0 and 100
```

**Solutions:**
1. **Valid Album Types**
```bash
# Use only valid album types
export DEFAULT_ALBUM_TYPE=Album         # Valid
export DEFAULT_ALBUM_TYPE=Live          # Valid
export DEFAULT_ALBUM_TYPE=Compilation   # Valid

# Invalid examples:
export DEFAULT_ALBUM_TYPE=Studio        # Invalid
export DEFAULT_ALBUM_TYPE=Regular       # Invalid
```

2. **Valid Confidence Range**
```bash
# Confidence must be 0.0 to 1.0
export TYPE_DETECTION_CONFIDENCE=0.8    # Valid
export TYPE_DETECTION_CONFIDENCE=1.5    # Invalid - too high
export TYPE_DETECTION_CONFIDENCE=-0.1   # Invalid - negative
```

3. **Valid Compliance Threshold**
```bash
# Threshold must be 0 to 100
export COMPLIANCE_THRESHOLD=75          # Valid
export COMPLIANCE_THRESHOLD=150         # Invalid - too high
export COMPLIANCE_THRESHOLD=-10         # Invalid - negative
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
"Invalid album type configuration"
```

2. **Test Container Interactively**
```bash
# Run container with shell access
docker run -it --entrypoint /bin/bash music-mcp-server

# Inside container, test components
python -c "from src.config import Config; print('Config OK')"
python -c "from src.tools.scanner import MusicScanner; print('Scanner OK')"
python -c "from src.models.validation import AlbumTypeDetector; print('Type Detection OK')"
```

3. **Check Resource Limits**
```bash
# Increase memory limit for large collections with type detection
docker run --memory=4g music-mcp-server

# Check system resources
docker system df
docker system prune  # Clean up space if needed
```

## Performance Issues

### Problem: "Scanning takes too long with type detection"

**Symptoms:**
```
Scan times significantly increased
High CPU usage during scanning
Memory usage growing during type detection
```

**Diagnostic Steps:**
1. **Profile Scanning Performance**
```bash
# Time the scanning process
time docker run --rm music-mcp-server python -c "
from src.tools.scanner import MusicScanner
from src.config import Config
import time
start = time.time()
scanner = MusicScanner(Config())
result = scanner.scan_music_folders(force_rescan=True)
print(f'Scan took {time.time() - start:.2f} seconds')
"
```

2. **Check Type Detection Overhead**
```bash
# Compare with and without type detection
# With type detection:
export ENABLE_TYPE_DETECTION=true
# Without type detection:
export ENABLE_TYPE_DETECTION=false
```

**Solutions:**
1. **Optimize Type Detection**
```bash
# Increase confidence threshold for faster scanning
export TYPE_DETECTION_CONFIDENCE=0.9

# Disable structure analysis for speed
export ENABLE_STRUCTURE_ANALYSIS=false

# Use higher log level
export LOG_LEVEL=ERROR
```

2. **Increase Resources**
```bash
# Allocate more memory and CPU
docker run --memory=4g --cpus=2 music-mcp-server
```

3. **Incremental Scanning**
```bash
# Use incremental scanning for regular updates
{
  "force_rescan": false,  # Only scan changed folders
  "detect_album_types": true
}
```

### Problem: "High memory usage during structure analysis"

**Symptoms:**
```
Memory usage growing during scanning
Out of memory errors for large collections
Docker container killed due to memory limits
```

**Solutions:**
1. **Disable Structure Analysis**
```bash
# For very large collections
export ENABLE_STRUCTURE_ANALYSIS=false
```

2. **Increase Memory Limits**
```bash
# Allocate more memory
docker run --memory=8g music-mcp-server
```

3. **Process in Batches**
```bash
# Scan smaller portions of collection at a time
# Split large collections into subdirectories
```

## Data Corruption Issues

### Problem: "Metadata files corrupted with type information"

**Symptoms:**
```
JSON decode errors when loading metadata
Invalid album type values in metadata
Compliance information missing or corrupted
```

**Diagnostic Steps:**
1. **Validate JSON Structure**
```bash
# Check specific metadata file
python -c "
import json
with open('/music/Band/.band_metadata.json') as f:
    try:
        data = json.load(f)
        print('JSON is valid')
        # Check for required fields
        for album in data.get('albums', []):
            if 'type' in album:
                print(f'Album {album[\"album_name\"]} type: {album[\"type\"]}')
    except json.JSONDecodeError as e:
        print(f'JSON error: {e}')
"
```

2. **Check Album Type Validation**
```bash
# Validate album types in metadata
python -c "
from src.models.band import AlbumType
valid_types = [t.value for t in AlbumType]
print(f'Valid types: {valid_types}')
"
```

**Solutions:**
1. **Restore from Backup**
```bash
# Find backup files
find /music -name "*.backup.*" -type f

# Restore from backup
cp "/music/Band/.band_metadata.json.backup.20250130-120000" \
   "/music/Band/.band_metadata.json"
```

2. **Fix Invalid Album Types**
```bash
# Edit metadata file to fix invalid types
# Replace invalid types with valid ones:
"type": "Studio"      # → "type": "Album"
"type": "Concert"     # → "type": "Live"  
"type": "Best Of"     # → "type": "Compilation"
```

3. **Regenerate Metadata**
```bash
# Delete corrupted file and rescan
rm "/music/Band/.band_metadata.json"
# Run scan to regenerate with type detection
```

### Problem: "Collection index corrupted with type distribution"

**Symptoms:**
```
Collection summary showing incorrect statistics
Type distribution data missing or invalid
Index file JSON errors
```

**Solutions:**
1. **Regenerate Collection Index**
```bash
# Delete corrupted index
rm "/music/.collection_index.json"

# Rescan to regenerate
docker run --rm music-mcp-server python -c "
from src.tools.scanner import MusicScanner
from src.config import Config
scanner = MusicScanner(Config())
scanner.scan_music_folders(force_rescan=True)
"
```

2. **Validate Index Structure**
```bash
# Check index file structure
python -c "
import json
with open('/music/.collection_index.json') as f:
    data = json.load(f)
    print('Index structure:')
    for key in data.keys():
        print(f'  {key}: {type(data[key])}')
"
```

## MCP Client Integration Issues

### Problem: "Type filtering not working in Claude Desktop"

**Symptoms:**
```
get_band_list with filter_album_types returns all bands
Type-based filtering parameters ignored
No error messages but filtering not applied
```

**Diagnostic Steps:**
1. **Test Filtering Directly**
```bash
# Test filtering outside of MCP client
docker run --rm music-mcp-server python -c "
from src.tools.storage import get_band_list
result = get_band_list(filter_album_types=['Live', 'Demo'])
print(f'Filtered results: {len(result[\"bands\"])} bands')
"
```

2. **Check Parameter Format**
```json
// Correct format
{
  "method": "tools/call",
  "params": {
    "name": "get_band_list", 
    "arguments": {
      "filter_album_types": ["Live", "Demo"],  // Array of strings
      "filter_compliance_levels": ["excellent", "good"]
    }
  }
}
```

**Solutions:**
1. **Verify Parameter Names**
```bash
# Use exact parameter names from API documentation
"filter_album_types"        # Not "album_types" or "types"
"filter_compliance_levels"  # Not "compliance" or "levels"
"filter_structure_types"    # Not "structure" or "structures"
```

2. **Check Case Sensitivity**
```bash
# Album types are case-sensitive
"Live"          # Correct
"live"          # Incorrect
"Compilation"   # Correct
"compilation"   # Incorrect
```

### Problem: "Resources not showing type information"

**Symptoms:**
```
band://info/{band_name} missing album type sections
collection://summary missing type distribution
Type information not appearing in markdown output
```

**Solutions:**
1. **Ensure Metadata Contains Type Information**
```bash
# Check if band metadata has type information
python -c "
import json
with open('/music/Pink Floyd/.band_metadata.json') as f:
    data = json.load(f)
    for album in data.get('albums', []):
        print(f'{album[\"album_name\"]}: {album.get(\"type\", \"No type\")}')
"
```

2. **Rescan with Type Detection**
```bash
# Rescan to add type information to existing metadata
{
  "method": "tools/call",
  "params": {
    "name": "scan_music_folders",
    "arguments": {
      "force_rescan": true,
      "detect_album_types": true
    }
  }
}
```

## Advanced Troubleshooting

### Enable Comprehensive Debugging

```bash
# Maximum debugging for type detection and structure analysis
docker run --rm \
  -e "LOG_LEVEL=DEBUG" \
  -e "ENABLE_TYPE_DETECTION=true" \
  -e "ENABLE_STRUCTURE_ANALYSIS=true" \
  -e "TYPE_DETECTION_CONFIDENCE=0.5" \
  -v "/path/to/music:/music" \
  music-mcp-server 2>&1 | tee debug.log
```

### Performance Profiling

```bash
# Profile type detection performance
docker run --rm music-mcp-server python -c "
import cProfile
import pstats
from src.tools.scanner import MusicScanner
from src.config import Config

def profile_scan():
    scanner = MusicScanner(Config())
    return scanner.scan_music_folders(force_rescan=True)

cProfile.run('profile_scan()', 'scan_profile.stats')
stats = pstats.Stats('scan_profile.stats')
stats.sort_stats('cumulative').print_stats(20)
"
```

### Memory Usage Analysis

```bash
# Monitor memory usage during scanning
docker run --rm music-mcp-server python -c "
import psutil
import os
from src.tools.scanner import MusicScanner
from src.config import Config

process = psutil.Process(os.getpid())
print(f'Initial memory: {process.memory_info().rss / 1024 / 1024:.2f} MB')

scanner = MusicScanner(Config())
result = scanner.scan_music_folders(force_rescan=True)

print(f'Final memory: {process.memory_info().rss / 1024 / 1024:.2f} MB')
print(f'Albums scanned: {result.stats.albums_found}')
"
```

## Getting Help

### Collecting Diagnostic Information

When reporting issues, include:

1. **System Information**
```bash
# System details
uname -a
docker --version
python --version

# Configuration
env | grep -E "(MUSIC_|ENABLE_|TYPE_|COMPLIANCE_)"
```

2. **Collection Statistics**
```bash
# Collection size (without sensitive paths)
find /path/to/music -type d -name "*" | wc -l  # Total folders
find /path/to/music -name "*.mp3" | wc -l      # Total files
```

3. **Error Logs**
```bash
# Recent error logs
docker logs music-mcp-container --tail 100 2>&1 | grep -E "(ERROR|WARN)"
```

4. **Type Detection Results**
```bash
# Type detection statistics
docker run --rm music-mcp-server python -c "
from src.tools.scanner import MusicScanner
from src.config import Config
scanner = MusicScanner(Config())
result = scanner.scan_music_folders()
print(f'Type distribution: {result.stats.album_type_distribution}')
print(f'Structure analysis: {result.stats.structure_analysis}')
"
```

### Common Log Patterns

**Successful Type Detection:**
```
DEBUG: Album type detected: Live (confidence: 0.95) for "1972 - Live at Pompeii"
DEBUG: Structure type detected: enhanced for band "Pink Floyd"
DEBUG: Compliance score calculated: 95/100 for band "Pink Floyd"
```

**Type Detection Issues:**
```
WARN: Low confidence type detection (0.4) for album "Unknown Album"
ERROR: Invalid album type "InvalidType" in metadata
ERROR: Structure analysis failed for band "Corrupted Band"
```

**Performance Issues:**
```
WARN: Type detection taking longer than expected (>5s per band)
WARN: High memory usage detected during structure analysis
```

---

## Version Information

- **Troubleshooting Guide Version**: 2.0.0
- **Album Type System**: 1.0.0
- **Folder Structure Analysis**: 1.0.0
- **Last Updated**: 2025-01-30 