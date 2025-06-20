# Music Collection MCP Server - Architecture Guide

## Overview

The Music Collection MCP Server is built using a modular, dependency-injected architecture that provides intelligent access to local music collections through the Model Context Protocol (MCP). The system features advanced album type classification, folder structure analysis, and separated album schemas for optimal collection management.

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
│  │   (8 tools)     │  │  (3 resources)  │  │   (4 prompts)   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                 Modular Server Layer                       │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │  │
│  │  │   Base      │  │   Error     │  │    Dependency       │  │  │
│  │  │  Handlers   │  │  Handlers   │  │    Injection        │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    Core Services                            │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │  │
│  │  │   Scanner   │  │   Storage   │  │      Cache &        │  │  │
│  │  │   Service   │  │   Service   │  │   Performance       │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                Enhanced Data Models                         │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │  │
│  │  │    Band     │  │ Collection  │  │   Album Type &      │  │  │
│  │  │   Models    │  │   Models    │  │ Structure Models    │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘  │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │  │
│  │  │ Compliance  │  │   Parser    │  │     Validation      │  │  │
│  │  │   Models    │  │   Models    │  │ & Analytics Models  │  │  │
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
│  │  Band A/ (Enhanced Structure)    Band B/ (Default)         │  │
│  │  ├── Album/                      ├── 1973 - Album Name/    │  │
│  │  │   └── 1979 - Album Name/      ├── 1975 - Live Album/    │  │
│  │  ├── Live/                       └── .band_metadata.json   │  │
│  │  │   └── 1980 - Live Album/                                │  │
│  │  ├── Demo/                                                 │  │
│  │  │   └── 1977 - Early Demo/                               │  │
│  │  └── .band_metadata.json                                   │  │
│  │                                                             │  │
│  │  .collection_index.json (with separated schema)            │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Core Architecture Components

### 1. Modular Server Layer (`src/mcp/`)

The server uses a completely modular architecture with individual components:

#### Server Structure
```
src/mcp_server/
├── main.py                   # Server initialization and configuration
├── base_handlers.py          # Abstract base classes for all handlers
├── error_handlers.py         # Centralized error handling
├── tools/                    # Individual tool implementations
│   ├── scan_music_folders_tool.py
│   ├── get_band_list_tool.py
│   ├── save_band_metadata_tool.py
│   ├── advanced_search_albums_tool.py
│   └── ... (8 total tools)
├── resources/                # Individual resource implementations
│   ├── band_info_resource.py
│   ├── collection_summary_resource.py
│   └── advanced_analytics_resource.py
└── prompts/                  # Individual prompt implementations
    ├── fetch_band_info_prompt.py
    ├── analyze_band_prompt.py
    └── ... (4 total prompts)
```

#### Responsibilities
- **Modular Design**: Each tool, resource, and prompt in separate files (under 350 lines each)
- **Base Handler System**: Standardized error handling and response formatting
- **Dependency Injection**: Single configuration instance with testable architecture
- **Performance Monitoring**: Built-in performance tracking and optimization
- **Type Safety**: Full Pydantic v2 integration with album type classification

### 2. Enhanced Data Models (`src/models/`)

#### Separated Albums Schema
The system now uses separated arrays for optimal album management:

```python
class BandMetadata(BaseModel):
    band_name: str
    albums: List[Album] = []           # Local albums (found in folders)
    albums_missing: List[Album] = []   # Missing albums (known from metadata)
    
    # Computed properties
    @property
    def albums_count(self) -> int:
        return len(self.albums) + len(self.albums_missing)
    
    @property
    def local_albums_count(self) -> int:
        return len(self.albums)
        
    @property
    def missing_albums_count(self) -> int:
        return len(self.albums_missing)
```

#### Album Type Classification
```python
class AlbumType(str, Enum):
    ALBUM = "Album"                # Standard studio albums
    COMPILATION = "Compilation"    # Greatest hits, collections
    EP = "EP"                     # Extended plays
    LIVE = "Live"                 # Live recordings
    SINGLE = "Single"             # Single releases
    DEMO = "Demo"                 # Demo recordings
    INSTRUMENTAL = "Instrumental" # Instrumental versions
    SPLIT = "Split"               # Split releases

class Album(BaseModel):
    album_name: str
    year: Optional[str] = None
    type: AlbumType = Field(default=AlbumType.ALBUM)
    edition: Optional[str] = None
    folder_path: Optional[str] = None
    folder_compliance: Optional[FolderCompliance] = None
```

