"""
Unit tests for collection data models.
Tests the BandIndexEntry, CollectionStats, CollectionInsight, and CollectionIndex Pydantic models.
"""

import pytest
import json
from datetime import datetime
from pydantic import ValidationError

from src.models.collection import (
    BandIndexEntry, 
    CollectionStats, 
    CollectionInsight, 
    CollectionIndex
)


class TestBandIndexEntry:
    """Test cases for BandIndexEntry model."""
    
    def test_band_index_entry_creation(self):
        """Test band index entry creation with required fields."""
        entry = BandIndexEntry(
            name="Test Band",
            folder_path="Test Band"
        )
        
        assert entry.name == "Test Band"
        assert entry.albums_count == 0
        assert entry.folder_path == "Test Band"
        assert entry.missing_albums_count == 0
        assert entry.has_metadata is False
        assert entry.last_updated != ""
    
    def test_band_index_entry_complete(self):
        """Test band index entry with all fields."""
        entry = BandIndexEntry(
            name="Test Band",
            albums_count=5,
            local_albums_count=3,
            folder_path="Test Band",
            missing_albums_count=2,
            has_metadata=True
        )
        
        assert entry.name == "Test Band"
        assert entry.albums_count == 5
        assert entry.local_albums_count == 3
        assert entry.missing_albums_count == 2
        assert entry.has_metadata is True
    
    def test_missing_albums_count_validation(self):
        """Test missing albums count is auto-corrected if it exceeds total albums."""
        # Create entry with missing_albums_count > albums_count
        entry = BandIndexEntry(
            name="Test Band",
            folder_path="Test Band",
            albums_count=3,
            missing_albums_count=5  # More than total
        )
        
        # Should auto-correct to match albums_count
        assert entry.missing_albums_count == 3
    
    def test_negative_albums_count(self):
        """Test albums count cannot be negative."""
        with pytest.raises(ValidationError):
            BandIndexEntry(
                name="Test Band",
                folder_path="Test Band",
                albums_count=-1
            )


class TestCollectionStats:
    """Test cases for CollectionStats model."""
    
    def test_collection_stats_default(self):
        """Test collection stats with default values."""
        stats = CollectionStats()
        
        assert stats.total_bands == 0
        assert stats.total_albums == 0
        assert stats.total_missing_albums == 0
        assert stats.bands_with_metadata == 0
        assert stats.top_genres == {}
        assert stats.avg_albums_per_band == 0.0
        assert stats.completion_percentage == 100.0
    
    def test_collection_stats_with_data(self):
        """Test collection stats with actual data."""
        stats = CollectionStats(
            total_bands=10,
            total_albums=50,
            total_local_albums=45,
            total_missing_albums=5,
            bands_with_metadata=8,
            top_genres={"Rock": 15, "Pop": 10},
            avg_albums_per_band=5.0
        )
        
        assert stats.total_bands == 10
        assert stats.total_albums == 50
        assert stats.total_local_albums == 45
        assert stats.total_missing_albums == 5
        assert stats.bands_with_metadata == 8
        assert stats.top_genres == {"Rock": 15, "Pop": 10}
        assert stats.avg_albums_per_band == 5.0
        # completion_percentage should be calculated automatically
        assert stats.completion_percentage == 90.0  # 45/50 * 100
    
    def test_completion_percentage_calculation(self):
        """Test completion percentage calculation."""
        # 100% completion (all albums local)
        stats = CollectionStats(total_albums=10, total_local_albums=10, total_missing_albums=0)
        assert stats.completion_percentage == 100.0
        
        # 50% completion
        stats = CollectionStats(total_albums=10, total_local_albums=5, total_missing_albums=5)
        assert stats.completion_percentage == 50.0
        
        # 0 albums case
        stats = CollectionStats(total_albums=0, total_local_albums=0, total_missing_albums=0)
        assert stats.completion_percentage == 100.0
    
    def test_completion_percentage_validation(self):
        """Test completion percentage is within valid range."""
        with pytest.raises(ValidationError):
            CollectionStats(completion_percentage=-10.0)
        
        with pytest.raises(ValidationError):
            CollectionStats(completion_percentage=110.0)


