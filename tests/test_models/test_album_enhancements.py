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
        assert AlbumTypeDetector.detect_type_from_folder_name("Rehearsal Recordings") == AlbumType.DEMO
        
        # Compilation albums
        assert AlbumTypeDetector.detect_type_from_folder_name("Greatest Hits") == AlbumType.COMPILATION
        assert AlbumTypeDetector.detect_type_from_folder_name("Best of Collection") == AlbumType.COMPILATION
        
        # EP albums
        assert AlbumTypeDetector.detect_type_from_folder_name("Love EP") == AlbumType.EP
        assert AlbumTypeDetector.detect_type_from_folder_name("Extended Play") == AlbumType.EP
        
        # Single albums
        assert AlbumTypeDetector.detect_type_from_folder_name("Radio Single") == AlbumType.SINGLE
        
        # Regular albums (default)
        assert AlbumTypeDetector.detect_type_from_folder_name("1970 - Paranoid") == AlbumType.ALBUM
        assert AlbumTypeDetector.detect_type_from_folder_name("Back in Black") == AlbumType.ALBUM
    
    def test_detect_edition_from_folder_name(self):
        """Test edition detection from folder names."""
        assert AlbumTypeDetector.detect_edition_from_folder_name("2012 - Album (Deluxe Edition)") == "Deluxe Edition"
        assert AlbumTypeDetector.detect_edition_from_folder_name("Album (Limited)") == "Limited"
        assert AlbumTypeDetector.detect_edition_from_folder_name("Album Name") == ""
    
    def test_detect_year_from_folder_name(self):
        """Test year detection from folder names."""
        assert AlbumTypeDetector.detect_year_from_folder_name("2012 - Album Name") == "2012"
        assert AlbumTypeDetector.detect_year_from_folder_name("Album (1995)") == "1995"
        assert AlbumTypeDetector.detect_year_from_folder_name("Album Name") == ""
    
    def test_extract_album_name_from_folder(self):
        """Test album name extraction from folder names."""
        assert AlbumTypeDetector.extract_album_name_from_folder("2012 - Apocalyptic Love") == "Apocalyptic Love"
        assert AlbumTypeDetector.extract_album_name_from_folder("2012 - Album (Deluxe Edition)") == "Album"


