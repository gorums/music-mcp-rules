# Music Collection MCP Server - Architecture Guide with Album Type Classification

## Overview

The Music Collection MCP Server is built using a modular, file-system-based architecture that provides intelligent access to local music collections through the Model Context Protocol (MCP). This document details the system architecture, design patterns, and integration strategies, including the new album type classification and folder structure analysis features.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        MCP Client Layer                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Claude App    │  │   Cline Plugin  │  │  Custom Client  │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────────────────────┐
                    │      JSON-RPC over stdio   │
                    └─────────────────────────────┘
                                  │
┌─────────────────────────────────────────────────────────────────┐
│                    Music Collection MCP Server                  │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │      Tools      │  │    Resources    │  │     Prompts     │  │
│  │   (5 tools)     │  │  (2 resources)  │  │   (4 prompts)   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    Core Services                            │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │  │
│  │  │   Scanner   │  │   Storage   │  │       Cache         │  │  │
│  │  │   Service   │  │   Service   │  │      Service        │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                   Enhanced Data Models                      │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │  │
│  │  │    Band     │  │ Collection  │  │   Album Type &      │  │  │
│  │  │   Models    │  │   Models    │  │ Structure Models    │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘  │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │  │
│  │  │ Compliance  │  │   Parser    │  │     Validation      │  │  │
│  │  │   Models    │  │   Models    │  │      Models         │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────────────────────────────────────┐
│                      File System Layer                         │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                  Music Collection                           │  │
│  │                                                             │  │
│  │  Band Folder 1/                Band Folder 2/              │  │
│  │  ├── Album/                     ├── 1973 - Album Name/     │  │
│  │  │   └── 1979 - Album Name/     ├── Live/                  │  │
│  │  ├── Live/                      │   └── 1975 - Live Album/ │  │
│  │  │   └── 1980 - Live Album/     └── .band_metadata.json    │  │
│  │  └── .band_metadata.json                                   │  │
│  │                                                             │  │
│  │  .collection_index.json (with type & structure metadata)   │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. MCP Server Core (`src/music_mcp_server.py`)

The main server implementation using FastMCP framework with enhanced album type support:

#### Responsibilities
- **Server Initialization**: FastMCP server setup and configuration
- **Component Registration**: Tools, resources, and prompts registration with type-aware features
- **Request Routing**: JSON-RPC request handling and routing
- **Error Handling**: Centralized error handling and logging
- **Configuration Management**: Environment variable and settings handling
- **Type System Integration**: Album type classification and validation

#### Key Features
- **FastMCP Integration**: Modern MCP framework with automatic serialization
- **Type Safety**: Full Pydantic v2 integration for type validation including AlbumType enum
- **Concurrent Safety**: File locking and atomic operations
- **Resource Management**: Efficient memory and file handle management
- **Album Type Support**: Intelligent type detection and classification throughout the system

### 2. Enhanced Data Models (`src/models/`)

Pydantic v2-based data models providing type safety and validation with album type classification:

#### Band Models (`band.py`)
```python
# Album type enumeration
class AlbumType(str, Enum):
    ALBUM = "Album"
    COMPILATION = "Compilation"
    EP = "EP"
    LIVE = "Live"
    SINGLE = "Single"
    DEMO = "Demo"
    INSTRUMENTAL = "Instrumental"
    SPLIT = "Split"

# Enhanced album representation with type classification
class Album(BaseModel):
    album_name: str
    year: Optional[str] = None
    type: AlbumType = Field(default=AlbumType.ALBUM)
    edition: Optional[str] = Field(default="", max_length=100)
    genres: List[str] = []
    tracks_count: Optional[int] = None
    duration: Optional[str] = None
    missing: bool = False
    
    # File system information
    folder_path: Optional[str] = None
    file_size_mb: Optional[float] = None
    last_modified: Optional[str] = None
    
    # Audio format information
    primary_format: Optional[str] = None
    format_distribution: Optional[Dict[str, int]] = None
    
    # Compliance and organization
    compliance: Optional[AlbumCompliance] = None

# Album compliance information
class AlbumCompliance(BaseModel):
    score: int = Field(default=0, ge=0, le=100)
    level: str = Field(default="unknown")
    issues: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

# Complete band metadata with type distribution
class BandMetadata(BaseModel):
    band_name: str
    formed: Optional[str] = None
    genres: List[str] = []
    origin: Optional[str] = None
    members: List[str] = []
    albums_count: int = 0
    description: Optional[str] = None
    albums: List[Album] = []
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    analyze: Optional[BandAnalysis] = None
    
    # Album type distribution
    album_type_distribution: Optional[Dict[str, int]] = None
    structure_analysis: Optional[Dict[str, Any]] = None
```

