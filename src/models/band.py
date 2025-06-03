from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict, field_serializer
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
from enum import Enum
import re

# Import FolderStructure at the top to avoid circular imports - it will be defined later
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .band_structure import FolderStructure


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


class FolderCompliance(BaseModel):
    """
    Folder compliance tracking for individual albums.
    
    Attributes:
        has_year_prefix: True if folder name has year prefix (YYYY - )
        has_edition_suffix: True if edition is properly formatted in folder name
        using_type_folders: True if album is organized in type folders
        compliance_score: Numerical score (0-100) representing folder naming compliance
        issues: List of identified compliance issues
        recommended_path: Recommended folder path for optimal organization
        original_path: Original folder path as found
        needs_migration: True if folder should be migrated for better organization
    """
    has_year_prefix: bool = Field(default=False, description="Has year prefix in folder name")
    has_edition_suffix: bool = Field(default=False, description="Has proper edition suffix")
    using_type_folders: bool = Field(default=False, description="Uses type-based folder organization")
    compliance_score: int = Field(default=0, ge=0, le=100, description="Compliance score (0-100)")
    issues: List[str] = Field(default_factory=list, description="List of compliance issues")
    recommended_path: str = Field(default="", description="Recommended folder path")
    original_path: str = Field(default="", description="Original folder path")
    needs_migration: bool = Field(default=False, description="Whether migration is recommended")

    def get_compliance_level(self) -> str:
        """Get compliance level based on score."""
        if self.compliance_score >= 90:
            return "excellent"
        elif self.compliance_score >= 75:
            return "good"
        elif self.compliance_score >= 50:
            return "fair"
        elif self.compliance_score >= 25:
            return "poor"
        else:
            return "critical"

    def is_compliant(self) -> bool:
        """Check if folder is considered compliant (score >= 75)."""
        return self.compliance_score >= 75


