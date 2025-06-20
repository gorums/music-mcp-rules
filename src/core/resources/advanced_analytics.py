"""
Advanced Analytics Resource for Music Collection MCP Server.

This module provides markdown-formatted advanced collection analytics including
type distribution analysis, health metrics, recommendations, and maturity assessment.
"""

# Standard library imports
import logging
from datetime import datetime
from typing import Any, Dict, List

# Local imports
from src.models.analytics import AdvancedCollectionInsights, CollectionAnalyzer
from src.core.tools.storage import StorageError, load_band_metadata, load_collection_index

logger = logging.getLogger(__name__)


def get_advanced_analytics_markdown() -> str:
    """
    Generate comprehensive advanced analytics in markdown format.
    
    This function creates a markdown resource containing:
    - Collection maturity assessment
    - Album type distribution analysis
    - Edition prevalence and upgrade opportunities
    - Collection health metrics and scoring
    - Type-specific recommendations
    - Discovery potential and value assessment
    - Organization recommendations
    - Decade and genre trend analysis
    
    Returns:
        Markdown-formatted string with complete advanced analytics
    """
    try:
        # Load collection index and band metadata
        collection_index = load_collection_index()
        
        if not collection_index:
            return _generate_no_collection_message()
        
        # Load metadata for all bands
        band_metadata = {}
        for band_entry in collection_index.bands:
            try:
                metadata = load_band_metadata(band_entry.name)
                if metadata:
                    band_metadata[band_entry.name] = metadata
            except Exception as e:
                logger.warning(f"Could not load metadata for band {band_entry.name}: {str(e)}")
        
        if not band_metadata:
            return _generate_no_metadata_message()
        
        # Perform comprehensive analysis
        insights = CollectionAnalyzer.analyze_collection(collection_index, band_metadata)
        
        # Generate comprehensive markdown
        return _generate_analytics_markdown(insights, collection_index, band_metadata)
        
    except StorageError as e:
        logger.error(f"Storage error loading advanced analytics: {e}")
        return _generate_error_message(str(e))
    except Exception as e:
        logger.error(f"Unexpected error loading advanced analytics: {e}")
        return _generate_error_message(f"Unexpected error: {e}")


def _generate_analytics_markdown(insights: AdvancedCollectionInsights, index, metadata: Dict[str, Any]) -> str:
    """
    Generate detailed markdown for advanced analytics.
    
    Args:
        insights: AdvancedCollectionInsights with complete analysis
        index: Collection index
        metadata: Band metadata dictionary
        
    Returns:
        Formatted markdown string
    """
    markdown_parts = []
    
    # Header and overview
    markdown_parts.append(_generate_header_section(insights))
    
    # Maturity and health overview
    markdown_parts.append(_generate_maturity_health_overview(insights))
    
    # Album type analysis
    markdown_parts.append(_generate_type_analysis_section(insights.type_analysis))
    
    # Edition analysis
    markdown_parts.append(_generate_edition_analysis_section(insights.edition_analysis))
    
    # Health metrics
    markdown_parts.append(_generate_health_metrics_section(insights.health_metrics))
    
    # Recommendations
    markdown_parts.append(_generate_recommendations_section(insights))
    
    # Collection patterns
    markdown_parts.append(_generate_patterns_section(insights))
    
    # Advanced metrics
    markdown_parts.append(_generate_advanced_metrics_section(insights))
    
    # Metadata information
    markdown_parts.append(_generate_analytics_metadata_section(insights, len(metadata)))
    
    return "\n\n".join(markdown_parts)


