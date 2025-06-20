"""
Comprehensive tests for advanced analytics functionality.

This module tests all components of the advanced album analysis and insights system
including collection analysis, health metrics, recommendations, and search capabilities.
"""

import pytest
from datetime import datetime
from typing import Dict, List

from models.analytics import (
    CollectionAnalyzer, AdvancedSearchEngine, AlbumSearchFilters,
    CollectionMaturityLevel, TypeRecommendation, EditionUpgrade,
    CollectionHealthMetrics, TypeAnalysis, EditionAnalysis,
    AdvancedCollectionInsights
)
from models.band import Album, AlbumType, BandMetadata, BandAnalysis, AlbumAnalysis
from models.collection import CollectionIndex, CollectionStats, BandIndexEntry


class TestCollectionAnalyzer:
    """Test suite for CollectionAnalyzer class."""
    
    def setup_method(self):
        """Set up test data."""
        # Create test albums with various types and editions
        self.test_albums = [
            Album(
                album_name="Master of Puppets",
                year="1986",
                type=AlbumType.ALBUM,
                edition="",
                track_count=8,
                genres=["Thrash Metal"]
            ),
            Album(
                album_name="Creeping Death EP",
                year="1984",
                type=AlbumType.EP,
                edition="",
                track_count=4,
                genres=["Thrash Metal"]
            ),
            Album(
                album_name="Live After Death",
                year="1985",
                type=AlbumType.LIVE,
                edition="Deluxe Edition",
                track_count=12,
                genres=["Heavy Metal"]
            ),
            Album(
                album_name="No Life 'Til Leather",
                year="1982",
                type=AlbumType.DEMO,
                edition="Demo",
                track_count=7,
                genres=["Thrash Metal"]
            ),
            Album(
                album_name="Best of the Beast",
                year="1996",
                type=AlbumType.COMPILATION,
                edition="",
                track_count=16,
                genres=["Heavy Metal"]
            )
        ]
        
        # Create test band metadata
        self.test_band_metadata = {
            "Metallica": BandMetadata(
                band_name="Metallica",
                formed="1981",
                genres=["Thrash Metal", "Heavy Metal"],
                origin="USA",
                albums=[self.test_albums[0], self.test_albums[1]],  # Local albums
                albums_missing=[self.test_albums[3]],  # Missing demo
                analyze=BandAnalysis(
                    rate=9,
                    review="Legendary thrash metal band",
                    albums=[
                        AlbumAnalysis(album_name="Master of Puppets", rate=10, review="Masterpiece"),
                        AlbumAnalysis(album_name="Creeping Death EP", rate=8, review="Great EP")
                    ]
                )
            ),
            "Iron Maiden": BandMetadata(
                band_name="Iron Maiden", 
                formed="1975",
                genres=["Heavy Metal"],
                origin="UK",
                albums=[self.test_albums[2]],  # Live album
                albums_missing=[self.test_albums[4]],  # Missing compilation
                analyze=BandAnalysis(
                    rate=8,
                    review="Iconic heavy metal band",
                    albums=[
                        AlbumAnalysis(album_name="Live After Death", rate=9, review="Epic live performance")
                    ]
                )
            )
        }
        
        # Create test collection index
        self.test_collection_index = CollectionIndex(
            stats=CollectionStats(
                total_bands=2,
                total_albums=5,
                total_local_albums=3,
                total_missing_albums=2,
                bands_with_metadata=2,
                completion_percentage=60.0
            ),
            bands=[
                BandIndexEntry(
                    name="Metallica",
                    albums_count=3,
                    local_albums_count=2,
                    folder_path="Metallica",
                    missing_albums_count=1,
                    has_metadata=True,
                    has_analysis=True
                ),
                BandIndexEntry(
                    name="Iron Maiden",
                    albums_count=2,
                    local_albums_count=1,
                    folder_path="Iron Maiden",
                    missing_albums_count=1,
                    has_metadata=True,
                    has_analysis=True
                )
            ]
        )
    
    def test_analyze_collection(self):
        """Test complete collection analysis."""
        insights = CollectionAnalyzer.analyze_collection(
            self.test_collection_index,
            self.test_band_metadata
        )
        
        assert isinstance(insights, AdvancedCollectionInsights)
        assert insights.collection_maturity == CollectionMaturityLevel.BEGINNER
        assert isinstance(insights.health_metrics, CollectionHealthMetrics)
        assert isinstance(insights.type_analysis, TypeAnalysis)
        assert isinstance(insights.edition_analysis, EditionAnalysis)
        
        # Check that recommendations are generated
        assert isinstance(insights.type_recommendations, list)
        assert isinstance(insights.edition_upgrades, list)
        assert isinstance(insights.organization_recommendations, list)
    
    def test_analyze_album_types(self):
        """Test album type analysis."""
        all_albums = []
        for metadata in self.test_band_metadata.values():
            all_albums.extend(metadata.albums)
            all_albums.extend(metadata.albums_missing)
        
        type_analysis = CollectionAnalyzer._analyze_album_types(all_albums)
        
        assert isinstance(type_analysis, TypeAnalysis)
        assert "Album" in type_analysis.type_distribution
        assert "EP" in type_analysis.type_distribution
        assert "Live" in type_analysis.type_distribution
        assert "Demo" in type_analysis.type_distribution
        assert "Compilation" in type_analysis.type_distribution
        
        # Check percentages
        assert type_analysis.type_percentages["Album"] == 20.0  # 1 out of 5 albums
        assert type_analysis.type_percentages["EP"] == 20.0
        
        # Check missing types
        assert "Instrumental" in type_analysis.missing_types or "Split" in type_analysis.missing_types
        
        # Check diversity score is calculated
        assert 0 <= type_analysis.type_diversity_score <= 100
    
    def test_analyze_editions(self):
        """Test edition analysis."""
        all_albums = []
        for metadata in self.test_band_metadata.values():
            all_albums.extend(metadata.albums)
            all_albums.extend(metadata.albums_missing)
        
        edition_analysis = CollectionAnalyzer._analyze_editions(all_albums)
        
        assert isinstance(edition_analysis, EditionAnalysis)
        assert "Standard" in edition_analysis.edition_distribution
        assert "Deluxe Edition" in edition_analysis.edition_distribution
        
        # Check percentages
        assert edition_analysis.deluxe_percentage == 20.0  # 1 deluxe out of 5 albums
        assert edition_analysis.standard_percentage > 0
    
    def test_calculate_health_metrics(self):
        """Test health metrics calculation."""
        all_albums = []
        for metadata in self.test_band_metadata.values():
            all_albums.extend(metadata.albums)
            all_albums.extend(metadata.albums_missing)
        
        health_metrics = CollectionAnalyzer._calculate_health_metrics(
            self.test_collection_index,
            all_albums,
            self.test_band_metadata
        )
        
        assert isinstance(health_metrics, CollectionHealthMetrics)
        assert 0 <= health_metrics.overall_score <= 100
        assert 0 <= health_metrics.type_diversity_score <= 100
        assert 0 <= health_metrics.genre_diversity_score <= 100
        assert health_metrics.completion_score == 60.0  # From collection index
        
        # Check health level
        health_level = health_metrics.get_health_level()
        assert health_level in ["Excellent", "Good", "Fair", "Poor", "Critical"]
        
        # Check that lists are populated
        assert isinstance(health_metrics.strengths, list)
        assert isinstance(health_metrics.weaknesses, list)
        assert isinstance(health_metrics.recommendations, list)
    
    def test_determine_maturity_level(self):
        """Test maturity level determination."""
        maturity = CollectionAnalyzer._determine_maturity_level(
            self.test_collection_index,
            self.test_band_metadata
        )
        
        assert isinstance(maturity, CollectionMaturityLevel)
        # With 2 bands, 5 albums, should be Beginner or Intermediate
        assert maturity in [CollectionMaturityLevel.BEGINNER, CollectionMaturityLevel.INTERMEDIATE]
    
    def test_generate_type_recommendations(self):
        """Test type recommendation generation."""
        recommendations = CollectionAnalyzer._generate_type_recommendations(
            self.test_band_metadata
        )
        
        assert isinstance(recommendations, list)
        for rec in recommendations:
            assert isinstance(rec, TypeRecommendation)
            assert rec.band_name in self.test_band_metadata.keys()
            # album_type is now serialized as string due to use_enum_values=True
            assert isinstance(rec.album_type, str)
            assert rec.album_type in [at.value for at in AlbumType]
            assert rec.priority in ["High", "Medium", "Low"]
            assert 0 <= rec.likelihood <= 1
    
    def test_calculate_decade_distribution(self):
        """Test decade distribution calculation."""
        all_albums = []
        for metadata in self.test_band_metadata.values():
            all_albums.extend(metadata.albums)
            all_albums.extend(metadata.albums_missing)
        
        decade_dist = CollectionAnalyzer._calculate_decade_distribution(all_albums)
        
        assert isinstance(decade_dist, dict)
        assert "1980s" in decade_dist  # Albums from 1982, 1984, 1985, 1986
        assert "1990s" in decade_dist  # Album from 1996
        assert decade_dist["1980s"] == 4
        assert decade_dist["1990s"] == 1
    
    def test_analyze_genre_trends(self):
        """Test genre trend analysis."""
        genre_trends = CollectionAnalyzer._analyze_genre_trends(self.test_band_metadata)
        
        assert isinstance(genre_trends, dict)
        assert "Thrash Metal" in genre_trends
        assert "Heavy Metal" in genre_trends
        
        # Check percentages are calculated correctly
        assert genre_trends["Thrash Metal"] == 50.0  # 1 out of 2 bands
        assert genre_trends["Heavy Metal"] == 100.0  # 2 out of 2 bands (both have it)
    
    def test_calculate_completion_rates(self):
        """Test completion rate calculation."""
        completion_rates = CollectionAnalyzer._calculate_completion_rates(
            self.test_band_metadata
        )
        
        assert isinstance(completion_rates, dict)
        assert "Metallica" in completion_rates
        assert "Iron Maiden" in completion_rates
        
        # Metallica: 2 local, 1 missing = 66.7%
        assert abs(completion_rates["Metallica"] - 66.7) < 0.1
        # Iron Maiden: 1 local, 1 missing = 50.0%
        assert completion_rates["Iron Maiden"] == 50.0
    
    def test_calculate_value_score(self):
        """Test collection value score calculation."""
        all_albums = []
        for metadata in self.test_band_metadata.values():
            all_albums.extend(metadata.albums)
            all_albums.extend(metadata.albums_missing)
        
        value_score = CollectionAnalyzer._calculate_value_score(
            all_albums,
            self.test_band_metadata
        )
        
        assert isinstance(value_score, int)
        assert 0 <= value_score <= 100
    
    def test_calculate_discovery_potential(self):
        """Test discovery potential calculation."""
        discovery_potential = CollectionAnalyzer._calculate_discovery_potential(
            self.test_band_metadata
        )
        
        assert isinstance(discovery_potential, int)
        assert 0 <= discovery_potential <= 100
    
    def test_empty_collection_analysis(self):
        """Test analysis with empty collection."""
        empty_collection = CollectionIndex()
        empty_metadata = {}
        
        insights = CollectionAnalyzer.analyze_collection(empty_collection, empty_metadata)
        
        assert isinstance(insights, AdvancedCollectionInsights)
        assert insights.collection_maturity == CollectionMaturityLevel.BEGINNER
        assert insights.health_metrics.overall_score == 0
        assert len(insights.type_recommendations) == 0


