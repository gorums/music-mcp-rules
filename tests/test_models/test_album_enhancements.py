"""
Test suite for enhanced album models and validation utilities.

This module tests the new album type classification system, edition management,
and data validation/migration functionality.
"""

import pytest
from pydantic import ValidationError
from src.models import (
    Album, AlbumType, BandMetadata,
    AlbumTypeDetector, AlbumDataMigrator, AlbumValidator,
    get_album_type_distribution, get_edition_distribution,
    filter_albums_by_type, search_albums_by_criteria
)


class TestAlbumType:
    """Test AlbumType enumeration."""
    
    def test_album_type_values(self):
        """Test all album type enum values."""
        assert AlbumType.ALBUM == "Album"
        assert AlbumType.COMPILATION == "Compilation"
        assert AlbumType.EP == "EP"
        assert AlbumType.LIVE == "Live"
        assert AlbumType.SINGLE == "Single"
        assert AlbumType.DEMO == "Demo"
        assert AlbumType.INSTRUMENTAL == "Instrumental"
        assert AlbumType.SPLIT == "Split"
    
    def test_album_type_from_string(self):
        """Test creating AlbumType from string."""
        assert AlbumType("Album") == AlbumType.ALBUM
        assert AlbumType("Live") == AlbumType.LIVE
        
        with pytest.raises(ValueError):
            AlbumType("Invalid")


class TestEnhancedAlbumModel:
    """Test enhanced Album model with type and edition."""
    
    def test_album_creation_with_defaults(self):
        """Test creating album with default values."""
        album = Album(album_name="Test Album")
        
        assert album.album_name == "Test Album"
        assert album.year == ""
        assert album.type == AlbumType.ALBUM
        assert album.edition == ""
        assert album.track_count == 0
        assert album.duration == ""
        assert album.genres == []
        assert album.folder_path == ""
    
    def test_album_creation_with_all_fields(self):
        """Test creating album with all fields specified."""
        album = Album(
            album_name="Apocalyptic Love",
            year="2012",
            type=AlbumType.ALBUM,
            edition="Deluxe Edition",
            track_count=15,
            duration="67min",
            genres=["Hard Rock", "Blues Rock"],
            folder_path="2012 - Apocalyptic Love (Deluxe Edition)"
        )
        
        assert album.album_name == "Apocalyptic Love"
        assert album.year == "2012"
        assert album.type == AlbumType.ALBUM
        assert album.edition == "Deluxe Edition"
        assert album.track_count == 15
        assert album.duration == "67min"
        assert album.genres == ["Hard Rock", "Blues Rock"]
        assert album.folder_path == "2012 - Apocalyptic Love (Deluxe Edition)"
    
    def test_album_type_validation(self):
        """Test album type validation."""
        # Valid type as enum
        album = Album(album_name="Test", type=AlbumType.LIVE)
        assert album.type == AlbumType.LIVE
        
        # Valid type as string
        album = Album(album_name="Test", type="Demo")
        assert album.type == AlbumType.DEMO
        
        # Invalid type - expect Pydantic ValidationError
        with pytest.raises(ValidationError, match="1 validation error for Album"):
            Album(album_name="Test", type="InvalidType")
    
    def test_edition_validation(self):
        """Test edition field validation and normalization."""
        # Edition with parentheses should be normalized
        album = Album(album_name="Test", edition="(Deluxe Edition)")
        assert album.edition == "Deluxe Edition"
        
        # Edition without parentheses
        album = Album(album_name="Test", edition="Deluxe Edition")
        assert album.edition == "Deluxe Edition"
        
        # Empty edition
        album = Album(album_name="Test", edition="")
        assert album.edition == ""
    
    def test_year_validation(self):
        """Test year format validation."""
        # Valid year
        album = Album(album_name="Test", year="2023")
        assert album.year == "2023"
        
        # Empty year (allowed)
        album = Album(album_name="Test", year="")
        assert album.year == ""
        
        # Invalid year format
        with pytest.raises(ValueError):
            Album(album_name="Test", year="23")
        
        with pytest.raises(ValueError):
            Album(album_name="Test", year="invalid")
    
    def test_track_count_validation(self):
        """Test track count validation."""
        # Valid track count
        album = Album(album_name="Test", track_count=15)
        assert album.track_count == 15
        
        # Zero track count (allowed)
        album = Album(album_name="Test", track_count=0)
        assert album.track_count == 0
        
        # Negative track count (not allowed)
        with pytest.raises(ValueError):
            Album(album_name="Test", track_count=-1)
    
    def test_auto_detect_metadata(self):
        """Test automatic metadata detection from folder path."""
        album = Album(
            album_name="Live at Wembley",
            folder_path="1985 - Live at Wembley (Live)"
        )
        album.auto_detect_metadata()
        
        assert album.type == AlbumType.LIVE
        assert album.edition == "Live"
    
    def test_detect_type_from_name(self):
        """Test album type detection from name patterns."""
        # Live album
        album = Album(album_name="Live at Madison Square Garden")
        assert album.detect_type_from_name() == AlbumType.LIVE
        
        # Demo album
        album = Album(album_name="Early Demos")
        assert album.detect_type_from_name() == AlbumType.DEMO
        
        # EP
        album = Album(album_name="Love EP")
        assert album.detect_type_from_name() == AlbumType.EP
        
        # Compilation
        album = Album(album_name="Greatest Hits")
        assert album.detect_type_from_name() == AlbumType.COMPILATION
        
        # Regular album (default)
        album = Album(album_name="Back in Black")
        assert album.detect_type_from_name() == AlbumType.ALBUM
    
    def test_detect_edition_from_folder(self):
        """Test edition detection from folder path."""
        # Deluxe edition
        album = Album(album_name="Album Name", folder_path="2012 - Album Name (Deluxe Edition)")
        assert album.detect_edition_from_folder() == "Deluxe Edition"
        
        # Limited edition
        album = Album(album_name="Album Name", folder_path="2012 - Album Name (Limited Edition)")
        assert album.detect_edition_from_folder() == "Limited Edition"
        
        # Remastered
        album = Album(album_name="Album Name", folder_path="2012 - Album Name (Remastered)")
        assert album.detect_edition_from_folder() == "Remastered"
        
        # No edition
        album = Album(album_name="Album Name", folder_path="2012 - Album Name")
        assert album.detect_edition_from_folder() == ""


