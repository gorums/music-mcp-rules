"""
Collection Summary Resource for Music Collection MCP Server.

This module provides markdown-formatted collection overview including
statistics, insights, top-rated content, and collection health metrics.
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..tools.storage import load_collection_index, StorageError
from ..models.collection import CollectionIndex, CollectionStats, CollectionInsight

logger = logging.getLogger(__name__)


def get_collection_summary() -> str:
    """
    Generate comprehensive collection summary in markdown format.
    
    This function creates a markdown resource containing:
    - Collection overview with key statistics
    - Band distribution and completion metrics
    - Genre analysis and trends
    - Missing albums summary
    - Top-rated content (if available)
    - Collection health and insights
    - Recent activity and recommendations
    
    Returns:
        Markdown-formatted string with complete collection summary
    """
    try:
        # Load collection index
        collection_index = load_collection_index()
        
        if not collection_index:
            return _generate_no_collection_message()
        
        # Generate comprehensive markdown
        return _generate_collection_markdown(collection_index)
        
    except StorageError as e:
        logger.error(f"Storage error loading collection summary: {e}")
        return _generate_error_message(str(e))
    except Exception as e:
        logger.error(f"Unexpected error loading collection summary: {e}")
        return _generate_error_message(f"Unexpected error: {e}")


def _generate_collection_markdown(index: CollectionIndex) -> str:
    """
    Generate detailed markdown for collection with complete statistics.
    
    Args:
        index: CollectionIndex instance with complete collection information
        
    Returns:
        Formatted markdown string
    """
    markdown_parts = []
    
    # Header and overview
    markdown_parts.append(_generate_header_section(index))
    
    # Quick stats overview
    markdown_parts.append(_generate_overview_section(index))
    
    # Detailed statistics
    markdown_parts.append(_generate_statistics_section(index))
    
    # Enhanced features sections
    markdown_parts.append(_generate_enhanced_statistics_section(index))
    
    # Band distribution analysis
    markdown_parts.append(_generate_band_distribution_section(index))
    
    # Missing albums section (if any)
    bands_with_missing = index.get_bands_with_missing_albums()
    if bands_with_missing:
        markdown_parts.append(_generate_missing_albums_section(bands_with_missing))
    
    # Insights section (if available)
    if index.insights:
        markdown_parts.append(_generate_insights_section(index.insights))
    
    # Collection health
    markdown_parts.append(_generate_health_section(index))
    
    # Metadata information
    markdown_parts.append(_generate_metadata_info_section(index))
    
    return "\n\n".join(markdown_parts)


def _generate_header_section(index: CollectionIndex) -> str:
    """Generate the header section with collection name and key status."""
    completion = index.stats.completion_percentage
    
    header = "# 🎵 Music Collection Summary"
    
    # Add status badges
    badges = []
    
    # Collection size badge
    if index.stats.total_bands >= 100:
        badges.append("🎭 **Large Collection**")
    elif index.stats.total_bands > 20:
        badges.append("🎭 **Medium Collection**")
    else:
        badges.append("🎭 **Small Collection**")
    
    # Completion status badge
    if completion >= 95:
        badges.append("✅ **Excellent Completion**")
    elif completion >= 80:
        badges.append("🟡 **Good Completion**")
    elif completion >= 60:
        badges.append("🟠 **Fair Completion**")
    else:
        badges.append("🔴 **Poor Completion**")
    
    # Analysis status badge
    bands_with_analysis = sum(1 for band in index.bands if band.has_analysis)
    if bands_with_analysis > 0:
        badges.append(f"📊 **{bands_with_analysis} Analyzed**")
    
    # Insights badge
    if index.insights:
        badges.append("💡 **Has Insights**")
    
    if badges:
        header += f"\n\n{' • '.join(badges)}"
    
    return header


def _generate_overview_section(index: CollectionIndex) -> str:
    """Generate the quick overview section with key metrics."""
    stats = index.stats
    
    overview = ["## 📊 Quick Overview"]
    
    # Main statistics table
    overview_table = [
        "| Metric | Value | Status |",
        "|--------|-------|--------|",
        f"| **Total Bands** | {stats.total_bands:,} | {_get_collection_size_status(stats.total_bands)} |",
        f"| **Total Albums** | {stats.total_albums:,} | {_get_albums_status(stats.total_albums)} |",
        f"| **Missing Albums** | {stats.total_missing_albums:,} | {_get_missing_status(stats.total_missing_albums)} |",
        f"| **Completion Rate** | {stats.completion_percentage:.1f}% | {_get_completion_status(stats.completion_percentage)} |",
        f"| **Avg Albums/Band** | {stats.avg_albums_per_band:.1f} | {_get_avg_albums_status(stats.avg_albums_per_band)} |",
        f"| **Bands with Metadata** | {stats.bands_with_metadata}/{stats.total_bands} | {_get_metadata_status(stats.bands_with_metadata, stats.total_bands)} |"
    ]
    
    overview.extend(overview_table)
    
    return "\n".join(overview)


def _generate_statistics_section(index: CollectionIndex) -> str:
    """Generate detailed statistics section."""
    stats = index.stats
    
    section = ["## 📈 Detailed Statistics"]
    
    # Collection metrics
    section.append("### Collection Metrics")
    section.append("")
    
    present_albums = stats.total_albums - stats.total_missing_albums
    
    metrics_table = [
        "| Category | Count | Percentage |",
        "|----------|-------|------------|",
        f"| Available Albums | {present_albums:,} | {((present_albums / max(stats.total_albums, 1)) * 100):.1f}% |",
        f"| Missing Albums | {stats.total_missing_albums:,} | {stats.completion_percentage:.1f}% |",
        f"| Bands with Data | {stats.bands_with_metadata:,} | {((stats.bands_with_metadata / max(stats.total_bands, 1)) * 100):.1f}% |",
        f"| Bands without Data | {stats.total_bands - stats.bands_with_metadata:,} | {(((stats.total_bands - stats.bands_with_metadata) / max(stats.total_bands, 1)) * 100):.1f}% |"
    ]
    
    section.extend(metrics_table)
    
    # Top genres (if available)
    if stats.top_genres:
        section.append("")
        section.append("### 🎭 Top Genres")
        section.append("")
        
        genre_table = ["| Genre | Frequency |", "|-------|-----------|"]
        
        # Sort genres by frequency
        sorted_genres = sorted(stats.top_genres.items(), key=lambda x: x[1], reverse=True)
        for genre, count in sorted_genres[:10]:  # Show top 10
            genre_table.append(f"| {genre} | {count} |")
        
        section.extend(genre_table)
    
    return "\n".join(section)


def _generate_enhanced_statistics_section(index: CollectionIndex) -> str:
    """Generate enhanced statistics including album types and compliance."""
    from ..tools.storage import load_band_metadata
    
    section = ["## 🎯 Enhanced Collection Analysis"]
    
    # Collect enhanced metadata
    album_types = {}
    compliance_scores = []
    structure_types = {}
    editions_count = 0
    total_analyzed_albums = 0
    
    for band_entry in index.bands:
        if band_entry.has_metadata:
            try:
                metadata = load_band_metadata(band_entry.name)
                if metadata and metadata.albums:
                    for album in metadata.albums:
                        total_analyzed_albums += 1
                        
                        # Count album types
                        album_type = album.type.value if hasattr(album.type, 'value') else str(album.type)
                        album_types[album_type] = album_types.get(album_type, 0) + 1
                        
                        # Count editions
                        if album.edition:
                            editions_count += 1
                    
                    # Count structure types
                    if metadata.folder_structure:
                        structure_type = metadata.folder_structure.structure_type.value
                        structure_types[structure_type] = structure_types.get(structure_type, 0) + 1
                        
            except Exception:
                # Skip bands with corrupted metadata
                continue
    
    # Album types distribution
    if album_types:
        section.append("### 🎼 Album Types Distribution")
        section.append("")
        
        types_table = [
            "| Type | Count | Percentage |",
            "|------|-------|------------|"
        ]
        
        # Sort by count (descending)
        sorted_types = sorted(album_types.items(), key=lambda x: x[1], reverse=True)
        for album_type, count in sorted_types:
            percentage = (count / total_analyzed_albums * 100) if total_analyzed_albums > 0 else 0
            types_table.append(f"| {album_type} | {count:,} | {percentage:.1f}% |")
        
        section.extend(types_table)
        section.append("")
    
    # Structure types distribution
    if structure_types:
        section.append("### 🗂️ Folder Structure Analysis")
        section.append("")
        
        structure_table = [
            "| Structure Type | Bands | Percentage |",
            "|----------------|-------|------------|"
        ]
        
        total_structured_bands = sum(structure_types.values())
        for structure_type, count in sorted(structure_types.items()):
            percentage = (count / total_structured_bands * 100) if total_structured_bands > 0 else 0
            structure_table.append(f"| {structure_type.title()} | {count:,} | {percentage:.1f}% |")
        
        section.extend(structure_table)
        section.append("")
    
    # Special editions summary
    if total_analyzed_albums > 0:
        section.append("### 🎖️ Special Editions")
        section.append("")
        
        editions_percentage = (editions_count / total_analyzed_albums * 100) if total_analyzed_albums > 0 else 0
        
        editions_table = [
            "| Metric | Value |",
            "|--------|-------|",
            f"| Albums with Special Editions | {editions_count:,} |",
            f"| Percentage of Collection | {editions_percentage:.1f}% |",
            f"| Standard Albums | {total_analyzed_albums - editions_count:,} |"
        ]
        
        section.extend(editions_table)
    
    return "\n".join(section)


def _generate_band_distribution_section(index: CollectionIndex) -> str:
    """Generate band distribution analysis section."""
    section = ["## 🎸 Band Distribution"]
    
    # Sort bands by album count for analysis
    bands_by_albums = sorted(index.bands, key=lambda b: b.albums_count, reverse=True)
    
    # Distribution categories
    large_bands = [b for b in bands_by_albums if b.albums_count >= 10]
    medium_bands = [b for b in bands_by_albums if 5 <= b.albums_count < 10]
    small_bands = [b for b in bands_by_albums if 1 <= b.albums_count < 5]
    no_albums = [b for b in bands_by_albums if b.albums_count == 0]
    
    # Distribution table
    distribution_table = [
        "| Category | Count | Percentage |",
        "|----------|-------|------------|",
        f"| Large (10+ albums) | {len(large_bands)} | {(len(large_bands) / max(len(index.bands), 1) * 100):.1f}% |",
        f"| Medium (5-9 albums) | {len(medium_bands)} | {(len(medium_bands) / max(len(index.bands), 1) * 100):.1f}% |",
        f"| Small (1-4 albums) | {len(small_bands)} | {(len(small_bands) / max(len(index.bands), 1) * 100):.1f}% |",
        f"| No Albums | {len(no_albums)} | {(len(no_albums) / max(len(index.bands), 1) * 100):.1f}% |"
    ]
    
    section.extend(distribution_table)
    
    # Top bands by album count
    if bands_by_albums:
        section.append("")
        section.append("### 🏆 Top Bands by Album Count")
        section.append("")
        
        for i, band in enumerate(bands_by_albums[:10], 1):
            completion_icon = "✅" if band.missing_albums_count == 0 else "⚠️"
            metadata_icon = "📄" if band.has_metadata else "❌"
            analysis_icon = "📊" if band.has_analysis else "⭕"
            
            section.append(f"{i}. **{band.name}** - {band.albums_count} albums {completion_icon} {metadata_icon} {analysis_icon}")
    
    return "\n".join(section)


def _generate_missing_albums_section(bands_with_missing: List) -> str:
    """Generate missing albums analysis section."""
    section = ["## 🔍 Missing Albums Analysis"]
    
    total_missing = sum(band.missing_albums_count for band in bands_with_missing)
    section.append(f"*{len(bands_with_missing)} bands have {total_missing} missing albums*")
    section.append("")
    
    # Sort by missing count
    sorted_bands = sorted(bands_with_missing, key=lambda b: b.missing_albums_count, reverse=True)
    
    missing_table = [
        "| Band | Missing Albums | Total Albums | Completion |",
        "|------|----------------|--------------|------------|"
    ]
    
    for band in sorted_bands[:15]:  # Show top 15 bands with missing albums
        completion = ((band.albums_count - band.missing_albums_count) / max(band.albums_count, 1)) * 100
        completion_icon = "🔴" if completion < 50 else "🟡" if completion < 80 else "🟢"
        
        missing_table.append(
            f"| {band.name} | {band.missing_albums_count} | {band.albums_count} | {completion:.1f}% {completion_icon} |"
        )
    
    section.extend(missing_table)
    
    if len(bands_with_missing) > 15:
        section.append("")
        section.append(f"*... and {len(bands_with_missing) - 15} more bands with missing albums*")
    
    return "\n".join(section)


def _generate_insights_section(insights: CollectionInsight) -> str:
    """Generate collection insights section."""
    section = ["## 💡 Collection Insights"]
    
    # Parse generation time
    try:
        generated_time = datetime.fromisoformat(insights.generated_at.replace('Z', '+00:00'))
        formatted_time = generated_time.strftime("%B %d, %Y")
    except:
        formatted_time = insights.generated_at
    
    section.append(f"*Generated on {formatted_time}*")
    section.append("")
    
    # Collection health
    health_icon = {
        "Excellent": "🟢",
        "Good": "🟡", 
        "Fair": "🟠",
        "Poor": "🔴"
    }.get(insights.collection_health, "⚪")
    
    section.append(f"**Collection Health:** {health_icon} {insights.collection_health}")
    section.append("")
    
    # Key insights
    if insights.insights:
        section.append("### 📋 Key Insights")
        section.append("")
        for insight in insights.insights[:5]:  # Show top 5 insights
            section.append(f"- {insight}")
        section.append("")
    
    # Recommendations
    if insights.recommendations:
        section.append("### 🎯 Recommendations")
        section.append("")
        for recommendation in insights.recommendations[:5]:  # Show top 5 recommendations
            section.append(f"- {recommendation}")
        section.append("")
    
    # Top rated bands
    if insights.top_rated_bands:
        section.append("### ⭐ Top Rated Bands")
        section.append("")
        top_rated_list = ", ".join(f"`{band}`" for band in insights.top_rated_bands[:10])
        section.append(top_rated_list)
        section.append("")
    
    # Suggested purchases
    if insights.suggested_purchases:
        section.append("### 🛒 Suggested Purchases")
        section.append("")
        for purchase in insights.suggested_purchases[:5]:  # Show top 5 suggestions
            section.append(f"- {purchase}")
    
    return "\n".join(section)


def _generate_health_section(index: CollectionIndex) -> str:
    """Generate collection health assessment section."""
    section = ["## 🏥 Collection Health"]
    
    stats = index.stats
    
    # Calculate health metrics
    metadata_coverage = (stats.bands_with_metadata / max(stats.total_bands, 1)) * 100
    
    health_table = [
        "| Health Metric | Value | Status |",
        "|---------------|-------|--------|",
        f"| **Album Completion** | {stats.completion_percentage:.1f}% | {_get_completion_status(stats.completion_percentage)} |",
        f"| **Metadata Coverage** | {metadata_coverage:.1f}% | {_get_metadata_coverage_status(metadata_coverage)} |",
        f"| **Average Albums/Band** | {stats.avg_albums_per_band:.1f} | {_get_avg_albums_status(stats.avg_albums_per_band)} |"
    ]
    
    section.extend(health_table)
    
    # Health recommendations
    section.append("")
    section.append("### 🎯 Health Recommendations")
    section.append("")
    
    recommendations = []
    
    if stats.completion_percentage < 80:
        recommendations.append("Consider acquiring missing albums to improve completion rate")
    
    if metadata_coverage < 70:
        recommendations.append("Use `fetch_band_info` prompt to gather missing band metadata")
    
    if stats.avg_albums_per_band < 3:
        recommendations.append("Collection may benefit from more diverse band selection")
    
    bands_without_analysis = sum(1 for band in index.bands if not band.has_analysis)
    if bands_without_analysis > stats.total_bands * 0.5:
        recommendations.append("Use `analyze_band` prompt to add reviews and ratings")
    
    if not recommendations:
        recommendations.append("Collection health looks excellent! Consider generating insights for deeper analysis.")
    
    for rec in recommendations:
        section.append(f"- {rec}")
    
    return "\n".join(section)


def _generate_metadata_info_section(index: CollectionIndex) -> str:
    """Generate metadata information section."""
    section = ["## ℹ️ Collection Metadata"]
    
    # Parse last scan timestamp
    try:
        last_scan = datetime.fromisoformat(index.last_scan.replace('Z', '+00:00'))
        formatted_scan = last_scan.strftime("%B %d, %Y at %I:%M %p")
    except:
        formatted_scan = index.last_scan
    
    meta_table = [
        "| | |",
        "|---|---|",
        f"| **Last Scan** | {formatted_scan} |",
        f"| **Schema Version** | {index.metadata_version} |",
        f"| **Data Source** | `.collection_index.json` |",
        f"| **MCP Resource** | `collection://summary` |",
        f"| **Total Size** | {len(index.bands)} bands, {index.stats.total_albums} albums |"
    ]
    
    section.extend(meta_table)
    
    return "\n".join(section)


# Status helper functions

def _get_collection_size_status(count: int) -> str:
    """Get status indicator for collection size."""
    if count >= 100:
        return "🎭 Large"
    elif count > 20:
        return "🎭 Medium" 
    else:
        return "🎭 Small"


def _get_albums_status(count: int) -> str:
    """Get status indicator for album count."""
    if count > 1000:
        return "📀 Huge"
    elif count > 500:
        return "📀 Large"
    elif count > 100:
        return "📀 Medium"
    else:
        return "📀 Small"


def _get_missing_status(count: int) -> str:
    """Get status indicator for missing albums."""
    if count == 0:
        return "✅ None"
    elif count < 10:
        return "🟡 Few"
    elif count < 50:
        return "🟠 Some"
    else:
        return "🔴 Many"


def _get_completion_status(percentage: float) -> str:
    """Get status indicator for completion percentage."""
    if percentage >= 95:
        return "🟢 Excellent"
    elif percentage >= 80:
        return "🟡 Good"
    elif percentage >= 60:
        return "🟠 Fair"
    else:
        return "🔴 Poor"


def _get_avg_albums_status(avg: float) -> str:
    """Get status indicator for average albums per band."""
    if avg > 8:
        return "🎵 High"
    elif avg > 5:
        return "🎵 Good"
    elif avg > 3:
        return "🎵 Fair"
    else:
        return "🎵 Low"


def _get_metadata_status(with_metadata: int, total: int) -> str:
    """Get status indicator for metadata coverage."""
    if total == 0:
        return "⚪ N/A"
    
    percentage = (with_metadata / total) * 100
    if percentage >= 90:
        return "🟢 Excellent"
    elif percentage >= 70:
        return "🟡 Good"
    elif percentage >= 50:
        return "🟠 Fair"
    else:
        return "🔴 Poor"


def _get_metadata_coverage_status(percentage: float) -> str:
    """Get status indicator for metadata coverage percentage."""
    if percentage >= 90:
        return "🟢 Excellent"
    elif percentage >= 70:
        return "🟡 Good"
    elif percentage >= 50:
        return "🟠 Fair"
    else:
        return "🔴 Poor"


def _generate_no_collection_message() -> str:
    """Generate message when no collection index is found."""
    return """# 🎵 Music Collection Summary