class TestAdvancedSearchEngine:
    """Test suite for AdvancedSearchEngine class."""
    
    def setup_method(self):
        """Set up test data."""
                # Create test albums with various attributes
        self.test_albums = [
            Album(
                album_name="Master of Puppets",
                year="1986",
                type=AlbumType.ALBUM,
                edition="",
                track_count=8,
                genres=["Thrash Metal"]
            ),
            Album(
                album_name="Ride the Lightning",
                year="1984",
                type=AlbumType.ALBUM,
                edition="Deluxe Edition",
                track_count=12,
                genres=["Thrash Metal"]
            ),
            Album(
                album_name="Creeping Death EP",
                year="1984",
                type=AlbumType.EP,
                edition="",
                track_count=4,
                genres=["Thrash Metal"]
            ),
            Album(
                album_name="Live After Death",
                year="1985",
                type=AlbumType.LIVE,
                edition="",
                track_count=10,
                genres=["Heavy Metal"]
            )
        ]

        # Create band metadata with analysis
        self.test_band_metadata = {
            "Metallica": BandMetadata(
                band_name="Metallica",
                formed="1981",
                genres=["Thrash Metal"],
                albums=[self.test_albums[0], self.test_albums[2]],  # Master of Puppets + EP
                albums_missing=[self.test_albums[1]],  # Ride the Lightning missing
                analyze=BandAnalysis(
                    rate=9,
                    albums=[
                        AlbumAnalysis(album_name="Master of Puppets", rate=10),
                        AlbumAnalysis(album_name="Creeping Death EP", rate=8)
                    ]
                )
            ),
            "Iron Maiden": BandMetadata(
                band_name="Iron Maiden",
                formed="1975",
                genres=["Heavy Metal"],
                albums=[self.test_albums[3]],  # Live album
                albums_missing=[]
            )
        }
    
    def test_search_albums_no_filters(self):
        """Test search with no filters."""
        filters = AlbumSearchFilters()
        results = AdvancedSearchEngine.search_albums(self.test_band_metadata, filters)
        
        assert isinstance(results, dict)
        assert "Metallica" in results
        assert "Iron Maiden" in results
        
        # Should return all albums (local + missing)
        metallica_albums = results["Metallica"]
        assert len(metallica_albums) == 3  # 2 local + 1 missing
        
        iron_maiden_albums = results["Iron Maiden"] 
        assert len(iron_maiden_albums) == 1
    
    def test_search_by_album_types(self):
        """Test search by album types."""
        filters = AlbumSearchFilters(album_types=[AlbumType.EP])
        results = AdvancedSearchEngine.search_albums(self.test_band_metadata, filters)
        
        assert "Metallica" in results
        assert len(results["Metallica"]) == 1
        assert results["Metallica"][0].album_name == "Creeping Death EP"
        
        # Iron Maiden should not appear (no EPs)
        assert "Iron Maiden" not in results
    
    def test_search_by_year_range(self):
        """Test search by year range."""
        filters = AlbumSearchFilters(year_min=1985, year_max=1986)
        results = AdvancedSearchEngine.search_albums(self.test_band_metadata, filters)
        
        # Should find Master of Puppets (1986) and Live After Death (1985)
        total_albums = sum(len(albums) for albums in results.values())
        assert total_albums == 2  # 1 Master of Puppets + 1 Live After Death
    
    def test_search_by_decades(self):
        """Test search by decades."""
        filters = AlbumSearchFilters(decades=["1980s"])
        results = AdvancedSearchEngine.search_albums(self.test_band_metadata, filters)
        
        # All test albums are from 1980s
        total_albums = sum(len(albums) for albums in results.values())
        assert total_albums == 4
    
    def test_search_by_editions(self):
        """Test search by editions."""
        filters = AlbumSearchFilters(editions=["Deluxe Edition"])
        results = AdvancedSearchEngine.search_albums(self.test_band_metadata, filters)
        
        assert "Metallica" in results
        assert len(results["Metallica"]) == 1
        assert results["Metallica"][0].edition == "Deluxe Edition"
        assert results["Metallica"][0].album_name == "Ride the Lightning"
    
    def test_search_by_genres(self):
        """Test search by genres."""
        filters = AlbumSearchFilters(genres=["Heavy Metal"])
        results = AdvancedSearchEngine.search_albums(self.test_band_metadata, filters)
        
        # Should only find Iron Maiden (Heavy Metal genre)
        assert "Iron Maiden" in results
        assert "Metallica" not in results  # Thrash Metal, not Heavy Metal
    
    def test_search_by_bands(self):
        """Test search by specific bands."""
        filters = AlbumSearchFilters(bands=["Metallica"])
        results = AdvancedSearchEngine.search_albums(self.test_band_metadata, filters)
        
        assert "Metallica" in results
        assert "Iron Maiden" not in results
        assert len(results["Metallica"]) == 3
    
    def test_search_by_ratings(self):
        """Test search by rating criteria."""
        filters = AlbumSearchFilters(has_rating=True, min_rating=9)
        results = AdvancedSearchEngine.search_albums(self.test_band_metadata, filters)
        
        # Should find Master of Puppets (rated 10)
        assert "Metallica" in results
        found_albums = [album.album_name for album in results["Metallica"]]
        assert "Master of Puppets" in found_albums
        
        # Should not find Creeping Death EP (rated 8, below min_rating 9)
        assert "Creeping Death EP" not in found_albums
    
    def test_search_by_local_status(self):
        """Test search by local vs missing status."""
        # Search for local albums only
        filters = AlbumSearchFilters(is_local=True)
        results = AdvancedSearchEngine.search_albums(self.test_band_metadata, filters)
        
        # Should find 3 local albums total
        total_albums = sum(len(albums) for albums in results.values())
        assert total_albums == 3
        
        # Search for missing albums only  
        filters = AlbumSearchFilters(is_local=False)
        results = AdvancedSearchEngine.search_albums(self.test_band_metadata, filters)
        
        # Should find 1 missing album (Ride the Lightning Deluxe)
        total_albums = sum(len(albums) for albums in results.values())
        assert total_albums == 1
    
    def test_search_by_track_count(self):
        """Test search by track count range."""
        filters = AlbumSearchFilters(track_count_min=8, track_count_max=12)
        results = AdvancedSearchEngine.search_albums(self.test_band_metadata, filters)
        
        # Should find albums with 8-12 tracks
        found_albums = []
        for albums in results.values():
            found_albums.extend(albums)
        
        for album in found_albums:
            assert 8 <= album.track_count <= 12
    
    def test_combined_filters(self):
        """Test search with multiple filters combined."""
        filters = AlbumSearchFilters(
            album_types=[AlbumType.ALBUM],
            year_min=1986,
            is_local=True
        )
        results = AdvancedSearchEngine.search_albums(self.test_band_metadata, filters)
        
        # Should find only local Album-type albums from 1986 or later
        assert "Metallica" in results
        assert len(results["Metallica"]) == 1
        found_album = results["Metallica"][0]
        assert found_album.album_name == "Master of Puppets"
        assert found_album.type == AlbumType.ALBUM
        assert found_album.year == "1986"
    
    def test_no_results_filters(self):
        """Test search with filters that yield no results."""
        filters = AlbumSearchFilters(
            album_types=[AlbumType.SINGLE],  # No singles in test data
            year_min=2000  # No albums from 2000+
        )
        results = AdvancedSearchEngine.search_albums(self.test_band_metadata, filters)
        
        assert len(results) == 0
    
    def test_filter_by_year_range_edge_cases(self):
        """Test year range filtering edge cases."""
        # Albums with no year
        album_no_year = Album(album_name="No Year Album", year="", type=AlbumType.ALBUM)
        test_metadata = {
            "Test Band": BandMetadata(
                band_name="Test Band",
                albums=[album_no_year],
                albums_missing=[]
            )
        }
        
        filters = AlbumSearchFilters(year_min=1980, year_max=1990)
        results = AdvancedSearchEngine.search_albums(test_metadata, filters)
        
        # Albums with no year should be excluded
        assert len(results) == 0
    
    def test_filter_by_decades_edge_cases(self):
        """Test decade filtering edge cases."""
        # Test decade boundary years
        album_1980 = Album(album_name="1980 Album", year="1980", type=AlbumType.ALBUM)
        album_1989 = Album(album_name="1989 Album", year="1989", type=AlbumType.ALBUM)
        
        test_metadata = {
            "Test Band": BandMetadata(
                band_name="Test Band",
                albums=[album_1980, album_1989],
                albums_missing=[]
            )
        }
        
        filters = AlbumSearchFilters(decades=["1980s"])
        results = AdvancedSearchEngine.search_albums(test_metadata, filters)
        
        # Both should be included in 1980s
        assert "Test Band" in results
        assert len(results["Test Band"]) == 2


