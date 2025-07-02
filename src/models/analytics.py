"""
Advanced Album Analysis and Insights Module

This module provides comprehensive collection analytics, recommendations, and health scoring
for music collections. It analyzes album distribution, edition prevalence, and generates
personalized insights and recommendations.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
from enum import Enum
import statistics
from collections import defaultdict

from .band import Album, AlbumType, BandMetadata, BandAnalysis, AlbumAnalysis
from .collection import CollectionStats, CollectionIndex, BandIndexEntry
from .validation import get_album_type_distribution, get_edition_distribution, filter_albums_by_type


class CollectionMaturityLevel(str, Enum):
    """
    Collection maturity levels based on variety and completeness.
    """
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate" 
    ADVANCED = "Advanced"
    EXPERT = "Expert"
    MASTER = "Master"


class RecommendationType(str, Enum):
    """
    Types of recommendations for collection improvement.
    """
    MISSING_TYPE = "Missing Type"
    EDITION_UPGRADE = "Edition Upgrade"
    SIMILAR_BAND = "Similar Band"
    GENRE_EXPANSION = "Genre Expansion"
    COMPLIANCE_FIX = "Compliance Fix"
    RARE_FIND = "Rare Find"
    COMPLETION = "Collection Completion"


class TypeRecommendation(BaseModel):
    """
    Recommendation for a specific album type for a band.
    """
    model_config = ConfigDict(use_enum_values=True)
    
    band_name: str = Field(..., description="Name of the band")
    album_type: AlbumType = Field(..., description="Recommended album type")
    priority: str = Field(..., description="Priority level: High, Medium, Low")
    reason: str = Field(..., description="Reason for recommendation")
    suggested_albums: List[str] = Field(default_factory=list, description="Specific album suggestions")
    likelihood: float = Field(default=0.0, ge=0, le=1, description="Likelihood this type exists")


class EditionUpgrade(BaseModel):
    """
    Recommendation to upgrade an album to a better edition.
    """
    band_name: str = Field(..., description="Name of the band")
    album_name: str = Field(..., description="Name of the album")
    current_edition: str = Field(..., description="Current edition (e.g., Standard)")
    suggested_edition: str = Field(..., description="Suggested edition (e.g., Deluxe)")
    benefits: List[str] = Field(default_factory=list, description="Benefits of upgrading")
    priority: str = Field(..., description="Priority level: High, Medium, Low")


class CollectionHealthMetrics(BaseModel):
    """
    Comprehensive collection health assessment.
    """
    overall_score: int = Field(default=0, ge=0, le=100, description="Overall health score")
    type_diversity_score: int = Field(default=0, ge=0, le=100, description="Album type diversity score")
    genre_diversity_score: int = Field(default=0, ge=0, le=100, description="Genre diversity score")
    completion_score: int = Field(default=0, ge=0, le=100, description="Collection completion score")
    organization_score: int = Field(default=0, ge=0, le=100, description="Organization quality score")
    quality_score: int = Field(default=0, ge=0, le=100, description="Collection quality score")
    
    strengths: List[str] = Field(default_factory=list, description="Collection strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Areas for improvement")
    recommendations: List[str] = Field(default_factory=list, description="Health improvement recommendations")
    
    def get_health_level(self) -> str:
        """Get overall health level based on score."""
        if self.overall_score >= 90:
            return "Excellent"
        elif self.overall_score >= 75:
            return "Good"
        elif self.overall_score >= 60:
            return "Fair"
        elif self.overall_score >= 40:
            return "Poor"
        else:
            return "Critical"


class TypeAnalysis(BaseModel):
    """
    Analysis of album types in the collection.
    """
    type_distribution: Dict[str, int] = Field(default_factory=dict, description="Count by album type")
    type_percentages: Dict[str, float] = Field(default_factory=dict, description="Percentage by album type")
    missing_types: List[str] = Field(default_factory=list, description="Album types not represented")
    dominant_types: List[str] = Field(default_factory=list, description="Most common album types")
    rare_types: List[str] = Field(default_factory=list, description="Least common album types")
    type_diversity_score: float = Field(default=0.0, ge=0, le=100, description="Type diversity score")
    
    # Type-specific insights
    album_to_ep_ratio: float = Field(default=0.0, description="Ratio of Albums to EPs")
    live_percentage: float = Field(default=0.0, description="Percentage of live albums")
    demo_percentage: float = Field(default=0.0, description="Percentage of demo albums")
    compilation_percentage: float = Field(default=0.0, description="Percentage of compilations")


class EditionAnalysis(BaseModel):
    """
    Analysis of album editions in the collection.
    """
    edition_distribution: Dict[str, int] = Field(default_factory=dict, description="Count by edition type")
    edition_percentages: Dict[str, float] = Field(default_factory=dict, description="Percentage by edition type")
    deluxe_percentage: float = Field(default=0.0, description="Percentage of deluxe editions")
    remaster_percentage: float = Field(default=0.0, description="Percentage of remastered albums")
    limited_percentage: float = Field(default=0.0, description="Percentage of limited editions")
    standard_percentage: float = Field(default=0.0, description="Percentage of standard editions")
    upgrade_opportunities: List[EditionUpgrade] = Field(default_factory=list, description="Edition upgrade suggestions")


class AdvancedCollectionInsights(BaseModel):
    """
    Advanced collection insights and analytics.
    """
    model_config = ConfigDict(use_enum_values=True)
    
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Generation timestamp")
    collection_maturity: CollectionMaturityLevel = Field(default=CollectionMaturityLevel.BEGINNER, description="Collection maturity level")
    health_metrics: CollectionHealthMetrics = Field(default_factory=CollectionHealthMetrics, description="Health assessment")
    type_analysis: TypeAnalysis = Field(default_factory=TypeAnalysis, description="Album type analysis")
    edition_analysis: EditionAnalysis = Field(default_factory=EditionAnalysis, description="Edition analysis")
    
    # Recommendations
    type_recommendations: List[TypeRecommendation] = Field(default_factory=list, description="Album type recommendations")
    edition_upgrades: List[EditionUpgrade] = Field(default_factory=list, description="Edition upgrade suggestions")
    
    # Collection patterns
    decade_distribution: Dict[str, int] = Field(default_factory=dict, description="Albums by decade")
    genre_trends: Dict[str, float] = Field(default_factory=dict, description="Genre popularity trends")
    band_completion_rates: Dict[str, float] = Field(default_factory=dict, description="Completion rate by band")
    
    # Advanced metrics
    collection_value_score: int = Field(default=0, ge=0, le=100, description="Collection value/rarity score")
    discovery_potential: int = Field(default=0, ge=0, le=100, description="Potential for new discoveries")
    organization_recommendations: List[str] = Field(default_factory=list, description="Organization improvement suggestions")


class AlbumSearchFilters(BaseModel):
    """
    Advanced search filters for albums.
    """
    model_config = ConfigDict(use_enum_values=True)
    
    album_types: Optional[List[AlbumType]] = Field(default=None, description="Filter by album types")
    year_min: Optional[int] = Field(default=None, ge=1950, le=2030, description="Minimum year")
    year_max: Optional[int] = Field(default=None, ge=1950, le=2030, description="Maximum year")
    decades: Optional[List[str]] = Field(default=None, description="Filter by decades (e.g., '1970s')")
    editions: Optional[List[str]] = Field(default=None, description="Filter by edition types")
    genres: Optional[List[str]] = Field(default=None, description="Filter by genres")
    bands: Optional[List[str]] = Field(default=None, description="Filter by band names")
    has_rating: Optional[bool] = Field(default=None, description="Filter by whether album has rating")
    min_rating: Optional[int] = Field(default=None, ge=1, le=10, description="Minimum rating")
    max_rating: Optional[int] = Field(default=None, ge=1, le=10, description="Maximum rating")
    is_local: Optional[bool] = Field(default=None, description="Filter by local vs missing status")
    track_count_min: Optional[int] = Field(default=None, ge=1, description="Minimum track count")
    track_count_max: Optional[int] = Field(default=None, ge=1, description="Maximum track count")


class CollectionAnalyzer:
    """
    Advanced collection analyzer for generating insights and recommendations.
    """
    
    # Reference distributions for healthy collections (used for scoring)
    IDEAL_TYPE_DISTRIBUTION = {
        AlbumType.ALBUM.value: 55.0,
        AlbumType.EP.value: 15.0,
        AlbumType.DEMO.value: 10.0,
        AlbumType.LIVE.value: 8.0,
        AlbumType.COMPILATION.value: 5.0,
        AlbumType.INSTRUMENTAL.value: 4.0,
        AlbumType.SPLIT.value: 2.0,
        AlbumType.SINGLE.value: 1.0
    }
    
    MATURITY_THRESHOLDS = {
        CollectionMaturityLevel.BEGINNER: {"bands": 1, "albums": 1, "types": 1},
        CollectionMaturityLevel.INTERMEDIATE: {"bands": 10, "albums": 25, "types": 3},
        CollectionMaturityLevel.ADVANCED: {"bands": 25, "albums": 75, "types": 5},
        CollectionMaturityLevel.EXPERT: {"bands": 50, "albums": 200, "types": 6},
        CollectionMaturityLevel.MASTER: {"bands": 100, "albums": 500, "types": 7}
    }
    
    @classmethod
    def analyze_collection(cls, collection_index: CollectionIndex, band_metadata: Dict[str, BandMetadata]) -> AdvancedCollectionInsights:
        """
        Perform comprehensive collection analysis.
        
        Args:
            collection_index: Collection index with basic statistics
            band_metadata: Dictionary of band metadata by band name
            
        Returns:
            Advanced collection insights
        """
        # Gather all albums from all bands
        all_albums = []
        all_local_albums = []
        all_missing_albums = []
        
        for band_name, metadata in band_metadata.items():
            all_albums.extend(metadata.albums)
            all_albums.extend(metadata.albums_missing)
            all_local_albums.extend(metadata.albums)
            all_missing_albums.extend(metadata.albums_missing)
        
        # Perform various analyses
        type_analysis = cls._analyze_album_types(all_albums)
        edition_analysis = cls._analyze_editions(all_albums)
        health_metrics = cls._calculate_health_metrics(collection_index, all_albums, band_metadata)
        maturity_level = cls._determine_maturity_level(collection_index, band_metadata)
        
        # Generate recommendations
        type_recommendations = cls._generate_type_recommendations(band_metadata)
        edition_upgrades = cls._generate_edition_upgrades(all_local_albums)
        
        # Calculate additional metrics
        decade_distribution = cls._calculate_decade_distribution(all_albums)
        genre_trends = cls._analyze_genre_trends(band_metadata)
        completion_rates = cls._calculate_completion_rates(band_metadata)
        value_score = cls._calculate_value_score(all_albums, band_metadata)
        discovery_potential = cls._calculate_discovery_potential(band_metadata)
        org_recommendations = cls._generate_organization_recommendations(collection_index, band_metadata)
        
        return AdvancedCollectionInsights(
            collection_maturity=maturity_level,
            health_metrics=health_metrics,
            type_analysis=type_analysis,
            edition_analysis=edition_analysis,
            type_recommendations=type_recommendations,
            edition_upgrades=edition_upgrades,
            decade_distribution=decade_distribution,
            genre_trends=genre_trends,
            band_completion_rates=completion_rates,
            collection_value_score=value_score,
            discovery_potential=discovery_potential,
            organization_recommendations=org_recommendations
        )
    
    @classmethod
    def _analyze_album_types(cls, albums: List[Album]) -> TypeAnalysis:
        """Analyze album type distribution and patterns."""
        if not albums:
            return TypeAnalysis()
        
        # Get distribution
        distribution = get_album_type_distribution(albums)
        total_albums = len(albums)
        
        # Calculate percentages
        percentages = {
            album_type: (count / total_albums) * 100 
            for album_type, count in distribution.items()
        }
        
        # Identify missing types
        all_types = {t.value for t in AlbumType}
        present_types = set(distribution.keys())
        missing_types = list(all_types - present_types)
        
        # Identify dominant and rare types
        sorted_types = sorted(distribution.items(), key=lambda x: x[1], reverse=True)
        dominant_types = [t[0] for t in sorted_types[:3]]
        rare_types = [t[0] for t in sorted_types[-2:] if t[1] <= 2]
        
        # Calculate diversity score (based on how well distribution matches ideal)
        diversity_score = cls._calculate_type_diversity_score(percentages)
        
        # Calculate specific ratios
        album_count = distribution.get(AlbumType.ALBUM.value, 0)
        ep_count = distribution.get(AlbumType.EP.value, 0)
        album_to_ep_ratio = album_count / max(ep_count, 1)
        
        live_percentage = percentages.get(AlbumType.LIVE.value, 0)
        demo_percentage = percentages.get(AlbumType.DEMO.value, 0)
        compilation_percentage = percentages.get(AlbumType.COMPILATION.value, 0)
        
        return TypeAnalysis(
            type_distribution=distribution,
            type_percentages=percentages,
            missing_types=missing_types,
            dominant_types=dominant_types,
            rare_types=rare_types,
            type_diversity_score=diversity_score,
            album_to_ep_ratio=album_to_ep_ratio,
            live_percentage=live_percentage,
            demo_percentage=demo_percentage,
            compilation_percentage=compilation_percentage
        )
    
    @classmethod
    def _analyze_editions(cls, albums: List[Album]) -> EditionAnalysis:
        """Analyze album edition distribution and upgrade opportunities."""
        if not albums:
            return EditionAnalysis()
        
        # Get edition distribution
        distribution = get_edition_distribution(albums)
        total_albums = len(albums)
        
        # Calculate percentages
        percentages = {
            edition: (count / total_albums) * 100 
            for edition, count in distribution.items()
        }
        
        # Calculate specific edition percentages
        deluxe_percentage = sum(
            percentages.get(edition, 0) 
            for edition in percentages.keys() 
            if 'deluxe' in edition.lower()
        )
        
        remaster_percentage = sum(
            percentages.get(edition, 0) 
            for edition in percentages.keys() 
            if any(word in edition.lower() for word in ['remaster', 'remastered'])
        )
        
        limited_percentage = sum(
            percentages.get(edition, 0) 
            for edition in percentages.keys() 
            if 'limited' in edition.lower()
        )
        
        standard_percentage = percentages.get("Standard", 0)
        
        return EditionAnalysis(
            edition_distribution=distribution,
            edition_percentages=percentages,
            deluxe_percentage=deluxe_percentage,
            remaster_percentage=remaster_percentage,
            limited_percentage=limited_percentage,
            standard_percentage=standard_percentage
        )
    
    @classmethod
    def _calculate_health_metrics(cls, collection_index: CollectionIndex, albums: List[Album], band_metadata: Dict[str, BandMetadata]) -> CollectionHealthMetrics:
        """Calculate comprehensive collection health metrics."""
        if not albums:
            return CollectionHealthMetrics()
        
        # Type diversity score
        type_analysis = cls._analyze_album_types(albums)
        type_diversity_score = type_analysis.type_diversity_score
        
        # Genre diversity score
        all_genres = set()
        for metadata in band_metadata.values():
            all_genres.update(metadata.genres)
        genre_diversity_score = min(len(all_genres) * 5, 100)  # 5 points per genre, max 100
        
        # Completion score (based on local vs missing albums)
        completion_score = collection_index.stats.completion_percentage
        
        # Organization score (placeholder - could be enhanced with compliance data)
        organization_score = 75  # Default good organization
        
        # Quality score (based on ratings if available)
        quality_score = cls._calculate_quality_score(band_metadata)
        
        # Overall score (weighted average)
        overall_score = int(
            type_diversity_score * 0.25 +
            genre_diversity_score * 0.20 +
            completion_score * 0.20 +
            organization_score * 0.20 +
            quality_score * 0.15
        )
        
        # Generate strengths and weaknesses
        strengths, weaknesses, recommendations = cls._analyze_health_factors(
            type_diversity_score, genre_diversity_score, completion_score, 
            organization_score, quality_score, collection_index
        )
        
        return CollectionHealthMetrics(
            overall_score=overall_score,
            type_diversity_score=int(type_diversity_score),
            genre_diversity_score=genre_diversity_score,
            completion_score=int(completion_score),
            organization_score=organization_score,
            quality_score=quality_score,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations
        )
    
    @classmethod
    def _determine_maturity_level(cls, collection_index: CollectionIndex, band_metadata: Dict[str, BandMetadata]) -> CollectionMaturityLevel:
        """Determine collection maturity level based on size and diversity."""
        total_bands = collection_index.stats.total_bands
        total_albums = collection_index.stats.total_albums
        
        # Count unique album types
        all_albums = []
        for metadata in band_metadata.values():
            all_albums.extend(metadata.albums)
            all_albums.extend(metadata.albums_missing)
        
        unique_types = len(set(album.type for album in all_albums))
        
        # Check against thresholds
        for level in reversed(list(CollectionMaturityLevel)):
            thresholds = cls.MATURITY_THRESHOLDS[level]
            if (total_bands >= thresholds["bands"] and 
                total_albums >= thresholds["albums"] and 
                unique_types >= thresholds["types"]):
                return level
        
        return CollectionMaturityLevel.BEGINNER
    
    @classmethod
    def _generate_type_recommendations(cls, band_metadata: Dict[str, BandMetadata]) -> List[TypeRecommendation]:
        """Generate recommendations for missing album types."""
        recommendations = []
        
        for band_name, metadata in band_metadata.items():
            all_albums = metadata.albums + metadata.albums_missing
            if not all_albums:
                continue
            
            present_types = {album.type for album in all_albums}
            
            # Recommend common missing types
            if AlbumType.EP not in present_types and len(all_albums) >= 2:
                recommendations.append(TypeRecommendation(
                    band_name=band_name,
                    album_type=AlbumType.EP,
                    priority="Medium",
                    reason="Most bands have EP releases between albums",
                    likelihood=0.7
                ))
            
            if AlbumType.LIVE not in present_types and len(all_albums) >= 3:
                recommendations.append(TypeRecommendation(
                    band_name=band_name,
                    album_type=AlbumType.LIVE,
                    priority="Low",
                    reason="Popular bands often have live recordings",
                    likelihood=0.6
                ))
            
            if AlbumType.COMPILATION not in present_types and len(all_albums) >= 5:
                recommendations.append(TypeRecommendation(
                    band_name=band_name,
                    album_type=AlbumType.COMPILATION,
                    priority="Low",
                    reason="Established bands typically have greatest hits compilations",
                    likelihood=0.8
                ))
        
        return recommendations[:20]  # Limit to top 20 recommendations
    
    @classmethod
    def _generate_edition_upgrades(cls, local_albums: List[Album]) -> List[EditionUpgrade]:
        """Generate edition upgrade recommendations."""
        upgrades = []
        
        # Group albums by band and name to find upgrade opportunities
        album_groups = defaultdict(list)
        for album in local_albums:
            key = f"{album.album_name}"
            album_groups[key].append(album)
        
        for album_key, album_list in album_groups.items():
            # If we only have standard edition, suggest deluxe
            standard_albums = [a for a in album_list if not a.edition or a.edition.lower() == "standard"]
            
            if standard_albums and len(standard_albums) == len(album_list):
                album = standard_albums[0]
                # Extract band name from folder path or similar
                band_name = "Unknown Band"  # Would need better band identification
                
                upgrades.append(EditionUpgrade(
                    band_name=band_name,
                    album_name=album.album_name,
                    current_edition=album.edition or "Standard",
                    suggested_edition="Deluxe Edition",
                    benefits=["Bonus tracks", "Enhanced audio quality", "Additional artwork"],
                    priority="Low"
                ))
        
        return upgrades[:10]  # Limit to top 10 upgrade suggestions
    
    @classmethod
    def _calculate_decade_distribution(cls, albums: List[Album]) -> Dict[str, int]:
        """Calculate album distribution by decade."""
        decade_counts = defaultdict(int)
        
        for album in albums:
            if album.year and album.year.isdigit():
                year = int(album.year)
                decade = f"{(year // 10) * 10}s"
                decade_counts[decade] += 1
        
        return dict(decade_counts)
    
    @classmethod
    def _analyze_genre_trends(cls, band_metadata: Dict[str, BandMetadata]) -> Dict[str, float]:
        """Analyze genre popularity trends."""
        genre_counts = defaultdict(int)
        total_bands = len(band_metadata)
        
        for metadata in band_metadata.values():
            for genre in metadata.genres:
                genre_counts[genre] += 1
        
        # Convert to percentages
        genre_trends = {
            genre: (count / total_bands) * 100 
            for genre, count in genre_counts.items()
        }
        
        return dict(sorted(genre_trends.items(), key=lambda x: x[1], reverse=True))
    
    @classmethod
    def _calculate_completion_rates(cls, band_metadata: Dict[str, BandMetadata]) -> Dict[str, float]:
        """Calculate completion rates by band."""
        completion_rates = {}
        
        for band_name, metadata in band_metadata.items():
            total_albums = len(metadata.albums) + len(metadata.albums_missing)
            local_albums = len(metadata.albums)
            
            if total_albums > 0:
                completion_rate = (local_albums / total_albums) * 100
                completion_rates[band_name] = round(completion_rate, 1)
        
        return completion_rates
    
    @classmethod
    def _calculate_type_diversity_score(cls, actual_percentages: Dict[str, float]) -> float:
        """Calculate how well the collection matches ideal type distribution."""
        if not actual_percentages:
            return 0.0
        
        # Calculate deviation from ideal distribution
        total_deviation = 0.0
        
        for album_type, ideal_percentage in cls.IDEAL_TYPE_DISTRIBUTION.items():
            actual_percentage = actual_percentages.get(album_type, 0.0)
            deviation = abs(ideal_percentage - actual_percentage)
            total_deviation += deviation
        
        # Convert deviation to score (lower deviation = higher score)
        max_possible_deviation = sum(cls.IDEAL_TYPE_DISTRIBUTION.values())
        score = max(0, 100 - (total_deviation / max_possible_deviation) * 100)
        
        return score
    
    @classmethod
    def _calculate_quality_score(cls, band_metadata: Dict[str, BandMetadata]) -> int:
        """Calculate overall collection quality score based on ratings."""
        all_ratings = []
        
        for metadata in band_metadata.values():
            if metadata.analyze:
                if metadata.analyze.rate > 0:
                    all_ratings.append(metadata.analyze.rate)
                
                for album_analysis in metadata.analyze.albums:
                    if album_analysis.rate > 0:
                        all_ratings.append(album_analysis.rate)
        
        if not all_ratings:
            return 75  # Default score when no ratings available
        
        # Convert average rating (1-10) to score (0-100)
        avg_rating = statistics.mean(all_ratings)
        quality_score = int((avg_rating / 10) * 100)
        
        return quality_score
    
    @classmethod
    def _analyze_health_factors(cls, type_score: float, genre_score: int, completion_score: float, 
                               org_score: int, quality_score: int, collection_index: CollectionIndex) -> Tuple[List[str], List[str], List[str]]:
        """Analyze health factors to generate strengths, weaknesses, and recommendations."""
        strengths = []
        weaknesses = []
        recommendations = []
        
        # Analyze type diversity
        if type_score >= 75:
            strengths.append("Excellent album type diversity")
        elif type_score < 50:
            weaknesses.append("Limited album type variety")
            recommendations.append("Consider adding EPs, live albums, and compilations")
        
        # Analyze genre diversity
        if genre_score >= 80:
            strengths.append("Outstanding genre diversity")
        elif genre_score < 40:
            weaknesses.append("Limited genre representation")
            recommendations.append("Explore bands from different genres")
        
        # Analyze completion
        if completion_score >= 90:
            strengths.append("Excellent collection completion rate")
        elif completion_score < 70:
            weaknesses.append("Many missing albums")
            recommendations.append("Focus on acquiring missing albums from favorite bands")
        
        # Analyze collection size
        if collection_index.stats.total_bands >= 50:
            strengths.append("Large, comprehensive collection")
        elif collection_index.stats.total_bands < 10:
            weaknesses.append("Small collection size")
            recommendations.append("Gradually expand collection with new bands")
        
        # Analyze quality
        if quality_score >= 80:
            strengths.append("High-quality, well-rated collection")
        elif quality_score < 60:
            weaknesses.append("Consider adding more highly-rated albums")
            recommendations.append("Research top-rated albums in your preferred genres")
        
        return strengths, weaknesses, recommendations
    
    @classmethod
    def _calculate_value_score(cls, albums: List[Album], band_metadata: Dict[str, BandMetadata]) -> int:
        """Calculate collection value/rarity score."""
        value_factors = 0
        total_factors = 0
        
        # Factor 1: Limited editions
        limited_editions = [a for a in albums if a.edition and 'limited' in a.edition.lower()]
        if albums:
            limited_ratio = len(limited_editions) / len(albums)
            value_factors += limited_ratio * 20
            total_factors += 20
        
        # Factor 2: Early albums (pre-1980)
        early_albums = [a for a in albums if a.year and a.year.isdigit() and int(a.year) < 1980]
        if albums:
            early_ratio = len(early_albums) / len(albums)
            value_factors += early_ratio * 15
            total_factors += 15
        
        # Factor 3: Demo recordings
        demos = [a for a in albums if a.type == AlbumType.DEMO]
        if albums:
            demo_ratio = len(demos) / len(albums)
            value_factors += demo_ratio * 25
            total_factors += 25
        
        # Factor 4: Instrumental versions
        instrumentals = [a for a in albums if a.type == AlbumType.INSTRUMENTAL]
        if albums:
            instrumental_ratio = len(instrumentals) / len(albums)
            value_factors += instrumental_ratio * 20
            total_factors += 20
        
        # Factor 5: Split releases
        splits = [a for a in albums if a.type == AlbumType.SPLIT]
        if albums:
            split_ratio = len(splits) / len(albums)
            value_factors += split_ratio * 20
            total_factors += 20
        
        if total_factors > 0:
            return int(value_factors)
        else:
            return 50  # Default middle score
    
    @classmethod
    def _calculate_discovery_potential(cls, band_metadata: Dict[str, BandMetadata]) -> int:
        """Calculate potential for discovering new music."""
        discovery_factors = 0
        
        # Factor 1: Missing albums provide discovery opportunities
        total_missing = sum(len(metadata.albums_missing) for metadata in band_metadata.values())
        if total_missing > 50:
            discovery_factors += 30
        elif total_missing > 20:
            discovery_factors += 20
        elif total_missing > 10:
            discovery_factors += 15
        else:
            discovery_factors += 10
        
        # Factor 2: Similar bands not in collection
        similar_bands_missing = []
        for metadata in band_metadata.values():
            if metadata.analyze:
                similar_bands_missing.extend(metadata.analyze.similar_bands_missing)
        
        unique_similar_missing = len(set(similar_bands_missing))
        if unique_similar_missing > 50:
            discovery_factors += 30
        elif unique_similar_missing > 25:
            discovery_factors += 20
        elif unique_similar_missing > 10:
            discovery_factors += 15
        else:
            discovery_factors += 10
        
        # Factor 3: Genre diversity suggests openness to discovery
        all_genres = set()
        for metadata in band_metadata.values():
            all_genres.update(metadata.genres)
        
        if len(all_genres) > 10:
            discovery_factors += 25
        elif len(all_genres) > 5:
            discovery_factors += 15
        else:
            discovery_factors += 10
        
        # Factor 4: Collection maturity suggests discovery capability
        total_bands = len(band_metadata)
        if total_bands > 100:
            discovery_factors += 15
        elif total_bands > 50:
            discovery_factors += 10
        else:
            discovery_factors += 5
        
        return min(discovery_factors, 100)
    
    @classmethod
    def _generate_organization_recommendations(cls, collection_index: CollectionIndex, band_metadata: Dict[str, BandMetadata]) -> List[str]:
        """Generate organization improvement recommendations."""
        recommendations = []
        
        # Basic recommendations based on collection size
        if collection_index.stats.total_bands > 50:
            recommendations.append("Consider organizing albums by type (Album, EP, Live, etc.) for better browsing")
        
        if collection_index.stats.total_missing_albums > 20:
            recommendations.append("Create a wishlist to track missing albums for future acquisition")
        
        # Check for bands with many missing albums
        high_missing_bands = [
            name for name, metadata in band_metadata.items()
            if len(metadata.albums_missing) > len(metadata.albums)
        ]
        
        if high_missing_bands:
            recommendations.append(f"Focus on completing collections for {len(high_missing_bands)} bands with many missing albums")
        
        # Check for unrated content
        unrated_bands = [
            name for name, metadata in band_metadata.items()
            if not metadata.analyze or metadata.analyze.rate == 0
        ]
        
        if len(unrated_bands) > 5:
            recommendations.append("Add ratings and reviews to help track your favorite content")
        
        return recommendations


class AdvancedSearchEngine:
    """
    Advanced search engine for complex album queries.
    """
    
    @classmethod
    def search_albums(cls, band_metadata: Dict[str, BandMetadata], filters: AlbumSearchFilters) -> Dict[str, List[Album]]:
        """
        Perform advanced album search across all bands.
        
        Args:
            band_metadata: Dictionary of band metadata
            filters: Search filters to apply
            
        Returns:
            Dictionary mapping band names to matching albums
        """
        results = {}
        
        for band_name, metadata in band_metadata.items():
            all_albums = metadata.albums + metadata.albums_missing
            matching_albums = cls._filter_albums(all_albums, filters, metadata)
            
            if matching_albums:
                results[band_name] = matching_albums
        
        return results
    
    @classmethod
    def _filter_albums(cls, albums: List[Album], filters: AlbumSearchFilters, band_metadata: BandMetadata) -> List[Album]:
        """Apply filters to album list."""
        filtered_albums = albums
        
        # Filter by album types
        if filters.album_types:
            filtered_albums = [a for a in filtered_albums if a.type in filters.album_types]
        
        # Filter by year range
        if filters.year_min or filters.year_max:
            filtered_albums = cls._filter_by_year_range(filtered_albums, filters.year_min, filters.year_max)
        
        # Filter by decades
        if filters.decades:
            filtered_albums = cls._filter_by_decades(filtered_albums, filters.decades)
        
        # Filter by editions
        if filters.editions:
            filtered_albums = [a for a in filtered_albums if a.edition in filters.editions]
        
        # Filter by genres (check band genres)
        if filters.genres:
            if any(genre in band_metadata.genres for genre in filters.genres):
                pass  # Keep all albums from this band
            else:
                filtered_albums = []  # Remove all albums if band doesn't match genre
        
        # Filter by bands
        if filters.bands:
            if band_metadata.band_name not in filters.bands:
                filtered_albums = []
        
        # Filter by ratings
        if filters.has_rating is not None or filters.min_rating or filters.max_rating:
            filtered_albums = cls._filter_by_ratings(filtered_albums, filters, band_metadata)
        
        # Filter by local/missing status
        if filters.is_local is not None:
            if filters.is_local:
                # Only local albums
                filtered_albums = [a for a in filtered_albums if a in band_metadata.albums]
            else:
                # Only missing albums
                filtered_albums = [a for a in filtered_albums if a in band_metadata.albums_missing]
        
        # Filter by track count
        if filters.track_count_min or filters.track_count_max:
            filtered_albums = cls._filter_by_track_count(filtered_albums, filters.track_count_min, filters.track_count_max)
        
        return filtered_albums
    
    @classmethod
    def _filter_by_year_range(cls, albums: List[Album], year_min: Optional[int], year_max: Optional[int]) -> List[Album]:
        """Filter albums by year range."""
        filtered = []
        for album in albums:
            if not album.year or not album.year.isdigit():
                continue
            
            year = int(album.year)
            if year_min and year < year_min:
                continue
            if year_max and year > year_max:
                continue
            
            filtered.append(album)
        
        return filtered
    
    @classmethod
    def _filter_by_decades(cls, albums: List[Album], decades: List[str]) -> List[Album]:
        """Filter albums by decades."""
        filtered = []
        for album in albums:
            if not album.year or not album.year.isdigit():
                continue
            
            year = int(album.year)
            decade = f"{(year // 10) * 10}s"
            
            if decade in decades:
                filtered.append(album)
        
        return filtered
    
    @classmethod
    def _filter_by_ratings(cls, albums: List[Album], filters: AlbumSearchFilters, band_metadata: BandMetadata) -> List[Album]:
        """Filter albums by rating criteria."""
        if not band_metadata.analyze:
            return [] if filters.has_rating else albums
        
        filtered = []
        for album in albums:
            # Find album analysis
            album_analysis = None
            for analysis in band_metadata.analyze.albums:
                if analysis.album_name == album.album_name:
                    album_analysis = analysis
                    break
            
            # Check rating filters
            if filters.has_rating is not None:
                has_rating = album_analysis is not None and album_analysis.rate > 0
                if filters.has_rating != has_rating:
                    continue
            
            if filters.min_rating and (not album_analysis or album_analysis.rate < filters.min_rating):
                continue
            
            if filters.max_rating and (not album_analysis or album_analysis.rate > filters.max_rating):
                continue
            
            filtered.append(album)
        
        return filtered
    
    @classmethod
    def _filter_by_track_count(cls, albums: List[Album], min_count: Optional[int], max_count: Optional[int]) -> List[Album]:
        """Filter albums by track count."""
        filtered = []
        for album in albums:
            if min_count and album.track_count < min_count:
                continue
            if max_count and album.track_count > max_count:
                continue
            
            filtered.append(album)
        
        return filtered


# Export all new classes
__all__ = [
    'CollectionMaturityLevel',
    'RecommendationType', 
    'TypeRecommendation',
    'EditionUpgrade',
    'CollectionHealthMetrics',
    'TypeAnalysis',
    'EditionAnalysis',
    'AdvancedCollectionInsights',
    'AlbumSearchFilters',
    'CollectionAnalyzer',
    'AdvancedSearchEngine'
] 