def _generate_header_section(insights: AdvancedCollectionInsights) -> str:
    """Generate the header section with collection analytics overview."""
    header = "# 📊 Advanced Collection Analytics"
    
    # Add status badges
    badges = []
    
    # Maturity badge
    maturity_icons = {
        "Beginner": "🌱",
        "Intermediate": "🌿", 
        "Advanced": "🌳",
        "Expert": "🎓",
        "Master": "👑"
    }
    maturity_icon = maturity_icons.get(insights.collection_maturity.value, "📊")
    badges.append(f"{maturity_icon} **{insights.collection_maturity.value} Collection**")
    
    # Health badge
    health_level = insights.health_metrics.get_health_level()
    health_icons = {
        "Excellent": "💚",
        "Good": "💛",
        "Fair": "🟠",
        "Poor": "🔴",
        "Critical": "💀"
    }
    health_icon = health_icons.get(health_level, "❓")
    badges.append(f"{health_icon} **{health_level} Health**")
    
    # Value badge
    if insights.collection_value_score >= 80:
        badges.append("💎 **High Value**")
    elif insights.collection_value_score >= 60:
        badges.append("🏆 **Good Value**")
    else:
        badges.append("📀 **Standard Value**")
    
    # Discovery badge
    if insights.discovery_potential >= 80:
        badges.append("🔍 **High Discovery**")
    elif insights.discovery_potential >= 60:
        badges.append("🔍 **Good Discovery**")
    else:
        badges.append("🔍 **Limited Discovery**")
    
    if badges:
        header += f"\n\n{' • '.join(badges)}"
    
    return header


def _generate_maturity_health_overview(insights: AdvancedCollectionInsights) -> str:
    """Generate the maturity and health overview section."""
    section = ["## 🎯 Collection Overview"]
    
    # Overview table
    overview_table = [
        "| Aspect | Score | Level | Status |",
        "|--------|-------|-------|--------|",
        f"| **Overall Health** | {insights.health_metrics.overall_score}/100 | {insights.health_metrics.get_health_level()} | {_get_health_emoji(insights.health_metrics.overall_score)} |",
        f"| **Type Diversity** | {insights.health_metrics.type_diversity_score}/100 | {_get_diversity_level(insights.health_metrics.type_diversity_score)} | {_get_diversity_emoji(insights.health_metrics.type_diversity_score)} |",
        f"| **Genre Diversity** | {insights.health_metrics.genre_diversity_score}/100 | {_get_diversity_level(insights.health_metrics.genre_diversity_score)} | {_get_diversity_emoji(insights.health_metrics.genre_diversity_score)} |",
        f"| **Collection Value** | {insights.collection_value_score}/100 | {_get_value_level(insights.collection_value_score)} | {_get_value_emoji(insights.collection_value_score)} |",
        f"| **Discovery Potential** | {insights.discovery_potential}/100 | {_get_discovery_level(insights.discovery_potential)} | {_get_discovery_emoji(insights.discovery_potential)} |"
    ]
    
    section.extend(overview_table)
    
    # Maturity description
    section.append("")
    section.append(f"### 🏆 Collection Maturity: **{insights.collection_maturity.value}**")
    section.append("")
    section.append(_get_maturity_description(insights.collection_maturity.value))
    
    return "\n".join(section)


def _generate_type_analysis_section(type_analysis) -> str:
    """Generate album type analysis section."""
    section = ["## 🎵 Album Type Analysis"]
    
    # Type distribution summary
    section.append("### Distribution Overview")
    section.append("")
    
    if type_analysis.type_distribution:
        type_table = [
            "| Album Type | Count | Percentage | Status |",
            "|------------|-------|------------|--------|"
        ]
        
        for album_type, count in type_analysis.type_distribution.items():
            percentage = type_analysis.type_percentages.get(album_type, 0)
            status = _get_type_status(album_type, percentage)
            type_table.append(f"| **{album_type}** | {count} | {percentage:.1f}% | {status} |")
        
        section.extend(type_table)
    else:
        section.append("*No album type data available.*")
    
    # Type insights
    section.append("")
    section.append("### 📊 Type Insights")
    section.append("")
    
    insights_list = [
        f"🎯 **Type Diversity Score**: {type_analysis.type_diversity_score:.1f}/100",
        f"📀 **Album to EP Ratio**: {type_analysis.album_to_ep_ratio:.1f}:1",
        f"🎤 **Live Albums**: {type_analysis.live_percentage:.1f}%",
        f"🎚️ **Demo Recordings**: {type_analysis.demo_percentage:.1f}%",
        f"📦 **Compilations**: {type_analysis.compilation_percentage:.1f}%"
    ]
    
    section.extend(insights_list)
    
    # Missing types
    if type_analysis.missing_types:
        section.append("")
        section.append("### ❌ Missing Album Types")
        section.append("")
        missing_list = [f"- **{album_type}**: Consider adding {album_type.lower()} releases" for album_type in type_analysis.missing_types]
        section.extend(missing_list)
    
    # Dominant types
    if type_analysis.dominant_types:
        section.append("")
        section.append("### 👑 Dominant Types")
        section.append("")
        dominant_list = [f"- **{album_type}**: Most common in your collection" for album_type in type_analysis.dominant_types[:3]]
        section.extend(dominant_list)
    
    return "\n".join(section)


