# Album Handling, Type Classification, and Folder Structure Analysis

## Overview

The Music Collection MCP Server implements sophisticated album handling, type classification, and folder structure analysis to manage comprehensive music collections. This document details the algorithms, data structures, and workflows used for album discovery, type detection, structure analysis, and missing album detection.

## Core Concepts

### Album Representation

Albums are represented at multiple levels within the system:

1. **Physical Albums**: Albums present as folders in the file system
2. **Metadata Albums**: Albums defined in band metadata (may include missing albums)
3. **Missing Albums**: Albums in metadata but not present in file system
4. **Hybrid Collections**: Collections containing both physical and missing albums

### Album States

```python
class AlbumState(Enum):
    """Possible states for albums in the collection."""
    LOCAL = "local"           # Present in file system
    MISSING = "missing"       # In metadata but not in file system
    UNKNOWN = "unknown"       # Present in file system but not in metadata
    CORRUPTED = "corrupted"   # Present but unreadable
```

### Album Type Classification System

The system supports 8 distinct album types with intelligent auto-detection:

```python
class AlbumType(str, Enum):
    """
    Enumeration of supported album types.
    
    Values:
        ALBUM: Standard studio album
        COMPILATION: Compilation or greatest hits album
        EP: Extended Play (typically 4-7 tracks)
        LIVE: Live recording album
        SINGLE: Single release
        DEMO: Demo recording
        INSTRUMENTAL: Instrumental version of an album
        SPLIT: Split release with multiple artists
    """
    ALBUM = "Album"
    COMPILATION = "Compilation"
    EP = "EP"
    LIVE = "Live"
    SINGLE = "Single"
    DEMO = "Demo"
    INSTRUMENTAL = "Instrumental"
    SPLIT = "Split"
```

### Folder Structure Types

The system recognizes and analyzes multiple folder organization patterns:

```python
class StructureType(str, Enum):
    """
    Enumeration of folder structure types.
    
    Values:
        DEFAULT: Standard flat structure with "YYYY - Album Name (Edition?)" pattern
        ENHANCED: Type-based structure with "Type/YYYY - Album Name (Edition?)" pattern
        MIXED: Combination of both default and enhanced structures
        LEGACY: Albums without year prefix, just "Album Name" pattern
        UNKNOWN: Unable to determine structure type
    """
    DEFAULT = "default"
    ENHANCED = "enhanced"
    MIXED = "mixed"
    LEGACY = "legacy"
    UNKNOWN = "unknown"
```

## Album Discovery Algorithm

### File System Scanning with Type Detection

The album discovery process includes type classification:

```python
def discover_albums_in_band_folder(band_path: Path) -> List[Album]:
    """
    Discover albums within a band's folder structure with type detection.
    
    Algorithm:
    1. Scan immediate subdirectories as potential albums
    2. Filter out system/hidden folders
    3. Validate album folders contain music files
    4. Extract album metadata from folder structure
    5. Detect album type from folder name and location
    6. Parse edition information
    7. Calculate compliance score
    8. Count tracks and calculate statistics
    
    Args:
        band_path: Path to the band's root folder
        
    Returns:
        List of discovered albums with metadata and type classification
    """
    albums = []
    
    # Step 1: Analyze folder structure first
    structure_detector = BandStructureDetector(band_path)
    structure_analysis = structure_detector.analyze_structure()
    
    # Step 2: Discover album folders
    for item in band_path.iterdir():
        if not item.is_dir():
            continue
            
        # Step 3: Filter system folders
        if item.name.startswith('.') or item.name.lower() in EXCLUDED_FOLDERS:
            continue
            
        # Step 4: Validate album folder
        if not contains_music_files(item):
            continue
            
        # Step 5: Extract album information with type detection
        album = create_album_from_folder_with_types(
            item, 
            structure_analysis.structure_type
        )
        albums.append(album)
    
    return albums

def create_album_from_folder_with_types(
    album_path: Path, 
    structure_type: StructureType
) -> Album:
    """
    Create Album object from folder path with comprehensive type detection.
    
    Args:
        album_path: Path to the album folder
        structure_type: Detected structure type for the band
        
    Returns:
        Album object with type, edition, and compliance information
    """
    # Parse folder structure
    if structure_type == StructureType.ENHANCED:
        parsed = AlbumFolderParser.parse_enhanced_folder_structure(str(album_path))
    else:
        parsed = AlbumFolderParser.parse_folder_name(album_path.name)
    
    # Detect album type
    album_type = AlbumType(parsed.get('album_type', AlbumType.ALBUM))
    if album_type == AlbumType.ALBUM:
        # Try additional detection methods
        album_type = AlbumTypeDetector.detect_type_from_folder_name(
            album_path.name, parsed.get('album_name', '')
        )
    
    # Calculate compliance
    compliance = AlbumComplianceValidator.validate_album_compliance(
        album_path, structure_type, album_type
    )
    
    # Count tracks
    track_count = count_tracks_in_album(album_path)
    
    return Album(
        album_name=parsed.get('album_name', album_path.name),
        year=parsed.get('year', ''),
        type=album_type,
        edition=parsed.get('edition', ''),
        tracks_count=track_count,
        folder_path=str(album_path.relative_to(album_path.parent)),
        compliance=compliance
    )
```

