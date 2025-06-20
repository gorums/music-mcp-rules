"""
Unit tests for metadata module - Metadata Management Functions.

Tests the high-level metadata functions that use the storage module.
"""

import tempfile
from unittest.mock import patch, MagicMock
import pytest

from src.core.tools.metadata import (
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

    @patch('src.core.tools.metadata._save_band_metadata')
    def test_save_band_metadata_success(self, mock_save):
        """Test successful band metadata save."""
        # Setup mock
        mock_save.return_value = {
            "status": "success",
            "message": "Band metadata saved for Test Band"
        }
        
        # Test data
        band_name = "Test Band"
        metadata = BandMetadata(
            band_name=band_name,
            formed="2000",
            genres=["Rock"]
        )
        
        # Call function
        result = save_band_metadata(band_name, metadata)
        
        # Verify
        assert result["status"] == "success"
        mock_save.assert_called_once_with(band_name, metadata)

    @patch('src.core.tools.metadata._save_band_metadata')
    def test_save_band_metadata_error(self, mock_save):
        """Test band metadata save with error."""
        # Setup mock to raise error
        mock_save.side_effect = StorageError("Save failed")
        
        # Test data
        band_name = "Test Band"
        metadata = BandMetadata(band_name=band_name)
        
        # Call function and expect error
        with pytest.raises(StorageError, match="Save failed"):
            save_band_metadata(band_name, metadata)

    @patch('src.core.tools.metadata._save_band_analyze')
    def test_save_band_analyze_success(self, mock_save):
        """Test successful band analysis save."""
        # Setup mock
        mock_save.return_value = {
            "status": "success",
            "band_rating": 8,
            "albums_analyzed": 2
        }
        
        # Test data
        band_name = "Test Band"
        analysis = BandAnalysis(
            review="Great band!",
            rate=8,
            albums=[
                AlbumAnalysis(album_name="Good album", review="Good album", rate=7),
                AlbumAnalysis(album_name="Better album", review="Better album", rate=9)
            ]
        )
        
        # Call function
        result = save_band_analyze(band_name, analysis)
        
        # Verify
        assert result["status"] == "success"
        assert result["band_rating"] == 8
        assert result["albums_analyzed"] == 2
        mock_save.assert_called_once_with(band_name, analysis)

    @patch('src.core.tools.metadata._save_band_analyze')
    def test_save_band_analyze_error(self, mock_save):
        """Test band analysis save with error."""
        # Setup mock to raise error
        mock_save.side_effect = StorageError("Analysis save failed")
        
        # Test data
        band_name = "Test Band"
        analysis = BandAnalysis(review="Test review", rate=5)
        
        # Call function and expect error
        with pytest.raises(StorageError, match="Analysis save failed"):
            save_band_analyze(band_name, analysis)

    @patch('src.core.tools.metadata._save_collection_insight')
    def test_save_collection_insight_success(self, mock_save):
        """Test successful collection insights save."""
        # Setup mock
        mock_save.return_value = {
            "status": "success",
            "insights_count": 3,
            "collection_health": "Good"
        }
        
        # Test data
        insights = CollectionInsight(
            insights=["Great variety", "Missing some genres", "Good overall"],
            recommendations=["Buy more jazz"],
            collection_health="Good"
        )
        
        # Call function
        result = save_collection_insight(insights)
        
        # Verify
        assert result["status"] == "success"
        assert result["insights_count"] == 3
        assert result["collection_health"] == "Good"
        mock_save.assert_called_once_with(insights)

    @patch('src.core.tools.metadata._save_collection_insight')
    def test_save_collection_insight_error(self, mock_save):
        """Test collection insights save with error."""
        # Setup mock to raise error
        mock_save.side_effect = StorageError("Insights save failed")
        
        # Test data
        insights = CollectionInsight(insights=["Test insight"])
        
        # Call function and expect error
        with pytest.raises(StorageError, match="Insights save failed"):
            save_collection_insight(insights)


class TestIntegrationScenarios:
    """Test integration scenarios with different data combinations."""

    @patch('src.core.tools.metadata._save_band_metadata')
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

    @patch('src.core.tools.metadata._save_band_analyze')  
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

    @patch('src.core.tools.metadata._save_collection_insight')
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