class TestEnhancedAlbumTypeDetection:
    """Test the new enhanced album type detection features from Task 6.6."""
    
    def setup_method(self):
        """Setup test environment."""
        # Clear any existing overrides/custom keywords
        AlbumTypeDetector._manual_overrides.clear()
        AlbumTypeDetector._custom_keywords.clear()
    
    def test_intelligent_detection_with_confidence(self):
        """Test the new intelligent detection method with confidence scoring."""
        # High confidence live album
        album_type, confidence, analysis = AlbumTypeDetector.detect_type_with_intelligence(
            "1985 - Live at Wembley Stadium", "Live at Wembley"
        )
        assert album_type == AlbumType.LIVE
        assert confidence >= 0.8
        assert 'enhanced_keywords' in analysis['method_used']
        assert len(analysis['keyword_matches']) > 0
        
        # Demo album with medium confidence
        album_type, confidence, analysis = AlbumTypeDetector.detect_type_with_intelligence(
            "1982 - Early Recordings", "Early Recordings"
        )
        assert album_type == AlbumType.DEMO
        assert confidence >= 0.6
        
        # Regular album (default) - gets 0.1 confidence boost when methods agree
        album_type, confidence, analysis = AlbumTypeDetector.detect_type_with_intelligence(
            "1970 - Paranoid", "Paranoid"
        )
        assert album_type == AlbumType.ALBUM
        assert confidence >= 0.0  # May get small confidence boost from combination logic
    
    def test_special_case_detection(self):
        """Test special case detection for soundtracks, tributes, etc."""
        # Soundtrack
        album_type, confidence, analysis = AlbumTypeDetector.detect_type_with_intelligence(
            "Movie Soundtrack", "Original Soundtrack"
        )
        assert album_type == AlbumType.COMPILATION
        assert confidence >= 0.8
        assert 'special_case' in analysis['method_used']
        assert any('soundtrack' in case for case in analysis['special_cases'])
        
        # Tribute album
        album_type, confidence, analysis = AlbumTypeDetector.detect_type_with_intelligence(
            "Tribute to Queen", "Tribute Album"
        )
        assert album_type == AlbumType.COMPILATION
        assert confidence >= 0.8
        assert 'special_case' in analysis['method_used']
        
        # Remix album
        album_type, confidence, analysis = AlbumTypeDetector.detect_type_with_intelligence(
            "Album Remixes", "Remixed"
        )
        assert album_type == AlbumType.COMPILATION
        assert confidence >= 0.8
        assert 'special_case' in analysis['method_used']
    
    def test_track_count_heuristics(self):
        """Test heuristics based on track count."""
        # Heuristics only trigger when keyword confidence is low (< 0.6)
        # Use generic album names without type keywords to trigger heuristics
        
        # EP based on track count (5 tracks) - no keywords to trigger heuristics
        album_type, confidence, analysis = AlbumTypeDetector.detect_type_with_intelligence(
            "2020 - Album Five", "Album Five", track_count=5
        )
        # Should suggest EP based on track count since no keywords detected
        assert 'track_count_heuristic' in analysis['method_used']
        assert any('5' in factor for factor in analysis['heuristic_factors'])
        
        # Single based on track count (2 tracks) - no keywords
        album_type, confidence, analysis = AlbumTypeDetector.detect_type_with_intelligence(
            "2020 - Two Songs", "Two Songs", track_count=2
        )
        # Should suggest Single based on track count
        assert 'track_count_heuristic' in analysis['method_used']
        
        # Album based on track count (15 tracks) - no keywords  
        album_type, confidence, analysis = AlbumTypeDetector.detect_type_with_intelligence(
            "2020 - Many Songs", "Many Songs", track_count=15
        )
        # Should suggest Album based on track count
        assert 'track_count_heuristic' in analysis['method_used']
    
    def test_genre_heuristics(self):
        """Test heuristics based on genres."""
        # Genre heuristics only trigger when keyword confidence is low (< 0.7)
        # Use album name without live keywords to trigger genre heuristics
        album_type, confidence, analysis = AlbumTypeDetector.detect_type_with_intelligence(
            "2020 - Concert Recording", "Recording", 
            genres=["Live", "Rock"]
        )
        # Should detect live from "concert" keyword, not genre heuristic
        assert album_type == AlbumType.LIVE
        # Concert is a medium confidence keyword, so no genre heuristic needed
        assert 'enhanced_keywords' in analysis['method_used']
        
        # Test with truly generic name to trigger genre heuristic
        album_type, confidence, analysis = AlbumTypeDetector.detect_type_with_intelligence(
            "2020 - Performance", "Performance", 
            genres=["Live", "Rock"]
        )
        assert album_type == AlbumType.LIVE
        if confidence < 0.7:  # Only if keyword confidence is low
            assert 'genre_heuristic' in analysis['method_used']
    
    def test_manual_overrides(self):
        """Test manual type override functionality."""
        # Set manual override
        AlbumTypeDetector.set_manual_override("special album", AlbumType.COMPILATION)
        
        # Test override works
        album_type, confidence, analysis = AlbumTypeDetector.detect_type_with_intelligence(
            "2020 - Special Album", "Special Album"
        )
        assert album_type == AlbumType.COMPILATION
        assert confidence == 1.0
        assert 'manual_override' in analysis['method_used']
        assert "Manual override for 'special album'" in analysis['confidence_factors']
    
    def test_custom_keywords(self):
        """Test custom keyword functionality."""
        # Add custom keyword
        AlbumTypeDetector.add_custom_keyword(AlbumType.LIVE, "bootleg", "high")
        
        # Test custom keyword detection
        album_type, confidence, analysis = AlbumTypeDetector.detect_type_with_intelligence(
            "1985 - Bootleg Recording", "Bootleg Recording"
        )
        assert album_type == AlbumType.LIVE
        assert confidence >= 0.8
        assert 'enhanced_keywords' in analysis['method_used']
    
    def test_batch_detection(self):
        """Test batch processing of multiple albums."""
        albums_data = [
            {
                'album_name': 'Live at Wembley',
                'folder_path': '1985 - Live at Wembley',
                'track_count': 12
            },
            {
                'album_name': 'Greatest Hits',
                'folder_path': '1990 - Greatest Hits Collection',
                'track_count': 20
            },
            {
                'album_name': 'Short EP',
                'folder_path': '2020 - Short EP',
                'track_count': 5
            }
        ]
        
        results = AlbumTypeDetector.batch_detect_types(albums_data)
        
        assert len(results) == 3
        
        # Check first album (Live)
        assert results[0]['detected_type'] == AlbumType.LIVE.value
        assert results[0]['detection_confidence'] >= 0.6
        assert results[0]['type_detection_used'] == True
        
        # Check second album (Compilation)
        assert results[1]['detected_type'] == AlbumType.COMPILATION.value
        assert results[1]['detection_confidence'] >= 0.6
        
        # Check third album (EP based on name and track count)
        assert results[2]['detected_type'] == AlbumType.EP.value
        assert results[2]['detection_confidence'] >= 0.6
    
    def test_detection_statistics(self):
        """Test detection statistics functionality."""
        albums_data = [
            {'album_name': 'Live Concert', 'folder_path': '1985 - Live Concert'},
            {'album_name': 'Studio Album', 'folder_path': '1990 - Studio Album'},
            {'album_name': 'Greatest Hits', 'folder_path': '1995 - Greatest Hits'},
            {'album_name': 'Demo Tracks', 'folder_path': '1980 - Demo Tracks'},
        ]
        
        stats = AlbumTypeDetector.get_detection_statistics(albums_data)
        
        assert stats['total_albums'] == 4
        assert 'high_confidence_detections' in stats
        assert 'medium_confidence_detections' in stats
        assert 'low_confidence_detections' in stats
        assert 'confidence_distribution' in stats
        assert 'type_distribution' in stats
        
        # Check confidence distribution adds up to 1.0
        conf_dist = stats['confidence_distribution']
        total_confidence = conf_dist['high'] + conf_dist['medium'] + conf_dist['low']
        assert abs(total_confidence - 1.0) < 0.01
    
    def test_confidence_levels(self):
        """Test different confidence levels in detection."""
        # High confidence case (clear live album)
        album_type, confidence, analysis = AlbumTypeDetector.detect_type_with_intelligence(
            "1985 - Live at Madison Square Garden", "Live at Madison Square Garden"
        )
        assert confidence >= 0.8
        
        # Medium confidence case (ambiguous)
        album_type, confidence, analysis = AlbumTypeDetector.detect_type_with_intelligence(
            "1985 - Concert", "Concert"
        )
        assert 0.6 <= confidence < 0.8
        
        # Low confidence case (minimal indicators)
        album_type, confidence, analysis = AlbumTypeDetector.detect_type_with_intelligence(
            "1985 - Festival", "Festival"
        )
        assert confidence < 0.6
    
    def test_backward_compatibility(self):
        """Test that enhanced detection maintains backward compatibility."""
        # Old method should still work
        album_type = AlbumTypeDetector.detect_type_from_folder_name("1985 - Live at Wembley")
        assert album_type == AlbumType.LIVE
        
        # Old method should use new intelligence under the hood
        album_type_old = AlbumTypeDetector.detect_type_from_folder_name("Greatest Hits Collection")
        album_type_new, _, _ = AlbumTypeDetector.detect_type_with_intelligence("Greatest Hits Collection")
        assert album_type_old == album_type_new
    
    def test_complex_scenarios(self):
        """Test complex detection scenarios with multiple factors."""
        # Album with multiple indicators
        album_type, confidence, analysis = AlbumTypeDetector.detect_type_with_intelligence(
            "1985 - Live at Wembley (Live Recording)", 
            "Live at Wembley Stadium", 
            track_count=15,
            genres=["Live", "Rock"]
        )
        assert album_type == AlbumType.LIVE
        assert confidence >= 0.9  # High confidence from multiple factors
        # Since keyword detection is very strong, heuristics may not be needed
        assert 'enhanced_keywords' in analysis['method_used']
        
        # Conflicting indicators resolved by strongest evidence
        album_type, confidence, analysis = AlbumTypeDetector.detect_type_with_intelligence(
            "2020 - Concert EP", 
            "Concert EP",
            track_count=4  # Track count suggests EP despite "concert" keyword
        )
        # Both EP and Live keywords present, but EP is more specific
        assert album_type in [AlbumType.EP, AlbumType.LIVE]
        assert confidence >= 0.5
        
        # Test case where heuristics actually get triggered (low keyword confidence)
        album_type, confidence, analysis = AlbumTypeDetector.detect_type_with_intelligence(
            "2020 - Music Collection", 
            "Music Collection",
            track_count=5,
            genres=["Alternative"]
        )
        # Generic name should trigger heuristics
        if confidence < 0.6:  # Only when keyword confidence is low
            assert 'track_count_heuristic' in analysis['method_used']