class TestCollectionInsight:
    """Test cases for CollectionInsight model."""
    
    def test_collection_insight_default(self):
        """Test collection insight with default values."""
        insight = CollectionInsight()
        
        assert insight.insights == []
        assert insight.recommendations == []
        assert insight.top_rated_bands == []
        assert insight.suggested_purchases == []
        assert insight.collection_health == "Good"
        assert insight.generated_at != ""
    
    def test_collection_insight_with_data(self):
        """Test collection insight with actual data."""
        insight = CollectionInsight(
            insights=["Your collection spans 5 genres", "Most albums from 1990s"],
            recommendations=["Consider adding more jazz albums"],
            top_rated_bands=["Band A", "Band B"],
            suggested_purchases=["Album X", "Album Y"],
            collection_health="Excellent"
        )
        
        assert len(insight.insights) == 2
        assert insight.recommendations[0] == "Consider adding more jazz albums"
        assert insight.top_rated_bands == ["Band A", "Band B"]
        assert insight.collection_health == "Excellent"
    
    def test_collection_health_validation(self):
        """Test collection health status validation."""
        valid_statuses = ['Excellent', 'Good', 'Fair', 'Poor']
        
        for status in valid_statuses:
            insight = CollectionInsight(collection_health=status)
            assert insight.collection_health == status
        
        with pytest.raises(ValidationError):
            CollectionInsight(collection_health="Invalid Status")