#### Folder Structure Models
```python
class StructureType(str, Enum):
    DEFAULT = "default"      # "YYYY - Album Name (Edition?)"
    ENHANCED = "enhanced"    # "Type/YYYY - Album Name (Edition?)"  
    MIXED = "mixed"          # Combination of both patterns
    LEGACY = "legacy"        # "Album Name" (no year)
    UNKNOWN = "unknown"      # Unrecognized pattern

class FolderStructure(BaseModel):
    structure_type: StructureType
    compliance_score: int = Field(ge=0, le=100)
    consistency_score: float = Field(ge=0.0, le=1.0)
    recommendations: List[str] = []
    analysis_metadata: Dict[str, Any] = {}
```

### 3. Core Services Layer

#### Scanner Service (`src/tools/scanner.py`)
- **Album Discovery**: Scans folders and populates only the `albums` array with local albums
- **Type Detection**: Automatically detects album types from folder names and keywords
- **Structure Analysis**: Analyzes folder organization patterns and compliance
- **Performance Optimized**: Uses `os.scandir()` for 20-30% faster directory scanning
- **Progress Reporting**: Automatic progress tracking for large collections (>50 bands)

#### Storage Service (`src/tools/storage.py`)
- **Separated Schema Handling**: Manages local vs missing albums in separate arrays
- **Metadata Integration**: Merges external metadata with local album data
- **Caching System**: In-memory cache with TTL and LRU eviction
- **Atomic Operations**: Ensures data consistency with file locking
- **Backward Compatibility**: Automatic migration from old schema format

#### Performance Service (`src/tools/performance.py`)
- **Batch File Operations**: Optimized file system operations
- **Performance Monitoring**: Comprehensive metrics tracking
- **Memory Management**: Reduced memory usage for large collections
- **Progress Tracking**: ETA calculations for long-running operations

### 4. Dependency Injection System (`src/di/`)

```python
# Thread-safe dependency container
class DependencyContainer:
    def __init__(self):
        self._dependencies = {}
        self._instances = {}
        self._lock = threading.RLock()
    
    def register(self, interface, implementation):
        # Register dependency factories
        
    def get(self, interface):
        # Get or create singleton instances

# Usage throughout the system
from src.di import get_config
config = get_config()  # Single instance across entire application
```

## Advanced Features

### 1. Album Type Classification System

#### Intelligent Type Detection
- **Keyword-based Classification**: Analyzes folder names for type indicators
- **Pattern Recognition**: Advanced regex-based parsing of album folder names
- **Fallback Logic**: Default to "Album" type when no specific indicators found
- **Confidence Scoring**: Multiple detection methods with confidence levels

#### Supported Patterns
```
# Default Structure Examples
1973 - The Dark Side of the Moon/
1979 - The Wall (Deluxe Edition)/
1988 - Delicate Sound of Thunder (Live)/
1983 - The Final Cut (Demo)/

# Enhanced Structure Examples
Album/1973 - The Dark Side of the Moon/
Live/1988 - Delicate Sound of Thunder/
Demo/1983 - The Final Cut/
Compilation/1971 - Relics/
```

### 2. Folder Structure Analysis

#### Structure Types Detection
- **Default**: Flat structure with "YYYY - Album Name (Edition?)" pattern
- **Enhanced**: Type-based folders with "Type/YYYY - Album Name (Edition?)" pattern
- **Mixed**: Combination of both patterns within same band
- **Legacy**: Albums without year prefix, just "Album Name" pattern

#### Compliance Scoring
- **Excellent** (90-100): All albums follow consistent naming pattern
- **Good** (70-89): Most albums follow pattern with minor issues
- **Fair** (50-69): Mixed patterns with some organization
- **Poor** (25-49): Inconsistent organization with multiple issues
- **Critical** (0-24): Little to no organization structure

### 3. Advanced Analytics (`src/models/analytics.py`)

#### Collection Analysis
```python
class CollectionAnalyzer:
    def analyze_collection(self) -> AdvancedCollectionInsights:
        # Comprehensive collection analysis
        
    def get_maturity_assessment(self) -> CollectionMaturityLevel:
        # Collection maturity scoring (Beginner to Master)
        
    def generate_recommendations(self) -> List[TypeRecommendation]:
        # Intelligent recommendations for collection improvement
```