def _generate_edition_analysis_section(edition_analysis) -> str:
    """Generate edition analysis section."""
    section = ["## 💿 Edition Analysis"]
    
    # Edition distribution
    section.append("### Edition Distribution")
    section.append("")
    
    if edition_analysis.edition_distribution:
        edition_table = [
            "| Edition Type | Count | Percentage |",
            "|--------------|-------|------------|"
        ]
        
        for edition, count in edition_analysis.edition_distribution.items():
            percentage = edition_analysis.edition_percentages.get(edition, 0)
            edition_table.append(f"| **{edition}** | {count} | {percentage:.1f}% |")
        
        section.extend(edition_table)
    else:
        section.append("*No edition data available.*")
    
    # Edition insights
    section.append("")
    section.append("### 🎁 Edition Insights")
    section.append("")
    
    edition_insights = [
        f"💎 **Deluxe Editions**: {edition_analysis.deluxe_percentage:.1f}%",
        f"🔧 **Remastered Albums**: {edition_analysis.remaster_percentage:.1f}%",
        f"🏆 **Limited Editions**: {edition_analysis.limited_percentage:.1f}%",
        f"📀 **Standard Editions**: {edition_analysis.standard_percentage:.1f}%"
    ]
    
    section.extend(edition_insights)
    
    # Edition upgrade opportunities
    if edition_analysis.upgrade_opportunities:
        section.append("")
        section.append("### ⬆️ Upgrade Opportunities")
        section.append("")
        section.append(f"Found **{len(edition_analysis.upgrade_opportunities)}** potential edition upgrades:")
        
        for upgrade in edition_analysis.upgrade_opportunities[:5]:  # Show top 5
            section.append(f"- **{upgrade.album_name}**: {upgrade.current_edition} → {upgrade.suggested_edition}")
    
    return "\n".join(section)


def _generate_health_metrics_section(health_metrics) -> str:
    """Generate health metrics section."""
    section = ["## 🏥 Collection Health Assessment"]
    
    # Health scores breakdown
    section.append("### Health Scores")
    section.append("")
    
    health_table = [
        "| Health Aspect | Score | Level | Recommendation |",
        "|---------------|-------|-------|----------------|",
        f"| **Overall Health** | {health_metrics.overall_score}/100 | {health_metrics.get_health_level()} | {_get_health_recommendation(health_metrics.overall_score)} |",
        f"| **Type Diversity** | {health_metrics.type_diversity_score}/100 | {_get_score_level(health_metrics.type_diversity_score)} | {_get_type_recommendation(health_metrics.type_diversity_score)} |",
        f"| **Genre Diversity** | {health_metrics.genre_diversity_score}/100 | {_get_score_level(health_metrics.genre_diversity_score)} | {_get_genre_recommendation(health_metrics.genre_diversity_score)} |",
        f"| **Completion Rate** | {health_metrics.completion_score}/100 | {_get_score_level(health_metrics.completion_score)} | {_get_completion_recommendation(health_metrics.completion_score)} |",
        f"| **Organization** | {health_metrics.organization_score}/100 | {_get_score_level(health_metrics.organization_score)} | {_get_org_recommendation(health_metrics.organization_score)} |",
        f"| **Quality Rating** | {health_metrics.quality_score}/100 | {_get_score_level(health_metrics.quality_score)} | {_get_quality_recommendation(health_metrics.quality_score)} |"
    ]
    
    section.extend(health_table)
    
    # Strengths
    if health_metrics.strengths:
        section.append("")
        section.append("### ✅ Collection Strengths")
        section.append("")
        strength_list = [f"- {strength}" for strength in health_metrics.strengths]
        section.extend(strength_list)
    
    # Weaknesses
    if health_metrics.weaknesses:
        section.append("")
        section.append("### ⚠️ Areas for Improvement")
        section.append("")
        weakness_list = [f"- {weakness}" for weakness in health_metrics.weaknesses]
        section.extend(weakness_list)
    
    # Recommendations
    if health_metrics.recommendations:
        section.append("")
        section.append("### 💡 Health Recommendations")
        section.append("")
        rec_list = [f"- {recommendation}" for recommendation in health_metrics.recommendations]
        section.extend(rec_list)
    
    return "\n".join(section)


