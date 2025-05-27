"""
Unit tests for band data models.
Tests the Album, AlbumAnalysis, BandAnalysis, and BandMetadata Pydantic models.
"""

import pytest
import json
from datetime import datetime
from pydantic import ValidationError

from src.models.band import Album, AlbumAnalysis, BandAnalysis, BandMetadata


class TestAlbum:
    """Test cases for Album model."""
    
    def test_album_creation_default_values(self):
        """Test album creation with only required fields."""
        album = Album(album_name="Test Album")
        
        assert album.album_name == "Test Album"
        assert album.missing is False
        assert album.tracks_count == 0
        assert album.duration == ""
        assert album.year == ""
        assert album.genres == []
    
    def test_album_creation_all_fields(self):
        """Test album creation with all fields provided."""
        album = Album(
            album_name="Test Album",
            missing=True,
            tracks_count=12,
            duration="45min",
            year="1990",
            genres=["Rock", "Alternative"]
        )
        
        assert album.album_name == "Test Album"
        assert album.missing is True
        assert album.tracks_count == 12
        assert album.duration == "45min"
        assert album.year == "1990"
        assert album.genres == ["Rock", "Alternative"]
    
    def test_album_year_validation_valid(self):
        """Test valid year formats."""
        valid_years = ["1990", "2023", "", "1800"]
        
        for year in valid_years:
            album = Album(album_name="Test", year=year)
            assert album.year == year
    
    def test_album_year_validation_invalid(self):
        """Test invalid year formats raise ValidationError."""
        invalid_years = ["90", "20230", "abc", "19-90"]
        
        for year in invalid_years:
            with pytest.raises(ValidationError):
                Album(album_name="Test", year=year)
    
    def test_album_tracks_count_negative(self):
        """Test tracks_count cannot be negative."""
        with pytest.raises(ValidationError):
            Album(album_name="Test", tracks_count=-1)


class TestAlbumAnalysis:
    """Test cases for AlbumAnalysis model."""
    
    def test_album_analysis_default_values(self):
        """Test album analysis creation with default values."""
        analysis = AlbumAnalysis()
        
        assert analysis.review == ""
        assert analysis.rate == 0
    
    def test_album_analysis_valid_rating(self):
        """Test valid rating values."""
        valid_ratings = [0, 1, 5, 10]
        
        for rating in valid_ratings:
            analysis = AlbumAnalysis(rate=rating)
            assert analysis.rate == rating
    
    def test_album_analysis_invalid_rating(self):
        """Test invalid rating values raise ValidationError."""
        invalid_ratings = [-1, 11, 15]
        
        for rating in invalid_ratings:
            with pytest.raises(ValidationError):
                AlbumAnalysis(rate=rating)
    
    def test_album_analysis_with_review(self):
        """Test album analysis with review text."""
        analysis = AlbumAnalysis(
            review="Great album with memorable tracks",
            rate=8
        )
        
        assert analysis.review == "Great album with memorable tracks"
        assert analysis.rate == 8


class TestBandAnalysis:
    """Test cases for BandAnalysis model."""
    
    def test_band_analysis_default_values(self):
        """Test band analysis creation with default values."""
        analysis = BandAnalysis()
        
        assert analysis.review == ""
        assert analysis.rate == 0
        assert analysis.albums == []
        assert analysis.similar_bands == []
    
    def test_band_analysis_with_album_analyses(self):
        """Test band analysis with album analysis data."""
        album_analysis1 = AlbumAnalysis(review="First album", rate=7)
        album_analysis2 = AlbumAnalysis(review="Second album", rate=9)
        
        analysis = BandAnalysis(
            review="Excellent band",
            rate=8,
            albums=[album_analysis1, album_analysis2],
            similar_bands=["Band A", "Band B"]
        )
        
        assert analysis.review == "Excellent band"
        assert analysis.rate == 8
        assert len(analysis.albums) == 2
        assert analysis.albums[0].review == "First album"
        assert analysis.similar_bands == ["Band A", "Band B"]
    
    def test_band_analysis_invalid_rating(self):
        """Test invalid band rating raises ValidationError."""
        with pytest.raises(ValidationError):
            BandAnalysis(rate=15)


