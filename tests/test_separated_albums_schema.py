"""
Test suite for the separated albums schema (Task 7.1).

This module tests the new album schema structure where albums are separated
into 'albums' (local) and 'albums_missing' arrays instead of using a missing flag.
"""

import pytest
import json
from src.models.band import BandMetadata, Album, AlbumType
from src.models.collection import BandIndexEntry, CollectionStats


class TestSeparatedAlbumsSchema:
    """Test the new separated albums schema functionality."""

    def test_band_metadata_new_schema(self):
        """Test BandMetadata with separated albums arrays."""
        # Create test albums
        local_album1 = Album(album_name="Test Album 1", year="2020", track_count=10)
        local_album2 = Album(album_name="Test Album 2", year="2021", track_count=12)
        missing_album1 = Album(album_name="Missing Album 1", year="2019", track_count=8)
        missing_album2 = Album(album_name="Missing Album 2", year="2022", track_count=9)

        # Create band metadata with separated albums
        band = BandMetadata(
            band_name="Test Band",
            albums=[local_album1, local_album2],
            albums_missing=[missing_album1, missing_album2]
        )

        # Test counts
        assert band.albums_count == 4  # Total albums (local + missing)
        assert band.local_albums_count == 2  # Local albums only
        assert band.missing_albums_count == 2  # Missing albums only
        assert len(band.get_local_albums()) == 2
        assert len(band.get_missing_albums()) == 2

    def test_band_metadata_album_count_sync(self):
        """Test that album counts are automatically synced."""
        band = BandMetadata(band_name="Test Band")
        
        # Initially empty
        assert band.albums_count == 0
        assert band.local_albums_count == 0
        assert band.missing_albums_count == 0

        # Add local album
        local_album = Album(album_name="Local Album", year="2020")
        band.add_local_album(local_album)
        
        assert band.albums_count == 1
        assert band.local_albums_count == 1
        assert band.missing_albums_count == 0

        # Add missing album
        missing_album = Album(album_name="Missing Album", year="2021")
        band.add_missing_album(missing_album)
        
        assert band.albums_count == 2
        assert band.local_albums_count == 1
        assert band.missing_albums_count == 1

    def test_no_duplicate_albums_validation(self):
        """Test that albums cannot exist in both arrays."""
        local_album = Album(album_name="Duplicate Album", year="2020")
        missing_album = Album(album_name="Duplicate Album", year="2020")  # Same name

        with pytest.raises(ValueError, match="Albums cannot exist in both local and missing arrays"):
            BandMetadata(
                band_name="Test Band",
                albums=[local_album],
                albums_missing=[missing_album]
            )

    def test_move_album_between_arrays(self):
        """Test moving albums between local and missing arrays."""
        band = BandMetadata(band_name="Test Band")
        
        # Add album to missing
        album = Album(album_name="Test Album", year="2020")
        band.add_missing_album(album)
        
        assert band.local_albums_count == 0
        assert band.missing_albums_count == 1

        # Move to local
        success = band.move_album_to_local("Test Album")
        assert success is True
        assert band.local_albums_count == 1
        assert band.missing_albums_count == 0

        # Move back to missing
        success = band.move_album_to_missing("Test Album")
        assert success is True
        assert band.local_albums_count == 0
        assert band.missing_albums_count == 1

    def test_backward_compatibility_old_schema(self):
        """Test loading old schema with missing field."""
        old_schema_json = json.dumps({
            "band_name": "Test Band",
            "albums": [
                {
                    "album_name": "Local Album",
                    "year": "2020",
                    "track_count": 10,
                    "missing": False
                },
                {
                    "album_name": "Missing Album",
                    "year": "2021",
                    "track_count": 8,
                    "missing": True
                }
            ]
        })

        # Load from old schema
        band = BandMetadata.from_json(old_schema_json)
        
        # Verify albums were separated correctly
        assert band.local_albums_count == 1
        assert band.missing_albums_count == 1
        assert band.albums_count == 2
        
        local_albums = band.get_local_albums()
        missing_albums = band.get_missing_albums()
        
        assert local_albums[0].album_name == "Local Album"
        assert missing_albums[0].album_name == "Missing Album"

    def test_new_schema_serialization(self):
        """Test that new schema serializes correctly."""
        band = BandMetadata(
            band_name="Test Band",
            albums=[Album(album_name="Local Album", year="2020")],
            albums_missing=[Album(album_name="Missing Album", year="2021")]
        )

        # Serialize to JSON
        json_str = band.to_json()
        json_data = json.loads(json_str)

        # Verify structure
        assert "albums" in json_data
        assert "albums_missing" in json_data
        assert len(json_data["albums"]) == 1
        assert len(json_data["albums_missing"]) == 1
        assert json_data["albums"][0]["album_name"] == "Local Album"
        assert json_data["albums_missing"][0]["album_name"] == "Missing Album"

        # Verify no missing field in albums
        for album in json_data["albums"] + json_data["albums_missing"]:
            assert "missing" not in album

    def test_band_index_entry_with_local_count(self):
        """Test BandIndexEntry with new local_albums_count field."""
        entry = BandIndexEntry(
            name="Test Band",
            albums_count=5,
            local_albums_count=3,
            missing_albums_count=2,
            folder_path="Test Band/"
        )

        assert entry.albums_count == 5
        assert entry.local_albums_count == 3
        assert entry.missing_albums_count == 2

    def test_band_index_entry_count_validation(self):
        """Test that BandIndexEntry validates album counts correctly."""
        # Test automatic adjustment of total count
        entry = BandIndexEntry(
            name="Test Band",
            albums_count=10,  # Will be adjusted to 5 (3+2)
            local_albums_count=3,
            missing_albums_count=2,
            folder_path="Test Band/"
        )

        assert entry.albums_count == 5  # Should be adjusted to local + missing

    def test_collection_stats_with_local_albums(self):
        """Test CollectionStats with new total_local_albums field."""
        stats = CollectionStats(
            total_bands=2,
            total_albums=10,
            total_local_albums=7,
            total_missing_albums=3
        )

        assert stats.total_albums == 10
        assert stats.total_local_albums == 7
        assert stats.total_missing_albums == 3
        assert stats.completion_percentage == 70.0  # 7/10 * 100

    def test_remove_album_from_both_arrays(self):
        """Test that remove_album works with both arrays."""
        band = BandMetadata(
            band_name="Test Band",
            albums=[Album(album_name="Local Album", year="2020")],
            albums_missing=[Album(album_name="Missing Album", year="2021")]
        )

        # Remove local album
        success = band.remove_album("Local Album")
        assert success is True
        assert band.local_albums_count == 0
        assert band.missing_albums_count == 1

        # Remove missing album
        success = band.remove_album("Missing Album")
        assert success is True
        assert band.local_albums_count == 0
        assert band.missing_albums_count == 0

        # Try to remove non-existent album
        success = band.remove_album("Non-existent Album")
        assert success is False

    def test_add_album_prevents_duplicates(self):
        """Test that add_album prevents duplicates between arrays."""
        band = BandMetadata(band_name="Test Band")
        
        # Add album to missing
        album1 = Album(album_name="Test Album", year="2020")
        band.add_missing_album(album1)
        assert band.missing_albums_count == 1
        assert band.local_albums_count == 0

        # Add same album name to local (should move from missing)
        album2 = Album(album_name="Test Album", year="2020", track_count=10)
        band.add_local_album(album2)
        assert band.missing_albums_count == 0
        assert band.local_albums_count == 1
        
        # Verify the album in local has the updated track count
        local_albums = band.get_local_albums()
        assert local_albums[0].track_count == 10


if __name__ == "__main__":
    pytest.main([__file__]) 