#### Album Type and Structure Models (`album_parser.py`, `band_structure.py`)
```python
# Folder structure types
class StructureType(str, Enum):
    DEFAULT = "default"      # Flat structure: "YYYY - Album Name"
    ENHANCED = "enhanced"    # Type-based: "Type/YYYY - Album Name"
    MIXED = "mixed"          # Combination of both
    LEGACY = "legacy"        # No year prefix: "Album Name"
    UNKNOWN = "unknown"      # Unrecognized pattern

# Folder structure analysis
class FolderStructure(BaseModel):
    structure_type: StructureType
    compliance_score: int = Field(ge=0, le=100)
    compliance_level: str
    pattern_consistency: float = Field(ge=0.0, le=1.0)
    recommendations: List[str] = Field(default_factory=list)
    issues: List[str] = Field(default_factory=list)
    
    # Structure metadata
    total_albums: int = 0
    albums_by_pattern: Dict[str, int] = Field(default_factory=dict)
    type_folder_usage: Dict[str, int] = Field(default_factory=dict)
```

#### Collection Models (`collection.py`)
```python
# Enhanced collection index entry
class BandIndexEntry(BaseModel):
    band_name: str
    folder_path: str
    albums_count: int = 0
    local_albums: int = 0
    missing_albums: int = 0
    has_metadata: bool = False
    has_analysis: bool = False
    last_updated: str
    
    # Album type distribution
    album_type_distribution: Dict[str, int] = Field(default_factory=dict)
    
    # Structure analysis
    structure_analysis: Optional[Dict[str, Any]] = None

# Collection-wide statistics with type analysis
class CollectionStats(BaseModel):
    total_bands: int = 0
    total_albums: int = 0
    total_missing_albums: int = 0
    bands_with_metadata: int = 0
    bands_with_analysis: int = 0
    completion_percentage: float = 0.0
    
    # Album type distribution across collection
    album_type_distribution: Dict[str, int] = Field(default_factory=dict)
    
    # Structure analysis across collection
    structure_distribution: Dict[str, int] = Field(default_factory=dict)
    average_compliance_score: float = 0.0
    compliance_distribution: Dict[str, int] = Field(default_factory=dict)
```

### 3. Enhanced Scanner Service (`src/tools/scanner.py`)

File system scanner with album type detection and structure analysis:

#### Architecture Pattern: Observer + Strategy + Type Detection
```python
class MusicScanner:
    def __init__(self, config: Config):
        self.config = config
        self.file_filters = self._setup_filters()
        self.observers = []  # Progress observers
        self.type_detector = AlbumTypeDetector()
        self.structure_analyzer = FolderStructureAnalyzer()
    
    def scan_music_folders(self, 
                          force_rescan: bool = False,
                          detect_album_types: bool = True,
                          analyze_structure: bool = True) -> ScanResult:
        # Strategy pattern for different scan modes with type detection
        strategy = FullScanStrategy() if force_rescan else IncrementalScanStrategy()
        strategy.enable_type_detection = detect_album_types
        strategy.enable_structure_analysis = analyze_structure
        return strategy.execute(self)
    
    def _scan_band_folder(self, band_path: Path) -> BandScanResult:
        """Scan individual band folder with type detection and structure analysis."""
        # Analyze folder structure first
        structure_analysis = self.structure_analyzer.analyze_band_structure(band_path)
        
        albums = []
        for album_path in self._get_album_folders(band_path):
            # Create album with type detection
            album = self._create_album_from_folder(album_path, structure_analysis.structure_type)
            albums.append(album)
        
        return BandScanResult(
            band_name=band_path.name,
            albums=albums,
            structure_analysis=structure_analysis,
            album_type_distribution=self._calculate_type_distribution(albums)
        )
```

#### Key Features
- **Album Type Detection**: Automatic classification during scanning
- **Structure Analysis**: Real-time folder organization assessment
- **Incremental Scanning**: Only scan changed directories with type awareness
- **File Type Detection**: Support for 9+ music file formats
- **Progress Reporting**: Real-time scan progress with type statistics
- **Error Recovery**: Graceful handling of permission errors
- **Concurrent Safety**: File locking during scan operations