class TestBandMetadata:
    """Test cases for BandMetadata model."""
    
    def test_band_metadata_required_field_only(self):
        """Test band metadata creation with only required field."""
        metadata = BandMetadata(band_name="Test Band")
        
        assert metadata.band_name == "Test Band"
        assert metadata.formed == ""
        assert metadata.genres == []
        assert metadata.origin == ""
        assert metadata.members == []
        assert metadata.albums_count == 0
        assert metadata.description == ""
        assert metadata.albums == []
        assert metadata.analyze is None
        # last_updated should be set automatically
        assert metadata.last_updated != ""
    
    def test_band_metadata_complete(self):
        """Test band metadata creation with complete data."""
        album1 = Album(album_name="Album 1", tracks_count=10)
        album2 = Album(album_name="Album 2", tracks_count=12)
        
        analysis = BandAnalysis(
            review="Great band",
            rate=9,
            similar_bands=["Similar Band"]
        )
        
        metadata = BandMetadata(
            band_name="Test Band",
            formed="1990",
            genres=["Rock", "Alternative"],
            origin="USA",
            members=["Singer", "Guitarist"],
            albums_count=2,
            description="A great rock band",
            albums=[album1, album2],
            analyze=analysis
        )
        
        assert metadata.band_name == "Test Band"
        assert metadata.formed == "1990"
        assert metadata.genres == ["Rock", "Alternative"]
        assert metadata.origin == "USA"
        assert metadata.members == ["Singer", "Guitarist"]
        assert metadata.albums_count == 2
        assert len(metadata.albums) == 2
        assert metadata.analyze.rate == 9
    
    def test_albums_count_sync_validator(self):
        """Test that albums_count syncs with albums list length."""
        album1 = Album(album_name="Album 1")
        album2 = Album(album_name="Album 2")
        
        # albums_count should be overridden to match albums list
        metadata = BandMetadata(
            band_name="Test Band",
            albums_count=5,  # This should be corrected to 2
            albums=[album1, album2]
        )
        
        assert metadata.albums_count == 2
    
    def test_to_json_serialization(self):
        """Test JSON serialization of band metadata."""
        metadata = BandMetadata(
            band_name="Test Band",
            formed="1990",
            genres=["Rock"]
        )
        
        json_str = metadata.to_json()
        assert isinstance(json_str, str)
        
        # Verify it's valid JSON
        parsed = json.loads(json_str)
        assert parsed["band_name"] == "Test Band"
        assert parsed["formed"] == "1990"
        assert parsed["genres"] == ["Rock"]
    
    def test_from_json_deserialization(self):
        """Test JSON deserialization of band metadata."""
        json_data = {
            "band_name": "Test Band",
            "formed": "1990",
            "genres": ["Rock"],
            "albums": [
                {
                    "album_name": "Test Album",
                    "tracks_count": 10
                }
            ]
        }
        
        metadata = BandMetadata.from_json(json.dumps(json_data))
        
        assert metadata.band_name == "Test Band"
        assert metadata.formed == "1990"
        assert len(metadata.albums) == 1
        assert metadata.albums[0].album_name == "Test Album"
    
    def test_from_json_invalid_data(self):
        """Test deserialization with invalid JSON raises ValueError."""
        with pytest.raises(ValueError, match="Invalid JSON format"):
            BandMetadata.from_json("invalid json")
        
        with pytest.raises(ValueError, match="Failed to create BandMetadata"):
            BandMetadata.from_json('{"invalid": "data"}')  # Missing required band_name
    
    def test_get_missing_albums(self):
        """Test getting list of missing albums."""
        album1 = Album(album_name="Present Album", missing=False)
        album2 = Album(album_name="Missing Album", missing=True)
        album3 = Album(album_name="Another Missing", missing=True)
        
        metadata = BandMetadata(
            band_name="Test Band",
            albums=[album1, album2, album3]
        )
        
        missing_albums = metadata.get_missing_albums()
        assert len(missing_albums) == 2
        assert missing_albums[0].album_name == "Missing Album"
        assert missing_albums[1].album_name == "Another Missing"
    
    def test_get_local_albums(self):
        """Test getting list of locally available albums."""
        album1 = Album(album_name="Present Album", missing=False)
        album2 = Album(album_name="Missing Album", missing=True)
        
        metadata = BandMetadata(
            band_name="Test Band",
            albums=[album1, album2]
        )
        
        local_albums = metadata.get_local_albums()
        assert len(local_albums) == 1
        assert local_albums[0].album_name == "Present Album"
    
    def test_add_album(self):
        """Test adding an album updates count and timestamp."""
        metadata = BandMetadata(band_name="Test Band")
        original_timestamp = metadata.last_updated
        
        # Add a small delay to ensure timestamp changes
        import time
        time.sleep(0.01)
        
        new_album = Album(album_name="New Album")
        metadata.add_album(new_album)
        
        assert metadata.albums_count == 1
        assert len(metadata.albums) == 1
        assert metadata.albums[0].album_name == "New Album"
        assert metadata.last_updated != original_timestamp
    
    def test_remove_album_success(self):
        """Test successful album removal."""
        album1 = Album(album_name="Album 1")
        album2 = Album(album_name="Album 2")
        
        metadata = BandMetadata(
            band_name="Test Band",
            albums=[album1, album2]
        )
        
        result = metadata.remove_album("Album 1")
        
        assert result is True
        assert metadata.albums_count == 1
        assert metadata.albums[0].album_name == "Album 2"
    
    def test_remove_album_not_found(self):
        """Test album removal when album doesn't exist."""
        album1 = Album(album_name="Album 1")
        
        metadata = BandMetadata(
            band_name="Test Band",
            albums=[album1]
        )
        
        result = metadata.remove_album("Nonexistent Album")
        
        assert result is False
        assert metadata.albums_count == 1
        assert metadata.albums[0].album_name == "Album 1"
    
    def test_update_timestamp(self):
        """Test manual timestamp update."""
        metadata = BandMetadata(band_name="Test Band")
        original_timestamp = metadata.last_updated
        
        # Add a small delay to ensure timestamp changes
        import time
        time.sleep(0.01)
        
        metadata.update_timestamp()
        
        assert metadata.last_updated != original_timestamp
        # Verify it's a valid ISO timestamp
        datetime.fromisoformat(metadata.last_updated) 