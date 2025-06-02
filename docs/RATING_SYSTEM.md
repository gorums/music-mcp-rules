# Rating System and Validation Rules with Album Type Classification

## Overview

The Music Collection MCP Server implements a comprehensive rating system for bands and albums, providing standardized evaluation criteria, validation rules, and analysis capabilities. This document details the rating methodology, validation logic, integration patterns, and the enhanced features for album type classification and folder structure compliance.

## Rating Scale

### 1-10 Point Scale

The system uses a **1-10 integer rating scale** for both bands and albums:

| Rating | Classification | Description |
|--------|---------------|-------------|
| **10** | Masterpiece | Perfect or near-perfect; essential listening |
| **9** | Excellent | Outstanding quality; highly recommended |
| **8** | Very Good | Strong quality; recommended |
| **7** | Good | Solid quality; worth listening to |
| **6** | Above Average | Decent quality; has merit |
| **5** | Average | Standard quality; acceptable |
| **4** | Below Average | Weak quality; limited appeal |
| **3** | Poor | Significant flaws; questionable value |
| **2** | Bad | Major problems; generally not recommended |
| **1** | Awful | Extremely poor; to be avoided |

### Rating Philosophy

#### Objective Criteria
- **Musical Composition**: Songwriting quality, structure, innovation
- **Performance Quality**: Technical skill, expression, cohesion
- **Production Value**: Sound quality, mixing, recording techniques
- **Historical Significance**: Influence, innovation, cultural impact
- **Artistic Merit**: Creativity, originality, artistic vision

#### Subjective Elements
- **Personal Enjoyment**: Individual taste and preference
- **Emotional Impact**: Connection and resonance
- **Repeat Listening Value**: Long-term appeal
- **Context Appreciation**: Understanding within genre/era

#### Album Type Considerations

Different album types may be evaluated with adjusted criteria:

##### Studio Albums (Album type)
- **Production Quality**: Highest expectations for studio polish
- **Songwriting**: Complete creative expression evaluation
- **Cohesion**: Album flow and thematic consistency
- **Innovation**: Artistic advancement and genre evolution

##### Live Albums (Live type)
- **Performance Energy**: Crowd interaction and band chemistry
- **Song Interpretation**: Live arrangements vs. studio versions
- **Audio Quality**: Recording/mixing quality in live setting
- **Historical Value**: Significance of the performance/venue

##### Compilations (Compilation type)
- **Track Selection**: Quality and representativeness of chosen songs
- **Curation**: Logical flow and narrative structure
- **Completeness**: Coverage of band's career phases
- **Accessibility**: Introduction value for new listeners

##### EPs (EP type)
- **Focus**: Concentrated artistic statement within shorter format
- **Quality Density**: High quality across fewer tracks
- **Purpose**: Clear artistic or experimental intention
- **Standalone Value**: Merit independent of full albums

##### Demo Albums (Demo type)
- **Historical Significance**: Insight into band's development
- **Raw Energy**: Unpolished but authentic expression
- **Rarity Value**: Unique or unreleased material
- **Evolution Documentation**: Shows artistic progression

##### Singles (Single type)
- **Commercial Appeal**: Accessibility and hook strength
- **Radio Quality**: Production suited for broadcast
- **Standalone Merit**: Quality independent of album context
- **Cultural Impact**: Chart performance and cultural significance

## Data Models and Validation with Album Types

### Enhanced Band Rating Model

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from enum import Enum

class AlbumType(str, Enum):
    """Album type enumeration for classification."""
    ALBUM = "Album"
    COMPILATION = "Compilation"
    EP = "EP"
    LIVE = "Live"
    SINGLE = "Single"
    DEMO = "Demo"
    INSTRUMENTAL = "Instrumental"
    SPLIT = "Split"

