# Music Collection Organization Best Practices

## Overview

This guide provides best practices for organizing your music collection to work optimally with the Music Collection MCP Server. Proper organization ensures accurate scanning, efficient metadata management, and the best user experience.

## Folder Structure Guidelines

### Recommended Hierarchy

```
Music Root Directory/
├── Band Name/                  # Level 1: Band folders
│   ├── Album Name/            # Level 2: Album folders
│   │   ├── 01 - Track Name.mp3    # Level 3: Music files
│   │   ├── 02 - Track Name.mp3
│   │   ├── 03 - Track Name.mp3
│   │   └── album_cover.jpg         # Optional: Album artwork
│   ├── Another Album/
│   │   └── *.mp3
│   └── .band_metadata.json         # Auto-generated metadata
├── Another Band/
│   ├── Album/
│   └── .band_metadata.json
└── .collection_index.json          # Auto-generated collection index
```

### Critical Requirements

✅ **Must Have:**
- Band folders at the top level
- Album folders within each band folder
- Music files within album folders
- Consistent naming across collection

❌ **Avoid:**
- Loose music files in band folders
- Mixed content (music + other files) in album folders
- Inconsistent folder naming
- Special characters that cause filesystem issues

## Naming Conventions

### Band Folder Names

#### Standard Format
```
Pink Floyd/
The Beatles/
Led Zeppelin/
Queen/
```

#### Special Cases
```
AC/DC/                    # Use forward slash, not backslash
Guns N' Roses/           # Use standard characters
Björk/                   # Unicode characters are supported
```

#### What to Avoid
```
Pink Floyd (Rock)/       # Don't include genres in folder names
The Beatles - 1960s/     # Don't include years
Led Zeppelin!!!!/        # Avoid excessive punctuation
```

### Album Folder Names

#### Standard Format
```
Pink Floyd/
├── The Wall/
├── Dark Side of the Moon/
├── Wish You Were Here/
└── Animals/
```

#### Include Year (Optional but Recommended)
```
Pink Floyd/
├── The Wall (1979)/
├── Dark Side of the Moon (1973)/
├── Wish You Were Here (1975)/
└── Animals (1977)/
```

#### Multiple Disc Albums
```
Pink Floyd/
├── The Wall/
├── The Wall CD1/         # Alternative approach
├── The Wall CD2/
└── Ummagumma Disc 1/
```

### Music File Names

#### Recommended Format
```
01 - In The Flesh.mp3
02 - The Thin Ice.mp3
03 - Another Brick in the Wall Pt. 1.mp3
```

#### Alternative Formats (Also Supported)
```
01 In The Flesh.mp3
01. In The Flesh.mp3
Track 01 - In The Flesh.mp3
Pink Floyd - In The Flesh.mp3
```

#### What Works Best
- **Track numbers**: Help with ordering and identification
- **Consistent formatting**: Easier to scan and process
- **Descriptive names**: Better for metadata extraction

## File Format Recommendations

### Supported Audio Formats

#### Primary Formats (Highly Recommended)
- **FLAC** (.flac) - Lossless, best quality
- **MP3** (.mp3) - Universal compatibility
- **AAC** (.aac, .m4a) - Good quality, Apple ecosystem

#### Secondary Formats (Supported)
- **WAV** (.wav) - Uncompressed, large files
- **OGG** (.ogg) - Open source, good compression
- **WMA** (.wma) - Windows Media Audio

#### File Quality Guidelines
- **Lossless**: FLAC preferred for archival collections
- **Lossy**: MP3 320kbps or AAC 256kbps minimum
- **Consistency**: Use same format throughout collection when possible

### Non-Audio Files

#### Recommended Inclusions
```
Album Folder/
├── 01 - Track.mp3
├── 02 - Track.mp3
├── album_cover.jpg      # Album artwork
├── folder.jpg           # Alternative artwork name
└── albumartsmall.jpg    # Thumbnail artwork
```

#### Files to Avoid in Music Folders
- `.DS_Store` (macOS system files)
- `Thumbs.db` (Windows thumbnail cache)
- `.tmp` files
- Other non-music content

## Organization Strategies by Collection Size

### Small Collections (1-100 Albums)

#### Simple Structure
```
Music/
├── Pink Floyd/
│   ├── The Wall/
│   └── Dark Side of the Moon/
├── The Beatles/
│   ├── Abbey Road/
│   └── Sgt Pepper/
└── Led Zeppelin/
    ├── Led Zeppelin IV/
    └── Physical Graffiti/
```

#### Benefits
- Easy to browse manually
- Fast scanning times
- Simple maintenance

### Medium Collections (100-1,000 Albums)

#### Genre Subdivision (Optional)
```
Music/
├── Rock/
│   ├── Pink Floyd/
│   ├── The Beatles/
│   └── Led Zeppelin/
├── Jazz/
│   ├── Miles Davis/
│   └── John Coltrane/
└── Classical/
    ├── Bach/
    └── Mozart/
```