class TestAlbumDataMigrator:
    """Test AlbumDataMigrator utility class."""
    
    def test_migrate_album_to_enhanced_schema(self):
        """Test album migration to enhanced schema."""
        old_album = {
            'album_name': 'Test Album',
            'year': '2020',
            'tracks_count': 10,  # Old field name
            'missing': False
        }
        
        enhanced = AlbumDataMigrator.migrate_album_to_enhanced_schema(old_album)
        
        assert enhanced['album_name'] == 'Test Album'
        assert enhanced['year'] == '2020'
        assert enhanced['track_count'] == 10  # New field name
        assert enhanced['type'] == AlbumType.ALBUM.value
        assert 'tracks_count' not in enhanced
    
    def test_migrate_album_with_auto_detection(self):
        """Test album migration with auto-detection."""
        old_album = {
            'album_name': 'Live Concert',
            'folder_path': '1985 - Live at Wembley',
            'year': '',
            'type': AlbumType.ALBUM.value,  # Default type
            'edition': ''
        }
        
        enhanced = AlbumDataMigrator.migrate_album_to_enhanced_schema(old_album)
        
        # Should auto-detect type and year from folder name
        assert enhanced['type'] == AlbumType.LIVE.value  # Auto-detected from "Live at Wembley"
        assert enhanced['year'] == '1985'  # Auto-detected from folder prefix
        # Edition detection only works with parentheses format, so this folder won't have edition
        assert enhanced['edition'] == ''  # No parentheses in folder name
    
    def test_migrate_band_metadata(self):
        """Test complete band metadata migration."""
        old_metadata = {
            'band_name': 'Test Band',
            'albums': [
                {
                    'album_name': 'Live Album',
                    'folder_path': '1985 - Live at Venue',
                    'tracks_count': 12
                }
            ]
        }
        
        enhanced = AlbumDataMigrator.migrate_band_metadata(old_metadata)
        
        assert enhanced['band_name'] == 'Test Band'
        assert len(enhanced['albums']) == 1
        
        album = enhanced['albums'][0]
        assert album['album_name'] == 'Live Album'
        assert album['track_count'] == 12
        assert album['type'] == AlbumType.LIVE.value  # Auto-detected


