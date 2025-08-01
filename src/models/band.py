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


class Album(BaseModel):
    """
    Enhanced album metadata model with type, edition, track information, and image gallery.
    
    Attributes:
        album_name: Name of the album
        year: Year of album release (YYYY format)
        type: Type of album (Album, EP, Demo, Live, etc.)
        edition: Edition information (Deluxe, Limited, etc.)
        track_count: Number of tracks in the album
        duration: Album duration in format "67min"
        genres: List of genres for this album
        folder_path: Original folder name/path for this album
        track_count_missing: Number of missing tracks (if local album has fewer than expected)
        not_found: True if album is not found locally
        gallery: List of image paths (relative to album folder) found in the album folder
    """
    album_name: str = Field(..., description="Name of the album")
    year: str = Field(default="", pattern=r"^\d{4}$|^$", description="Release year in YYYY format")
    type: AlbumType = Field(default=AlbumType.ALBUM, description="Type of album")
    edition: str = Field(default="", description="Edition information (Deluxe, Limited, etc.)")
    track_count: int = Field(default=0, ge=0, description="Number of tracks in album")
    duration: str = Field(default="", description="Album duration (e.g., '67min')")
    genres: List[str] = Field(default_factory=list, description="List of album genres")
    folder_path: str = Field(default="", description="Original folder name/path for this album")
    track_count_missing: Optional[int] = Field(default=None, description="Number of missing tracks (if local album has fewer than expected)")
    not_found: bool = Field(default=False, description="True if album is not found locally")
    gallery: List[str] = Field(default_factory=list, description="List of image paths (relative to album folder) found in the album folder")

    @field_serializer('type')
    def serialize_album_type(self, value: AlbumType) -> str:
        """Serialize AlbumType enum to string value."""
        return value.value

    def model_dump(self, **kwargs):
        """
        Custom model dump that excludes edition field for standard/regular releases.
        
        Only includes the edition field when the album IS an edition (Deluxe, Limited, etc.).
        Removes the field when the album is NOT an edition (standard/regular release).
        """
        data = super().model_dump(**kwargs)
        # Remove edition field if it's empty or None (meaning this is NOT an edition)
        if 'edition' in data and (not data['edition'] or data['edition'].strip() == ""):
            del data['edition']
        # Remove folder_path field if it's empty or None
        if 'folder_path' in data and (not data['folder_path'] or data['folder_path'].strip() == ""):
            del data['folder_path']
        # Remove track_count_missing field if it's empty or None
        if 'track_count_missing' in data and (not data['track_count_missing'] or data['track_count_missing'] == None):
            del data['track_count_missing']
        # Remove not_found field if it's True
        if 'not_found' in data and data['not_found'] == False:
            del data['not_found']
        if 'gallery' in data and (not data['gallery'] or data['gallery'] == []):
            del data['gallery']
        return data

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
        similar_bands: List of similar band names that exist in the local collection
        similar_bands_missing: List of similar band names not in the local collection
    """
    review: str = Field(default="", description="Overall band review")
    rate: int = Field(default=0, ge=0, le=10, description="Overall band rating (1-10 scale)")
    albums: List[AlbumAnalysis] = Field(default_factory=list, description="Album-specific analysis")
    similar_bands: List[str] = Field(default_factory=list, description="Names of similar bands in the local collection")
    similar_bands_missing: List[str] = Field(default_factory=list, description="Names of similar bands not in the local collection")

    @field_validator('rate')
    @classmethod
    def validate_rating(cls, v):
        """Validate rating is between 1-10, allow 0 for unrated."""
        if v < 0 or v > 10:
            raise ValueError('Rating must be between 0-10 (0 = unrated)')
        return v

    @model_validator(mode='after')
    def validate_no_duplicate_similar_bands(self):
        """Ensure no band exists in both similar_bands and similar_bands_missing arrays."""
        local = {b.lower() for b in self.similar_bands}
        missing = {b.lower() for b in self.similar_bands_missing}
        duplicates = local.intersection(missing)
        if duplicates:
            raise ValueError(f"Bands cannot exist in both similar_bands and similar_bands_missing: {', '.join(duplicates)}")
        return self

    @property
    def all_similar_bands(self) -> List[str]:
        """Return all similar bands (in collection and missing)."""
        return self.similar_bands + self.similar_bands_missing

    @property
    def total_similar_bands_count(self) -> int:
        """Return the total number of similar bands (in collection + missing)."""
        return len(self.similar_bands) + len(self.similar_bands_missing)


class BandMetadata(BaseModel):
    """
    Complete band metadata including basic information, albums, analysis, folder structure, and image gallery.
    
    Attributes:
        band_name: Name of the band
        formed: Year band was formed (YYYY format)
        genres: List of band genres
        origin: Country/location of origin
        members: List of band member names
        albums_count: Total number of albums (local + missing)
        description: Band description/biography
        albums: List of local album metadata (found in folder structure)
        albums_missing: List of missing album metadata (not found locally but known from metadata)
        last_updated: ISO datetime of last metadata update
        last_metadata_saved: ISO datetime when metadata was last saved via save_band_metadata_tool
        analyze: Optional analysis data with reviews and ratings
        folder_structure: Optional folder structure analysis data
        gallery: List of image paths (relative to band folder) found in the band folder
    """
    band_name: str = Field(..., description="Band name")
    formed: str = Field(default="", pattern=r"^\d{4}$|^$", description="Formation year (YYYY)")
    genres: List[str] = Field(default_factory=list, description="Band genres")
    origin: str = Field(default="", description="Country/location of origin")
    members: List[str] = Field(default_factory=list, description="Band member names")
    albums_count: int = Field(default=0, ge=0, description="Total number of albums (local + missing)")
    description: str = Field(default="", description="Band description/biography")
    albums: List[Album] = Field(default_factory=list, description="Local album metadata list (found in folder structure)")
    albums_missing: List[Album] = Field(default_factory=list, description="Missing album metadata list (not found locally)")
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Last update timestamp")
    last_metadata_saved: Optional[str] = Field(default=None, description="Last metadata save timestamp via save_band_metadata_tool")
    analyze: Optional[BandAnalysis] = Field(default=None, description="Band analysis data")
    folder_structure: Optional['FolderStructure'] = Field(default=None, description="Folder structure analysis data")
    gallery: List[str] = Field(default_factory=list, description="List of image paths (relative to band folder) found in the band folder")

    @model_validator(mode='before')
    @classmethod
    def sync_albums_count(cls, data):
        """Ensure albums_count matches total length of albums + albums_missing lists."""
        if isinstance(data, dict):
            albums = data.get('albums', [])
            albums_missing = data.get('albums_missing', [])
            if isinstance(albums, list) and isinstance(albums_missing, list):
                data['albums_count'] = len(albums) + len(albums_missing)
        return data

    @model_validator(mode='after')
    def validate_albums_count_post(self):
        """Ensure albums_count is always synced with total albums after creation."""
        self.albums_count = len(self.albums) + len(self.albums_missing)
        return self

    @model_validator(mode='after')
    def validate_no_duplicate_albums(self):
        """Ensure no album exists in both albums and albums_missing arrays."""
        local_names = {album.album_name.lower() for album in self.albums}
        missing_names = {album.album_name.lower() for album in self.albums_missing}
        duplicates = local_names.intersection(missing_names)
        if duplicates:
            raise ValueError(f"Albums cannot exist in both local and missing arrays: {', '.join(duplicates)}")
        return self

    def model_dump(self, **kwargs):
        """
        Custom model dump that properly handles Album serialization.
        
        Ensures that empty edition fields are excluded from Album objects
        when serializing the BandMetadata to JSON.
        """
        data = super().model_dump(**kwargs)
        
        # Process albums array to remove empty edition fields
        if 'albums' in data and data['albums']:
            processed_albums = []
            for album_data in data['albums']:
                # Remove edition field if it's empty
                if 'edition' in album_data and (not album_data['edition'] or album_data['edition'].strip() == ""):
                    del album_data['edition']
                if 'track_count_missing' in album_data and (not album_data['track_count_missing'] or album_data['track_count_missing'] == None):
                    del album_data['track_count_missing']
                if 'not_found' in album_data and album_data['not_found'] == False:
                    del album_data['not_found']
                if 'gallery' in album_data and (not album_data['gallery'] or album_data['gallery'] == []):
                    del album_data['gallery']
                processed_albums.append(album_data)
            data['albums'] = processed_albums
        
        # Process albums_missing array to remove empty edition fields
        if 'albums_missing' in data and data['albums_missing']:
            processed_missing = []
            for album_data in data['albums_missing']:
                # Remove edition field if it's empty
                if 'edition' in album_data and (not album_data['edition'] or album_data['edition'].strip() == ""):
                    del album_data['edition']
                if 'folder_path' in album_data and (not album_data['folder_path'] or album_data['folder_path'].strip() == ""):
                    del album_data['folder_path']
                if 'track_count_missing' in album_data and (not album_data['track_count_missing'] or album_data['track_count_missing'] == None):
                    del album_data['track_count_missing']
                if 'not_found' in album_data and album_data['not_found'] == False:
                    del album_data['not_found']
                if 'gallery' in album_data and (not album_data['gallery'] or album_data['gallery'] == []):
                    del album_data['gallery']
                processed_missing.append(album_data)
            data['albums_missing'] = processed_missing
        
        return data

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
        Deserialize band metadata from JSON string with backward compatibility.
        
        Args:
            json_str: JSON string to deserialize
            
        Returns:
            BandMetadata instance
            
        Raises:
            ValueError: If JSON is invalid or validation fails
        """
        try:
            data = json.loads(json_str)
            
            # Handle backward compatibility for old schema with missing field
            if 'albums' in data and 'albums_missing' not in data:
                albums = data.get('albums', [])
                local_albums = []
                missing_albums = []
                
                for album_data in albums:
                    # Create a copy to avoid modifying original data
                    album_copy = album_data.copy()
                    
                    # Check if this album has the old 'missing' field
                    is_missing = album_copy.pop('missing', False)
                    
                    if is_missing:
                        missing_albums.append(album_copy)
                    else:
                        local_albums.append(album_copy)
                
                # Update data with separated arrays
                data['albums'] = local_albums
                data['albums_missing'] = missing_albums
            
            return cls(**data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
        except Exception as e:
            raise ValueError(f"Failed to create BandMetadata: {e}")

    def get_missing_albums(self) -> List[Album]:
        """
        Get list of albums marked as missing.
        
        Returns:
            List of albums from albums_missing array
        """
        return list(self.albums_missing)

    def get_local_albums(self) -> List[Album]:
        """
        Get list of albums present locally.
        
        Returns:
            List of albums from albums array (local albums)
        """
        return list(self.albums)

    @property
    def local_albums_count(self) -> int:
        """
        Get count of local albums (found in folder structure).
        
        Returns:
            Number of albums in the albums array
        """
        return len(self.albums)

    @property
    def missing_albums_count(self) -> int:
        """
        Get count of missing albums (not found locally).
        
        Returns:
            Number of albums in the albums_missing array
        """
        return len(self.albums_missing)

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

    def add_album(self, album: Album, is_local: bool = True) -> None:
        """
        Add an album to the appropriate array based on availability.
        
        Args:
            album: Album instance to add
            is_local: True to add to local albums, False to add to missing albums
        """
        # Remove from the other array if it exists there
        self.remove_album(album.album_name)
        
        if is_local:
            self.albums.append(album)
        else:
            self.albums_missing.append(album)
        
        self.albums_count = len(self.albums) + len(self.albums_missing)
        self.update_timestamp()

    def add_local_album(self, album: Album) -> None:
        """
        Add an album to the local albums array.
        
        Args:
            album: Album instance to add to local albums
        """
        self.add_album(album, is_local=True)

    def add_missing_album(self, album: Album) -> None:
        """
        Add an album to the missing albums array.
        
        Args:
            album: Album instance to add to missing albums
        """
        self.add_album(album, is_local=False)

    def remove_album(self, album_name: str) -> bool:
        """
        Remove an album by name from both local and missing arrays.
        
        Args:
            album_name: Name of album to remove
            
        Returns:
            True if album was found and removed, False otherwise
        """
        removed = False
        
        # Remove from local albums
        for i, album in enumerate(self.albums):
            if album.album_name == album_name:
                del self.albums[i]
                removed = True
                break
        
        # Remove from missing albums
        for i, album in enumerate(self.albums_missing):
            if album.album_name == album_name:
                del self.albums_missing[i]
                removed = True
                break
        
        if removed:
            self.albums_count = len(self.albums) + len(self.albums_missing)
            self.update_timestamp()
        
        return removed

    def move_album_to_local(self, album_name: str) -> bool:
        """
        Move an album from missing to local array.
        
        Args:
            album_name: Name of album to move
            
        Returns:
            True if album was found and moved, False otherwise
        """
        for i, album in enumerate(self.albums_missing):
            if album.album_name == album_name:
                moved_album = self.albums_missing.pop(i)
                self.albums.append(moved_album)
                self.update_timestamp()
                return True
        return False

    def move_album_to_missing(self, album_name: str) -> bool:
        """
        Move an album from local to missing array.
        
        Args:
            album_name: Name of album to move
            
        Returns:
            True if album was found and moved, False otherwise
        """
        for i, album in enumerate(self.albums):
            if album.album_name == album_name:
                moved_album = self.albums.pop(i)
                self.albums_missing.append(moved_album)
                self.update_timestamp()
                return True
        return False 