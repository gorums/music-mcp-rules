# Rating System and Validation Rules

## Overview

The Music Collection MCP Server implements a comprehensive rating system for bands and albums, providing standardized evaluation criteria, validation rules, and analysis capabilities. This document details the rating methodology, validation logic, and integration patterns.

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

## Data Models and Validation

### Band Rating Model

```python
from pydantic import BaseModel, Field, validator
from typing import Optional

class BandAnalysis(BaseModel):
    """Analysis and rating data for a band."""
    
    review: Optional[str] = Field(None, max_length=5000)
    rate: Optional[int] = Field(None, ge=1, le=10)
    similar_bands: List[str] = Field(default_factory=list)
    
    # Analysis metadata
    analysis_date: Optional[str] = Field(None)
    reviewer: Optional[str] = Field(None)
    
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
        """Validate review meets quality standards."""
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
```

### Album Rating Model

```python
class AlbumAnalysis(BaseModel):
    """Analysis and rating data for a specific album."""
    
    album_name: str = Field(..., min_length=1)
    review: Optional[str] = Field(None, max_length=5000)
    rate: Optional[int] = Field(None, ge=1, le=10)
    
    # Album-specific metrics
    standout_tracks: List[str] = Field(default_factory=list)
    genres: List[str] = Field(default_factory=list)
    
    @validator('rate')
    def validate_album_rating(cls, v):
        """Validate album rating follows system rules."""
        if v is not None:
            if not isinstance(v, int):
                raise ValueError("Album rating must be an integer")
            if v < 1 or v > 10:
                raise ValueError("Album rating must be between 1 and 10")
        return v
    
    @validator('album_name')
    def validate_album_reference(cls, v):
        """Ensure album name is properly formatted."""
        if not v or not v.strip():
            raise ValueError("Album name cannot be empty")
        return v.strip()
```

## Rating Validation Logic

### Core Validation Functions

```python
from typing import Optional, Dict, Any, List

class RatingValidator:
    """Comprehensive rating validation system."""
    
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
    def validate_rating_consistency(
        band_rating: Optional[int],
        album_ratings: List[int]
    ) -> Dict[str, Any]:
        """
        Validate consistency between band and album ratings.
        
        Args:
            band_rating: Overall band rating
            album_ratings: List of album ratings for the band
            
        Returns:
            Validation result with warnings and suggestions
        """
        result = {
            "valid": True,
            "warnings": [],
            "suggestions": []
        }
        
        if not album_ratings:
            return result
        
        # Calculate album statistics
        avg_album_rating = sum(album_ratings) / len(album_ratings)
        max_album_rating = max(album_ratings)
        min_album_rating = min(album_ratings)
        
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
            
            # Check against average
            rating_diff = abs(band_rating - avg_album_rating)
            if rating_diff > 2:
                result["warnings"].append(
                    f"Band rating ({band_rating}) differs significantly from album average ({avg_album_rating:.1f})"
                )
                result["suggestions"].append(
                    f"Consider rating closer to album average: {round(avg_album_rating)}"
                )
        
        return result
    
    @staticmethod
    def validate_genre_rating_consistency(
        rating: int,
        genres: List[str],
        genre_rating_norms: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Validate rating against genre norms and expectations.
        
        Args:
            rating: Rating to validate
            genres: Genres associated with the rating
            genre_rating_norms: Expected rating ranges by genre
            
        Returns:
            Validation result with genre-specific feedback
        """
        result = {
            "valid": True,
            "warnings": [],
            "genre_context": []
        }
        
        for genre in genres:
            if genre in genre_rating_norms:
                expected_rating = genre_rating_norms[genre]
                
                # Check if rating is within reasonable range for genre
                if abs(rating - expected_rating) > 2:
                    result["warnings"].append(
                        f"Rating {rating} unusual for {genre} (typical: {expected_rating:.1f})"
                    )
                
                result["genre_context"].append({
                    "genre": genre,
                    "expected_rating": expected_rating,
                    "rating_difference": rating - expected_rating
                })
        
        return result
```

### Advanced Validation Rules