def _generate_recommendations_section(insights: AdvancedCollectionInsights) -> str:
    """Generate recommendations section."""
    section = ["## 🎯 Collection Recommendations"]
    
    # Type recommendations
    if insights.type_recommendations:
        section.append("### 🎵 Missing Album Type Recommendations")
        section.append("")
        
        high_priority = [rec for rec in insights.type_recommendations if rec.priority == "High"]
        medium_priority = [rec for rec in insights.type_recommendations if rec.priority == "Medium"]
        
        if high_priority:
            section.append("#### 🔥 High Priority")
            for rec in high_priority[:5]:
                section.append(f"- **{rec.band_name}**: Add {rec.album_type.value} ({rec.reason})")
        
        if medium_priority:
            section.append("")
            section.append("#### 🟡 Medium Priority")
            for rec in medium_priority[:5]:
                section.append(f"- **{rec.band_name}**: Consider {rec.album_type.value} ({rec.reason})")
    
    # Edition upgrades
    if insights.edition_upgrades:
        section.append("")
        section.append("### ⬆️ Edition Upgrade Recommendations")
        section.append("")
        for upgrade in insights.edition_upgrades[:5]:
            benefits = ", ".join(upgrade.benefits) if upgrade.benefits else "Enhanced content"
            section.append(f"- **{upgrade.band_name} - {upgrade.album_name}**: {upgrade.current_edition} → {upgrade.suggested_edition} ({benefits})")
    
    # Organization recommendations
    if insights.organization_recommendations:
        section.append("")
        section.append("### 📁 Organization Recommendations")
        section.append("")
        org_list = [f"- {recommendation}" for recommendation in insights.organization_recommendations]
        section.extend(org_list)
    
    return "\n".join(section)