class TestAlbumTypeDetector:
    """Test AlbumTypeDetector utility class."""
    
    def test_detect_type_from_folder_name(self):
        """Test type detection from folder names."""
        # Live albums
        assert AlbumTypeDetector.detect_type_from_folder_name("1985 - Live at Wembley") == AlbumType.LIVE
        assert AlbumTypeDetector.detect_type_from_folder_name("Unplugged in New York") == AlbumType.LIVE
        
        # Demo albums
        assert AlbumTypeDetector.detect_type_from_folder_name("1982 - Early Demos") == AlbumType.DEMO
        assert AlbumTypeDetector.detect_type_from_folder_name("Unreleased Tracks") == AlbumType.DEMO
        
        # EP albums
        assert AlbumTypeDetector.detect_type_from_folder_name("Love EP") == AlbumType.EP
        
        # Compilation albums
        assert AlbumTypeDetector.detect_type_from_folder_name("Greatest Hits") == AlbumType.COMPILATION
        assert AlbumTypeDetector.detect_type_from_folder_name("Best of Queen") == AlbumType.COMPILATION
        
        # Instrumental albums
        assert AlbumTypeDetector.detect_type_from_folder_name("Album (Instrumental)") == AlbumType.INSTRUMENTAL
        
        # Split albums
        assert AlbumTypeDetector.detect_type_from_folder_name("Band A vs. Band B") == AlbumType.SPLIT
        
        # Regular album (default)
        assert AlbumTypeDetector.detect_type_from_folder_name("1980 - Back in Black") == AlbumType.ALBUM
    
    def test_detect_edition_from_folder_name(self):
        """Test edition detection from folder names."""
        assert AlbumTypeDetector.detect_edition_from_folder_name("Album (Deluxe Edition)") == "Deluxe Edition"
        assert AlbumTypeDetector.detect_edition_from_folder_name("Album (Limited)") == "Limited"
        assert AlbumTypeDetector.detect_edition_from_folder_name("Album (Remastered)") == "Remastered"
        assert AlbumTypeDetector.detect_edition_from_folder_name("Regular Album") == ""
    
    def test_detect_year_from_folder_name(self):
        """Test year extraction from folder names."""
        assert AlbumTypeDetector.detect_year_from_folder_name("1980 - Back in Black") == "1980"
        assert AlbumTypeDetector.detect_year_from_folder_name("Album (1975)") == "1975"
        assert AlbumTypeDetector.detect_year_from_folder_name("Album Name") == ""
        assert AlbumTypeDetector.detect_year_from_folder_name("1800 - Too Old") == ""  # Invalid year
    
    def test_extract_album_name_from_folder(self):
        """Test album name extraction from folder names."""
        assert AlbumTypeDetector.extract_album_name_from_folder("1980 - Back in Black") == "Back in Black"
        assert AlbumTypeDetector.extract_album_name_from_folder("1980 - Album (Deluxe Edition)") == "Album"
        assert AlbumTypeDetector.extract_album_name_from_folder("Album Name") == "Album Name"