class BandAnalysis(BaseModel):
    """Analysis and rating data for a band with type-aware validation."""
    
    review: Optional[str] = Field(None, max_length=5000)
    rate: Optional[int] = Field(None, ge=1, le=10)
    similar_bands: List[str] = Field(default_factory=list)
    
    # Enhanced album analysis with type support
    albums: List['AlbumAnalysis'] = Field(default_factory=list)
    
    # Analysis metadata
    analysis_date: Optional[str] = Field(None)
    reviewer: Optional[str] = Field(None)
    
    # Type-based statistics
    type_distribution: Optional[Dict[str, int]] = Field(default_factory=dict)
    average_rating_by_type: Optional[Dict[str, float]] = Field(default_factory=dict)
    
    @validator('rate')
    def validate_band_rating(cls, v):
        """Validate band rating is within acceptable range."""
        if v is not None:
            if not isinstance(v, int):
                raise ValueError("Rating must be an integer")
            if v < 1 or v > 10:
                raise ValueError("Rating must be between 1 and 10 (inclusive)")
        return v
    
    @validator('review')
    def validate_review_quality(cls, v, values):
        """Validate review meets quality standards with type awareness."""
        if v is not None:
            # Check minimum length for meaningful reviews
            if len(v.strip()) < 10:
                raise ValueError("Review must be at least 10 characters")
            
            # Check for rating consistency
            if 'rate' in values and values['rate'] is not None:
                rating = values['rate']
                v_lower = v.lower()
                
                # Basic consistency checks
                if rating >= 8 and any(word in v_lower for word in ['terrible', 'awful', 'horrible']):
                    raise ValueError("Review content inconsistent with high rating")
                if rating <= 3 and any(word in v_lower for word in ['excellent', 'amazing', 'perfect']):
                    raise ValueError("Review content inconsistent with low rating")
        
        return v
    
    def calculate_type_statistics(self) -> None:
        """Calculate type-based rating statistics."""
        if not self.albums:
            return
        
        # Calculate type distribution
        type_counts = {}
        type_ratings = {}
        
        for album_analysis in self.albums:
            # This would need to be cross-referenced with actual album data
            # for album type information
            album_type = getattr(album_analysis, 'album_type', 'Album')
            
            type_counts[album_type] = type_counts.get(album_type, 0) + 1
            
            if album_analysis.rate is not None:
                if album_type not in type_ratings:
                    type_ratings[album_type] = []
                type_ratings[album_type].append(album_analysis.rate)
        
        self.type_distribution = type_counts
        self.average_rating_by_type = {
            album_type: sum(ratings) / len(ratings)
            for album_type, ratings in type_ratings.items()
        }
```

### Enhanced Album Rating Model

```python
class AlbumAnalysis(BaseModel):
    """Analysis and rating data for a specific album with type awareness."""
    
    album_name: str = Field(..., min_length=1)
    review: Optional[str] = Field(None, max_length=5000)
    rate: Optional[int] = Field(None, ge=1, le=10)
    
    # Album type for context-aware validation
    album_type: Optional[AlbumType] = Field(None)
    
    # Type-specific metrics
    standout_tracks: List[str] = Field(default_factory=list)
    genres: List[str] = Field(default_factory=list)
    
    # Context-specific fields based on album type
    live_venue: Optional[str] = Field(None)  # For Live albums
    compilation_scope: Optional[str] = Field(None)  # For Compilations
    ep_concept: Optional[str] = Field(None)  # For EPs
    demo_period: Optional[str] = Field(None)  # For Demos
    
    @validator('rate')
    def validate_album_rating_with_type_context(cls, v, values):
        """Validate album rating with album type context."""
        if v is not None:
            if not isinstance(v, int):
                raise ValueError("Album rating must be an integer")
            if v < 1 or v > 10:
                raise ValueError("Album rating must be between 1 and 10")
            
            # Type-specific validation
            album_type = values.get('album_type')
            if album_type:
                if album_type == AlbumType.DEMO and v > 8:
                    # Demos rarely achieve the highest ratings due to production limitations
                    pass  # Allow but could warn
                elif album_type == AlbumType.COMPILATION and v < 3:
                    # Compilations should generally be decent due to curated content
                    pass  # Allow but could warn
        
        return v
    
    @validator('album_name')
    def validate_album_reference(cls, v):
        """Ensure album name is properly formatted."""
        if not v or not v.strip():
            raise ValueError("Album name cannot be empty")
        return v.strip()
    
    @validator('review')
    def validate_review_type_appropriateness(cls, v, values):
        """Validate review content is appropriate for album type."""
        if v is not None and 'album_type' in values:
            album_type = values['album_type']
            v_lower = v.lower()
            
            # Type-specific review validation
            if album_type == AlbumType.LIVE:
                # Live album reviews should mention performance aspects
                live_keywords = ['performance', 'energy', 'crowd', 'venue', 'concert', 'audience']
                if not any(keyword in v_lower for keyword in live_keywords):
                    # Warning: Live album review might benefit from performance commentary
                    pass
            
            elif album_type == AlbumType.DEMO:
                # Demo reviews should acknowledge the developmental nature
                demo_keywords = ['early', 'development', 'raw', 'unpolished', 'potential', 'rough']
                if not any(keyword in v_lower for keyword in demo_keywords):
                    # Warning: Demo review might benefit from developmental context
                    pass
        
        return v