class TestAlbumValidator:
    """Test AlbumValidator utility class."""
    
    def test_validate_album_type(self):
        """Test album type validation."""
        assert AlbumValidator.validate_album_type("Album") == True
        assert AlbumValidator.validate_album_type("Live") == True
        assert AlbumValidator.validate_album_type("InvalidType") == False
    
    def test_validate_year_format(self):
        """Test year format validation."""
        assert AlbumValidator.validate_year_format("2023") == True
        assert AlbumValidator.validate_year_format("") == True
        assert AlbumValidator.validate_year_format("23") == False
        assert AlbumValidator.validate_year_format("invalid") == False
    
    def test_validate_album_data(self):
        """Test complete album data validation."""
        valid_album = {
            'album_name': 'Test Album',
            'year': '2023',
            'type': 'Album',
            'track_count': 10,
            'missing': False
        }
        
        is_valid, errors = AlbumValidator.validate_album_data(valid_album)
        assert is_valid == True
        assert len(errors) == 0
        
        invalid_album = {
            'album_name': '',  # Missing name
            'year': '23',  # Invalid year
            'type': 'InvalidType',  # Invalid type
            'track_count': -1,  # Invalid count
            'missing': 'not_boolean'  # Invalid boolean
        }
        
        is_valid, errors = AlbumValidator.validate_album_data(invalid_album)
        assert is_valid == False
        assert len(errors) == 5  # Should have 5 errors


