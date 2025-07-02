from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Dict, Optional, Any
from datetime import datetime
import json


class BandIndexEntry(BaseModel):
    """
    Index entry for a single band in the collection.
    
    Attributes:
        name: Band name
        albums_count: Total number of albums (local + missing)
        local_albums_count: Number of local albums found in folder structure
        folder_path: Relative path to band folder
        missing_albums_count: Number of albums marked as missing
        has_metadata: True if .band_metadata.json exists
        has_analysis: True if band has analysis data (review, rating, etc.)
        last_updated: ISO datetime of last metadata update
    """
    name: str = Field(..., description="Band name")
    albums_count: int = Field(default=0, ge=0, description="Total number of albums (local + missing)")
    local_albums_count: int = Field(default=0, ge=0, description="Number of local albums found in folder structure")
    folder_path: str = Field(..., description="Relative path to band folder")
    missing_albums_count: int = Field(default=0, ge=0, description="Number of missing albums")
    has_metadata: bool = Field(default=False, description="True if metadata file exists")
    has_analysis: bool = Field(default=False, description="True if band has analysis data")
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Last update timestamp")

    @model_validator(mode='after')
    def validate_album_counts(self):
        """Ensure album counts are consistent and valid."""
        # Ensure missing albums count doesn't exceed total albums count
        if self.missing_albums_count > self.albums_count:
            self.missing_albums_count = self.albums_count
        
        # Ensure local albums count doesn't exceed total albums count
        if self.local_albums_count > self.albums_count:
            self.local_albums_count = self.albums_count
        
        # Ensure local + missing equals total (adjust total if needed)
        calculated_total = self.local_albums_count + self.missing_albums_count
        if calculated_total != self.albums_count:
            self.albums_count = calculated_total
        
        return self


class CollectionStats(BaseModel):
    """
    Collection statistics and analytics with enhanced album type distribution.
    
    Attributes:
        total_bands: Total number of bands
        total_albums: Total number of albums (local + missing)
        total_local_albums: Total number of local albums found in folder structure
        total_missing_albums: Total missing albums across collection
        bands_with_metadata: Number of bands with metadata files
        top_genres: Most common genres in collection
        avg_albums_per_band: Average albums per band
        completion_percentage: Percentage of albums present locally
        album_type_distribution: Distribution of albums by type
        edition_distribution: Distribution of albums by edition
    """
    total_bands: int = Field(default=0, ge=0, description="Total number of bands")
    total_albums: int = Field(default=0, ge=0, description="Total number of albums (local + missing)")
    total_local_albums: int = Field(default=0, ge=0, description="Total number of local albums found in folder structure")
    total_missing_albums: int = Field(default=0, ge=0, description="Total missing albums")
    bands_with_metadata: int = Field(default=0, ge=0, description="Bands with metadata files")
    top_genres: Dict[str, int] = Field(default_factory=dict, description="Genre frequency map")
    avg_albums_per_band: float = Field(default=0.0, ge=0, description="Average albums per band")
    completion_percentage: float = Field(default=100.0, ge=0, le=100, description="Collection completion percentage")
    album_type_distribution: Dict[str, int] = Field(default_factory=dict, description="Album type frequency map")
    edition_distribution: Dict[str, int] = Field(default_factory=dict, description="Edition frequency map")

    @model_validator(mode='after')
    def calculate_completion_percentage(self):
        """Calculate completion percentage based on local albums vs total albums."""
        if self.total_albums == 0:
            self.completion_percentage = 100.0
        else:
            self.completion_percentage = round((self.total_local_albums / self.total_albums) * 100, 2)
        return self


class CollectionInsight(BaseModel):
    """
    Collection insights and recommendations.
    
    Attributes:
        insights: List of insight text descriptions
        recommendations: List of actionable recommendations
        top_rated_bands: List of highest rated bands
        suggested_purchases: Albums suggested for acquisition
        collection_health: Overall collection health status
        generated_at: Timestamp when insights were generated
    """
    insights: List[str] = Field(default_factory=list, description="Collection insights")
    recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations")
    top_rated_bands: List[str] = Field(default_factory=list, description="Highest rated bands")
    suggested_purchases: List[str] = Field(default_factory=list, description="Suggested albums to acquire")
    collection_health: str = Field(default="Good", description="Overall collection health")
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Generation timestamp")

    @field_validator('collection_health')
    @classmethod
    def validate_health_status(cls, v):
        """Validate collection health is one of allowed values."""
        allowed_statuses = ['Excellent', 'Good', 'Fair', 'Poor']
        if v not in allowed_statuses:
            raise ValueError(f'Health status must be one of: {allowed_statuses}')
        return v