def _generate_patterns_section(insights: AdvancedCollectionInsights) -> str:
    """Generate collection patterns section."""
    section = ["## 📈 Collection Patterns & Trends"]
    
    # Decade distribution
    if insights.decade_distribution:
        section.append("### 📅 Decade Distribution")
        section.append("")
        
        decade_table = [
            "| Decade | Albums | Percentage |",
            "|--------|--------|------------|"
        ]
        
        total_albums = sum(insights.decade_distribution.values())
        sorted_decades = sorted(insights.decade_distribution.items())
        
        for decade, count in sorted_decades:
            percentage = (count / total_albums) * 100 if total_albums > 0 else 0
            decade_table.append(f"| **{decade}** | {count} | {percentage:.1f}% |")
        
        section.extend(decade_table)
    
    # Genre trends
    if insights.genre_trends:
        section.append("")
        section.append("### 🎭 Genre Popularity")
        section.append("")
        
        genre_table = [
            "| Genre | Prevalence | Status |",
            "|-------|------------|--------|"
        ]
        
        sorted_genres = sorted(insights.genre_trends.items(), key=lambda x: x[1], reverse=True)
        for genre, percentage in sorted_genres[:10]:
            status = _get_genre_status(percentage)
            genre_table.append(f"| **{genre}** | {percentage:.1f}% | {status} |")
        
        section.extend(genre_table)
    
    # Band completion rates
    if insights.band_completion_rates:
        section.append("")
        section.append("### 🎯 Band Completion Rates")
        section.append("")
        
        completion_ranges = {
            "Complete (100%)": 0,
            "Nearly Complete (90-99%)": 0,
            "Good (75-89%)": 0,
            "Fair (50-74%)": 0,
            "Poor (<50%)": 0
        }
        
        for completion_rate in insights.band_completion_rates.values():
            if completion_rate == 100:
                completion_ranges["Complete (100%)"] += 1
            elif completion_rate >= 90:
                completion_ranges["Nearly Complete (90-99%)"] += 1
            elif completion_rate >= 75:
                completion_ranges["Good (75-89%)"] += 1
            elif completion_rate >= 50:
                completion_ranges["Fair (50-74%)"] += 1
            else:
                completion_ranges["Poor (<50%)"] += 1
        
        completion_table = [
            "| Completion Level | Bands | Status |",
            "|------------------|-------|--------|"
        ]
        
        for level, count in completion_ranges.items():
            status = _get_completion_range_status(level)
            completion_table.append(f"| **{level}** | {count} | {status} |")
        
        section.extend(completion_table)
    
    return "\n".join(section)


def _generate_advanced_metrics_section(insights: AdvancedCollectionInsights) -> str:
    """Generate advanced metrics section."""
    section = ["## 🔬 Advanced Metrics"]
    
    # Advanced scores
    advanced_table = [
        "| Metric | Score | Assessment | Impact |",
        "|--------|-------|------------|--------|",
        f"| **Collection Value** | {insights.collection_value_score}/100 | {_get_value_assessment(insights.collection_value_score)} | {_get_value_impact(insights.collection_value_score)} |",
        f"| **Discovery Potential** | {insights.discovery_potential}/100 | {_get_discovery_assessment(insights.discovery_potential)} | {_get_discovery_impact(insights.discovery_potential)} |"
    ]
    
    section.extend(advanced_table)
    
    # Value factors
    section.append("")
    section.append("### 💎 Value Assessment")
    section.append("")
    value_factors = [
        "- **Rarity**: Limited editions, early releases, and demo recordings",
        "- **Completeness**: Comprehensive band discographies", 
        "- **Diversity**: Wide range of album types and editions",
        "- **Quality**: High-rated albums and critical favorites"
    ]
    section.extend(value_factors)
    
    # Discovery factors
    section.append("")
    section.append("### 🔍 Discovery Potential")
    section.append("")
    discovery_factors = [
        "- **Missing Albums**: Opportunities to complete existing collections",
        "- **Similar Bands**: Recommendations from analyzed bands",
        "- **Genre Exploration**: Expansion into new musical territories",
        "- **Collection Growth**: Room for continued expansion and discovery"
    ]
    section.extend(discovery_factors)
    
    return "\n".join(section)


def _generate_analytics_metadata_section(insights: AdvancedCollectionInsights, bands_analyzed: int) -> str:
    """Generate analytics metadata section."""
    section = ["## ℹ️ Analytics Information"]
    
    metadata_table = [
        "| Information | Value |",
        "|-------------|-------|",
        f"| **Analysis Date** | {insights.generated_at[:19].replace('T', ' ')} |",
        f"| **Bands Analyzed** | {bands_analyzed} |",
        f"| **Collection Maturity** | {insights.collection_maturity.value} |",
        f"| **Analytics Version** | Advanced Analytics v1.0.0 |",
        f"| **Analysis Features** | Type Distribution, Health Metrics, Recommendations |"
    ]
    
    section.extend(metadata_table)
    
    # Resource URIs
    section.append("")
    section.append("### 🔗 Related Resources")
    section.append("")
    section.append("- `collection://summary` - Basic collection overview")
    section.append("- `band://info/{band_name}` - Individual band analytics")
    section.append("- Use `analyze_collection_insights_tool` for updated analysis")
    section.append("- Use `advanced_search_albums_tool` for detailed album filtering")
    
    return "\n".join(section)