class TestAlbumSearchFilters:
    """Test suite for AlbumSearchFilters model."""
    
    def test_default_filters(self):
        """Test default filter creation."""
        filters = AlbumSearchFilters()
        
        assert filters.album_types is None
        assert filters.year_min is None
        assert filters.year_max is None
        assert filters.decades is None
        assert filters.editions is None
        assert filters.genres is None
        assert filters.bands is None
        assert filters.has_rating is None
        assert filters.min_rating is None
        assert filters.max_rating is None
        assert filters.is_local is None
        assert filters.track_count_min is None
        assert filters.track_count_max is None
    
    def test_filter_validation(self):
        """Test filter validation."""
        # Valid filters
        filters = AlbumSearchFilters(
            year_min=1980,
            year_max=2020,
            min_rating=1,
            max_rating=10,
            track_count_min=1
        )
        assert filters.year_min == 1980
        assert filters.year_max == 2020
        assert filters.min_rating == 1
        assert filters.max_rating == 10
        assert filters.track_count_min == 1
    
    def test_invalid_year_range(self):
        """Test invalid year range validation."""
        with pytest.raises(Exception):
            AlbumSearchFilters(year_min=1949)  # Below minimum
        
        with pytest.raises(Exception):
            AlbumSearchFilters(year_max=2031)  # Above maximum
    
    def test_invalid_rating_range(self):
        """Test invalid rating range validation."""
        with pytest.raises(Exception):
            AlbumSearchFilters(min_rating=0)  # Below minimum
        
        with pytest.raises(Exception):
            AlbumSearchFilters(max_rating=11)  # Above maximum