```

## Rating Validation Logic with Album Types

### Core Validation Functions

```python
from typing import Optional, Dict, Any, List

class RatingValidator:
    """Comprehensive rating validation system with album type support."""
    
    @staticmethod
    def validate_rating_value(rating: Any) -> Optional[int]:
        """
        Validate individual rating value.
        
        Args:
            rating: Rating value to validate
            
        Returns:
            Validated integer rating or None
            
        Raises:
            ValueError: If rating is invalid
        """
        if rating is None:
            return None
        
        # Type validation
        if isinstance(rating, str):
            try:
                rating = int(rating)
            except ValueError:
                raise ValueError(f"Cannot convert '{rating}' to integer rating")
        
        if not isinstance(rating, int):
            raise ValueError(f"Rating must be integer, got {type(rating)}")
        
        # Range validation
        if rating < 1 or rating > 10:
            raise ValueError(f"Rating {rating} must be between 1 and 10 (inclusive)")
        
        return rating
    
    @staticmethod
    def validate_rating_consistency_with_types(
        band_rating: Optional[int],
        album_ratings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate consistency between band and album ratings with type awareness.
        
        Args:
            band_rating: Overall band rating
            album_ratings: List of album ratings with type information
            
        Returns:
            Validation result with warnings and suggestions
        """
        result = {
            "valid": True,
            "warnings": [],
            "suggestions": [],
            "type_analysis": {}
        }
        
        if not album_ratings:
            return result
        
        # Separate ratings by type
        ratings_by_type = {}
        for album_data in album_ratings:
            album_type = album_data.get('type', 'Album')
            rating = album_data.get('rate')
            
            if rating is not None:
                if album_type not in ratings_by_type:
                    ratings_by_type[album_type] = []
                ratings_by_type[album_type].append(rating)
        
        # Calculate statistics by type
        for album_type, ratings in ratings_by_type.items():
            avg_rating = sum(ratings) / len(ratings)
            max_rating = max(ratings)
            min_rating = min(ratings)
            
            result["type_analysis"][album_type] = {
                "count": len(ratings),
                "average": round(avg_rating, 1),
                "max": max_rating,
                "min": min_rating,
                "range": max_rating - min_rating
            }
        
        # Overall statistics
        all_ratings = [r for ratings in ratings_by_type.values() for r in ratings]
        avg_album_rating = sum(all_ratings) / len(all_ratings)
        max_album_rating = max(all_ratings)
        min_album_rating = min(all_ratings)
        
        if band_rating is not None:
            # Check if band rating is reasonable compared to albums
            if band_rating > max_album_rating + 1:
                result["warnings"].append(
                    f"Band rating ({band_rating}) significantly higher than best album ({max_album_rating})"
                )
            
            if band_rating < min_album_rating - 1:
                result["warnings"].append(
                    f"Band rating ({band_rating}) significantly lower than worst album ({min_album_rating})"
                )
            
            # Type-specific validation
            if 'Album' in ratings_by_type:
                studio_avg = result["type_analysis"]['Album']['average']
                if abs(band_rating - studio_avg) > 2:
                    result["suggestions"].append(
                        f"Band rating ({band_rating}) differs significantly from studio album average ({studio_avg:.1f})"
                    )
            
            # Check for type rating patterns
            if len(ratings_by_type) > 1:
                type_averages = {t: stats['average'] for t, stats in result["type_analysis"].items()}
                
                # Live albums should generally be slightly lower than studio albums
                if 'Album' in type_averages and 'Live' in type_averages:
                    if type_averages['Live'] > type_averages['Album'] + 1:
                        result["suggestions"].append(
                            "Live albums rated higher than studio albums - consider if this reflects actual quality"
                        )
                
                # Demos should generally be lower rated
                if 'Album' in type_averages and 'Demo' in type_averages:
                    if type_averages['Demo'] > type_averages['Album']:
                        result["suggestions"].append(
                            "Demo albums rated higher than studio albums - verify these ratings"
                        )
        
        return result
    
    @staticmethod
    def validate_collection_rating_patterns(collection_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate rating patterns across the entire collection with type analysis.
        
        Args:
            collection_data: List of band data with ratings and album types
            
        Returns:
            Collection-wide validation results and recommendations
        """
        result = {
            "valid": True,
            "warnings": [],
            "recommendations": [],
            "statistics": {
                "total_bands": len(collection_data),
                "rated_bands": 0,
                "type_statistics": {},
                "rating_distribution": {}
            }
        }
        
        all_band_ratings = []
        all_album_ratings_by_type = {}
        rating_distribution = {i: 0 for i in range(1, 11)}
        
        for band_data in collection_data:
            band_rating = band_data.get('rating')
            albums = band_data.get('albums', [])
            
            if band_rating is not None:
                all_band_ratings.append(band_rating)
                rating_distribution[band_rating] += 1
                result["statistics"]["rated_bands"] += 1
            
            # Process album ratings by type
            for album in albums:
                album_type = album.get('type', 'Album')
                album_rating = album.get('rate')
                
                if album_rating is not None:
                    if album_type not in all_album_ratings_by_type:
                        all_album_ratings_by_type[album_type] = []
                    all_album_ratings_by_type[album_type].append(album_rating)
        
        # Calculate type statistics
        for album_type, ratings in all_album_ratings_by_type.items():
            if ratings:
                avg_rating = sum(ratings) / len(ratings)
                result["statistics"]["type_statistics"][album_type] = {
                    "count": len(ratings),
                    "average": round(avg_rating, 1),
                    "max": max(ratings),
                    "min": min(ratings)
                }
        
        result["statistics"]["rating_distribution"] = rating_distribution
        
        # Generate recommendations based on patterns
        if all_band_ratings:
            avg_band_rating = sum(all_band_ratings) / len(all_band_ratings)
            
            if avg_band_rating > 8:
                result["recommendations"].append(
                    "Collection has very high average rating - consider more critical evaluation"
                )
            elif avg_band_rating < 5:
                result["recommendations"].append(
                    "Collection has low average rating - consider focusing on higher quality bands"
                )
        
        # Type-specific recommendations
        type_stats = result["statistics"]["type_statistics"]
        
        if 'Album' in type_stats and 'Live' in type_stats:
            studio_avg = type_stats['Album']['average']
            live_avg = type_stats['Live']['average']
            
            if live_avg > studio_avg + 0.5:
                result["recommendations"].append(
                    "Live albums rated higher than studio albums on average - verify rating criteria"
                )
        
        if 'Demo' in type_stats:
            demo_avg = type_stats['Demo']['average']
            if demo_avg > 7:
                result["recommendations"].append(
                    "Demo albums have high average rating - ensure they're truly exceptional or consider rating adjustment"
                )
        
        return result
```

## Folder Structure Compliance Integration

### Compliance Scoring in Rating Context

```python
class ComplianceAwareRating:
    """Rating system that considers folder structure compliance."""
    
    @staticmethod
    def adjust_rating_for_compliance(
        base_rating: int,
        compliance_score: int,
        include_compliance: bool = False
    ) -> Dict[str, Any]:
        """
        Optionally adjust or contextualize ratings based on folder organization quality.
        
        Args:
            base_rating: The musical quality rating (1-10)
            compliance_score: Folder organization compliance (0-100)
            include_compliance: Whether to include compliance in final assessment
            
        Returns:
            Rating information with optional compliance context
        """
        result = {
            "musical_rating": base_rating,
            "compliance_score": compliance_score,
            "compliance_level": get_compliance_level(compliance_score)
        }
        
        if include_compliance:
            # Optional: Could provide a combined score that considers both music and organization
            # However, musical quality should remain the primary factor
            organization_bonus = min(compliance_score / 100 * 0.5, 0.5)  # Max 0.5 point bonus
            result["organization_adjusted_rating"] = min(base_rating + organization_bonus, 10)
            
            result["notes"] = []
            if compliance_score >= 90:
                result["notes"].append("Excellently organized collection")
            elif compliance_score < 50:
                result["notes"].append("Consider improving folder organization")
        
        return result

def get_compliance_level(score: int) -> str:
    """Convert compliance score to level."""
    if score >= 90:
        return "excellent"
    elif score >= 70:
        return "good"
    elif score >= 50:
        return "fair"
    elif score >= 25:
        return "poor"
    else:
        return "critical"
```

## Advanced Rating Analytics with Album Types

### Type-Specific Rating Trends

```python
class TypeAwareRatingAnalytics:
    """Advanced analytics considering album types and structure compliance."""
    
    def analyze_rating_trends_by_type(self, collection_data: List[Dict]) -> Dict[str, Any]:
        """Analyze how ratings vary by album type across the collection."""
        
        results = {
            "type_comparisons": {},
            "quality_insights": {},
            "recommendations": []
        }
        
        # Group ratings by type
        ratings_by_type = {}
        for band_data in collection_data:
            for album in band_data.get('albums', []):
                album_type = album.get('type', 'Album')
                rating = album.get('rate')
                compliance = album.get('compliance', {}).get('score', 0)
                
                if rating is not None:
                    if album_type not in ratings_by_type:
                        ratings_by_type[album_type] = {
                            'ratings': [],
                            'compliance_scores': []
                        }
                    ratings_by_type[album_type]['ratings'].append(rating)
                    ratings_by_type[album_type]['compliance_scores'].append(compliance)
        
        # Calculate comparative statistics
        for album_type, data in ratings_by_type.items():
            ratings = data['ratings']
            compliance_scores = data['compliance_scores']
            
            if ratings:
                results["type_comparisons"][album_type] = {
                    "count": len(ratings),
                    "average_rating": round(sum(ratings) / len(ratings), 2),
                    "rating_range": max(ratings) - min(ratings),
                    "high_quality_count": len([r for r in ratings if r >= 8]),
                    "average_compliance": round(sum(compliance_scores) / len(compliance_scores), 1) if compliance_scores else 0
                }
        
        # Generate insights
        if 'Album' in results["type_comparisons"] and 'Live' in results["type_comparisons"]:
            studio_avg = results["type_comparisons"]['Album']['average_rating']
            live_avg = results["type_comparisons"]['Live']['average_rating']
            
            if live_avg > studio_avg:
                results["quality_insights"]["live_vs_studio"] = "Live albums rated higher than studio albums on average"
            else:
                results["quality_insights"]["live_vs_studio"] = "Studio albums maintain higher average rating than live albums"
        
        return results
```

This enhanced rating system provides comprehensive evaluation capabilities while maintaining the core focus on musical quality, with optional consideration of album types and organizational factors for a complete collection management experience. 