# Helper functions for status and level assessment

def _get_health_emoji(score: int) -> str:
    """Get emoji for health score."""
    if score >= 90: return "💚"
    elif score >= 75: return "💛"
    elif score >= 60: return "🟠"
    elif score >= 40: return "🔴"
    else: return "💀"

def _get_diversity_level(score: int) -> str:
    """Get diversity level description."""
    if score >= 80: return "Excellent"
    elif score >= 60: return "Good"
    elif score >= 40: return "Fair"
    else: return "Limited"

def _get_diversity_emoji(score: int) -> str:
    """Get emoji for diversity score."""
    if score >= 80: return "🌈"
    elif score >= 60: return "🎨"
    elif score >= 40: return "🟡"
    else: return "⚪"

def _get_value_level(score: int) -> str:
    """Get value level description."""
    if score >= 80: return "High Value"
    elif score >= 60: return "Good Value"
    elif score >= 40: return "Standard Value"
    else: return "Basic Value"

def _get_value_emoji(score: int) -> str:
    """Get emoji for value score."""
    if score >= 80: return "💎"
    elif score >= 60: return "🏆"
    elif score >= 40: return "🥉"
    else: return "📀"

def _get_discovery_level(score: int) -> str:
    """Get discovery level description."""
    if score >= 80: return "High Potential"
    elif score >= 60: return "Good Potential"
    elif score >= 40: return "Limited Potential"
    else: return "Low Potential"

def _get_discovery_emoji(score: int) -> str:
    """Get emoji for discovery score."""
    if score >= 80: return "🔍"
    elif score >= 60: return "🔎"
    elif score >= 40: return "👀"
    else: return "😴"

def _get_maturity_description(maturity: str) -> str:
    """Get description for maturity level."""
    descriptions = {
        "Beginner": "🌱 Starting your collection journey with foundational albums.",
        "Intermediate": "🌿 Building a solid collection with growing diversity.",
        "Advanced": "🌳 Well-established collection with good variety and depth.",
        "Expert": "🎓 Comprehensive collection with excellent organization and analysis.",
        "Master": "👑 Exceptional collection representing mastery of music curation."
    }
    return descriptions.get(maturity, "📊 Collection maturity assessment.")

def _get_type_status(album_type: str, percentage: float) -> str:
    """Get status for album type percentage."""
    # Ideal percentages for comparison
    ideal = {
        "Album": 55, "EP": 15, "Demo": 10, "Live": 8,
        "Compilation": 5, "Instrumental": 4, "Split": 2, "Single": 1
    }
    
    ideal_pct = ideal.get(album_type, 5)
    
    if percentage >= ideal_pct * 1.5:
        return "🔥 Abundant"
    elif percentage >= ideal_pct * 0.8:
        return "✅ Balanced"
    elif percentage >= ideal_pct * 0.5:
        return "🟡 Low"
    else:
        return "🔴 Rare"

def _get_score_level(score: int) -> str:
    """Get level description for a score."""
    if score >= 90: return "Excellent"
    elif score >= 75: return "Good"
    elif score >= 60: return "Fair"
    elif score >= 40: return "Poor"
    else: return "Critical"

def _get_health_recommendation(score: int) -> str:
    """Get health recommendation."""
    if score >= 90: return "Maintain excellence"
    elif score >= 75: return "Minor improvements"
    elif score >= 60: return "Focus on weak areas"
    else: return "Major improvements needed"

def _get_type_recommendation(score: int) -> str:
    """Get type diversity recommendation."""
    if score < 60: return "Add missing album types"
    else: return "Good type variety"