class TestTypeRecommendation:
    """Test suite for TypeRecommendation model."""
    
    def test_type_recommendation_creation(self):
        """Test TypeRecommendation model creation."""
        rec = TypeRecommendation(
            band_name="Test Band",
            album_type=AlbumType.EP,
            priority="High",
            reason="Band needs EP releases",
            suggested_albums=["EP Vol. 1", "EP Vol. 2"],
            likelihood=0.8
        )
        
        assert rec.band_name == "Test Band"
        assert rec.album_type == AlbumType.EP
        assert rec.priority == "High"
        assert rec.reason == "Band needs EP releases"
        assert len(rec.suggested_albums) == 2
        assert rec.likelihood == 0.8
    
    def test_likelihood_validation(self):
        """Test likelihood range validation."""
        # Valid likelihood
        rec = TypeRecommendation(
            band_name="Test",
            album_type=AlbumType.ALBUM,
            priority="Medium",
            reason="Test",
            likelihood=0.5
        )
        assert rec.likelihood == 0.5
        
        # Test boundary values
        rec_min = TypeRecommendation(
            band_name="Test",
            album_type=AlbumType.ALBUM,
            priority="Low",
            reason="Test",
            likelihood=0.0
        )
        assert rec_min.likelihood == 0.0
        
        rec_max = TypeRecommendation(
            band_name="Test",
            album_type=AlbumType.ALBUM,
            priority="High",
            reason="Test",
            likelihood=1.0
        )
        assert rec_max.likelihood == 1.0


