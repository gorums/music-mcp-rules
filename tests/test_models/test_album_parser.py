"""
Tests for Album Naming Convention Processing and Parsing

This module tests the comprehensive parsing functionality for album folder names,
including multiple folder structure patterns and validation.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

from src.models.album_parser import AlbumFolderParser, FolderStructureValidator
from src.models.band import AlbumType


class TestAlbumFolderParser:
    """Test cases for AlbumFolderParser class."""
    
    def test_parse_default_with_edition(self):
        """Test parsing default pattern with edition: 'YYYY - Album Name (Edition)'."""
        test_cases = [
            ("2012 - Apocalyptic Love (Deluxe Edition)", {
                'year': '2012',
                'album_name': 'Apocalyptic Love',
                'edition': 'Deluxe Edition',
                'pattern_type': 'default_with_edition'
            }),
            ("1991 - The Black Album (Remastered)", {
                'year': '1991',
                'album_name': 'The Black Album',
                'edition': 'Remastered',
                'pattern_type': 'default_with_edition'
            }),
            ("1982 - No Life 'Til Leather (Demo)", {
                'year': '1982',
                'album_name': "No Life 'Til Leather",
                'edition': 'Demo',
                'pattern_type': 'default_with_edition'
            }),
            ("1988 - ...And Justice for All (Instrumental)", {
                'year': '1988',
                'album_name': '...And Justice for All',
                'edition': 'Instrumental',
                'pattern_type': 'default_with_edition'
            })
        ]
        
        for folder_name, expected in test_cases:
            result = AlbumFolderParser.parse_folder_name(folder_name)
            assert result == expected, f"Failed for {folder_name}"
    
    def test_parse_default_no_edition(self):
        """Test parsing default pattern without edition: 'YYYY - Album Name'."""
        test_cases = [
            ("2014 - World on Fire", {
                'year': '2014',
                'album_name': 'World on Fire',
                'edition': '',
                'pattern_type': 'default_no_edition'
            }),
            ("1975 - A Night at the Opera", {
                'year': '1975',
                'album_name': 'A Night at the Opera',
                'edition': '',
                'pattern_type': 'default_no_edition'
            }),
            ("1969 - Abbey Road", {
                'year': '1969',
                'album_name': 'Abbey Road',
                'edition': '',
                'pattern_type': 'default_no_edition'
            })
        ]
        
        for folder_name, expected in test_cases:
            result = AlbumFolderParser.parse_folder_name(folder_name)
            assert result == expected, f"Failed for {folder_name}"
    
    def test_parse_legacy_with_edition(self):
        """Test parsing legacy pattern with edition: 'Album Name (Edition)'."""
        test_cases = [
            ("Physical Graffiti (Deluxe)", {
                'year': '',
                'album_name': 'Physical Graffiti',
                'edition': 'Deluxe',
                'pattern_type': 'legacy_with_edition'
            }),
            ("Unplugged in New York (Live)", {
                'year': '',
                'album_name': 'Unplugged in New York',
                'edition': 'Live',
                'pattern_type': 'legacy_with_edition'
            })
        ]
        
        for folder_name, expected in test_cases:
            result = AlbumFolderParser.parse_folder_name(folder_name)
            assert result == expected, f"Failed for {folder_name}"
    
    def test_parse_legacy_no_edition(self):
        """Test parsing legacy pattern without edition: 'Album Name'."""
        test_cases = [
            ("Nevermind", {
                'year': '',
                'album_name': 'Nevermind',
                'edition': '',
                'pattern_type': 'legacy_no_edition'
            }),
            ("Led Zeppelin IV", {
                'year': '',
                'album_name': 'Led Zeppelin IV',
                'edition': '',
                'pattern_type': 'legacy_no_edition'
            })
        ]
        
        for folder_name, expected in test_cases:
            result = AlbumFolderParser.parse_folder_name(folder_name)
            assert result == expected, f"Failed for {folder_name}"
    
    def test_parse_edge_cases(self):
        """Test parsing edge cases and complex patterns."""
        test_cases = [
            # Empty or invalid input
            ("", {
                'year': '',
                'album_name': '',
                'edition': '',
                'pattern_type': 'invalid'
            }),
            # Invalid year (too old)
            ("1940 - Invalid Year", {
                'year': '',
                'album_name': '1940 - Invalid Year',
                'edition': '',
                'pattern_type': 'legacy_no_edition'
            }),
            # Invalid year (too new)
            ("2040 - Future Album", {
                'year': '',
                'album_name': '2040 - Future Album',
                'edition': '',
                'pattern_type': 'legacy_no_edition'
            }),
            # Invalid edition (not recognized keywords) - year is valid so treated as default with unrecognized edition
            ("2020 - Test Album (Random Text)", {
                'year': '2020',
                'album_name': 'Test Album (Random Text)',
                'edition': '',
                'pattern_type': 'default_no_edition'
            }),
            # Complex album name with special characters
            ("1967 - Sgt. Pepper's Lonely Hearts Club Band (Deluxe)", {
                'year': '1967',
                'album_name': "Sgt. Pepper's Lonely Hearts Club Band",
                'edition': 'Deluxe',
                'pattern_type': 'default_with_edition'
            })
        ]
        
        for folder_name, expected in test_cases:
            result = AlbumFolderParser.parse_folder_name(folder_name)
            assert result == expected, f"Failed for {folder_name}"
    
    def test_parse_enhanced_folder_structure(self):
        """Test parsing enhanced folder structure with type folders."""
        test_cases = [
            # Enhanced structure paths
            ("Iron Maiden/Album/1982 - The Number of the Beast", {
                'year': '1982',
                'album_name': 'The Number of the Beast',
                'edition': '',
                'pattern_type': 'enhanced_default_no_edition',
                'album_type': 'Album'
            }),
            ("Metallica/Demo/1982 - No Life 'Til Leather (Demo)", {
                'year': '1982',
                'album_name': "No Life 'Til Leather",
                'edition': 'Demo',
                'pattern_type': 'enhanced_default_with_edition',
                'album_type': 'Demo'
            }),
            ("Queen/Live/1985 - Live Aid", {
                'year': '1985',
                'album_name': 'Live Aid',
                'edition': '',
                'pattern_type': 'enhanced_default_no_edition',
                'album_type': 'Live'
            }),
            # Default structure (not enhanced)
            ("Metallica/1991 - The Black Album", {
                'year': '1991',
                'album_name': 'The Black Album',
                'edition': '',
                'pattern_type': 'default_no_edition',
                'album_type': 'Album'
            })
        ]
        
        for folder_path, expected in test_cases:
            result = AlbumFolderParser.parse_enhanced_folder_structure(folder_path)
            assert result == expected, f"Failed for {folder_path}"
    
    def test_normalize_album_name(self):
        """Test album name normalization."""
        test_cases = [
            ("  Messy   Spacing  ", "Messy Spacing"),
            ("Album.Name.With.Dots", "Album. Name. With. Dots"),
            ("Album,With,Commas", "Album, With, Commas"),
            ("Album:With:Colons", "Album: With: Colons"),
            ("Trailing Dots...", "Trailing Dots. . ."),  # Multiple periods are normalized to ". . ."
            ("Trailing,Commas,", "Trailing, Commas"),     # Comma normalization adds space, then trailing comma removed
            ("Normal Album Name", "Normal Album Name")
        ]
        
        for input_name, expected in test_cases:
            result = AlbumFolderParser.normalize_album_name(input_name)
            assert result == expected, f"Failed for '{input_name}'"
    
    def test_normalize_edition(self):
        """Test edition normalization."""
        test_cases = [
            ("deluxe", "Deluxe Edition"),
            ("Deluxe Edition", "Deluxe Edition"),
            ("limited", "Limited Edition"),
            ("remaster", "Remastered"),
            ("anniversary", "Anniversary Edition"),
            ("demo", "Demo"),
            ("live", "Live"),
            ("instrumental", "Instrumental"),
            ("Custom Edition", "Custom Edition"),  # Not standardized
            ("", "")  # Empty edition
        ]
        
        for input_edition, expected in test_cases:
            result = AlbumFolderParser.normalize_edition(input_edition)
            assert result == expected, f"Failed for '{input_edition}'"
    
    def test_detect_folder_structure_type(self):
        """Test folder structure type detection."""
        # Create temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            band_dir = Path(temp_dir) / "Test Band"
            band_dir.mkdir()
            
            # Create enhanced structure - all albums in type folders
            (band_dir / "Album").mkdir()
            (band_dir / "Album" / "2020 - Test Album").mkdir()
            (band_dir / "Live").mkdir()
            (band_dir / "Live" / "2021 - Live Concert").mkdir()
            (band_dir / "Demo").mkdir()
            (band_dir / "Demo" / "2019 - Early Demo").mkdir()
            
            result = AlbumFolderParser.detect_folder_structure_type(str(band_dir))
            
            # Should be enhanced since all albums are in type folders
            assert result['structure_type'] == 'enhanced'
            assert result['pattern_consistency'] in ['consistent', 'mostly_consistent']
            assert result['albums_analyzed'] == 3
            assert 'Album' in result['type_folders_found']
            assert 'Live' in result['type_folders_found']
            assert 'Demo' in result['type_folders_found']
    
    def test_detect_folder_structure_type_default(self):
        """Test detection of default folder structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            band_dir = Path(temp_dir) / "Test Band"
            band_dir.mkdir()
            
            # Create default structure
            (band_dir / "2020 - Album One").mkdir()
            (band_dir / "2021 - Album Two (Deluxe)").mkdir()
            (band_dir / "2022 - Album Three").mkdir()
            
            result = AlbumFolderParser.detect_folder_structure_type(str(band_dir))
            
            assert result['structure_type'] == 'default'
            assert result['pattern_consistency'] in ['consistent', 'mostly_consistent']
            assert result['albums_analyzed'] == 3
            assert result['type_folders_found'] == []
    
    def test_detect_folder_structure_type_mixed(self):
        """Test detection of mixed folder structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            band_dir = Path(temp_dir) / "Test Band"
            band_dir.mkdir()
            
            # Create mixed structure - some albums in type folders, some direct
            (band_dir / "2020 - Album One").mkdir()  # Direct album
            (band_dir / "Album").mkdir()
            (band_dir / "Album" / "2021 - Album Two").mkdir()  # Enhanced
            (band_dir / "Legacy Album").mkdir()  # Direct legacy album
            
            result = AlbumFolderParser.detect_folder_structure_type(str(band_dir))
            
            assert result['structure_type'] == 'mixed'
            assert 'Album' in result['type_folders_found']
            assert len(result['recommendations']) > 0
    
    def test_year_validation(self):
        """Test year validation logic."""
        valid_years = ['1950', '1975', '2000', '2025', '2030']
        invalid_years = ['1949', '2031', '1900', '2100', 'abcd', '']
        
        for year in valid_years:
            assert AlbumFolderParser._is_valid_year(year), f"Year {year} should be valid"
        
        for year in invalid_years:
            assert not AlbumFolderParser._is_valid_year(year), f"Year {year} should be invalid"
    
    def test_edition_validation(self):
        """Test edition validation logic."""
        valid_editions = [
            'Deluxe Edition', 'Limited', 'Remastered', 'Demo', 'Live',
            'Instrumental', 'Split', 'Anniversary Edition'
        ]
        invalid_editions = [
            'Random Text', 'Not An Edition', 'Just Words', ''
        ]
        
        for edition in valid_editions:
            assert AlbumFolderParser._is_valid_edition(edition), f"Edition '{edition}' should be valid"
        
        for edition in invalid_editions:
            assert not AlbumFolderParser._is_valid_edition(edition), f"Edition '{edition}' should be invalid"
    
    def test_album_type_detection(self):
        """Test album type detection from folder names."""
        test_cases = [
            ('Album', AlbumType.ALBUM),
            ('Live', AlbumType.LIVE),
            ('Demo', AlbumType.DEMO),
            ('Compilation', AlbumType.COMPILATION),
            ('EP', AlbumType.EP),
            ('Single', AlbumType.SINGLE),
            ('Instrumental', AlbumType.INSTRUMENTAL),
            ('Split', AlbumType.SPLIT),
            ('Random Folder', AlbumType.ALBUM)  # Default fallback
        ]
        
        for folder_name, expected_type in test_cases:
            result = AlbumFolderParser._detect_album_type_from_folder(folder_name)
            assert result == expected_type, f"Failed for folder '{folder_name}'"


class TestFolderStructureValidator:
    """Test cases for FolderStructureValidator class."""
    
    def test_validate_folder_name_default_pattern(self):
        """Test validation of folder names against default pattern."""
        test_cases = [
            # Valid default patterns
            ("2020 - Perfect Album", 100),
            ("2021 - Album With Edition (Deluxe)", 90),  # Gets -10 for edition standardization
            # Missing year
            ("Album Without Year", 70),  # 100 - 30
            # Invalid year
            ("1940 - Old Album", 70),     # 100 - 30 (missing year since invalid)
            # Short album name
            ("2020 - A", 80),             # 100 - 20
            # Empty album name (gets both missing year and missing album name penalties)
            ("2020 - ", 20)               # 100 - 30 (missing year) - 50 (missing album name) = 20
        ]
        
        for folder_name, expected_min_score in test_cases:
            result = FolderStructureValidator.validate_folder_name(folder_name, 'default')
            assert result['compliance_score'] >= expected_min_score, f"Score too low for '{folder_name}': {result['compliance_score']}"
    
    def test_validate_folder_name_legacy_pattern(self):
        """Test validation of folder names against legacy pattern."""
        # Legacy pattern should be more lenient about missing years
        result = FolderStructureValidator.validate_folder_name("Album Without Year", 'legacy')
        assert result['compliance_score'] == 100, "Legacy pattern should allow missing years"
    
    def test_validate_edition_standardization(self):
        """Test edition standardization suggestions."""
        test_cases = [
            ("2020 - Album (deluxe)", "2020 - Album (Deluxe Edition)"),
            ("2020 - Album (limited)", "2020 - Album (Limited Edition)"),
            ("2020 - Album (remaster)", "2020 - Album (Remastered)")
        ]
        
        for folder_name, expected_recommendation in test_cases:
            result = FolderStructureValidator.validate_folder_name(folder_name, 'default')
            # Should suggest standardization
            assert any("standardized" in issue for issue in result['issues'])
    
    def test_generate_recommended_name(self):
        """Test recommended name generation."""
        test_cases = [
            ({
                'year': '2020',
                'album_name': 'Test Album',
                'edition': 'Deluxe Edition',
                'pattern_type': 'default_with_edition'
            }, "2020 - Test Album (Deluxe Edition)"),
            ({
                'year': '2020',
                'album_name': 'Test Album',
                'edition': '',
                'pattern_type': 'default_no_edition'
            }, "2020 - Test Album"),
            ({
                'year': '',
                'album_name': 'Legacy Album',
                'edition': 'Live',
                'pattern_type': 'legacy_with_edition'
            }, "Legacy Album (Live)"),
            ({
                'year': '',
                'album_name': 'Legacy Album',
                'edition': '',
                'pattern_type': 'legacy_no_edition'
            }, "Legacy Album")
        ]
        
        for parsed_data, expected in test_cases:
            result = FolderStructureValidator._generate_recommended_name(parsed_data)
            assert result == expected, f"Failed for {parsed_data}"
    
    def test_compliance_score_calculation(self):
        """Test compliance score calculation logic."""
        # Perfect folder
        result = FolderStructureValidator.validate_folder_name("2020 - Perfect Album (Deluxe Edition)", 'default')
        assert result['compliance_score'] == 100
        
        # Multiple issues
        result = FolderStructureValidator.validate_folder_name("A", 'default')  # Short name, no year
        assert result['compliance_score'] <= 50  # Should have multiple deductions
    
    def test_validation_issues_detection(self):
        """Test detection of various validation issues."""
        test_cases = [
            ("Album Without Year", ["Missing year prefix"]),
            ("2040 - Future Album", ["Missing year prefix"]),  # Invalid year treated as missing year
            ("2020 - A", ["Album name too short"]),
            ("2020 - ", ["Missing or invalid album name"]),
            ("2020 - Album (deluxe)", ["standardized"])
        ]
        
        for folder_name, expected_issue_keywords in test_cases:
            result = FolderStructureValidator.validate_folder_name(folder_name, 'default')
            issues_text = ' '.join(result['issues']).lower()
            
            for keyword in expected_issue_keywords:
                assert keyword.lower() in issues_text, f"Expected issue '{keyword}' not found for '{folder_name}'"


class TestIntegration:
    """Integration tests for album parsing functionality."""
    
    def test_real_world_folder_names(self):
        """Test parsing of real-world folder names from test collection."""
        real_folder_names = [
            "1967 - Sgt. Pepper's Lonely Hearts Club Band (Deluxe Edition)",
            "1982 - No Life 'Til Leather (Demo)",
            "1988 - ...And Justice for All (Instrumental)",
            "1999 - S&M (Live)",
            "1998 - Garage Inc. (Compilation)",
            "1969 - Abbey Road",
            "Physical Graffiti",
            "Unplugged in New York"
        ]
        
        for folder_name in real_folder_names:
            result = AlbumFolderParser.parse_folder_name(folder_name)
            # Should parse without errors
            assert 'album_name' in result
            assert 'year' in result
            assert 'edition' in result
            assert 'pattern_type' in result
            
            # Album name should not be empty
            assert result['album_name'], f"Album name empty for '{folder_name}'"
    
    def test_full_workflow_example(self):
        """Test complete workflow from parsing to validation."""
        folder_name = "2012 - Apocalyptic Love (deluxe edition)"
        
        # Parse the folder name
        parsed = AlbumFolderParser.parse_folder_name(folder_name)
        assert parsed['year'] == '2012'
        assert parsed['album_name'] == 'Apocalyptic Love'
        assert parsed['edition'] == 'deluxe edition'
        
        # Validate the folder name
        validation = FolderStructureValidator.validate_folder_name(folder_name, 'default')
        assert validation['compliance_score'] >= 90  # Should be mostly compliant
        
        # Check for standardization suggestion
        assert any("standardized" in issue for issue in validation['issues'])
        
        # Get recommended name
        recommended = validation['recommended_name']
        assert recommended == "2012 - Apocalyptic Love (Deluxe Edition)"
    
    def test_enhanced_structure_workflow(self):
        """Test workflow with enhanced folder structure."""
        folder_path = "Iron Maiden/Demo/1978 - The Soundhouse Tapes (Demo)"
        
        # Parse enhanced structure
        parsed = AlbumFolderParser.parse_enhanced_folder_structure(folder_path)
        assert parsed['album_type'] == 'Demo'
        assert parsed['year'] == '1978'
        assert parsed['album_name'] == 'The Soundhouse Tapes'
        assert parsed['edition'] == 'Demo'
        assert 'enhanced' in parsed['pattern_type'] 