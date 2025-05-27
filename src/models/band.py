from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import List, Optional
from datetime import datetime
import json


class Album(BaseModel):
    """
    Album metadata model with track information and missing status.
    
    Attributes:
        album_name: Name of the album
        missing: True if album is in metadata but not in local folders
        tracks_count: Number of tracks in the album
        duration: Album duration in format "67min"
        year: Year of album release (YYYY format)
        genres: List of genres for this album
    """
    album_name: str = Field(..., description="Name of the album")
    missing: bool = Field(default=False, description="True if album not found in local folders")
    tracks_count: int = Field(default=0, ge=0, description="Number of tracks in album")
    duration: str = Field(default="", description="Album duration (e.g., '67min')")
    year: str = Field(default="", pattern=r"^\d{4}$|^$", description="Release year in YYYY format")
    genres: List[str] = Field(default_factory=list, description="List of album genres")

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class AlbumAnalysis(BaseModel):
    """
    Analysis data for individual albums including review and rating.
    
    Attributes:
        review: Detailed review text for the album
        rate: Rating from 1-10 scale
    """
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
    Complete band metadata including basic information, albums, and analysis.
    
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
        analyze: Optional analysis data with reviews and ratings
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
    analyze: Optional[BandAnalysis] = Field(default=None, description="Band analysis data")

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )

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