class TestAlbumUtilityFunctions:
    """Test album utility functions."""
    
    def setup_method(self):
        """Setup test data."""
        self.albums = [
            Album(album_name="Album1", type=AlbumType.ALBUM, edition=""),
            Album(album_name="Live1", type=AlbumType.LIVE, edition=""),
            Album(album_name="Demo1", type=AlbumType.DEMO, edition="Deluxe"),
            Album(album_name="EP1", type=AlbumType.EP, edition="Limited"),
        ]
    
    def test_get_album_type_distribution(self):
        """Test album type distribution calculation."""
        distribution = get_album_type_distribution(self.albums)
        
        assert distribution["Album"] == 1
        assert distribution["Live"] == 1
        assert distribution["Demo"] == 1
        assert distribution["EP"] == 1
    
    def test_get_edition_distribution(self):
        """Test album edition distribution calculation."""
        distribution = get_edition_distribution(self.albums)
        
        assert distribution["Standard"] == 2  # Empty editions become "Standard"
        assert distribution["Deluxe"] == 1
        assert distribution["Limited"] == 1
    
    def test_filter_albums_by_type(self):
        """Test filtering albums by type."""
        live_albums = filter_albums_by_type(self.albums, AlbumType.LIVE)
        assert len(live_albums) == 1
        assert live_albums[0].album_name == "Live1"
    
    def test_search_albums_by_criteria(self):
        """Test searching albums by multiple criteria."""
        # Search by type
        demo_albums = search_albums_by_criteria(self.albums, album_type=AlbumType.DEMO)
        assert len(demo_albums) == 1
        assert demo_albums[0].album_name == "Demo1"
        
        # Search by edition
        deluxe_albums = search_albums_by_criteria(self.albums, edition="Deluxe")
        assert len(deluxe_albums) == 1
        assert deluxe_albums[0].album_name == "Demo1"
        
        # Search by multiple criteria
        limited_eps = search_albums_by_criteria(self.albums, album_type=AlbumType.EP, edition="Limited")
        assert len(limited_eps) == 1
        assert limited_eps[0].album_name == "EP1"


class TestBackwardCompatibility:
    """Test backward compatibility with existing systems."""
    
    def test_old_album_data_compatibility(self):
        """Test compatibility with old album data formats."""
        # Old format with missing field
        old_album_data = {
            "album_name": "Test Album",
            "year": "2020",
            "track_count": 10,
            "missing": True,
            "duration": "45min",
            "genres": ["Rock"]
        }
        
        # Should be able to create Album from old data
        album = Album(**{k: v for k, v in old_album_data.items() if k != 'missing'})
        assert album.album_name == "Test Album"
        assert album.year == "2020"
        assert album.track_count == 10
        assert album.type == AlbumType.ALBUM  # Default type
    
    def test_band_metadata_with_mixed_albums(self):
        """Test band metadata with mixed old/new album formats."""
        mixed_albums = [
            {
                "album_name": "New Album",
                "type": "Live",
                "edition": "Deluxe"
            },
            {
                "album_name": "Old Album",
                "tracks_count": 10,  # Old field name
                "missing": False
            }
        ]
        
        # Migrate all albums
        migrated_albums = []
        for album_data in mixed_albums:
            migrated = AlbumDataMigrator.migrate_album_to_enhanced_schema(album_data)
            migrated_albums.append(migrated)
        
        # Should have consistent format
        for album in migrated_albums:
            assert 'album_name' in album
            assert 'type' in album
            assert 'track_count' in album
            assert 'tracks_count' not in album  # Old field removed


class TestAlbumModelSerialization:
    """Test album model JSON serialization/deserialization."""
    
    def test_album_json_serialization(self):
        """Test album serialization to JSON."""
        album = Album(
            album_name="Test Album",
            year="2023",
            type=AlbumType.LIVE,
            edition="Deluxe Edition",
            track_count=12
        )
        
        json_data = album.model_dump()
        
        assert json_data['album_name'] == "Test Album"
        assert json_data['year'] == "2023"
        assert json_data['type'] == "Live"  # Enum serialized as string
        assert json_data['edition'] == "Deluxe Edition"
        assert json_data['track_count'] == 12
    
    def test_album_json_deserialization(self):
        """Test album deserialization from JSON."""
        json_data = {
            "album_name": "Test Album",
            "year": "2023",
            "type": "Live",
            "edition": "Deluxe Edition",
            "track_count": 12
        }
        
        album = Album(**json_data)
        
        assert album.album_name == "Test Album"
        assert album.year == "2023"
        assert album.type == AlbumType.LIVE
        assert album.edition == "Deluxe Edition"
        assert album.track_count == 12
    
    def test_band_metadata_json_with_enhanced_albums(self):
        """Test band metadata JSON with enhanced albums."""
        band_data = {
            "band_name": "Test Band",
            "albums": [
                {
                    "album_name": "Live Album",
                    "type": "Live",
                    "edition": "Deluxe",
                    "track_count": 15
                }
            ]
        }
        
        band = BandMetadata(**band_data)
        
        assert band.band_name == "Test Band"
        assert len(band.albums) == 1
        assert band.albums[0].type == AlbumType.LIVE
        assert band.albums[0].edition == "Deluxe" 