class TestCollectionIndex:
    """Test cases for CollectionIndex model."""
    
    def test_collection_index_default(self):
        """Test collection index with default values."""
        index = CollectionIndex()
        
        assert isinstance(index.stats, CollectionStats)
        assert index.bands == []
        assert index.last_scan != ""
        assert index.insights is None
        assert index.metadata_version == "1.0"
    
    def test_collection_index_with_bands(self):
        """Test collection index with band entries."""
        band1 = BandIndexEntry(name="Band 1", folder_path="Band 1", albums_count=3, local_albums_count=3)
        band2 = BandIndexEntry(name="Band 2", folder_path="Band 2", albums_count=5, local_albums_count=5)
        
        index = CollectionIndex(bands=[band1, band2])
        
        assert len(index.bands) == 2
        assert index.bands[0].name == "Band 1"
        assert index.bands[1].name == "Band 2"
    
    def test_to_json_serialization(self):
        """Test JSON serialization of collection index."""
        band1 = BandIndexEntry(name="Band 1", folder_path="Band 1")
        index = CollectionIndex(bands=[band1])
        
        json_str = index.to_json()
        assert isinstance(json_str, str)
        
        # Verify it's valid JSON
        parsed = json.loads(json_str)
        assert "stats" in parsed
        assert "bands" in parsed
        assert len(parsed["bands"]) == 1
        assert parsed["bands"][0]["name"] == "Band 1"
    
    def test_from_json_deserialization(self):
        """Test JSON deserialization of collection index."""
        json_data = {
            "stats": {
                "total_bands": 1,
                "total_albums": 3,
                "total_local_albums": 3
            },
            "bands": [
                {
                    "name": "Test Band",
                    "albums_count": 3,
                    "local_albums_count": 3,
                    "folder_path": "Test Band"
                }
            ]
        }
        
        index = CollectionIndex.from_json(json.dumps(json_data))
        
        assert index.stats.total_bands == 1
        assert index.stats.total_albums == 3
        assert index.stats.total_local_albums == 3
        assert len(index.bands) == 1
        assert index.bands[0].name == "Test Band"
    
    def test_from_json_invalid_data(self):
        """Test deserialization with invalid JSON raises ValueError."""
        with pytest.raises(ValueError, match="Invalid JSON format"):
            CollectionIndex.from_json("invalid json")
    
    def test_add_band(self):
        """Test adding a band to the index."""
        index = CollectionIndex()
        band = BandIndexEntry(name="New Band", folder_path="New Band", albums_count=5, local_albums_count=5)
        
        index.add_band(band)
        
        assert len(index.bands) == 1
        assert index.bands[0].name == "New Band"
        assert index.stats.total_bands == 1
        assert index.stats.total_albums == 5
    
    def test_add_band_replace_existing(self):
        """Test adding a band replaces existing entry with same name."""
        band1 = BandIndexEntry(name="Band", folder_path="Band", albums_count=3, local_albums_count=3)
        band2 = BandIndexEntry(name="Band", folder_path="Band", albums_count=5, local_albums_count=5)
        
        index = CollectionIndex(bands=[band1])
        index.add_band(band2)
        
        assert len(index.bands) == 1
        assert index.bands[0].albums_count == 5  # Updated value
    
    def test_remove_band_success(self):
        """Test successful band removal."""
        band = BandIndexEntry(name="Band to Remove", folder_path="Band to Remove")
        index = CollectionIndex(bands=[band])
        
        result = index.remove_band("Band to Remove")
        
        assert result is True
        assert len(index.bands) == 0
        assert index.stats.total_bands == 0
    
    def test_remove_band_not_found(self):
        """Test band removal when band doesn't exist."""
        band = BandIndexEntry(name="Existing Band", folder_path="Existing Band")
        index = CollectionIndex(bands=[band])
        
        result = index.remove_band("Nonexistent Band")
        
        assert result is False
        assert len(index.bands) == 1
    
    def test_get_band_found(self):
        """Test getting an existing band."""
        band = BandIndexEntry(name="Test Band", folder_path="Test Band")
        index = CollectionIndex(bands=[band])
        
        found_band = index.get_band("Test Band")
        
        assert found_band is not None
        assert found_band.name == "Test Band"
    
    def test_get_band_not_found(self):
        """Test getting a non-existent band."""
        index = CollectionIndex()
        
        found_band = index.get_band("Nonexistent Band")
        
        assert found_band is None
    
    def test_get_bands_without_metadata(self):
        """Test getting bands without metadata files."""
        band1 = BandIndexEntry(name="Band 1", folder_path="Band 1", has_metadata=True)
        band2 = BandIndexEntry(name="Band 2", folder_path="Band 2", has_metadata=False)
        band3 = BandIndexEntry(name="Band 3", folder_path="Band 3", has_metadata=False)
        
        index = CollectionIndex(bands=[band1, band2, band3])
        
        bands_without_metadata = index.get_bands_without_metadata()
        
        assert len(bands_without_metadata) == 2
        assert bands_without_metadata[0].name == "Band 2"
        assert bands_without_metadata[1].name == "Band 3"
    
    def test_get_bands_with_missing_albums(self):
        """Test getting bands with missing albums."""
        band1 = BandIndexEntry(name="Band 1", folder_path="Band 1", albums_count=3, local_albums_count=3, missing_albums_count=0)
        band2 = BandIndexEntry(name="Band 2", folder_path="Band 2", albums_count=5, local_albums_count=3, missing_albums_count=2)
        band3 = BandIndexEntry(name="Band 3", folder_path="Band 3", albums_count=2, local_albums_count=1, missing_albums_count=1)
        
        index = CollectionIndex(bands=[band1, band2, band3])
        
        bands_with_missing = index.get_bands_with_missing_albums()
        
        assert len(bands_with_missing) == 2
        assert bands_with_missing[0].name == "Band 2"
        assert bands_with_missing[1].name == "Band 3"
    
    def test_update_insights(self):
        """Test updating collection insights."""
        index = CollectionIndex()
        insights = CollectionInsight(
            insights=["Test insight"],
            collection_health="Excellent"
        )
        
        index.update_insights(insights)
        
        assert index.insights is not None
        assert index.insights.insights == ["Test insight"]
        assert index.insights.collection_health == "Excellent"
    
    def test_get_summary_stats(self):
        """Test getting summary statistics."""
        band1 = BandIndexEntry(name="Band 1", folder_path="Band 1", albums_count=3, local_albums_count=3)
        band2 = BandIndexEntry(name="Band 2", folder_path="Band 2", albums_count=5, local_albums_count=5)
        
        index = CollectionIndex(bands=[band1, band2])
        
        summary = index.get_summary_stats()
        
        assert summary["total_bands"] == 2
        assert summary["total_albums"] == 8
        assert summary["avg_albums_per_band"] == 4.0
        assert "last_scan" in summary
        assert "completion_percentage" in summary
    
    def test_stats_update_on_band_operations(self):
        """Test that statistics are updated when bands are added/removed."""
        index = CollectionIndex()
        
        # Add first band
        band1 = BandIndexEntry(name="Band 1", folder_path="Band 1", albums_count=5, local_albums_count=5)
        index.add_band(band1)
        
        assert index.stats.total_bands == 1
        assert index.stats.total_albums == 5
        assert index.stats.avg_albums_per_band == 5.0
        
        # Add second band
        band2 = BandIndexEntry(name="Band 2", folder_path="Band 2", albums_count=3, local_albums_count=3)
        index.add_band(band2)
        
        assert index.stats.total_bands == 2
        assert index.stats.total_albums == 8
        assert index.stats.avg_albums_per_band == 4.0
        
        # Remove a band
        index.remove_band("Band 1")
        
        assert index.stats.total_bands == 1
        assert index.stats.total_albums == 3
        assert index.stats.avg_albums_per_band == 3.0 