### Album Type Detection Algorithms

The system uses multiple strategies for type detection:

```python
class AlbumTypeDetector:
    """
    Utility class for detecting album types from folder names and metadata.
    """
    
    # Keywords for album type detection
    TYPE_KEYWORDS = {
        AlbumType.LIVE: [
            'live', 'concert', 'unplugged', 'acoustic', 'in concert',
            'live at', 'live in', 'live from', 'concert at'
        ],
        AlbumType.COMPILATION: [
            'greatest hits', 'best of', 'collection', 'anthology', 
            'compilation', 'hits', 'complete', 'essential'
        ],
        AlbumType.EP: ['ep', 'e.p.'],
        AlbumType.SINGLE: ['single'],
        AlbumType.DEMO: [
            'demo', 'demos', 'early recordings', 'unreleased',
            'rough mixes', 'rehearsal', 'pre-production'
        ],
        AlbumType.INSTRUMENTAL: ['instrumental', 'instrumentals'],
        AlbumType.SPLIT: ['split', 'vs.', 'vs', 'versus', 'with']
    }
    
    @classmethod
    def detect_type_from_folder_name(cls, folder_name: str, album_name: str = "") -> AlbumType:
        """
        Detect album type from folder name and album name.
        
        Args:
            folder_name: The album folder name
            album_name: The album name (optional)
            
        Returns:
            Detected AlbumType
        """
        folder_lower = folder_name.lower()
        name_lower = album_name.lower() if album_name else ""
        
        # Check for type indicators in folder name or album name
        for album_type, keywords in cls.TYPE_KEYWORDS.items():
            if any(keyword in folder_lower or keyword in name_lower for keyword in keywords):
                return album_type
        
        # Check for type folder structure
        path_parts = Path(folder_name).parts
        if len(path_parts) >= 2:
            potential_type_folder = path_parts[-2].lower()
            for album_type in AlbumType:
                if potential_type_folder == album_type.value.lower():
                    return album_type
        
        return AlbumType.ALBUM

    @classmethod
    def detect_from_track_count(cls, track_count: int) -> AlbumType:
        """
        Provide type hints based on track count heuristics.
        
        Args:
            track_count: Number of tracks in the album
            
        Returns:
            Suggested AlbumType based on track count
        """
        if track_count == 1:
            return AlbumType.SINGLE
        elif 2 <= track_count <= 7:
            return AlbumType.EP
        else:
            return AlbumType.ALBUM
```

### Folder Structure Analysis

The system analyzes folder organization patterns for compliance and recommendations:

```python
class BandStructureDetector:
    """
    Comprehensive analysis of band folder organization patterns.
    """
    
    def analyze_structure(self) -> FolderStructure:
        """
        Analyze band folder structure and generate comprehensive assessment.
        
        Returns:
            FolderStructure object with detailed analysis
        """
        albums = self._discover_album_folders()
        
        # Analyze patterns
        pattern_analysis = self._analyze_patterns(albums)
        
        # Detect structure type
        structure_type = self._determine_structure_type(pattern_analysis)
        
        # Calculate scores
        consistency_score = self._calculate_consistency_score(pattern_analysis)
        structure_score = self._calculate_structure_score(pattern_analysis, structure_type)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            pattern_analysis, structure_type, consistency_score
        )
        
        # Detect issues
        issues = self._detect_issues(pattern_analysis, structure_type)
        
        return FolderStructure(
            structure_type=structure_type,
            consistency=self._get_consistency_level(consistency_score),
            consistency_score=consistency_score,
            albums_analyzed=len(albums),
            albums_with_year_prefix=pattern_analysis['year_prefix_count'],
            albums_without_year_prefix=pattern_analysis['no_year_prefix_count'],
            albums_with_type_folders=pattern_analysis['type_folder_count'],
            detected_patterns=pattern_analysis['patterns_found'],
            type_folders_found=pattern_analysis['type_folders'],
            structure_score=structure_score,
            recommendations=recommendations,
            issues=issues,
            analysis_metadata={
                'pattern_counts': pattern_analysis['pattern_counts'],
                'compliance_distribution': pattern_analysis['compliance_distribution'],
                'structure_health': self._assess_structure_health(structure_score),
                'album_type_distribution': pattern_analysis['type_distribution'],
                'edition_usage': pattern_analysis['edition_usage']
            }
        )
    
    def _determine_structure_type(self, pattern_analysis: Dict) -> StructureType:
        """Determine the primary structure type based on analysis."""
        type_folder_ratio = pattern_analysis['type_folder_count'] / max(pattern_analysis['total_albums'], 1)
        year_prefix_ratio = pattern_analysis['year_prefix_count'] / max(pattern_analysis['total_albums'], 1)
        
        if type_folder_ratio >= 0.8:
            return StructureType.ENHANCED
        elif year_prefix_ratio >= 0.8:
            return StructureType.DEFAULT
        elif type_folder_ratio > 0.2 and year_prefix_ratio > 0.2:
            return StructureType.MIXED
        elif year_prefix_ratio < 0.3:
            return StructureType.LEGACY
        else:
            return StructureType.UNKNOWN
```

### Music File Detection

```python
SUPPORTED_MUSIC_FORMATS = {
    '.mp3': 'MP3',
    '.flac': 'FLAC', 
    '.wav': 'WAV',
    '.aac': 'AAC',
    '.m4a': 'M4A',
    '.ogg': 'OGG',
    '.wma': 'WMA',
    '.mp4': 'MP4',
    '.m4p': 'M4P'
}

def contains_music_files(folder_path: Path) -> bool:
    """Check if folder contains music files."""
    for file_path in folder_path.iterdir():
        if file_path.suffix.lower() in SUPPORTED_MUSIC_FORMATS:
            return True
    return False

def count_tracks_in_album(album_path: Path) -> int:
    """Count music tracks in album folder."""
    track_count = 0
    for file_path in album_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_MUSIC_FORMATS:
            track_count += 1
    return track_count
```

## Missing Album Detection

### Detection Algorithm with Type Awareness

Missing albums are identified by comparing metadata with file system state:

```python
def detect_missing_albums(
    band_path: Path, 
    metadata_albums: List[Album]
) -> Tuple[List[Album], List[Album]]:
    """
    Detect missing albums by comparing metadata with file system.
    
    Algorithm:
    1. Discover physical albums in file system with type detection
    2. Create mapping of album names to paths and types
    3. Compare metadata albums against physical albums
    4. Classify albums as present or missing
    5. Handle name variations and fuzzy matching
    6. Preserve type information in results
    
    Returns:
        Tuple of (present_albums, missing_albums)
    """
    # Step 1: Discover physical albums with type detection
    physical_albums = discover_albums_in_band_folder(band_path)
    physical_album_map = {
        normalize_album_name(album.album_name): album 
        for album in physical_albums
    }
    
    present_albums = []
    missing_albums = []
    
    # Step 2: Compare each metadata album
    for metadata_album in metadata_albums:
        normalized_name = normalize_album_name(metadata_album.album_name)
        
        if normalized_name in physical_album_map:
            # Album is present - merge physical and metadata info
            physical_album = physical_album_map[normalized_name]
            merged_album = merge_album_data_with_types(physical_album, metadata_album)
            merged_album.missing = False
            present_albums.append(merged_album)
        else:
            # Album is missing - mark as missing but preserve type
            metadata_album.missing = True
            # Generate compliance score for missing album
            metadata_album.compliance = generate_missing_album_compliance(
                metadata_album, band_path
            )
            missing_albums.append(metadata_album)
    
    return present_albums, missing_albums

def merge_album_data_with_types(physical_album: Album, metadata_album: Album) -> Album:
    """
    Merge physical album data with metadata, preserving type information.
    
    Priority order:
    1. Physical folder structure data (type, edition, folder_path, compliance)
    2. Metadata information (genres, duration, track count)
    3. Combined information where appropriate
    """
    return Album(
        album_name=metadata_album.album_name,  # Use metadata name as canonical
        year=metadata_album.year or physical_album.year,
        type=physical_album.type,  # Trust physical structure for type
        edition=physical_album.edition or metadata_album.edition,
        genres=metadata_album.genres or physical_album.genres,
        tracks_count=physical_album.tracks_count or metadata_album.tracks_count,
        duration=metadata_album.duration,
        folder_path=physical_album.folder_path,
        compliance=physical_album.compliance,
        missing=False
    )
```