class TestEditionUpgrade:
    """Test suite for EditionUpgrade model."""
    
    def test_edition_upgrade_creation(self):
        """Test EditionUpgrade model creation."""
        upgrade = EditionUpgrade(
            band_name="Test Band",
            album_name="Test Album",
            current_edition="Standard",
            suggested_edition="Deluxe Edition",
            benefits=["Bonus tracks", "Enhanced audio"],
            priority="Medium"
        )
        
        assert upgrade.band_name == "Test Band"
        assert upgrade.album_name == "Test Album"
        assert upgrade.current_edition == "Standard"
        assert upgrade.suggested_edition == "Deluxe Edition"
        assert len(upgrade.benefits) == 2
        assert upgrade.priority == "Medium"


class TestCollectionHealthMetrics:
    """Test suite for CollectionHealthMetrics model."""
    
    def test_health_metrics_creation(self):
        """Test CollectionHealthMetrics creation."""
        metrics = CollectionHealthMetrics(
            overall_score=85,
            type_diversity_score=80,
            genre_diversity_score=90,
            completion_score=75,
            organization_score=85,
            quality_score=88,
            strengths=["Great genre diversity", "High completion rate"],
            weaknesses=["Limited album types"],
            recommendations=["Add more EPs", "Improve organization"]
        )
        
        assert metrics.overall_score == 85
        assert metrics.type_diversity_score == 80
        assert metrics.genre_diversity_score == 90
        assert metrics.completion_score == 75
        assert metrics.organization_score == 85
        assert metrics.quality_score == 88
        assert len(metrics.strengths) == 2
        assert len(metrics.weaknesses) == 1
        assert len(metrics.recommendations) == 2
    
    def test_get_health_level(self):
        """Test health level determination."""
        # Test all health levels
        excellent = CollectionHealthMetrics(overall_score=95)
        assert excellent.get_health_level() == "Excellent"
        
        good = CollectionHealthMetrics(overall_score=80)
        assert good.get_health_level() == "Good"
        
        fair = CollectionHealthMetrics(overall_score=65)
        assert fair.get_health_level() == "Fair"
        
        poor = CollectionHealthMetrics(overall_score=45)
        assert poor.get_health_level() == "Poor"
        
        critical = CollectionHealthMetrics(overall_score=20)
        assert critical.get_health_level() == "Critical"
    
    def test_score_range_validation(self):
        """Test score range validation."""
        # Valid scores
        metrics = CollectionHealthMetrics(
            overall_score=50,
            type_diversity_score=0,
            genre_diversity_score=100
        )
        assert metrics.overall_score == 50
        assert metrics.type_diversity_score == 0
        assert metrics.genre_diversity_score == 100


