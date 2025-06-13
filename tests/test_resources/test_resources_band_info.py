"""
Unit tests for Band Info Resource module.

This module tests the markdown generation functionality for band information resources,
including metadata loading, formatting, error handling, and edge cases.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.resources.band_info import (
    get_band_info_markdown,
    _generate_band_markdown,
    _generate_header_section,
    _generate_details_section,
    _generate_albums_section,
    _generate_missing_albums_section,
    _generate_analysis_section,
    _generate_statistics_section,
    _generate_metadata_section,
    _format_album_info,
    _calculate_completion_percentage,
    _generate_no_metadata_message,
    _generate_error_message
)
from src.models import BandMetadata, Album, BandAnalysis, AlbumAnalysis
from src.tools.storage import StorageError


class TestGetBandInfoMarkdown:
    """Test the main band info markdown generation function."""
    
    def test_successful_band_info_generation(self):
        """Test successful markdown generation for existing band."""
        # Create test metadata
        metadata = BandMetadata(
            band_name="Pink Floyd",
            formed="1965",
            genres=["Progressive Rock", "Psychedelic Rock"],
            origin="London, England",
            members=["David Gilmour", "Roger Waters"],
            description="Legendary progressive rock band",
            albums=[
                Album(
                    album_name="The Wall",
                    track_count=26,
                    year="1979",
                    duration="81min"
                )
            ]
        )
        
        with patch('src.resources.band_info.load_band_metadata', return_value=metadata):
            result = get_band_info_markdown("Pink Floyd")
            
            # Verify markdown structure
            assert "# Pink Floyd (1965)" in result
            assert "## Band Information" in result
            assert "## Albums" in result
            assert "## 📈 Collection Statistics" in result
            assert "Progressive Rock, Psychedelic Rock" in result
            assert "The Wall" in result
    
    def test_band_not_found(self):
        """Test markdown generation for non-existent band."""
        with patch('src.resources.band_info.load_band_metadata', return_value=None):
            result = get_band_info_markdown("Non-Existent Band")
            
            assert "# Non-Existent Band" in result
            assert "❌ No Metadata Available" in result
            assert "scan_music_folders" in result
            assert "fetch_band_info" in result
    
    def test_storage_error_handling(self):
        """Test error handling for storage failures."""
        error_msg = "File permission denied"
        
        with patch('src.resources.band_info.load_band_metadata', 
                  side_effect=StorageError(error_msg)):
            result = get_band_info_markdown("Test Band")
            
            assert "# Test Band" in result
            assert "⚠️ Error Loading Band Information" in result
            assert error_msg in result
            assert "Troubleshooting" in result
    
    def test_unexpected_error_handling(self):
        """Test handling of unexpected errors."""
        with patch('src.resources.band_info.load_band_metadata', 
                  side_effect=Exception("Unexpected error")):
            result = get_band_info_markdown("Test Band")
            
            assert "⚠️ Error Loading Band Information" in result
            assert "Unexpected error" in result


class TestHeaderSection:
    """Test header section generation."""
    
    def test_header_with_full_info(self):
        """Test header generation with complete information."""
        metadata = BandMetadata(
            band_name="Pink Floyd",
            formed="1965",
            albums=[
                Album(album_name="Album1")
            ],
            albums_missing=[
                Album(album_name="Album2")
            ],
            analyze=BandAnalysis(rate=9)
        )
        
        result = _generate_header_section(metadata)
        
        assert "# Pink Floyd (1965)" in result
        assert "⭐ **9/10**" in result
        assert "⚠️ **1 missing albums**" in result
        assert "📊 **Analyzed**" in result
    
    def test_header_complete_collection(self):
        """Test header for complete collection."""
        metadata = BandMetadata(
            band_name="Complete Band",
            albums=[
                Album(album_name="Album1"),
                Album(album_name="Album2")
            ]
        )
        
        result = _generate_header_section(metadata)
        
        assert "✅ **Complete collection**" in result
        assert "missing albums" not in result
    
    def test_header_minimal_info(self):
        """Test header with minimal information."""
        metadata = BandMetadata(band_name="Simple Band")
        
        result = _generate_header_section(metadata)
        
        assert "# Simple Band" in result
        assert "✅ **Complete collection**" in result


class TestDetailsSection:
    """Test band details section generation."""
    
    def test_complete_details_section(self):
        """Test details section with all information."""
        metadata = BandMetadata(
            band_name="Pink Floyd",
            formed="1965",
            genres=["Progressive Rock", "Psychedelic Rock"],
            origin="London, England",
            members=["David Gilmour", "Roger Waters"],
            description="Legendary progressive rock band",
            albums=[
                Album(album_name="Album1")
            ],
            albums_missing=[
                Album(album_name="Album2")
            ]
        )
        
        result = _generate_details_section(metadata)
        
        assert "## Band Information" in result
        assert "*Legendary progressive rock band*" in result
        assert "| **Formed** | 1965 |" in result
        assert "Progressive Rock, Psychedelic Rock" in result
        assert "| **Origin** | London, England |" in result
        assert "David Gilmour, Roger Waters" in result
        assert "| **Total Albums** | 2 |" in result
    
    def test_minimal_details_section(self):
        """Test details section with minimal information."""
        metadata = BandMetadata(band_name="Simple Band", albums_count=0)
        
        result = _generate_details_section(metadata)
        
        assert "## Band Information" in result
        assert "| **Total Albums** | 0 |" in result
        assert "| **Collection Status** | 100.0% complete |" in result


class TestAlbumsSection:
    """Test albums section generation."""
    
    def test_albums_with_local_and_missing(self):
        """Test albums section with both local and missing albums."""
        metadata = BandMetadata(
            band_name="Test Band",
            albums=[
                Album(
                    album_name="Local Album",
                    track_count=10,
                    year="1979",
                    duration="45min"
                )
            ],
            albums_missing=[
                Album(
                    album_name="Missing Album",
                    track_count=8,
                    year="1981"
                )
            ]
        )
        
        result = _generate_albums_section(metadata)
        
        assert "## Albums" in result
        assert "### 🎵 Available Albums" in result
        assert "Local Album" in result
        assert "Missing Album" not in result  # Should be in missing section instead
    
    def test_no_albums(self):
        """Test albums section with no albums."""
        metadata = BandMetadata(band_name="No Albums Band", albums=[])
        
        result = _generate_albums_section(metadata)
        
        assert "## Albums" in result
        assert "*No album information available.*" in result


class TestMissingAlbumsSection:
    """Test missing albums section generation."""
    
    def test_missing_albums_section(self):
        """Test missing albums section generation."""
        missing_albums = [
            Album(
                album_name="Missing Album 1",
                track_count=10,
                year="1979"
            ),
            Album(
                album_name="Missing Album 2",
                track_count=8,
                year="1981"
            )
        ]
        
        result = _generate_missing_albums_section(missing_albums)
        
        assert "## 🔍 Missing Albums" in result
        assert "*2 albums not found in local collection*" in result
        assert "Missing Album 1" in result
        assert "Missing Album 2" in result
        assert "🔍 Missing" in result


class TestAnalysisSection:
    """Test analysis section generation."""
    
    def test_complete_analysis_section(self):
        """Test complete analysis section with all components."""
        analysis = BandAnalysis(
            review="Excellent progressive rock band with innovative sound.",
            rate=9,
            albums=[
                AlbumAnalysis(
                    album_name="The Wall",
                    review="Masterpiece rock opera.",
                    rate=10
                )
            ],
            similar_bands=["Yes", "Genesis", "King Crimson"]
        )
        
        result = _generate_analysis_section(analysis)
        
        assert "## 📊 Analysis & Reviews" in result
        assert "### Overall Review" in result
        assert "**Rating: 9/10**" in result
        assert "Excellent progressive rock band" in result
        assert "### Album Reviews" in result
        assert "#### The Wall" in result
        assert "**Rating: 10/10**" in result
        assert "Masterpiece rock opera" in result
        assert "### Similar Bands in Your Collection" in result
        assert "`Yes`" in result
        assert "`Genesis`" in result
        assert "`King Crimson`" in result
    
    def test_minimal_analysis_section(self):
        """Test analysis section with minimal information."""
        analysis = BandAnalysis(
            review="Good band",
            rate=7,
            albums=[],
            similar_bands=[]
        )
        
        result = _generate_analysis_section(analysis)
        
        assert "## 📊 Analysis & Reviews" in result
        assert "**Rating: 7/10**" in result
        assert "Good band" in result
        assert "### Album Reviews" not in result
        assert "### Similar Artists" not in result
    
    def test_complete_analysis_section_with_separated_similar_bands(self):
        """Test analysis section with both similar_bands and similar_bands_missing."""
        analysis = BandAnalysis(
            review="Great band with excellent music",
            rate=9,
            albums=[
                AlbumAnalysis(album_name="Test Album", review="Fantastic album", rate=10)
            ],
            similar_bands=["Band A", "Band B"],
            similar_bands_missing=["Band X", "Band Y"]
        )
        result = _generate_analysis_section(analysis)
        assert "### Similar Bands in Your Collection" in result
        assert "Band A" in result and "Band B" in result
        assert "### Similar Bands Not in Your Collection" in result
        assert "Band X" in result and "Band Y" in result
        assert "💡" in result  # acquisition suggestion
    
    def test_analysis_section_only_in_collection(self):
        """Test analysis section with only similar_bands (in collection)."""
        analysis = BandAnalysis(
            review="Test",
            rate=7,
            similar_bands=["Band A"],
            similar_bands_missing=[]
        )
        result = _generate_analysis_section(analysis)
        assert "### Similar Bands in Your Collection" in result
        assert "Band A" in result
        assert "### Similar Bands Not in Your Collection" not in result
    
    def test_analysis_section_only_missing(self):
        """Test analysis section with only similar_bands_missing (not in collection)."""
        analysis = BandAnalysis(
            review="Test",
            rate=7,
            similar_bands=[],
            similar_bands_missing=["Band X"]
        )
        result = _generate_analysis_section(analysis)
        assert "### Similar Bands Not in Your Collection" in result
        assert "Band X" in result
        assert "### Similar Bands in Your Collection" not in result
    
    def test_analysis_section_no_similar_bands(self):
        """Test analysis section with no similar bands at all."""
        analysis = BandAnalysis(
            review="Test",
            rate=7,
            similar_bands=[],
            similar_bands_missing=[]
        )
        result = _generate_analysis_section(analysis)
        assert "### Similar Bands in Your Collection" not in result
        assert "### Similar Bands Not in Your Collection" not in result


class TestStatisticsSection:
    """Test statistics section generation."""
    
    def test_complete_statistics_section(self):
        """Test statistics section with complete data."""
        metadata = BandMetadata(
            band_name="Pink Floyd",
            albums=[
                Album(album_name="Album1", track_count=10),
                Album(album_name="Album3", track_count=12)
            ],
            albums_missing=[
                Album(album_name="Album2", track_count=8)
            ],
            genres=["Progressive Rock", "Psychedelic Rock"],
            members=["Member1", "Member2", "Member3"],
            analyze=BandAnalysis(rate=9)
        )
        
        result = _generate_statistics_section(metadata)
        
        assert "## 📈 Collection Statistics" in result
        assert "| Total Albums | 3 |" in result
        assert "| Available Locally | 2 |" in result
        assert "| Missing | 1 |" in result
        assert "| Completion | 66.7% |" in result
        assert "| Genres | 2 |" in result
        assert "| Members | 3 |" in result
        assert "| Total Tracks | 30 |" in result
        assert "| Has Analysis | ✅ Yes |" in result
    
    def test_minimal_statistics_section(self):
        """Test statistics section with minimal data."""
        metadata = BandMetadata(band_name="Simple Band", albums=[])
        
        result = _generate_statistics_section(metadata)
        
        assert "| Total Albums | 0 |" in result
        assert "| Available Locally | 0 |" in result
        assert "| Missing | 0 |" in result
        assert "| Completion | 100.0% |" in result
        assert "| Has Analysis | ❌ No |" in result


class TestMetadataSection:
    """Test metadata information section generation."""
    
    def test_metadata_section(self):
        """Test metadata section generation."""
        metadata = BandMetadata(
            band_name="Pink Floyd",
            last_updated="2025-01-28T15:30:45.123456"
        )
        
        result = _generate_metadata_section(metadata)
        
        assert "## ℹ️ Metadata Information" in result
        assert "| **Last Updated** |" in result
        assert "| **Data Source** | `.band_metadata.json` |" in result
        assert "| **MCP Resource** | `band://info/Pink Floyd` |" in result
    
    def test_metadata_section_invalid_timestamp(self):
        """Test metadata section with invalid timestamp."""
        metadata = BandMetadata(
            band_name="Test Band",
            last_updated="invalid-timestamp"
        )
        
        result = _generate_metadata_section(metadata)
        
        assert "invalid-timestamp" in result


class TestFormatAlbumInfo:
    """Test individual album formatting."""
    
    def test_complete_album_info(self):
        """Test formatting complete album information."""
        album = Album(
            album_name="The Wall",
            track_count=26,
            year="1979",
            duration="81min",
            genres=["Progressive Rock", "Rock Opera"]
        )
        
        analysis = BandAnalysis(
            albums=[
                AlbumAnalysis(
                    album_name="The Wall",
                    review="Masterpiece rock opera about isolation.",
                    rate=10
                )
            ]
        )
        
        result = _format_album_info(album, analysis)
        
        assert "**The Wall** (1979, 26 tracks, 81min) - 🎵 Available" in result
        assert "*Progressive Rock, Rock Opera*" in result
        assert "⭐ **10/10**" in result
        assert "*Masterpiece rock opera about isolation.*" in result
    
    def test_missing_album_info(self):
        """Test formatting missing album information."""
        album = Album(
            album_name="Missing Album",
            track_count=10,
            year="1975"
        )
        
        result = _format_album_info(album, None, is_missing=True)
        
        assert "**Missing Album** (1975, 10 tracks) - 🔍 Missing" in result
    
    def test_minimal_album_info(self):
        """Test formatting minimal album information."""
        album = Album(album_name="Simple Album")
        
        result = _format_album_info(album, None)
        
        assert "**Simple Album** - 🎵 Available" in result


class TestCalculateCompletionPercentage:
    """Test completion percentage calculation."""
    
    def test_complete_collection(self):
        """Test completion percentage for complete collection."""
        metadata = BandMetadata(
            band_name="Complete Band",
            albums=[
                Album(album_name="Album1"),
                Album(album_name="Album2")
            ]
        )
        
        result = _calculate_completion_percentage(metadata)
        assert result == 100.0
    
    def test_partial_collection(self):
        """Test completion percentage for partial collection."""
        metadata = BandMetadata(
            band_name="Partial Band",
            albums=[
                Album(album_name="Album1"),
                Album(album_name="Album3")
            ],
            albums_missing=[
                Album(album_name="Album2")
            ]
        )
        
        result = _calculate_completion_percentage(metadata)
        assert abs(result - 66.67) < 0.1  # Approximately 2/3
    
    def test_no_albums(self):
        """Test completion percentage for band with no albums."""
        metadata = BandMetadata(band_name="No Albums Band", albums=[])
        
        result = _calculate_completion_percentage(metadata)
        assert result == 100.0


class TestErrorMessages:
    """Test error message generation."""
    
    def test_no_metadata_message(self):
        """Test no metadata message generation."""
        result = _generate_no_metadata_message("Test Band")
        
        assert "# Test Band" in result
        assert "❌ No Metadata Available" in result
        assert "scan_music_folders" in result
        assert "fetch_band_info" in result
        assert "save_band_metadata" in result
        assert "get_band_list" in result
    
    def test_error_message(self):
        """Test error message generation."""
        error = "File permission denied"
        result = _generate_error_message("Test Band", error)
        
        assert "# Test Band" in result
        assert "⚠️ Error Loading Band Information" in result
        assert error in result
        assert "Troubleshooting" in result
        assert "validate_band_metadata" in result
        assert "schema://band_metadata" in result


class TestCompleteIntegration:
    """Integration tests for complete band info generation."""
    
    def test_band_with_analysis_and_missing_albums(self):
        """Test complete band info with analysis and missing albums."""
        metadata = BandMetadata(
            band_name="Pink Floyd",
            formed="1965",
            genres=["Progressive Rock"],
            origin="London, England",
            members=["David Gilmour", "Roger Waters"],
            description="Legendary progressive rock band",
            albums=[
                Album(
                    album_name="The Wall",
                    track_count=26,
                    year="1979"
                )
            ],
            albums_missing=[
                Album(
                    album_name="Dark Side",
                    track_count=10,
                    year="1973"
                )
            ],
            analyze=BandAnalysis(
                review="Masterful progressive rock band",
                rate=10,
                albums=[
                    AlbumAnalysis(
                        album_name="The Wall",
                        review="Epic rock opera",
                        rate=10
                    )
                ],
                similar_bands=["Yes", "Genesis"]
            )
        )
        
        result = _generate_band_markdown(metadata)
        
        # Verify all sections are present
        assert "# Pink Floyd (1965)" in result
        assert "⭐ **10/10**" in result
        assert "⚠️ **1 missing albums**" in result
        assert "📊 **Analyzed**" in result
        assert "## Band Information" in result
        assert "## Albums" in result
        assert "## 🔍 Missing Albums" in result
        assert "## 📊 Analysis & Reviews" in result
        assert "## 📈 Collection Statistics" in result
        assert "## ℹ️ Metadata Information" in result
        
        # Verify content
        assert "The Wall" in result
        assert "Dark Side" in result
        assert "Epic rock opera" in result
        assert "`Yes`" in result
        assert "`Genesis`" in result
    
    def test_simple_band_without_analysis(self):
        """Test simple band without analysis."""
        metadata = BandMetadata(
            band_name="Simple Band",
            albums=[
                Album(
                    album_name="Only Album",
                    track_count=10
                )
            ]
        )
        
        result = _generate_band_markdown(metadata)
        
        assert "# Simple Band" in result
        assert "✅ **Complete collection**" in result
        assert "## Albums" in result
        assert "Only Album" in result
        assert "🔍 Missing Albums" not in result
        assert "📊 Analysis & Reviews" not in result 