```python
class AdvancedRatingValidator:
    """Advanced validation with context and history."""
    
    def __init__(self):
        self.rating_history: Dict[str, List[int]] = {}
        self.genre_statistics: Dict[str, Dict[str, float]] = {}
    
    def validate_with_context(
        self,
        band_name: str,
        rating: int,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate rating with historical and contextual data.
        
        Args:
            band_name: Name of the band being rated
            rating: Rating value
            context: Additional context (genres, year, etc.)
            
        Returns:
            Comprehensive validation result
        """
        result = {
            "valid": True,
            "rating": rating,
            "warnings": [],
            "suggestions": [],
            "context_analysis": {}
        }
        
        # Basic validation
        try:
            validated_rating = RatingValidator.validate_rating_value(rating)
            if validated_rating is None:
                result["valid"] = False
                return result
        except ValueError as e:
            result["valid"] = False
            result["error"] = str(e)
            return result
        
        # Historical consistency check
        if band_name in self.rating_history:
            previous_ratings = self.rating_history[band_name]
            avg_previous = sum(previous_ratings) / len(previous_ratings)
            
            if abs(rating - avg_previous) > 2:
                result["warnings"].append(
                    f"Rating differs significantly from previous ratings (avg: {avg_previous:.1f})"
                )
        
        # Genre context validation
        if "genres" in context:
            genre_validation = RatingValidator.validate_genre_rating_consistency(
                rating, context["genres"], self.genre_statistics
            )
            result["context_analysis"]["genre_analysis"] = genre_validation
        
        # Year context validation
        if "year" in context:
            year_validation = self._validate_year_context(rating, context["year"])
            result["context_analysis"]["year_analysis"] = year_validation
        
        return result
    
    def _validate_year_context(self, rating: int, year: str) -> Dict[str, Any]:
        """Validate rating against release year context."""
        try:
            release_year = int(year)
            current_year = datetime.now().year
            age = current_year - release_year
            
            # Context-based validation
            result = {"age_context": age}
            
            # Very old albums might have historical significance
            if age > 50 and rating >= 8:
                result["note"] = "High rating for vintage album - consider historical significance"
            
            # Very recent albums with perfect ratings might be premature
            if age < 2 and rating == 10:
                result["warning"] = "Perfect rating for very recent release - allow time for perspective"
            
            return result
            
        except ValueError:
            return {"warning": f"Invalid year format: {year}"}
```

## Rating Analytics and Insights

### Statistical Analysis

```python
class RatingAnalytics:
    """Analytics and insights for rating data."""
    
    def __init__(self, collection_data: Dict[str, Any]):
        self.collection_data = collection_data
    
    def calculate_rating_distribution(self) -> Dict[int, int]:
        """Calculate distribution of ratings across collection."""
        distribution = {i: 0 for i in range(1, 11)}
        
        for band_data in self.collection_data.values():
            if "analyze" in band_data and "rate" in band_data["analyze"]:
                rating = band_data["analyze"]["rate"]
                if rating:
                    distribution[rating] += 1
        
        return distribution
    
    def calculate_average_ratings(self) -> Dict[str, float]:
        """Calculate various average ratings."""
        ratings = []
        album_ratings = []
        
        for band_data in self.collection_data.values():
            # Band ratings
            if "analyze" in band_data and "rate" in band_data["analyze"]:
                rating = band_data["analyze"]["rate"]
                if rating:
                    ratings.append(rating)
            
            # Album ratings
            if "analyze" in band_data and "albums" in band_data["analyze"]:
                for album in band_data["analyze"]["albums"]:
                    if "rate" in album and album["rate"]:
                        album_ratings.append(album["rate"])
        
        return {
            "overall_average": sum(ratings) / len(ratings) if ratings else 0,
            "album_average": sum(album_ratings) / len(album_ratings) if album_ratings else 0,
            "total_rated_bands": len(ratings),
            "total_rated_albums": len(album_ratings)
        }
    
    def analyze_genre_ratings(self) -> Dict[str, Dict[str, float]]:
        """Analyze ratings by genre."""
        genre_ratings = {}
        
        for band_data in self.collection_data.values():
            genres = band_data.get("genres", [])
            band_rating = None
            
            if "analyze" in band_data and "rate" in band_data["analyze"]:
                band_rating = band_data["analyze"]["rate"]
            
            if band_rating and genres:
                for genre in genres:
                    if genre not in genre_ratings:
                        genre_ratings[genre] = []
                    genre_ratings[genre].append(band_rating)
        
        # Calculate statistics for each genre
        genre_stats = {}
        for genre, ratings in genre_ratings.items():
            if ratings:
                genre_stats[genre] = {
                    "average": sum(ratings) / len(ratings),
                    "count": len(ratings),
                    "max": max(ratings),
                    "min": min(ratings),
                    "median": sorted(ratings)[len(ratings) // 2]
                }
        
        return genre_stats
    
    def identify_rating_outliers(self, threshold: float = 2.0) -> List[Dict[str, Any]]:
        """Identify bands with unusual ratings."""
        outliers = []
        all_ratings = []
        
        # Collect all ratings
        for band_data in self.collection_data.values():
            if "analyze" in band_data and "rate" in band_data["analyze"]:
                rating = band_data["analyze"]["rate"]
                if rating:
                    all_ratings.append(rating)
        
        if not all_ratings:
            return outliers
        
        # Calculate mean and standard deviation
        mean_rating = sum(all_ratings) / len(all_ratings)
        variance = sum((r - mean_rating) ** 2 for r in all_ratings) / len(all_ratings)
        std_dev = variance ** 0.5
        
        # Identify outliers
        for band_name, band_data in self.collection_data.items():
            if "analyze" in band_data and "rate" in band_data["analyze"]:
                rating = band_data["analyze"]["rate"]
                if rating:
                    z_score = abs(rating - mean_rating) / std_dev if std_dev > 0 else 0
                    
                    if z_score > threshold:
                        outliers.append({
                            "band_name": band_name,
                            "rating": rating,
                            "z_score": z_score,
                            "deviation": rating - mean_rating,
                            "type": "high" if rating > mean_rating else "low"
                        })
        
        return sorted(outliers, key=lambda x: x["z_score"], reverse=True)
```