class CollectionIndex(BaseModel):
    """
    Complete collection index with bands, statistics, and insights.
    
    Attributes:
        stats: Collection statistics
        bands: List of band index entries
        last_scan: ISO datetime of last collection scan
        insights: Collection insights and recommendations
        metadata_version: Schema version for migration support
    """
    stats: CollectionStats = Field(default_factory=CollectionStats, description="Collection statistics")
    bands: List[BandIndexEntry] = Field(default_factory=list, description="Band index entries")
    last_scan: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Last scan timestamp")
    insights: Optional[CollectionInsight] = Field(default=None, description="Collection insights")
    metadata_version: str = Field(default="1.0", description="Schema version")

    @model_validator(mode='after')
    def update_stats_on_creation(self):
        """Update statistics when bands are provided in constructor."""
        if self.bands:
            self._update_stats()
        return self

    def to_json(self) -> str:
        """
        Serialize collection index to JSON string.
        
        Returns:
            JSON string representation of the index
        """
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'CollectionIndex':
        """
        Deserialize collection index from JSON string.
        
        Args:
            json_str: JSON string to deserialize
            
        Returns:
            CollectionIndex instance
            
        Raises:
            ValueError: If JSON is invalid or validation fails
        """
        try:
            data = json.loads(json_str)
            return cls(**data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
        except Exception as e:
            raise ValueError(f"Failed to create CollectionIndex: {e}")

    def add_band(self, band_entry: BandIndexEntry) -> None:
        """
        Add a band to the index and update statistics.
        
        Args:
            band_entry: BandIndexEntry to add
        """
        # Remove existing entry if present
        self.bands = [b for b in self.bands if b.name != band_entry.name]
        
        # Add new entry
        self.bands.append(band_entry)
        
        # Update statistics
        self._update_stats()
        self.last_scan = datetime.now().isoformat()

    def remove_band(self, band_name: str) -> bool:
        """
        Remove a band from the index and update statistics.
        
        Args:
            band_name: Name of band to remove
            
        Returns:
            True if band was found and removed, False otherwise
        """
        initial_count = len(self.bands)
        self.bands = [b for b in self.bands if b.name != band_name]
        
        if len(self.bands) < initial_count:
            self._update_stats()
            self.last_scan = datetime.now().isoformat()
            return True
        
        return False

    def get_band(self, band_name: str) -> Optional[BandIndexEntry]:
        """
        Get band entry by name.
        
        Args:
            band_name: Name of band to find
            
        Returns:
            BandIndexEntry if found, None otherwise
        """
        for band in self.bands:
            if band.name == band_name:
                return band
        return None

    def get_bands_without_metadata(self) -> List[BandIndexEntry]:
        """
        Get list of bands that don't have metadata files.
        
        Returns:
            List of bands with has_metadata=False
        """
        return [band for band in self.bands if not band.has_metadata]

    def get_bands_with_missing_albums(self) -> List[BandIndexEntry]:
        """
        Get list of bands that have missing albums.
        
        Returns:
            List of bands with missing_albums_count > 0
        """
        return [band for band in self.bands if band.missing_albums_count > 0]

    def _update_stats(self) -> None:
        """Update collection statistics based on current bands."""
        self.stats.total_bands = len(self.bands)
        self.stats.total_albums = sum(band.albums_count for band in self.bands)
        self.stats.total_local_albums = sum(band.local_albums_count for band in self.bands)
        self.stats.total_missing_albums = sum(band.missing_albums_count for band in self.bands)
        self.stats.bands_with_metadata = sum(1 for band in self.bands if band.has_metadata)
        
        # Calculate average albums per band
        if self.stats.total_bands > 0:
            self.stats.avg_albums_per_band = round(self.stats.total_albums / self.stats.total_bands, 2)
        else:
            self.stats.avg_albums_per_band = 0.0
        
        # Calculate completion percentage based on local albums vs total albums
        if self.stats.total_albums == 0:
            self.stats.completion_percentage = 100.0
        else:
            self.stats.completion_percentage = round((self.stats.total_local_albums / self.stats.total_albums) * 100, 2)

    def update_insights(self, insights: CollectionInsight) -> None:
        """
        Update collection insights.
        
        Args:
            insights: New insights to store
        """
        self.insights = insights

    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics as dictionary.
        
        Returns:
            Dictionary of key statistics
        """
        return {
            "total_bands": self.stats.total_bands,
            "total_albums": self.stats.total_albums,
            "total_missing_albums": self.stats.total_missing_albums,
            "bands_with_metadata": self.stats.bands_with_metadata,
            "avg_albums_per_band": self.stats.avg_albums_per_band,
            "completion_percentage": self.stats.completion_percentage,
            "last_scan": self.last_scan
        } 