#### Alphabetical Organization
```
Music/
├── A-C/
│   ├── AC/DC/
│   ├── The Beatles/
│   └── Black Sabbath/
├── D-M/
│   ├── Deep Purple/
│   └── Led Zeppelin/
└── N-Z/
    ├── Pink Floyd/
    └── Queen/
```

### Large Collections (1,000+ Albums)

#### Hybrid Approach
```
Music/
├── Rock/
│   ├── A-L/
│   │   ├── AC/DC/
│   │   └── Led Zeppelin/
│   └── M-Z/
│       ├── Pink Floyd/
│       └── Queen/
├── Jazz/
│   ├── Classic/
│   └── Modern/
└── Other/
```

#### Performance Considerations
- Use SSD storage for large collections
- Consider network storage for archives
- Regular cleanup and organization

## Metadata Integration

### Working with Existing Tags

#### ID3 Tags in MP3 Files
The server reads folder structure, not ID3 tags, but maintaining good tags helps with:
- Media player compatibility
- Backup organization
- Cross-platform consistency

#### Recommended ID3 Fields
```
Artist: Pink Floyd
Album: The Wall
Title: In The Flesh?
Track: 1
Year: 1979
Genre: Progressive Rock
```

### Server-Generated Metadata

#### What the Server Creates
```json
{
  "band_name": "Pink Floyd",
  "albums": [
    {
      "album_name": "The Wall",
      "missing": false,
      "tracks_count": 26,
      "year": "1979"
    }
  ]
}
```

#### Metadata Files Location
- **Band metadata**: `{band_folder}/.band_metadata.json`
- **Collection index**: `{music_root}/.collection_index.json`

## Handling Special Cases

### Various Artists/Compilations

#### Option 1: Dedicated Compilations Section
```
Music/
├── Regular Bands.../
├── Compilations/
│   ├── Now That's What I Call Music 80s/
│   ├── Greatest Rock Ballads/
│   └── Progressive Rock Anthology/
└── Soundtracks/
    ├── Guardians of the Galaxy/
    └── Pulp Fiction/
```

#### Option 2: Genre-Based Organization
```
Music/
├── Rock Compilations/
│   ├── Classic Rock Hits/
│   └── 70s Rock Collection/
└── Various Artists/
    └── Mixed Genre Collections/
```

### Multi-Artist Albums

#### Collaborative Albums
```
Music/
├── David Bowie & Queen/     # Joint artist folder
│   └── Under Pressure/
├── Johnny Cash/
│   └── American Recordings/  # Featuring various artists
```

#### Split by Primary Artist
```
Music/
├── David Bowie/
│   ├── Solo Albums/
│   └── Under Pressure (with Queen)/
├── Queen/
│   ├── Studio Albums/
│   └── Under Pressure (with David Bowie)/
```

### Duplicate Albums

#### Multiple Versions
```
Pink Floyd/
├── The Wall/                    # Original version
├── The Wall (Remastered)/      # Remastered version
├── The Wall (Deluxe Edition)/  # Special edition
└── The Wall (Live)/            # Live version
```

#### Box Sets and Collections
```
Pink Floyd/
├── Individual Albums/
│   ├── The Wall/
│   └── Dark Side of the Moon/
└── Box Sets/
    ├── The Complete Studio Albums/
    └── Early Years 1965-1972/
```

## Maintenance and Best Practices

### Regular Maintenance Tasks

#### Monthly Tasks
1. **Scan for new music**: Run `scan_music_folders` tool
2. **Check for metadata updates**: Verify `.band_metadata.json` files
3. **Review collection stats**: Use `collection://summary` resource
4. **Backup metadata**: Copy `.json` files to backup location

#### Quarterly Tasks
1. **Reorganize misplaced files**: Fix folder structure issues
2. **Update incomplete metadata**: Use Brave Search integration
3. **Clean up duplicate files**: Remove or reorganize duplicates
4. **Performance review**: Check scanning speed and optimize if needed

### Automation Opportunities

#### Automated Scanning
```bash
# Set up regular scanning (example cron job)
0 2 * * 0 docker run --rm -v "/music:/music" -e "MUSIC_ROOT_PATH=/music" music-mcp-server python -c "from src.tools.scanner import scan_music_folders; scan_music_folders()"
```

#### Backup Scripts
```bash
#!/bin/bash
# Backup all metadata files
find /music -name "*.json" -exec cp {} /backup/metadata/ \;
```

### Quality Control

#### Common Issues to Watch For
1. **Empty album folders**: Remove or populate with music
2. **Inconsistent naming**: Standardize across collection
3. **Missing album artwork**: Add cover images where possible
4. **Corrupted metadata files**: Monitor for JSON syntax errors