### Name Normalization with Type Awareness

Album name matching handles variations in naming while considering types:

```python
def normalize_album_name(name: str) -> str:
    """
    Normalize album name for comparison.
    
    Handles:
    - Case differences
    - Special characters
    - Extra whitespace
    - Common abbreviations
    - Unicode variations
    - Type-specific keywords
    """
    import re
    import unicodedata
    
    # Convert to lowercase
    normalized = name.lower()
    
    # Remove Unicode accents
    normalized = unicodedata.normalize('NFD', normalized)
    normalized = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    
    # Remove special characters except spaces and alphanumeric
    normalized = re.sub(r'[^\w\s]', '', normalized)
    
    # Normalize whitespace
    normalized = ' '.join(normalized.split())
    
    # Handle common abbreviations
    normalized = normalized.replace(' and ', ' & ')
    normalized = normalized.replace(' pt ', ' part ')
    
    # Remove common type indicators for better matching
    type_indicators = ['live', 'demo', 'ep', 'single', 'compilation', 'instrumental']
    for indicator in type_indicators:
        if normalized.endswith(f' {indicator}'):
            normalized = normalized[:-len(f' {indicator}')]
    
    return normalized
```

## Album Data Structures

### Enhanced Album Model with Type and Compliance

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum

class AlbumCompliance(BaseModel):
    """Compliance information for album folder organization."""
    score: int = Field(0, ge=0, le=100)
    level: str = Field("unknown")  # excellent, good, fair, poor, critical
    issues: List[str] = Field(default_factory=list)
    recommended_path: Optional[str] = Field(None)

class Album(BaseModel):
    """
    Enhanced album representation with type classification and compliance.
    
    Combines file system information with user-provided metadata
    to create a complete album representation including type detection
    and folder structure compliance analysis.
    """
    album_name: str = Field(..., min_length=1, max_length=200)
    year: Optional[str] = Field(None, regex=r'^\d{4}$')
    type: AlbumType = Field(default=AlbumType.ALBUM)
    edition: Optional[str] = Field(default="", max_length=100)
    genres: List[str] = Field(default_factory=list)
    tracks_count: Optional[int] = Field(None, ge=0, le=999)
    track_count: Optional[int] = Field(None, ge=0, le=999)  # Alias
    duration: Optional[str] = Field(None, regex=r'^\d+min$')
    missing: bool = Field(default=False)
    
    # File system information
    folder_path: Optional[str] = Field(None)  # Relative path from band folder
    file_size_mb: Optional[float] = Field(None, ge=0)
    last_modified: Optional[str] = Field(None)  # ISO datetime string
    
    # Audio format information
    primary_format: Optional[str] = Field(None)  # e.g., "MP3", "FLAC"
    format_distribution: Optional[Dict[str, int]] = Field(default_factory=dict)
    
    # Compliance and organization
    compliance: Optional[AlbumCompliance] = Field(default_factory=AlbumCompliance)
    
    class Config:
        # Enable validation on assignment
        validate_assignment = True
        
        # Custom validation
        @validator('tracks_count', 'track_count')
        def validate_track_count(cls, v, values):
            if v is not None and v == 0:
                # Allow 0 tracks for certain types like singles or missing albums
                pass
            return v
        
        @validator('type')
        def validate_album_type(cls, v):
            if isinstance(v, str):
                try:
                    return AlbumType(v)
                except ValueError:
                    raise ValueError(f'Invalid album type: {v}. Must be one of: {[t.value for t in AlbumType]}')
            return v
    
    def auto_detect_metadata(self) -> None:
        """Automatically detect type and edition from folder path."""
        if self.folder_path:
            parsed = AlbumFolderParser.parse_folder_name(self.folder_path)
            if not self.type or self.type == AlbumType.ALBUM:
                self.type = AlbumTypeDetector.detect_type_from_folder_name(
                    self.folder_path, self.album_name
                )
            if not self.edition:
                self.edition = parsed.get('edition', '')
    
    def detect_type_from_name(self) -> AlbumType:
        """
        Detect album type from album name and folder path using keywords.
        
        Returns:
            Detected AlbumType based on name patterns
        """
        return AlbumTypeDetector.detect_type_from_folder_name(
            self.folder_path or '', self.album_name
        )
    
    def calculate_compliance_score(self, structure_type: StructureType) -> AlbumCompliance:
        """Calculate compliance score based on folder structure."""
        return AlbumComplianceValidator.validate_album_compliance(
            self.folder_path, structure_type, self.type
        )