class Album(BaseModel):
    """
    Enhanced album metadata model with type, edition, and track information.
    
    Attributes:
        album_name: Name of the album
        year: Year of album release (YYYY format)
        type: Type of album (Album, EP, Demo, Live, etc.)
        edition: Edition information (Deluxe, Limited, etc.)
        track_count: Number of tracks in the album
        missing: True if album is in metadata but not in local folders
        duration: Album duration in format "67min"
        genres: List of genres for this album
        folder_path: Original folder name/path for this album
    """
    album_name: str = Field(..., description="Name of the album")
    year: str = Field(default="", pattern=r"^\d{4}$|^$", description="Release year in YYYY format")
    type: AlbumType = Field(default=AlbumType.ALBUM, description="Type of album")
    edition: str = Field(default="", description="Edition information (Deluxe, Limited, etc.)")
    track_count: int = Field(default=0, ge=0, description="Number of tracks in album")
    missing: bool = Field(default=False, description="True if album not found in local folders")
    duration: str = Field(default="", description="Album duration (e.g., '67min')")
    genres: List[str] = Field(default_factory=list, description="List of album genres")
    folder_path: str = Field(default="", description="Original folder name/path")

    @field_serializer('type')
    def serialize_album_type(self, value: AlbumType) -> str:
        """Serialize AlbumType enum to string value."""
        return value.value

    @field_validator('type')
    @classmethod
    def validate_album_type(cls, v):
        """Validate album type is a valid AlbumType enum value."""
        if isinstance(v, str):
            try:
                return AlbumType(v)
            except ValueError:
                raise ValueError(f'Invalid album type: {v}. Must be one of: {[t.value for t in AlbumType]}')
        return v

    @field_validator('edition')
    @classmethod
    def validate_edition(cls, v):
        """Validate and normalize edition field."""
        if v:
            # Remove common parentheses patterns if they exist
            v = v.strip()
            if v.startswith('(') and v.endswith(')'):
                v = v[1:-1]
        return v

    def detect_type_from_name(self) -> AlbumType:
        """
        Detect album type from album name and folder path using keywords.
        
        Returns:
            Detected AlbumType based on name patterns
        """
        name_lower = self.album_name.lower()
        folder_lower = self.folder_path.lower()
        
        # Check for type indicators in name or folder
        type_keywords = {
            AlbumType.LIVE: ['live', 'concert', 'unplugged', 'acoustic'],
            AlbumType.COMPILATION: ['greatest hits', 'best of', 'collection', 'anthology', 'compilation'],
            AlbumType.EP: ['ep'],
            AlbumType.SINGLE: ['single'],
            AlbumType.DEMO: ['demo', 'demos', 'early recordings', 'unreleased'],
            AlbumType.INSTRUMENTAL: ['instrumental', 'instrumentals'],
            AlbumType.SPLIT: ['split', 'vs.', 'vs', 'versus']
        }
        
        for album_type, keywords in type_keywords.items():
            if any(keyword in name_lower or keyword in folder_lower for keyword in keywords):
                return album_type
        
        # Default to Album if no indicators found
        return AlbumType.ALBUM

    def detect_edition_from_folder(self) -> str:
        """
        Detect edition information from folder path.
        
        Returns:
            Detected edition string or empty string
        """
        folder_lower = self.folder_path.lower()
        
        # Look for content in parentheses that might be edition info
        parentheses_match = re.search(r'\(([^)]+)\)', self.folder_path)
        if parentheses_match:
            content = parentheses_match.group(1).strip()
            content_lower = content.lower()
            
            # Check if the parentheses content indicates an edition
            edition_indicators = [
                'deluxe edition', 'deluxe', 'limited edition', 'limited',
                'anniversary edition', 'remastered', 'remaster',
                'special edition', 'expanded edition', 'director\'s cut',
                'collector\'s edition', 'premium edition', 'ultimate edition',
                # Also include type indicators that can be editions when in parentheses
                'live', 'demo', 'instrumental', 'split'
            ]
            
            for indicator in edition_indicators:
                if indicator in content_lower:
                    # Return the original case content
                    return content
        
        return ""

    def auto_detect_metadata(self) -> None:
        """Auto-detect type and edition from name and folder path."""
        # Only auto-detect type if it's the default value and we have folder path
        if self.type == AlbumType.ALBUM and self.folder_path:
            detected_type = self.detect_type_from_name()
            if detected_type != AlbumType.ALBUM:
                self.type = detected_type
        
        # Only auto-detect edition if not already set and we have folder path
        if not self.edition and self.folder_path:
            self.edition = self.detect_edition_from_folder()


class AlbumAnalysis(BaseModel):
    """
    Analysis data for individual albums including review and rating.
    
    Attributes:
        album_name: Name of the album (required)
        review: Detailed review text for the album
        rate: Rating from 1-10 scale
    """
    album_name: str = Field(..., description="Name of the album")
    review: str = Field(default="", description="Album review text")
    rate: int = Field(default=0, ge=0, le=10, description="Album rating (1-10 scale)")

    @field_validator('rate')
    @classmethod
    def validate_rating(cls, v):
        """Validate rating is between 1-10, allow 0 for unrated."""
        if v < 0 or v > 10:
            raise ValueError('Rating must be between 0-10 (0 = unrated)')
        return v


class BandAnalysis(BaseModel):
    """
    Complete analysis data for a band including reviews, ratings, and similar bands.
    
    Attributes:
        review: Overall band review
        rate: Overall band rating (1-10 scale)
        albums: List of album analysis data
        similar_bands: List of similar band names
    """
    review: str = Field(default="", description="Overall band review")
    rate: int = Field(default=0, ge=0, le=10, description="Overall band rating (1-10 scale)")
    albums: List[AlbumAnalysis] = Field(default_factory=list, description="Album-specific analysis")
    similar_bands: List[str] = Field(default_factory=list, description="Names of similar bands")

    @field_validator('rate')
    @classmethod
    def validate_rating(cls, v):
        """Validate rating is between 1-10, allow 0 for unrated."""
        if v < 0 or v > 10:
            raise ValueError('Rating must be between 0-10 (0 = unrated)')
        return v