#### Validation Tools
```bash
# Check for empty folders
find /music -type d -empty

# Validate JSON files
find /music -name "*.json" -exec python -m json.tool {} \; > /dev/null

# Count music files per album
find /music -name "*.mp3" | cut -d'/' -f4 | sort | uniq -c
```

## Migration and Conversion

### From Other Organization Systems

#### iTunes/Apple Music Organization
```
# Before (iTunes style)
iTunes Media/Music/Artist/Album/Track.mp3

# After (MCP Server style)  
Music/Artist/Album/Track.mp3
```

#### Flat File Organization
```
# Before (flat structure)
Music/Artist - Album - Track.mp3

# After (folder structure)
Music/Artist/Album/Track.mp3
```

### Migration Tools and Scripts

#### Basic Reorganization Script
```bash
#!/bin/bash
# Example script to reorganize from flat to folder structure
for file in *.mp3; do
    artist=$(echo "$file" | cut -d'-' -f1 | sed 's/ *$//')
    album=$(echo "$file" | cut -d'-' -f2 | sed 's/^ *//' | sed 's/ *$//')
    track=$(echo "$file" | cut -d'-' -f3- | sed 's/^ *//')
    
    mkdir -p "$artist/$album"
    mv "$file" "$artist/$album/$track"
done
```

## Performance Optimization

### Storage Performance

#### SSD vs HDD
- **SSD**: Recommended for large collections (>1000 albums)
- **HDD**: Acceptable for smaller collections, slower scanning
- **Network Storage**: Possible but expect slower performance

#### File System Considerations
- **Local file systems**: ext4, NTFS, APFS all work well
- **Network file systems**: NFS, SMB supported but slower
- **Case sensitivity**: Be consistent across platforms

### Collection Size Guidelines

#### Recommended Limits per Folder
- **Band folders**: No practical limit
- **Albums per band**: 100+ albums supported
- **Tracks per album**: 100+ tracks supported
- **Total collection**: Tested up to 10,000+ albums

#### Performance Thresholds
- **Small** (1-100 bands): Instant scanning
- **Medium** (100-1,000 bands): 1-10 seconds
- **Large** (1,000+ bands): 10-60 seconds
- **Very Large** (10,000+ bands): May need optimization

## Tools and Utilities

### Recommended File Management Tools

#### Cross-Platform
- **File managers with bulk rename**: Better organization efficiency
- **Audio file taggers**: Mp3tag, Kid3 for metadata consistency
- **Duplicate finders**: Remove duplicate files before organizing

#### macOS
- **Name Mangler**: Batch file renaming
- **Hazel**: Automated file organization
- **Audio file processors**: XLD for format conversion

#### Windows
- **PowerRename**: Built-in bulk renaming tool
- **Bulk Rename Utility**: Advanced renaming capabilities
- **File management**: Total Commander, Directory Opus

#### Linux
- **Ranger**: Terminal-based file manager
- **Thunar bulk rename**: GUI bulk renaming
- **Command line tools**: find, sed, awk for scripting

### Validation and Health Check Tools

#### Collection Health Scripts
```bash
# Check for bands with no albums
find /music -maxdepth 1 -type d -exec sh -c 'test -z "$(find "$1" -maxdepth 1 -type d ! -path "$1")"' _ {} \; -print

# Find albums with no music files  
find /music -mindepth 2 -type d -exec sh -c 'test -z "$(find "$1" -name "*.mp3" -o -name "*.flac")"' _ {} \; -print

# Check metadata file integrity
find /music -name "*.json" -exec python -m json.tool {} \; > /dev/null
```

## Troubleshooting Organization Issues

### Common Problems and Solutions

#### Problem: "Band not detected during scanning"
**Cause**: Band folder structure incorrect
**Solution**: Ensure music files are in album folders within band folders

#### Problem: "Albums not appearing in band listing"
**Cause**: No music files in album folders
**Solution**: Verify supported file formats are present

#### Problem: "Inconsistent album counts"
**Cause**: Mixed folder organization
**Solution**: Standardize folder structure across collection

#### Problem: "Scanning takes too long"
**Cause**: Large collection or slow storage
**Solution**: Use SSD storage, optimize folder structure

### Best Practices Summary

#### Organization Checklist
- [ ] Band folders at top level
- [ ] Album folders within bands
- [ ] Music files within albums  
- [ ] Consistent naming conventions
- [ ] Supported file formats only
- [ ] Remove empty folders
- [ ] Clean metadata files
- [ ] Regular maintenance schedule

#### Performance Checklist  
- [ ] Use SSD for large collections
- [ ] Optimize folder depth
- [ ] Regular cleanup and organization
- [ ] Monitor scanning performance
- [ ] Backup metadata files

For additional help with collection organization, see:
- [Installation Guide](INSTALLATION.md)
- [Configuration Guide](CONFIGURATION.md) 
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [FAQ](FAQ.md) 