```

### Album Analysis with Type Distribution

```python
class AlbumAnalysis(BaseModel):
    """Analysis data for a specific album."""
    album_name: str  # Must match album in main albums list
    review: Optional[str] = Field(None, max_length=5000)
    rate: Optional[int] = Field(None, ge=1, le=10)
    
    # Analysis metadata
    analysis_date: Optional[str] = Field(None)  # ISO datetime
    analysis_source: Optional[str] = Field(None)  # e.g., "user", "ai", "external"
    
    @validator('album_name')
    def album_name_must_exist(cls, v, values, **kwargs):
        """Validate that album_name references an existing album."""
        # Note: This validation requires context from parent model
        return v
```

## Collection Index Integration

### Band Index Entry

The collection index maintains album statistics for fast access:

```python
class BandIndexEntry(BaseModel):
    """Entry in the collection index for a single band."""
    band_name: str
    folder_path: str  # Relative to collection root
    
    # Album statistics
    albums_count: int = 0        # Total albums (physical + missing)
    local_albums: int = 0        # Albums present in file system
    missing_albums: int = 0      # Albums in metadata but missing
    
    # Metadata status
    has_metadata: bool = False   # Has .band_metadata.json file
    has_analysis: bool = False   # Has analysis data in metadata
    
    # Timestamps
    last_updated: str           # Last metadata update
    last_scanned: Optional[str] = None  # Last file system scan
    
    @property
    def completion_percentage(self) -> float:
        """Calculate collection completion percentage."""
        if self.albums_count == 0:
            return 100.0
        return (self.local_albums / self.albums_count) * 100

    def update_from_scan(self, scan_result: BandScanResult) -> None:
        """Update index entry from scan results."""
        self.local_albums = len(scan_result.physical_albums)
        self.missing_albums = len(scan_result.missing_albums)
        self.albums_count = self.local_albums + self.missing_albums
        self.last_scanned = datetime.utcnow().isoformat()