class TestAlbumDataMigrator:
    """Test AlbumDataMigrator utility class."""
    
    def test_migrate_album_to_enhanced_schema(self):
        """Test migrating album data to enhanced schema."""
        # Old schema album
        old_album = {
            'album_name': 'Test Album',
            'tracks_count': 12,  # Old field name
            'duration': '45min',
            'year': '2020',
            'genres': ['Rock']
        }
        
        enhanced = AlbumDataMigrator.migrate_album_to_enhanced_schema(old_album)
        
        assert enhanced['album_name'] == 'Test Album'
        assert enhanced['track_count'] == 12  # Field name updated
        assert enhanced['type'] == AlbumType.ALBUM.value
        assert enhanced['edition'] == ''
        # Note: missing field removed in separated albums schema
        assert enhanced['duration'] == '45min'
        assert enhanced['year'] == '2020'
        assert enhanced['genres'] == ['Rock']
        assert enhanced['folder_path'] == ''
    
    def test_migrate_album_with_auto_detection(self):
        """Test migration with automatic type/edition detection."""
        old_album = {
            'album_name': 'Live at Wembley',
            'folder_path': '1985 - Live at Wembley (Live)',
            'tracks_count': 20
        }
        
        enhanced = AlbumDataMigrator.migrate_album_to_enhanced_schema(old_album)
        
        assert enhanced['type'] == AlbumType.LIVE.value
        assert enhanced['edition'] == 'Live'
        assert enhanced['year'] == '1985'
    
    def test_migrate_band_metadata(self):
        """Test migrating complete band metadata."""
        old_metadata = {
            'band_name': 'Test Band',
            'albums': [
                {
                    'album_name': 'Album 1',
                    'tracks_count': 10
                },
                {
                    'album_name': 'Live Album',
                    'folder_path': '1985 - Live Album (Live)',
                    'tracks_count': 15
                }
            ]
        }
        
        enhanced = AlbumDataMigrator.migrate_band_metadata(old_metadata)
        
        assert enhanced['band_name'] == 'Test Band'
        assert len(enhanced['albums']) == 2
        assert enhanced['albums'][0]['track_count'] == 10
        assert enhanced['albums'][1]['type'] == AlbumType.LIVE.value


class TestAlbumValidator:
    """Test AlbumValidator utility class."""
    
    def test_validate_album_type(self):
        """Test album type validation."""
        assert AlbumValidator.validate_album_type("Album") == True
        assert AlbumValidator.validate_album_type("Live") == True
        assert AlbumValidator.validate_album_type("Invalid") == False
    
    def test_validate_year_format(self):
        """Test year format validation."""
        assert AlbumValidator.validate_year_format("2023") == True
        assert AlbumValidator.validate_year_format("") == True  # Empty allowed
        assert AlbumValidator.validate_year_format("23") == False
        assert AlbumValidator.validate_year_format("invalid") == False
    
    def test_validate_album_data(self):
        """Test complete album data validation."""
        # Valid album data
        valid_album = {
            'album_name': 'Test Album',
            'type': 'Album',
            'year': '2023',
            'track_count': 10
        }
        
        is_valid, errors = AlbumValidator.validate_album_data(valid_album)
        assert is_valid == True
        assert errors == []
        
        # Invalid album data
        invalid_album = {
            'album_name': '',  # Required field empty
            'type': 'InvalidType',  # Invalid type
            'year': '23',  # Invalid year format
            'track_count': -1  # Negative track count
        }
        
        is_valid, errors = AlbumValidator.validate_album_data(invalid_album)
        assert is_valid == False
        assert len(errors) == 4  # Reduced by 1 since missing field removed


