"""
Unit tests for metadata module - Metadata Management Functions.

Tests the high-level metadata functions that use the storage module.
"""

import tempfile
from unittest.mock import patch, MagicMock
import pytest

from src.core.tools.storage import (
    save_band_metadata,
    save_band_analyze,
    save_collection_insight
)
from src.core.tools.storage import StorageError
from src.models import (
    BandMetadata,
    BandAnalysis,
    AlbumAnalysis,
    CollectionInsight
)


class TestMetadataFunctions:
    """Test metadata management functions."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_band_metadata_success(self):
        """Test successful band metadata save."""
        band_name = "Test Band"
        metadata = BandMetadata(
            band_name=band_name,
            formed="2000",
            genres=["Rock"]
        )
        result = save_band_metadata(band_name, metadata)
        assert result["status"] == "success"
        assert "message" in result

    def test_save_band_metadata_error(self):
        """Test band metadata save with error."""
        band_name = "Test Band"
        # Pass an invalid metadata type to trigger error
        from src.exceptions import ValidationError
        with pytest.raises(ValidationError):
            save_band_metadata(band_name, None)

    def test_save_band_analyze_success(self):
        """Test successful band analysis save."""
        band_name = "Test Band"
        analysis = BandAnalysis(
            review="Great band!",
            rate=8,
            albums=[
                AlbumAnalysis(album_name="Good album", review="Good album", rate=7),
                AlbumAnalysis(album_name="Better album", review="Better album", rate=9)
            ]
        )
        result = save_band_analyze(band_name, analysis)
        assert result["status"] == "success"
        assert "band_rating" in result
        assert "albums_analyzed" in result

    def test_save_band_analyze_error(self):
        """Test band analysis save with error."""
        band_name = "Test Band"
        # Pass an invalid analysis type to trigger error
        with pytest.raises(StorageError):
            save_band_analyze(band_name, None)

    def test_save_collection_insight_success(self):
        """Test successful collection insights save."""
        insights = CollectionInsight(
            insights=["Great variety", "Missing some genres", "Good overall"],
            recommendations=["Buy more jazz"],
            collection_health="Good"
        )
        result = save_collection_insight(insights)
        assert result["status"] == "success"
        assert "insights_count" in result
        assert "collection_health" in result

    def test_save_collection_insight_error(self):
        """Test collection insights save with error."""
        # Pass an invalid insights type to trigger error
        with pytest.raises(StorageError):
            save_collection_insight(None)


class TestIntegrationScenarios:
    """Test integration scenarios with different data combinations."""

    @patch('src.core.tools.storage.save_band_metadata')
    def test_save_metadata_with_albums(self, mock_save):
        """Test saving metadata with album information."""
        # Setup mock
        mock_save.return_value = {"status": "success", "albums_count": 2}
        
        # Test data with albums
        metadata = BandMetadata(
            band_name="Test Band",
            albums=[
                {"album_name": "Album 1", "year": "2000"},
                {"album_name": "Album 2", "year": "2005"}
            ]
        )
        
        result = save_band_metadata("Test Band", metadata)
        
        assert result["status"] == "success"
        assert result["albums_count"] == 2

    @patch('src.core.tools.storage.save_band_analyze')  
    def test_save_analysis_with_album_reviews(self, mock_save):
        """Test saving analysis with album-specific reviews."""
        # Setup mock
        mock_save.return_value = {
            "status": "success",
            "albums_analyzed": 3,
            "similar_bands_count": 2
        }
        
        # Test data with album analysis
        analysis = BandAnalysis(
            review="Excellent progressive rock band",
            rate=9,
            albums=[
                AlbumAnalysis(album_name="Debut masterpiece", review="Debut masterpiece", rate=10),
                AlbumAnalysis(album_name="Solid follow-up", review="Solid follow-up", rate=8),
                AlbumAnalysis(album_name="Experimental phase", review="Experimental phase", rate=7)
            ],
            similar_bands=["Pink Floyd", "Yes"]
        )
        
        result = save_band_analyze("Progressive Band", analysis)
        
        assert result["status"] == "success"
        assert result["albums_analyzed"] == 3
        assert result["similar_bands_count"] == 2

    @patch('src.core.tools.storage.save_collection_insight')
    def test_save_comprehensive_insights(self, mock_save):
        """Test saving comprehensive collection insights."""
        # Setup mock
        mock_save.return_value = {
            "status": "success",
            "insights_count": 4,
            "recommendations_count": 3,
            "collection_health": "Excellent"
        }
        
        # Test comprehensive insights
        insights = CollectionInsight(
            insights=[
                "Excellent genre diversity",
                "Strong representation of classic rock",
                "Missing modern electronic music",
                "High-quality album collection"
            ],
            recommendations=[
                "Consider adding ambient electronic artists",
                "Explore more contemporary jazz",
                "Fill gaps in 1990s alternative rock"
            ],
            top_rated_bands=["Pink Floyd", "The Beatles", "Radiohead"],
            suggested_purchases=["Kid A", "In Rainbows", "The Wall"],
            collection_health="Excellent"
        )
        
        result = save_collection_insight(insights)
        
        assert result["status"] == "success"
        assert result["insights_count"] == 4
        assert result["recommendations_count"] == 3
        assert result["collection_health"] == "Excellent" 
