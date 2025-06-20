"""
Unit tests for Collection Summary Resource module.

This module tests the markdown generation functionality for collection summary resources,
including collection index loading, formatting, error handling, and edge cases.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.core.resources.collection_summary import (
    get_collection_summary,
    _generate_collection_markdown,
    _generate_header_section,
    _generate_overview_section,
    _generate_statistics_section,
    _generate_band_distribution_section,
    _generate_missing_albums_section,
    _generate_insights_section,
    _generate_health_section,
    _generate_metadata_info_section,
    _get_collection_size_status,
    _get_albums_status,
    _get_missing_status,
    _get_completion_status,
    _get_avg_albums_status,
    _get_metadata_status,
    _get_metadata_coverage_status,
    _generate_no_collection_message,
    _generate_error_message
)
from src.models.collection import (
    CollectionIndex,
    CollectionStats,
    CollectionInsight,
    BandIndexEntry
)
from src.core.tools.storage import StorageError


class TestGetCollectionSummary:
    """Test the main collection summary generation function."""
    
    def test_successful_collection_summary_generation(self):
        """Test successful markdown generation for existing collection."""
        # Create test collection index
        bands = [
            BandIndexEntry(
                name="Pink Floyd",
                albums_count=15,
                folder_path="Pink Floyd",
                missing_albums_count=5,
                has_metadata=True,
                has_analysis=True
            ),
            BandIndexEntry(
                name="The Beatles",
                albums_count=13,
                folder_path="The Beatles",
                missing_albums_count=2,
                has_metadata=True,
                has_analysis=False
            )
        ]
        
        collection_index = CollectionIndex(bands=bands)
        
        with patch('src.core.resources.collection_summary.load_collection_index', return_value=collection_index):
            result = get_collection_summary()
            
            # Verify markdown structure
            assert "# 🎵 Music Collection Summary" in result
            assert "## 📊 Quick Overview" in result
            assert "## 📈 Detailed Statistics" in result
            assert "## 🎸 Band Distribution" in result
            assert "## 🏥 Collection Health" in result
            assert "Pink Floyd" in result
            assert "The Beatles" in result
    
    def test_collection_not_found(self):
        """Test markdown generation when no collection index exists."""
        with patch('src.core.resources.collection_summary.load_collection_index', return_value=None):
            result = get_collection_summary()
            
            assert "# 🎵 Music Collection Summary" in result
            assert "❌ No Collection Data Available" in result
            assert "scan_music_folders" in result
            assert "Getting Started" in result
    
    def test_storage_error_handling(self):
        """Test error handling for storage failures."""
        error_msg = "File permission denied"
        
        with patch('src.core.resources.collection_summary.load_collection_index', 
                  side_effect=StorageError(error_msg)):
            result = get_collection_summary()
            
            assert "# 🎵 Music Collection Summary" in result
            assert "⚠️ Error Loading Collection Data" in result
            assert error_msg in result
            assert "Troubleshooting" in result
    
    def test_unexpected_error_handling(self):
        """Test handling of unexpected errors."""
        with patch('src.core.resources.collection_summary.load_collection_index', 
                  side_effect=Exception("Unexpected error")):
            result = get_collection_summary()
            
            assert "⚠️ Error Loading Collection Data" in result
            assert "Unexpected error" in result


class TestHeaderSection:
    """Test header section generation."""
    
    def test_header_large_collection_excellent_completion(self):
        """Test header generation for large collection with excellent completion."""
        bands = [
            BandIndexEntry(
                name=f"Band {i}",
                albums_count=10,
                folder_path=f"Band {i}",
                missing_albums_count=0,
                has_metadata=True,
                has_analysis=True
            ) for i in range(150)
        ]
        
        collection_index = CollectionIndex(bands=bands)
        
        result = _generate_header_section(collection_index)
        
        assert "# 🎵 Music Collection Summary" in result
        assert "🎭 **Large Collection**" in result
        assert "✅ **Excellent Completion**" in result
        assert "📊 **150 Analyzed**" in result
    
    def test_header_medium_collection_with_insights(self):
        """Test header for medium collection with insights."""
        bands = [
            BandIndexEntry(name=f"Band {i}", albums_count=5, folder_path=f"Band {i}")
            for i in range(50)
        ]
        
        insights = CollectionInsight(
            insights=["Great collection!"],
            collection_health="Good"
        )
        
        collection_index = CollectionIndex(bands=bands, insights=insights)
        
        result = _generate_header_section(collection_index)
        
        assert "🎭 **Medium Collection**" in result
        assert "💡 **Has Insights**" in result
    
    def test_header_small_collection_poor_completion(self):
        """Test header for small collection with poor completion."""
        bands = [
            BandIndexEntry(
                name="Band 1",
                albums_count=10,
                folder_path="Band 1",
                missing_albums_count=8
            )
        ]
        
        collection_index = CollectionIndex(bands=bands)
        
        result = _generate_header_section(collection_index)
        
        assert "🎭 **Small Collection**" in result
        assert "🔴 **Poor Completion**" in result


class TestOverviewSection:
    """Test overview section generation."""
    
    def test_complete_overview_section(self):
        """Test overview section with complete collection data."""
        bands = [
            BandIndexEntry(
                name="Pink Floyd",
                albums_count=15,
                local_albums_count=12,
                folder_path="Pink Floyd",
                missing_albums_count=3,
                has_metadata=True
            ),
            BandIndexEntry(
                name="The Beatles",
                albums_count=13,
                local_albums_count=13,
                folder_path="The Beatles",
                missing_albums_count=0,
                has_metadata=False
            )
        ]
        
        collection_index = CollectionIndex(bands=bands)
        
        result = _generate_overview_section(collection_index)
        
        assert "## 📊 Quick Overview" in result
        assert "| **Total Bands** | 2 |" in result
        assert "| **Total Albums** | 28 |" in result
        assert "| **Missing Albums** | 3 |" in result
        assert "| **Completion Rate** |" in result
        assert "| **Avg Albums/Band** |" in result
        assert "| **Bands with Metadata** | 1/2 |" in result
    
    def test_empty_collection_overview(self):
        """Test overview section with empty collection."""
        collection_index = CollectionIndex()
        
        result = _generate_overview_section(collection_index)
        
        assert "| **Total Bands** | 0 |" in result
        assert "| **Total Albums** | 0 |" in result
        assert "| **Missing Albums** | 0 |" in result


class TestStatisticsSection:
    """Test detailed statistics section generation."""
    
    def test_statistics_section_with_genres(self):
        """Test statistics section including genre information."""
        bands = [
            BandIndexEntry(name="Band 1", albums_count=10, local_albums_count=10, folder_path="Band 1", has_metadata=True),
            BandIndexEntry(name="Band 2", albums_count=5, local_albums_count=3, folder_path="Band 2", missing_albums_count=2)
        ]
        
        stats = CollectionStats(
            total_bands=2,
            total_albums=15,
            total_missing_albums=2,
            bands_with_metadata=1,
            top_genres={"Rock": 5, "Pop": 3, "Jazz": 1}
        )
        
        collection_index = CollectionIndex(bands=bands, stats=stats)
        
        result = _generate_statistics_section(collection_index)
        
        assert "## 📈 Detailed Statistics" in result
        assert "### Collection Metrics" in result
        assert "| Available Albums |" in result
        assert "| Missing Albums |" in result
        assert "### 🎭 Top Genres" in result
        assert "| Rock | 5 |" in result
        assert "| Pop | 3 |" in result
    
    def test_statistics_section_no_genres(self):
        """Test statistics section without genre data."""
        collection_index = CollectionIndex()
        
        result = _generate_statistics_section(collection_index)
        
        assert "## 📈 Detailed Statistics" in result
        assert "Top Genres" not in result


class TestBandDistributionSection:
    """Test band distribution section generation."""
    
    def test_band_distribution_all_categories(self):
        """Test band distribution with all size categories."""
        bands = [
            BandIndexEntry(name="Large Band 1", albums_count=15, local_albums_count=15, folder_path="Large Band 1", has_metadata=True, has_analysis=True),
            BandIndexEntry(name="Large Band 2", albums_count=12, local_albums_count=12, folder_path="Large Band 2"),
            BandIndexEntry(name="Medium Band 1", albums_count=7, local_albums_count=7, folder_path="Medium Band 1", has_metadata=True),
            BandIndexEntry(name="Medium Band 2", albums_count=6, local_albums_count=6, folder_path="Medium Band 2"),
            BandIndexEntry(name="Small Band 1", albums_count=3, local_albums_count=3, folder_path="Small Band 1"),
            BandIndexEntry(name="Small Band 2", albums_count=2, local_albums_count=2, folder_path="Small Band 2"),
            BandIndexEntry(name="No Albums Band", albums_count=0, local_albums_count=0, folder_path="No Albums Band")
        ]
        
        collection_index = CollectionIndex(bands=bands)
        
        result = _generate_band_distribution_section(collection_index)
        
        assert "## 🎸 Band Distribution" in result
        assert "| Large (10+ albums) | 2 |" in result
        assert "| Medium (5-9 albums) | 2 |" in result
        assert "| Small (1-4 albums) | 2 |" in result
        assert "| No Albums | 1 |" in result
        assert "### 🏆 Top Bands by Album Count" in result
        assert "1. **Large Band 1** - 15 albums ✅ 📄 📊" in result
    
    def test_band_distribution_empty(self):
        """Test band distribution with no bands."""
        collection_index = CollectionIndex()
        
        result = _generate_band_distribution_section(collection_index)
        
        assert "## 🎸 Band Distribution" in result
        assert "| Large (10+ albums) | 0 |" in result
        assert "Top Bands by Album Count" not in result


class TestMissingAlbumsSection:
    """Test missing albums section generation."""
    
    def test_missing_albums_section(self):
        """Test missing albums section with bands having missing albums."""
        bands_with_missing = [
            BandIndexEntry(
                name="Pink Floyd",
                albums_count=15,
                local_albums_count=7,
                folder_path="Pink Floyd",
                missing_albums_count=8
            ),
            BandIndexEntry(
                name="The Beatles",
                albums_count=13,
                local_albums_count=10,
                folder_path="The Beatles",
                missing_albums_count=3
            ),
            BandIndexEntry(
                name="Led Zeppelin",
                albums_count=8,
                local_albums_count=7,
                folder_path="Led Zeppelin",
                missing_albums_count=1
            )
        ]
        
        result = _generate_missing_albums_section(bands_with_missing)
        
        assert "## 🔍 Missing Albums Analysis" in result
        assert "*3 bands have 12 missing albums*" in result
        assert "| Pink Floyd | 8 | 15 | 46.7% 🔴 |" in result
        assert "| The Beatles | 3 | 13 | 76.9% 🟡 |" in result
        assert "| Led Zeppelin | 1 | 8 | 87.5% 🟢 |" in result
    
    def test_missing_albums_section_many_bands(self):
        """Test missing albums section with many bands (tests truncation)."""
        bands_with_missing = [
            BandIndexEntry(
                name=f"Band {i}",
                albums_count=10,
                local_albums_count=10 - (i % 3 + 1),
                folder_path=f"Band {i}",
                missing_albums_count=i % 3 + 1
            ) for i in range(20)
        ]
        
        result = _generate_missing_albums_section(bands_with_missing)
        
        assert "## 🔍 Missing Albums Analysis" in result
        assert "*20 bands have" in result
        assert "... and 5 more bands with missing albums" in result


class TestInsightsSection:
    """Test insights section generation."""
    
    def test_complete_insights_section(self):
        """Test insights section with all data types."""
        insights = CollectionInsight(
            insights=[
                "Your collection focuses heavily on classic rock",
                "Pink Floyd has the most albums",
                "Consider adding more modern artists"
            ],
            recommendations=[
                "Acquire missing Pink Floyd albums",
                "Add metadata for 5 bands",
                "Analyze remaining bands for ratings"
            ],
            top_rated_bands=["Pink Floyd", "The Beatles", "Led Zeppelin"],
            suggested_purchases=[
                "Pink Floyd - The Wall",
                "The Beatles - Abbey Road",
                "Led Zeppelin - IV"
            ],
            collection_health="Good",
            generated_at="2024-01-25T10:30:00Z"
        )
        
        result = _generate_insights_section(insights)
        
        assert "## 💡 Collection Insights" in result
        assert "*Generated on January 25, 2024*" in result
        assert "**Collection Health:** 🟡 Good" in result
        assert "### 📋 Key Insights" in result
        assert "- Your collection focuses heavily on classic rock" in result
        assert "### 🎯 Recommendations" in result
        assert "- Acquire missing Pink Floyd albums" in result
        assert "### ⭐ Top Rated Bands" in result
        assert "`Pink Floyd`, `The Beatles`, `Led Zeppelin`" in result
        assert "### 🛒 Suggested Purchases" in result
        assert "- Pink Floyd - The Wall" in result
    
    def test_minimal_insights_section(self):
        """Test insights section with minimal data."""
        insights = CollectionInsight(
            collection_health="Excellent",
            generated_at="2024-01-25T10:30:00Z"
        )
        
        result = _generate_insights_section(insights)
        
        assert "## 💡 Collection Insights" in result
        assert "**Collection Health:** 🟢 Excellent" in result
        assert "Key Insights" not in result
        assert "Recommendations" not in result


class TestHealthSection:
    """Test collection health section generation."""
    
    def test_health_section_with_recommendations(self):
        """Test health section that generates recommendations."""
        bands = [
            BandIndexEntry(
                name="Band 1",
                albums_count=10,
                folder_path="Band 1",
                missing_albums_count=6,  # 40% completion
                has_metadata=False,
                has_analysis=False
            ),
            BandIndexEntry(
                name="Band 2",
                albums_count=5,
                folder_path="Band 2",
                missing_albums_count=0,
                has_metadata=False,
                has_analysis=False
            )
        ]
        
        collection_index = CollectionIndex(bands=bands)
        
        result = _generate_health_section(collection_index)
        
        assert "## 🏥 Collection Health" in result
        assert "### 🎯 Health Recommendations" in result
        assert "Consider acquiring missing albums" in result
        assert "Use `fetch_band_info` prompt" in result
        assert "Use `analyze_band` prompt" in result
    
    def test_health_section_excellent_collection(self):
        """Test health section for excellent collection."""
        bands = [
            BandIndexEntry(
                name="Band 1",
                albums_count=10,
                local_albums_count=10,
                folder_path="Band 1",
                missing_albums_count=0,
                has_metadata=True,
                has_analysis=True
            )
        ]
        
        collection_index = CollectionIndex(bands=bands)
        
        result = _generate_health_section(collection_index)
        
        assert "Collection health looks excellent!" in result


class TestMetadataInfoSection:
    """Test metadata information section generation."""
    
    def test_metadata_info_section(self):
        """Test metadata information section."""
        bands = [
            BandIndexEntry(name="Band 1", albums_count=5, local_albums_count=5, folder_path="Band 1")
        ]
        
        collection_index = CollectionIndex(
            bands=bands,
            last_scan="2024-01-25T14:30:00Z",
            metadata_version="1.0"
        )
        
        result = _generate_metadata_info_section(collection_index)
        
        assert "## ℹ️ Collection Metadata" in result
        assert "| **Last Scan** |" in result
        assert "| **Schema Version** | 1.0 |" in result
        assert "| **Data Source** | `.collection_index.json` |" in result
        assert "| **MCP Resource** | `collection://summary` |" in result
        assert "| **Total Size** | 1 bands, 5 albums |" in result


class TestStatusHelperFunctions:
    """Test status indicator helper functions."""
    
    def test_collection_size_status(self):
        """Test collection size status indicators."""
        assert _get_collection_size_status(150) == "🎭 Large"
        assert _get_collection_size_status(100) == "🎭 Large"  # Boundary case: exactly 100 is large
        assert _get_collection_size_status(50) == "🎭 Medium"
        assert _get_collection_size_status(10) == "🎭 Small"
    
    def test_albums_status(self):
        """Test albums count status indicators."""
        assert _get_albums_status(1500) == "📀 Huge"
        assert _get_albums_status(750) == "📀 Large"
        assert _get_albums_status(200) == "📀 Medium"
        assert _get_albums_status(50) == "📀 Small"
    
    def test_missing_status(self):
        """Test missing albums status indicators."""
        assert _get_missing_status(0) == "✅ None"
        assert _get_missing_status(5) == "🟡 Few"
        assert _get_missing_status(25) == "🟠 Some"
        assert _get_missing_status(100) == "🔴 Many"
    
    def test_completion_status(self):
        """Test completion percentage status indicators."""
        assert _get_completion_status(98.5) == "🟢 Excellent"
        assert _get_completion_status(85.0) == "🟡 Good"
        assert _get_completion_status(70.0) == "🟠 Fair"
        assert _get_completion_status(40.0) == "🔴 Poor"
    
    def test_avg_albums_status(self):
        """Test average albums per band status indicators."""
        assert _get_avg_albums_status(10.0) == "🎵 High"
        assert _get_avg_albums_status(6.5) == "🎵 Good"
        assert _get_avg_albums_status(4.0) == "🎵 Fair"
        assert _get_avg_albums_status(2.0) == "🎵 Low"
    
    def test_metadata_status(self):
        """Test metadata coverage status indicators."""
        assert _get_metadata_status(0, 0) == "⚪ N/A"
        assert _get_metadata_status(18, 20) == "🟢 Excellent"  # 90%
        assert _get_metadata_status(14, 20) == "🟡 Good"      # 70%
        assert _get_metadata_status(10, 20) == "🟠 Fair"      # 50%
        assert _get_metadata_status(5, 20) == "🔴 Poor"       # 25%
    
    def test_metadata_coverage_status(self):
        """Test metadata coverage percentage status indicators."""
        assert _get_metadata_coverage_status(95.0) == "🟢 Excellent"
        assert _get_metadata_coverage_status(75.0) == "🟡 Good"
        assert _get_metadata_coverage_status(55.0) == "🟠 Fair"
        assert _get_metadata_coverage_status(25.0) == "🔴 Poor"


class TestErrorMessages:
    """Test error message generation."""
    
    def test_no_collection_message(self):
        """Test message generation when no collection exists."""
        result = _generate_no_collection_message()
        
        assert "# 🎵 Music Collection Summary" in result
        assert "❌ No Collection Data Available" in result
        assert "Getting Started" in result
        assert "scan_music_folders" in result
        assert "Collection Structure" in result
    
    def test_error_message(self):
        """Test generic error message generation."""
        error_text = "File not found"
        result = _generate_error_message(error_text)
        
        assert "# 🎵 Music Collection Summary" in result
        assert "⚠️ Error Loading Collection Data" in result
        assert "File not found" in result
        assert "Troubleshooting" in result
        assert "Recovery Options" in result


class TestIntegrationScenarios:
    """Test complete integration scenarios."""
    
    def test_large_diverse_collection(self):
        """Test complete summary for large, diverse collection."""
        bands = []
        
        # Create diverse collection
        for i in range(100):
            albums_count = (i % 20) + 1  # 1-20 albums
            missing_count = (i % 5)  # 0-4 missing
            local_count = albums_count - missing_count
            band = BandIndexEntry(
                name=f"Band {i}",
                albums_count=albums_count,
                local_albums_count=local_count,
                folder_path=f"Band {i}",
                missing_albums_count=missing_count,
                has_metadata=(i % 3 == 0),  # 1/3 have metadata
                has_analysis=(i % 4 == 0)   # 1/4 have analysis
            )
            bands.append(band)
        
        insights = CollectionInsight(
            insights=["Large and diverse collection", "Good completion rate"],
            recommendations=["Add more metadata", "Analyze top bands"],
            top_rated_bands=["Band 5", "Band 10", "Band 15"],
            collection_health="Good"
        )
        
        collection_index = CollectionIndex(bands=bands, insights=insights)
        
        result = _generate_collection_markdown(collection_index)
        
        # Verify all major sections are present
        assert "# 🎵 Music Collection Summary" in result
        assert "🎭 **Large Collection**" in result
        assert "## 📊 Quick Overview" in result
        assert "## 📈 Detailed Statistics" in result
        assert "## 🎸 Band Distribution" in result
        assert "## 🔍 Missing Albums Analysis" in result
        assert "## 💡 Collection Insights" in result
        assert "## 🏥 Collection Health" in result
        assert "## ℹ️ Collection Metadata" in result
        
        # Verify statistics are calculated
        assert "| **Total Bands** | 100 |" in result
        assert "Large and diverse collection" in result
    
    def test_small_incomplete_collection(self):
        """Test summary for small collection with many missing albums."""
        bands = [
            BandIndexEntry(
                name="Pink Floyd",
                albums_count=15,
                local_albums_count=3,
                folder_path="Pink Floyd",
                missing_albums_count=12,
                has_metadata=False,
                has_analysis=False
            ),
            BandIndexEntry(
                name="The Beatles",
                albums_count=13,
                local_albums_count=3,
                folder_path="The Beatles",
                missing_albums_count=10,
                has_metadata=False,
                has_analysis=False
            )
        ]
        
        collection_index = CollectionIndex(bands=bands)
        
        result = _generate_collection_markdown(collection_index)
        
        assert "🎭 **Small Collection**" in result
        assert "🔴 **Poor Completion**" in result
        assert "## 🔍 Missing Albums Analysis" in result
        assert "Consider acquiring missing albums" in result
        assert "Use `fetch_band_info` prompt" in result 