class TestAlbumUtilityFunctions:
    """Test utility functions for album statistics and filtering."""
    
    def setup_method(self):
        """Set up test albums for utility function tests."""
        self.albums = [
            Album(album_name="Album 1", type=AlbumType.ALBUM, edition="Standard"),
            Album(album_name="Album 2", type=AlbumType.ALBUM, edition="Deluxe Edition"),
            Album(album_name="Live Album", type=AlbumType.LIVE, edition=""),
            Album(album_name="Demo Album", type=AlbumType.DEMO, edition=""),
            Album(album_name="EP Album", type=AlbumType.EP, edition="Limited Edition"),
        ]
    
    def test_get_album_type_distribution(self):
        """Test album type distribution calculation."""
        distribution = get_album_type_distribution(self.albums)
        
        expected = {
            "Album": 2,
            "Live": 1,
            "Demo": 1,
            "EP": 1
        }
        
        assert distribution == expected
    
    def test_get_edition_distribution(self):
        """Test album edition distribution calculation."""
        distribution = get_edition_distribution(self.albums)
        
        expected = {
            "Standard": 3,  # One explicit, two default for empty editions
            "Deluxe Edition": 1,
            "Limited Edition": 1
        }
        
        assert distribution == expected
    
    def test_filter_albums_by_type(self):
        """Test filtering albums by type."""
        album_albums = filter_albums_by_type(self.albums, AlbumType.ALBUM)
        assert len(album_albums) == 2
        assert all(album.type == AlbumType.ALBUM for album in album_albums)
        
        live_albums = filter_albums_by_type(self.albums, AlbumType.LIVE)
        assert len(live_albums) == 1
        assert live_albums[0].album_name == "Live Album"
    
    def test_search_albums_by_criteria(self):
        """Test searching albums by multiple criteria."""
        # Search by type
        results = search_albums_by_criteria(self.albums, album_type=AlbumType.ALBUM)
        assert len(results) == 2
        
        # Search by edition
        results = search_albums_by_criteria(self.albums, edition="Deluxe Edition")
        assert len(results) == 1
        assert results[0].album_name == "Album 2"
        
        # Search by multiple criteria
        results = search_albums_by_criteria(
            self.albums, 
            album_type=AlbumType.EP, 
            edition="Limited Edition"
        )
        assert len(results) == 1
        assert results[0].album_name == "EP Album"
        
        # No results
        results = search_albums_by_criteria(self.albums, album_type=AlbumType.SINGLE)
        assert len(results) == 0


class TestBackwardCompatibility:
    """Test backward compatibility with existing album data."""
    
    def test_old_album_data_compatibility(self):
        """Test that old album data can still be loaded."""
        # Simulate old album data structure
        old_data = {
            'album_name': 'Test Album',
            'tracks_count': 12,  # Old field name
            'duration': '45min',
            'year': '2020',
            'genres': ['Rock']
        }
        
        # Should be able to migrate and create new Album
        migrated = AlbumDataMigrator.migrate_album_to_enhanced_schema(old_data)
        album = Album(**migrated)
        
        assert album.album_name == 'Test Album'
        assert album.track_count == 12
        assert album.type == AlbumType.ALBUM  # Default type
        assert album.edition == ""  # Default edition
    
    def test_band_metadata_with_mixed_albums(self):
        """Test band metadata with mix of old and new album formats."""
        metadata_dict = {
            'band_name': 'Test Band',
            'albums': [
                # Old format
                {
                    'album_name': 'Old Album',
                    'tracks_count': 10
                },
                # New format
                {
                    'album_name': 'New Album',
                    'type': 'Live',
                    'edition': 'Deluxe Edition',
                    'track_count': 15
                }
            ]
        }
        
        # Migrate and create BandMetadata
        migrated = AlbumDataMigrator.migrate_band_metadata(metadata_dict)
        band = BandMetadata(**migrated)
        
        assert len(band.albums) == 2
        assert band.albums[0].album_name == 'Old Album'
        assert band.albums[0].track_count == 10
        assert band.albums[0].type == AlbumType.ALBUM
        
        assert band.albums[1].album_name == 'New Album'
        assert band.albums[1].type == AlbumType.LIVE
        assert band.albums[1].edition == 'Deluxe Edition'


class TestAlbumModelSerialization:
    """Test JSON serialization/deserialization of enhanced album models."""
    
    def test_album_json_serialization(self):
        """Test album JSON serialization."""
        album = Album(
            album_name="Test Album",
            type=AlbumType.LIVE,
            edition="Deluxe Edition",
            year="2023"
        )
        
        json_str = album.model_dump_json()
        assert '"type":"Live"' in json_str
        assert '"edition":"Deluxe Edition"' in json_str
    
    def test_album_json_deserialization(self):
        """Test album JSON deserialization."""
        json_data = {
            "album_name": "Test Album",
            "type": "Live",
            "edition": "Deluxe Edition",
            "year": "2023",
            "track_count": 10
        }
        
        album = Album(**json_data)
        assert album.type == AlbumType.LIVE
        assert album.edition == "Deluxe Edition"
    
    def test_band_metadata_json_with_enhanced_albums(self):
        """Test BandMetadata JSON operations with enhanced albums."""
        band = BandMetadata(
            band_name="Test Band",
            albums=[
                Album(album_name="Album 1", type=AlbumType.ALBUM),
                Album(album_name="Live Album", type=AlbumType.LIVE, edition="Live")
            ]
        )
        
        json_str = band.to_json()
        restored_band = BandMetadata.from_json(json_str)
        
        assert len(restored_band.albums) == 2
        assert restored_band.albums[0].type == AlbumType.ALBUM
        assert restored_band.albums[1].type == AlbumType.LIVE
        assert restored_band.albums[1].edition == "Live" 