#### Features
- **Maturity Assessment**: 5-level system (Beginner, Intermediate, Advanced, Expert, Master)
- **Health Scoring**: Multi-factor analysis including type diversity, organization quality
- **Type Distribution Analysis**: Compare actual vs ideal album type distributions
- **Discovery Recommendations**: Suggest missing album types and similar bands

## Integration Patterns

### 1. MCP Client Integration

#### Tool Registration Pattern
```python
# Individual tool files use shared server instance
from src.mcp.main import app

@app.tool()
async def scan_music_folders(
    force_rescan: bool = False,
    analyze_structure: bool = True,
    detect_album_types: bool = True
) -> ScanResult:
    # Tool implementation
```

#### Resource Pattern
```python
@app.resource("band://info/{band_name}")
async def get_band_info(band_name: str) -> str:
    # Resource implementation with type-organized display
```

### 2. Error Handling Pattern

#### Centralized Exception System
```python
# src/exceptions.py
class MusicMCPError(Exception):
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM):
        self.severity = severity
        super().__init__(message)

class StorageError(MusicMCPError):
    pass

class ScanningError(MusicMCPError):
    pass
```

#### Handler Integration
```python
# Base handler with standardized error handling
class BaseToolHandler(ABC):
    def handle_error(self, error: Exception) -> HandlerResponse:
        # Centralized error processing with context
```

### 3. Performance Optimization Patterns

#### Batch Operations
```python
class BatchFileOperations:
    def fast_scandir(self, path: Path) -> List[Path]:
        # 20-30% faster than pathlib.iterdir()
        return [entry.path for entry in os.scandir(path)]
        
    def count_files_optimized(self, directory: Path) -> int:
        # Optimized file counting for large directories
```

#### Caching Strategy
```python
class SimpleCache:
    def __init__(self, ttl_seconds: int = 300):
        self._cache = {}
        self._timestamps = {}
        self._ttl = ttl_seconds
        
    def get_with_ttl(self, key: str) -> Optional[Any]:
        # TTL-based cache with automatic expiration
```

## Data Flow Architecture

### 1. Scanning Workflow
```
User Request → scan_music_folders_tool
    ↓
Scanner Service (enhanced with type detection)
    ↓
Album Folder Parser (structure analysis)
    ↓
Band Structure Detector (compliance scoring)
    ↓
Update Collection Index (separated schema)
    ↓
Return Results (with type distribution)
```

### 2. Metadata Integration Workflow
```
External Metadata → save_band_metadata_tool
    ↓
Load Existing Metadata (with separated arrays)
    ↓
Separate Albums by Local Availability
    ↓
Merge with Local Album Data
    ↓
Update timestamps and collection index
    ↓
Return Status (with local/missing counts)
```

### 3. Analytics Workflow
```
Collection Data → analyze_collection_insights_tool
    ↓
Collection Analyzer (comprehensive analysis)
    ↓
Maturity Assessment (5-level scoring)
    ↓
Health Metrics (multi-factor scoring)
    ↓
Generate Recommendations (type-specific)
    ↓
Return Insights (with actionable suggestions)
```

## Quality Assurance Architecture

### 1. Testing Strategy
- **Unit Tests**: Individual component testing with 95%+ coverage
- **Integration Tests**: End-to-end workflow validation
- **Performance Tests**: Large collection testing (10,000+ albums)
- **Concurrent Tests**: Thread-safety validation
- **Error Handling Tests**: Exception recovery validation

### 2. Code Quality Standards
- **Function Size**: All functions under 50 lines following single responsibility
- **Type Safety**: Full type hints with Pydantic v2 validation
- **Error Handling**: Comprehensive exception hierarchy with context
- **Documentation**: Complete docstrings with Google style
- **Modularity**: Each component in separate file under 350 lines

### 3. Performance Standards
- **File System**: 20-30% improvement with optimized scanning
- **Memory Usage**: Reduced footprint through batch operations
- **Response Time**: <30 seconds for all operations
- **Concurrent Safety**: Thread-safe operations throughout
- **Progress Reporting**: Automatic progress for operations >50 items

## Future Extensibility

The modular architecture supports easy extension through:

1. **New Tool Addition**: Create individual tool file following base handler pattern
2. **Custom Album Types**: Extend AlbumType enum with new classifications
3. **Additional Structure Types**: Add new patterns to StructureType enum
4. **Enhanced Analytics**: Extend CollectionAnalyzer with new metrics
5. **Custom Compliance Rules**: Add validation rules to compliance system

The system is designed for continued growth while maintaining performance, reliability, and ease of use.