### Rating Recommendations

```python
class RatingRecommendationEngine:
    """Generate rating suggestions and recommendations."""
    
    def __init__(self, analytics: RatingAnalytics):
        self.analytics = analytics
    
    def suggest_rating_for_band(
        self,
        band_data: Dict[str, Any],
        similar_bands: List[str] = None
    ) -> Dict[str, Any]:
        """
        Suggest a rating for a band based on various factors.
        
        Args:
            band_data: Band metadata
            similar_bands: List of similar bands for comparison
            
        Returns:
            Rating suggestion with reasoning
        """
        suggestion = {
            "suggested_rating": None,
            "confidence": 0.0,
            "reasoning": [],
            "factors": {}
        }
        
        factors = []
        
        # Factor 1: Genre-based suggestion
        if "genres" in band_data:
            genre_stats = self.analytics.analyze_genre_ratings()
            genre_ratings = []
            
            for genre in band_data["genres"]:
                if genre in genre_stats:
                    genre_ratings.append(genre_stats[genre]["average"])
                    suggestion["reasoning"].append(
                        f"Genre '{genre}' typically rated {genre_stats[genre]['average']:.1f}"
                    )
            
            if genre_ratings:
                genre_average = sum(genre_ratings) / len(genre_ratings)
                factors.append(("genre", genre_average, 0.3))
        
        # Factor 2: Similar bands comparison
        if similar_bands:
            similar_ratings = []
            for similar_band in similar_bands:
                if similar_band in self.analytics.collection_data:
                    similar_data = self.analytics.collection_data[similar_band]
                    if "analyze" in similar_data and "rate" in similar_data["analyze"]:
                        similar_rating = similar_data["analyze"]["rate"]
                        if similar_rating:
                            similar_ratings.append(similar_rating)
            
            if similar_ratings:
                similar_average = sum(similar_ratings) / len(similar_ratings)
                factors.append(("similar_bands", similar_average, 0.4))
                suggestion["reasoning"].append(
                    f"Similar bands average {similar_average:.1f} ({len(similar_ratings)} bands)"
                )
        
        # Factor 3: Collection average
        collection_avg = self.analytics.calculate_average_ratings()["overall_average"]
        if collection_avg > 0:
            factors.append(("collection_average", collection_avg, 0.2))
            suggestion["reasoning"].append(f"Collection average is {collection_avg:.1f}")
        
        # Factor 4: Album ratings if available
        if "analyze" in band_data and "albums" in band_data["analyze"]:
            album_ratings = [
                album["rate"] for album in band_data["analyze"]["albums"]
                if "rate" in album and album["rate"]
            ]
            
            if album_ratings:
                album_average = sum(album_ratings) / len(album_ratings)
                factors.append(("album_average", album_average, 0.5))
                suggestion["reasoning"].append(
                    f"Album ratings average {album_average:.1f} ({len(album_ratings)} albums)"
                )
        
        # Calculate weighted suggestion
        if factors:
            weighted_sum = sum(rating * weight for _, rating, weight in factors)
            total_weight = sum(weight for _, _, weight in factors)
            
            suggested_rating = round(weighted_sum / total_weight)
            
            # Ensure rating is in valid range
            suggested_rating = max(1, min(10, suggested_rating))
            
            suggestion["suggested_rating"] = suggested_rating
            suggestion["confidence"] = min(1.0, total_weight / 1.0)  # Normalize confidence
            suggestion["factors"] = {
                factor_name: {"rating": rating, "weight": weight}
                for factor_name, rating, weight in factors
            }
        
        return suggestion
```