class BandMetadata(BaseModel):
    """
    Complete band metadata including basic information, albums, analysis, and folder structure.
    
    Attributes:
        band_name: Name of the band
        formed: Year band was formed (YYYY format)
        genres: List of band genres
        origin: Country/location of origin
        members: List of band member names
        albums_count: Total number of albums
        description: Band description/biography
        albums: List of album metadata
        last_updated: ISO datetime of last metadata update
        last_metadata_saved: ISO datetime when metadata was last saved via save_band_metadata_tool
        analyze: Optional analysis data with reviews and ratings
        folder_structure: Optional folder structure analysis data
    """
    band_name: str = Field(..., description="Band name")
    formed: str = Field(default="", pattern=r"^\d{4}$|^$", description="Formation year (YYYY)")
    genres: List[str] = Field(default_factory=list, description="Band genres")
    origin: str = Field(default="", description="Country/location of origin")
    members: List[str] = Field(default_factory=list, description="Band member names")
    albums_count: int = Field(default=0, ge=0, description="Total number of albums")
    description: str = Field(default="", description="Band description/biography")
    albums: List[Album] = Field(default_factory=list, description="Album metadata list")
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Last update timestamp")
    last_metadata_saved: Optional[str] = Field(default=None, description="Last metadata save timestamp via save_band_metadata_tool")
    analyze: Optional[BandAnalysis] = Field(default=None, description="Band analysis data")
    folder_structure: Optional['FolderStructure'] = Field(default=None, description="Folder structure analysis data")

    @model_validator(mode='before')
    @classmethod
    def sync_albums_count(cls, data):
        """Ensure albums_count matches length of albums list."""
        if isinstance(data, dict) and 'albums' in data:
            albums = data['albums']
            if isinstance(albums, list):
                data['albums_count'] = len(albums)
        return data

    @model_validator(mode='after')
    def validate_albums_count_post(self):
        """Ensure albums_count is always synced with albums list after creation."""
        self.albums_count = len(self.albums)
        return self

    def to_json(self) -> str:
        """
        Serialize band metadata to JSON string.
        
        Returns:
            JSON string representation of the metadata
        """
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'BandMetadata':
        """
        Deserialize band metadata from JSON string.
        
        Args:
            json_str: JSON string to deserialize
            
        Returns:
            BandMetadata instance
            
        Raises:
            ValueError: If JSON is invalid or validation fails
        """
        try:
            data = json.loads(json_str)
            return cls(**data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
        except Exception as e:
            raise ValueError(f"Failed to create BandMetadata: {e}")

    def get_missing_albums(self) -> List[Album]:
        """
        Get list of albums marked as missing.
        
        Returns:
            List of albums with missing=True
        """
        return [album for album in self.albums if album.missing]

    def get_local_albums(self) -> List[Album]:
        """
        Get list of albums present locally.
        
        Returns:
            List of albums with missing=False
        """
        return [album for album in self.albums if not album.missing]

    def update_timestamp(self) -> None:
        """Update the last_updated timestamp to current time."""
        self.last_updated = datetime.now().isoformat()

    def update_metadata_saved_timestamp(self) -> None:
        """Update the last_metadata_saved timestamp to current time."""
        self.last_metadata_saved = datetime.now().isoformat()
        self.update_timestamp()  # Also update the general timestamp

    def has_metadata_saved(self) -> bool:
        """Check if metadata has been saved via save_band_metadata_tool."""
        return self.last_metadata_saved is not None

    def add_album(self, album: Album) -> None:
        """
        Add an album to the band's album list and update count.
        
        Args:
            album: Album instance to add
        """
        self.albums.append(album)
        self.albums_count = len(self.albums)
        self.update_timestamp()

    def remove_album(self, album_name: str) -> bool:
        """
        Remove an album by name and update count.
        
        Args:
            album_name: Name of album to remove
            
        Returns:
            True if album was found and removed, False otherwise
        """
        for i, album in enumerate(self.albums):
            if album.album_name == album_name:
                del self.albums[i]
                self.albums_count = len(self.albums)
                self.update_timestamp()
                return True
        return False 