```

### Collection Statistics

```python
class CollectionStats(BaseModel):
    """Collection-wide album statistics."""
    total_bands: int = 0
    total_albums: int = 0           # All albums (physical + missing)
    total_missing_albums: int = 0   # Missing albums across collection
    
    # Completion metrics
    completion_percentage: float = 0.0  # Overall collection completion
    bands_with_metadata: int = 0        # Bands with metadata files
    bands_with_analysis: int = 0        # Bands with analysis data
    
    # Distribution metrics
    avg_albums_per_band: float = 0.0
    median_albums_per_band: float = 0.0
    largest_collection_size: int = 0
    smallest_collection_size: int = 0
    
    def calculate_from_bands(self, bands: List[BandIndexEntry]) -> None:
        """Calculate statistics from band index entries."""
        if not bands:
            return
            
        self.total_bands = len(bands)
        self.total_albums = sum(band.albums_count for band in bands)
        self.total_missing_albums = sum(band.missing_albums for band in bands)
        
        # Completion percentage
        if self.total_albums > 0:
            local_albums = self.total_albums - self.total_missing_albums
            self.completion_percentage = (local_albums / self.total_albums) * 100
        
        # Band statistics
        self.bands_with_metadata = sum(1 for band in bands if band.has_metadata)
        self.bands_with_analysis = sum(1 for band in bands if band.has_analysis)
        
        # Distribution statistics
        album_counts = [band.albums_count for band in bands if band.albums_count > 0]
        if album_counts:
            self.avg_albums_per_band = sum(album_counts) / len(album_counts)
            self.median_albums_per_band = sorted(album_counts)[len(album_counts) // 2]
            self.largest_collection_size = max(album_counts)
            self.smallest_collection_size = min(album_counts)
```

## Scanning Workflows

### Full Collection Scan

```python
def perform_full_collection_scan(collection_path: Path) -> CollectionScanResult:
    """
    Perform complete collection scan with album discovery.
    
    Workflow:
    1. Discover all band folders
    2. Scan each band for albums
    3. Load existing metadata
    4. Detect missing albums
    5. Update collection index
    6. Generate scan report
    """
    scan_start = datetime.utcnow()
    
    # Step 1: Discover band folders
    band_folders = discover_band_folders(collection_path)
    
    band_results = []
    total_albums = 0
    total_missing = 0
    
    # Step 2: Scan each band
    for band_folder in band_folders:
        band_result = scan_single_band(band_folder)
        band_results.append(band_result)
        
        total_albums += band_result.albums_count
        total_missing += band_result.missing_albums_count
    
    # Step 3: Update collection index
    collection_index = update_collection_index(collection_path, band_results)
    
    scan_duration = datetime.utcnow() - scan_start
    
    return CollectionScanResult(
        success=True,
        bands_scanned=len(band_results),
        albums_found=total_albums,
        missing_albums=total_missing,
        scan_duration=scan_duration.total_seconds(),
        collection_index=collection_index
    )

def scan_single_band(band_path: Path) -> BandScanResult:
    """Scan individual band folder for albums."""
    # Discover physical albums
    physical_albums = discover_albums_in_band_folder(band_path)
    
    # Load existing metadata
    metadata = load_band_metadata(band_path)
    
    # Detect missing albums
    if metadata and metadata.albums:
        present_albums, missing_albums = detect_missing_albums(
            band_path, metadata.albums
        )
    else:
        present_albums = physical_albums
        missing_albums = []
    
    return BandScanResult(
        band_name=band_path.name,
        physical_albums=physical_albums,
        present_albums=present_albums,
        missing_albums=missing_albums,
        albums_count=len(present_albums) + len(missing_albums),
        missing_albums_count=len(missing_albums)
    )
```

### Incremental Scan

```python
def perform_incremental_scan(
    collection_path: Path, 
    last_scan_time: datetime
) -> CollectionScanResult:
    """
    Perform incremental scan of changed folders only.
    
    Only scans bands where:
    - Folder modification time > last_scan_time
    - Metadata file modification time > last_scan_time
    - Band not in collection index
    """
    collection_index = load_collection_index(collection_path)
    
    bands_to_scan = []
    
    # Check each band folder for changes
    for band_folder in discover_band_folders(collection_path):
        band_name = band_folder.name
        
        # Check if band needs scanning
        needs_scan = should_scan_band(
            band_folder, 
            band_name, 
            collection_index, 
            last_scan_time
        )
        
        if needs_scan:
            bands_to_scan.append(band_folder)
    
    # Scan only changed bands
    if not bands_to_scan:
        return CollectionScanResult(
            success=True,
            bands_scanned=0,
            albums_found=0,
            missing_albums=0,
            scan_duration=0.0,
            message="No changes detected"
        )
    
    # Perform partial scan
    return scan_band_subset(bands_to_scan, collection_index)

def should_scan_band(
    band_folder: Path,
    band_name: str,
    collection_index: CollectionIndex,
    last_scan_time: datetime
) -> bool:
    """Determine if band folder needs scanning."""
    # Band not in index - needs scan
    band_entry = collection_index.get_band(band_name)
    if not band_entry:
        return True
    
    # Check folder modification time
    folder_mtime = datetime.fromtimestamp(band_folder.stat().st_mtime)
    if folder_mtime > last_scan_time:
        return True
    
    # Check metadata file modification time
    metadata_file = band_folder / '.band_metadata.json'
    if metadata_file.exists():
        metadata_mtime = datetime.fromtimestamp(metadata_file.stat().st_mtime)
        if metadata_mtime > last_scan_time:
            return True
    
    return False
```

## Performance Optimization

### Caching Strategy

```python
class AlbumCache:
    """Cache for album discovery results."""
    
    def __init__(self, cache_duration: timedelta = timedelta(hours=1)):
        self._cache: Dict[str, Tuple[List[Album], datetime]] = {}
        self._cache_duration = cache_duration
    
    def get_albums(self, band_path: Path) -> Optional[List[Album]]:
        """Get cached albums for band if still valid."""
        cache_key = str(band_path)
        
        if cache_key not in self._cache:
            return None
        
        albums, cache_time = self._cache[cache_key]
        
        # Check if cache is still valid
        if datetime.utcnow() - cache_time > self._cache_duration:
            del self._cache[cache_key]
            return None
        
        # Check if folder has been modified since caching
        folder_mtime = datetime.fromtimestamp(band_path.stat().st_mtime)
        if folder_mtime > cache_time:
            del self._cache[cache_key]
            return None
        
        return albums
    
    def cache_albums(self, band_path: Path, albums: List[Album]) -> None:
        """Cache albums for band."""
        cache_key = str(band_path)
        self._cache[cache_key] = (albums, datetime.utcnow())
```

### Parallel Processing

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def scan_bands_parallel(
    band_folders: List[Path], 
    max_workers: int = 4
) -> List[BandScanResult]:
    """Scan multiple bands in parallel."""
    
    loop = asyncio.get_event_loop()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Create tasks for each band
        tasks = [
            loop.run_in_executor(executor, scan_single_band, band_folder)
            for band_folder in band_folders
        ]
        
        # Wait for all scans to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return successful results
        return [
            result for result in results 
            if isinstance(result, BandScanResult)
        ]
```

## Error Handling and Recovery

### Common Error Scenarios

```python
class AlbumScanError(Exception):
    """Errors during album scanning operations."""
    pass

def scan_album_with_recovery(album_path: Path) -> Album:
    """Scan album with error recovery mechanisms."""
    try:
        return scan_album_folder(album_path)
        
    except PermissionError:
        # Handle permission errors gracefully
        logger.warning(f"Permission denied accessing {album_path}")
        return create_placeholder_album(album_path)
        
    except FileNotFoundError:
        # Handle disappeared folders
        logger.warning(f"Album folder disappeared: {album_path}")
        raise AlbumScanError(f"Album folder not found: {album_path}")
        
    except UnicodeDecodeError:
        # Handle encoding issues
        logger.warning(f"Encoding issues in album folder: {album_path}")
        return scan_album_with_fallback_encoding(album_path)
        
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error scanning {album_path}: {e}")
        raise AlbumScanError(f"Failed to scan album: {album_path}")

def create_placeholder_album(album_path: Path) -> Album:
    """Create placeholder album for inaccessible folders."""
    return Album(
        album_name=album_path.name,
        tracks_count=0,
        missing=False,
        folder_path=str(album_path),
        # Mark as inaccessible
        primary_format="UNKNOWN"
    )
```

## Integration with MCP Tools

### Tool Integration

The album handling system integrates with MCP tools:

```python
# In scan_music_folders tool
@app.tool()
def scan_music_folders(
    force_rescan: bool = False,
    force_full_scan: bool = False
) -> Dict[str, Any]:
    """MCP tool for scanning music collection."""
    
    config = get_config()
    scanner = MusicScanner(config)
    
    # Determine scan type
    if force_full_scan or force_rescan:
        result = scanner.perform_full_collection_scan()
    else:
        result = scanner.perform_incremental_scan()
    
    return {
        "success": result.success,
        "message": result.message,
        "stats": {
            "bands_scanned": result.bands_scanned,
            "albums_found": result.albums_found,
            "local_albums": result.albums_found - result.missing_albums,
            "missing_albums": result.missing_albums,
            "scan_duration": f"{result.scan_duration:.1f}s"
        }
    }

# In save_band_metadata tool
@app.tool()
def save_band_metadata(
    band_name: str,
    metadata: Dict[str, Any],
    preserve_analyze: bool = True
) -> Dict[str, Any]:
    """Save band metadata with album handling."""
    
    # Convert to BandMetadata model
    band_metadata = BandMetadata(**metadata)
    
    # Perform album reconciliation
    result = reconcile_albums_with_filesystem(band_name, band_metadata)
    
    # Save updated metadata
    save_result = storage.save_band_metadata(
        band_name, 
        result.reconciled_metadata,
        preserve_analyze=preserve_analyze
    )
    
    return save_result.to_dict()
```

This comprehensive album handling system provides robust support for complex music collections with both physical and missing albums, enabling intelligent collection management through the MCP interface. 