class TestAdvancedCollectionInsights:
    """Test suite for AdvancedCollectionInsights model."""
    
    def test_insights_creation(self):
        """Test AdvancedCollectionInsights creation."""
        insights = AdvancedCollectionInsights(
            collection_maturity=CollectionMaturityLevel.ADVANCED,
            health_metrics=CollectionHealthMetrics(overall_score=85),
            type_analysis=TypeAnalysis(),
            edition_analysis=EditionAnalysis(),
            collection_value_score=75,
            discovery_potential=80
        )
        
        assert insights.collection_maturity == CollectionMaturityLevel.ADVANCED
        assert insights.health_metrics.overall_score == 85
        assert isinstance(insights.type_analysis, TypeAnalysis)
        assert isinstance(insights.edition_analysis, EditionAnalysis)
        assert insights.collection_value_score == 75
        assert insights.discovery_potential == 80
        
        # Check that generated_at is set
        assert insights.generated_at is not None
        assert isinstance(insights.generated_at, str)
    
    def test_default_values(self):
        """Test default values for AdvancedCollectionInsights."""
        insights = AdvancedCollectionInsights()
        
        assert insights.collection_maturity == CollectionMaturityLevel.BEGINNER
        assert isinstance(insights.health_metrics, CollectionHealthMetrics)
        assert isinstance(insights.type_analysis, TypeAnalysis)
        assert isinstance(insights.edition_analysis, EditionAnalysis)
        assert isinstance(insights.type_recommendations, list)
        assert isinstance(insights.edition_upgrades, list)
        assert isinstance(insights.decade_distribution, dict)
        assert isinstance(insights.genre_trends, dict)
        assert isinstance(insights.band_completion_rates, dict)
        assert insights.collection_value_score == 0
        assert insights.discovery_potential == 0
        assert isinstance(insights.organization_recommendations, list)


if __name__ == "__main__":
    pytest.main([__file__]) 