### 4. Enhanced Storage Service (`src/tools/storage.py`)

Atomic file operations with album type and compliance validation:

#### Architecture Pattern: Repository + Unit of Work + Type Validation
```python
class StorageService:
    def __init__(self, config: Config):
        self.config = config
        self.file_locks = {}  # Concurrent access control
        self.backup_manager = BackupManager()
        self.type_validator = AlbumTypeValidator()
        self.compliance_validator = ComplianceValidator()
    
    async def save_band_metadata(self, 
                                band_name: str, 
                                metadata: BandMetadata) -> SaveResult:
        async with self._get_lock(band_name):
            # Validate album types and compliance
            validation_result = self._validate_metadata_with_types(metadata)
            
            # Unit of work pattern with type-aware backup
            with self.backup_manager.create_backup(band_name):
                # Enhance metadata with type distribution and structure analysis
                enhanced_metadata = self._enhance_metadata_with_types(metadata)
                return await self._atomic_save(band_name, enhanced_metadata)
    
    def _validate_metadata_with_types(self, metadata: BandMetadata) -> ValidationResult:
        """Validate metadata including album types and compliance."""
        errors = []
        warnings = []
        
        for album in metadata.albums:
            # Validate album type
            if not self.type_validator.is_valid_type(album.type):
                errors.append(f"Invalid album type '{album.type}' for album '{album.album_name}'")
            
            # Validate compliance if present
            if album.compliance:
                compliance_validation = self.compliance_validator.validate(album)
                if compliance_validation.has_errors():
                    warnings.extend(compliance_validation.warnings)
        
        return ValidationResult(errors=errors, warnings=warnings)
```

#### Key Features
- **Type-Aware Operations**: All operations consider album types
- **Compliance Validation**: Automatic folder structure compliance checking
- **Atomic Operations**: All-or-nothing file writes with type preservation
- **Backup Management**: Automatic backup creation before modifications
- **File Locking**: Thread-safe concurrent access
- **Data Validation**: Pydantic integration with AlbumType validation
- **Error Recovery**: Rollback capabilities on failure

### 5. Album Type Detection System (`src/models/validation.py`)

Intelligent album type classification and validation:

#### Architecture Pattern: Strategy + Factory + Rule Engine
```python
class AlbumTypeDetector:
    """Intelligent album type detection using multiple strategies."""
    
    TYPE_KEYWORDS = {
        AlbumType.LIVE: ['live', 'concert', 'unplugged', 'acoustic'],
        AlbumType.COMPILATION: ['greatest hits', 'best of', 'collection'],
        AlbumType.EP: ['ep', 'e.p.'],
        AlbumType.DEMO: ['demo', 'demos', 'unreleased'],
        # ... more type keywords
    }
    
    @classmethod
    def detect_type_from_folder_name(cls, folder_name: str, album_name: str = "") -> AlbumType:
        """Multi-strategy type detection."""
        # Strategy 1: Keyword matching
        detected_type = cls._detect_from_keywords(folder_name, album_name)
        if detected_type != AlbumType.ALBUM:
            return detected_type
        
        # Strategy 2: Folder structure analysis
        detected_type = cls._detect_from_structure(folder_name)
        if detected_type != AlbumType.ALBUM:
            return detected_type
        
        # Strategy 3: Track count heuristics (if available)
        # Strategy 4: Metadata analysis (if available)
        
        return AlbumType.ALBUM
    
    @classmethod
    def detect_from_track_count(cls, track_count: int) -> AlbumType:
        """Heuristic type detection based on track count."""
        if track_count == 1:
            return AlbumType.SINGLE
        elif 2 <= track_count <= 7:
            return AlbumType.EP
        else:
            return AlbumType.ALBUM
```

### 6. Folder Structure Analysis System (`src/models/band_structure.py`)

Comprehensive folder organization analysis and compliance scoring:

#### Architecture Pattern: Analyzer + Scorer + Recommender
```python
class FolderStructureAnalyzer:
    """Analyzes band folder organization patterns and compliance."""
    
    def analyze_band_structure(self, band_path: Path) -> FolderStructure:
        """Comprehensive structure analysis."""
        albums = list(self._get_album_folders(band_path))
        
        # Detect structure type
        structure_type = self._detect_structure_type(albums)
        
        # Calculate compliance score
        compliance_score = self._calculate_compliance_score(albums, structure_type)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(albums, structure_type, compliance_score)
        
        return FolderStructure(
            structure_type=structure_type,
            compliance_score=compliance_score,
            compliance_level=self._get_compliance_level(compliance_score),
            recommendations=recommendations,
            total_albums=len(albums),
            albums_by_pattern=self._analyze_patterns(albums),
            type_folder_usage=self._analyze_type_folders(albums)
        )
    
    def _calculate_compliance_score(self, albums: List[Path], structure_type: StructureType) -> int:
        """Calculate compliance score based on structure consistency."""
        if not albums:
            return 0
        
        score = 100
        
        # Deduct points for inconsistencies
        for album_path in albums:
            # Check naming convention compliance
            if not self._follows_naming_convention(album_path, structure_type):
                score -= 10
            
            # Check type folder consistency (for enhanced structures)
            if structure_type == StructureType.ENHANCED:
                if not self._has_proper_type_folder(album_path):
                    score -= 15
        
        return max(0, score)
```

### 7. Cache Service with Type Awareness (`src/tools/cache.py`)

Intelligent caching with album type and structure metadata:

#### Architecture Pattern: Cache-Aside + TTL + Type-Aware Invalidation
```python
class CacheService:
    def __init__(self, config: Config):
        self.config = config
        self.memory_cache = {}  # In-memory cache
        self.file_cache = FileCacheManager()  # Persistent cache
        self.type_cache = AlbumTypeCache()  # Type-specific caching
    
    def get_band_metadata(self, band_name: str) -> Optional[BandMetadata]:
        """Get cached band metadata with type information."""
        cache_key = f"band_metadata:{band_name}"
        
        # Check memory cache first
        if cache_key in self.memory_cache:
            cached_data = self.memory_cache[cache_key]
            if self._is_cache_valid(cached_data):
                return cached_data['metadata']
        
        # Check file cache
        cached_metadata = self.file_cache.get(cache_key)
        if cached_metadata and self._is_metadata_current(cached_metadata):
            # Validate album types are still current
            if self._validate_cached_types(cached_metadata):
                self.memory_cache[cache_key] = {
                    'metadata': cached_metadata,
                    'timestamp': time.time()
                }
                return cached_metadata
        
        return None
    
    def invalidate_type_cache(self, album_type: AlbumType):
        """Invalidate cache entries for specific album type."""
        self.type_cache.invalidate_type(album_type)
```

## Data Flow Architecture

### 1. Album Type Detection Flow

```
File System Scan → Folder Name Analysis → Type Detection → Validation → Storage
                                      ↓
                   Track Count Analysis → Type Confirmation → Metadata Enhancement
                                      ↓
                   Structure Analysis → Compliance Scoring → Recommendations
```

### 2. Structure Analysis Flow

```
Band Folder → Album Folders Discovery → Pattern Analysis → Structure Type Detection
                                                        ↓
            Compliance Validation → Scoring → Issue Identification → Recommendations
                                                        ↓
            Type Folder Analysis → Distribution Calculation → Enhancement Suggestions
```

### 3. Enhanced Metadata Flow

```
Raw Metadata → Type Validation → Structure Analysis → Compliance Scoring
                              ↓
            Enhanced Metadata → Distribution Calculation → Storage → Index Update
                              ↓
            Cache Update → Resource Generation → Client Response
```

## Integration Patterns

### 1. Type-Aware Resource Generation

Resources now include album type information and structure analysis:

```python
class BandInfoResource:
    def generate_markdown(self, band_metadata: BandMetadata) -> str:
        """Generate markdown with album type organization."""
        sections = []
        
        # Band overview
        sections.append(self._generate_overview(band_metadata))
        
        # Album type distribution
        sections.append(self._generate_type_distribution(band_metadata))
        
        # Albums organized by type
        sections.append(self._generate_albums_by_type(band_metadata))
        
        # Structure analysis
        sections.append(self._generate_structure_analysis(band_metadata))
        
        return "\n\n".join(sections)
```

### 2. Type-Aware Filtering and Search

Enhanced filtering capabilities across all tools:

```python
class BandListFilter:
    def apply_filters(self, 
                     bands: List[BandIndexEntry],
                     album_types: List[AlbumType] = None,
                     compliance_levels: List[str] = None,
                     structure_types: List[StructureType] = None) -> List[BandIndexEntry]:
        """Apply type-aware filtering."""
        filtered_bands = bands
        
        if album_types:
            filtered_bands = [b for b in filtered_bands 
                            if self._has_album_types(b, album_types)]
        
        if compliance_levels:
            filtered_bands = [b for b in filtered_bands 
                            if self._meets_compliance(b, compliance_levels)]
        
        if structure_types:
            filtered_bands = [b for b in filtered_bands 
                            if self._has_structure_type(b, structure_types)]
        
        return filtered_bands
```

## Performance Considerations

### 1. Type Detection Optimization

- **Keyword Caching**: Pre-compiled regex patterns for type detection
- **Structure Memoization**: Cache structure analysis results
- **Incremental Updates**: Only re-analyze changed folders

### 2. Compliance Scoring Efficiency

- **Lazy Evaluation**: Calculate compliance scores only when needed
- **Batch Processing**: Analyze multiple albums in single pass
- **Score Caching**: Cache compliance scores with folder modification timestamps

### 3. Memory Management

- **Type Distribution Caching**: Cache album type distributions
- **Structure Analysis Pooling**: Reuse structure analysis objects
- **Selective Loading**: Load only required album type information

## Error Handling and Validation

### 1. Type Validation Errors

```python
class AlbumTypeValidationError(Exception):
    def __init__(self, album_name: str, invalid_type: str, valid_types: List[str]):
        self.album_name = album_name
        self.invalid_type = invalid_type
        self.valid_types = valid_types
        super().__init__(f"Invalid album type '{invalid_type}' for album '{album_name}'")
```

### 2. Structure Compliance Errors

```python
class StructureComplianceError(Exception):
    def __init__(self, band_name: str, compliance_score: int, issues: List[str]):
        self.band_name = band_name
        self.compliance_score = compliance_score
        self.issues = issues
        super().__init__(f"Low compliance score ({compliance_score}) for band '{band_name}'")
```

## Security and Validation

### 1. Input Validation

- **Album Type Validation**: Strict enum validation for album types
- **Structure Type Validation**: Validation of folder structure patterns
- **Compliance Score Validation**: Range validation for compliance scores

### 2. File System Security

- **Path Traversal Protection**: Prevent access outside music root
- **Type Folder Validation**: Validate type folder names against enum
- **Structure Consistency Checks**: Ensure folder structure integrity

## Deployment Architecture

### 1. Docker Integration with Type Support

```dockerfile
# Enhanced Dockerfile with type detection dependencies
FROM python:3.11-slim

# Install additional dependencies for type detection
RUN pip install pydantic[email] regex

# Copy enhanced models and type detection modules
COPY src/models/ /app/src/models/
COPY src/tools/ /app/src/tools/

# Set environment variables for type detection
ENV ENABLE_TYPE_DETECTION=true
ENV ENABLE_STRUCTURE_ANALYSIS=true
```

### 2. Configuration Management

```python
class EnhancedConfig:
    # Existing configuration
    MUSIC_ROOT_PATH: str
    CACHE_DURATION_DAYS: int
    
    # New type-related configuration
    ENABLE_TYPE_DETECTION: bool = True
    ENABLE_STRUCTURE_ANALYSIS: bool = True
    DEFAULT_ALBUM_TYPE: AlbumType = AlbumType.ALBUM
    COMPLIANCE_THRESHOLD: int = 70
    AUTO_MIGRATE_STRUCTURE: bool = False
```

## Future Architecture Considerations

### 1. Machine Learning Integration

- **Type Prediction Models**: ML models for better type detection
- **Structure Optimization**: AI-driven folder organization recommendations
- **Quality Assessment**: Automated quality scoring based on multiple factors

### 2. Distributed Processing

- **Parallel Type Detection**: Multi-threaded type detection for large collections
- **Distributed Structure Analysis**: Cluster-based structure analysis
- **Caching Strategies**: Distributed caching for type and structure information

### 3. API Evolution

- **GraphQL Integration**: Type-aware GraphQL schema for flexible queries
- **Real-time Updates**: WebSocket support for real-time type and structure updates
- **Plugin Architecture**: Extensible type detection and structure analysis plugins

---

## Version Information

- **Architecture Version**: 2.0.0
- **Album Type System**: 1.0.0
- **Folder Structure Analysis**: 1.0.0
- **Core MCP Framework**: 1.1.0
- **Last Updated**: 2025-01-30 