## Integration with MCP Tools

### Tool Integration

```python
# In save_band_analyze tool
@app.tool()
def save_band_analyze(
    band_name: str,
    analysis: Dict[str, Any],
    analyze_missing_albums: bool = False
) -> Dict[str, Any]:
    """Save band analysis with rating validation."""
    
    try:
        # Validate band rating
        if "rate" in analysis:
            analysis["rate"] = RatingValidator.validate_rating_value(analysis["rate"])
        
        # Validate album ratings
        if "albums" in analysis:
            for album in analysis["albums"]:
                if "rate" in album:
                    album["rate"] = RatingValidator.validate_rating_value(album["rate"])
        
        # Create analysis model
        band_analysis = BandAnalysis(**analysis)
        
        # Perform consistency validation
        album_ratings = [
            album.rate for album in band_analysis.albums 
            if album.rate is not None
        ]
        
        consistency_check = RatingValidator.validate_rating_consistency(
            band_analysis.rate, album_ratings
        )
        
        # Save analysis
        result = storage.save_band_analyze(
            band_name,
            band_analysis,
            analyze_missing_albums=analyze_missing_albums
        )
        
        # Add validation results to response
        result["validation"] = {
            "consistency_check": consistency_check,
            "band_rating_valid": band_analysis.rate is not None,
            "album_ratings_count": len(album_ratings)
        }
        
        return result
        
    except ValueError as e:
        return {
            "success": False,
            "error": {
                "code": "RATING_VALIDATION_ERROR",
                "message": str(e)
            }
        }
```

### Rating System Best Practices

#### For Users
1. **Consistency**: Use the same criteria across all ratings
2. **Context**: Consider genre, era, and personal taste
3. **Perspective**: Allow time for ratings to settle
4. **Documentation**: Include reviews to explain ratings
5. **Comparison**: Use other rated items as reference points

#### For Developers
1. **Validation**: Always validate rating inputs
2. **Consistency Checks**: Implement cross-validation
3. **User Feedback**: Provide helpful validation messages
4. **Analytics**: Track rating patterns and outliers
5. **Flexibility**: Allow rating updates and corrections

#### Rating Guidelines by Genre

```python
GENRE_RATING_GUIDELINES = {
    "Progressive Rock": {
        "description": "Focus on complexity, innovation, and artistic ambition",
        "criteria": ["Technical skill", "Compositional complexity", "Innovation", "Concept execution"],
        "typical_range": (6, 9),
        "legendary_examples": ["Pink Floyd - Dark Side", "Yes - Close to the Edge"]
    },
    "Jazz": {
        "description": "Emphasize improvisation, technical skill, and innovation",
        "criteria": ["Improvisation quality", "Technical mastery", "Innovation", "Swing/groove"],
        "typical_range": (5, 10),
        "legendary_examples": ["Miles Davis - Kind of Blue", "John Coltrane - A Love Supreme"]
    },
    "Classical": {
        "description": "Consider composition, performance, and historical significance",
        "criteria": ["Compositional merit", "Performance quality", "Recording quality", "Historical importance"],
        "typical_range": (7, 10),
        "legendary_examples": ["Bach - Goldberg Variations", "Beethoven - Symphony No. 9"]
    }
}
```

This comprehensive rating system ensures consistent, meaningful evaluation of musical content while providing flexibility for personal taste and contextual factors. 