## ❌ No Collection Data Available

No collection index found. Your music collection has not been scanned yet.

### Getting Started

1. **Scan Your Collection**: Use the `scan_music_folders` tool to discover your music
2. **Set Music Path**: Ensure `MUSIC_ROOT_PATH` environment variable is correctly set
3. **Add Metadata**: Use `fetch_band_info` and `save_band_metadata` tools to enrich your collection
4. **Analyze Bands**: Use `analyze_band` prompt for reviews and ratings

### Help

- Check that your music folder exists and contains band folders
- Verify the `MUSIC_ROOT_PATH` configuration points to the correct directory
- Use the `get_band_list` tool after scanning to see discovered bands
- Review the documentation for proper folder structure

### Collection Structure

Your music should be organized as:
```
Music Root/
├── Band Name 1/
│   ├── Album 1/
│   └── Album 2/
├── Band Name 2/
│   └── Album 1/
```
"""


def _generate_error_message(error: str) -> str:
    """Generate error message for failed operations."""
    return f"""# 🎵 Music Collection Summary

## ⚠️ Error Loading Collection Data

An error occurred while loading the collection summary:

```
{error}
```

### Troubleshooting

1. **Check File Permissions**: Ensure the collection index file is readable
2. **Validate JSON**: The `.collection_index.json` file may be corrupted
3. **Rescan Collection**: Use `scan_music_folders` to refresh the collection index
4. **Check Configuration**: Verify the music root path is correctly set

### Recovery Options

- Use the `scan_music_folders` tool with `force_rescan=true` to rebuild the index
- Check the `.collection_index.json` file in your music root directory
- Review system logs for additional error details

### Support

If the problem persists, the collection index may need to be rebuilt from scratch.
"""