def _get_genre_recommendation(score: int) -> str:
    """Get genre diversity recommendation."""
    if score < 40: return "Explore new genres"
    else: return "Good genre diversity"

def _get_completion_recommendation(score: int) -> str:
    """Get completion recommendation."""
    if score < 70: return "Focus on missing albums"
    else: return "Good completion rate"

def _get_org_recommendation(score: int) -> str:
    """Get organization recommendation."""
    if score < 75: return "Improve organization"
    else: return "Well organized"

def _get_quality_recommendation(score: int) -> str:
    """Get quality recommendation."""
    if score < 60: return "Add more ratings"
    else: return "Quality collection"

def _get_genre_status(percentage: float) -> str:
    """Get status for genre percentage."""
    if percentage >= 25: return "🔥 Dominant"
    elif percentage >= 15: return "👑 Major"
    elif percentage >= 10: return "✅ Significant"
    elif percentage >= 5: return "🟡 Present"
    else: return "⚪ Minor"

def _get_completion_range_status(level: str) -> str:
    """Get status emoji for completion range."""
    if "Complete" in level: return "🎯"
    elif "Nearly" in level: return "🥇"
    elif "Good" in level: return "🥈"
    elif "Fair" in level: return "🥉"
    else: return "📈"

def _get_value_assessment(score: int) -> str:
    """Get value assessment description."""
    if score >= 80: return "Exceptional value with rare items"
    elif score >= 60: return "Good value with some special items"
    elif score >= 40: return "Standard value collection"
    else: return "Basic collection value"

def _get_value_impact(score: int) -> str:
    """Get value impact description."""
    if score >= 80: return "High collector interest"
    elif score >= 60: return "Moderate collector interest"
    else: return "Personal enjoyment focus"

def _get_discovery_assessment(score: int) -> str:
    """Get discovery assessment description."""
    if score >= 80: return "Excellent growth opportunities"
    elif score >= 60: return "Good expansion potential"
    elif score >= 40: return "Limited growth opportunities"
    else: return "Mature, complete collection"

def _get_discovery_impact(score: int) -> str:
    """Get discovery impact description."""
    if score >= 80: return "Many new music opportunities"
    elif score >= 60: return "Some expansion possibilities"
    else: return "Focus on depth over breadth"

def _generate_no_collection_message() -> str:
    """Generate message when no collection is found."""
    return """# 📊 Advanced Collection Analytics

## ❌ No Collection Found

No music collection has been scanned yet. To generate advanced analytics:

1. **Scan your collection** using the `scan_music_folders` tool
2. **Add metadata** for bands using `save_band_metadata_tool`
3. **Return here** to view comprehensive analytics

### Getting Started

Use the `scan_music_folders` tool to discover your music collection, then use the metadata tools to enrich your collection data before viewing advanced analytics.
"""

def _generate_no_metadata_message() -> str:
    """Generate message when no metadata is available."""
    return """# 📊 Advanced Collection Analytics

## ⚠️ No Metadata Available

Your collection has been scanned, but no band metadata is available for analysis.

### Required for Analytics

Advanced analytics requires:
- **Band metadata** with album information
- **Genre classifications** 
- **Analysis data** (ratings, reviews)

### Next Steps

1. Use the `save_band_metadata_tool` to add band information
2. Use the `save_band_analyze_tool` to add ratings and reviews  
3. Return here for comprehensive analytics

The more metadata you add, the more detailed your analytics will be!
"""

def _generate_error_message(error: str) -> str:
    """Generate error message for analytics failures."""
    return f"""# 📊 Advanced Collection Analytics

## ❌ Error Loading Analytics

An error occurred while generating advanced analytics:

```
{error}
```

### Troubleshooting

1. **Check collection scan**: Ensure your collection has been scanned recently
2. **Verify metadata files**: Check that band metadata files are accessible
3. **Try again**: Re-run the analytics generation
4. **Contact support**: If the error persists

### Alternative Resources

- Use `collection://summary` for basic collection information
- Use `band://info/{{band_name}}` for individual band details
""" 