"""
Band Info Resource for Music Collection MCP Server.

This module provides markdown-formatted band information resources including
detailed metadata, album information, analysis data, and missing album tracking.
"""

import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from ..tools.storage import load_band_metadata, StorageError
from ..models import BandMetadata, Album, AlbumAnalysis

logger = logging.getLogger(__name__)


def get_band_info_markdown(band_name: str) -> str:
    """
    Generate detailed band information in markdown format.
    
    This function creates a comprehensive markdown resource containing:
    - Band overview (name, formation, genre, origin, members)
    - Album listing with track counts, years, and missing status
    - Analysis section with reviews and ratings
    - Similar bands information
    - Collection statistics and completion status
    
    Args:
        band_name: Name of the band to retrieve information for
        
    Returns:
        Markdown-formatted string with complete band information
    """
    try:
        # Load band metadata
        metadata = load_band_metadata(band_name)
        
        if not metadata:
            return _generate_no_metadata_message(band_name)
        
        # Generate comprehensive markdown
        return _generate_band_markdown(metadata)
        
    except StorageError as e:
        logger.error(f"Storage error loading band info for {band_name}: {e}")
        return _generate_error_message(band_name, str(e))
    except Exception as e:
        logger.error(f"Unexpected error loading band info for {band_name}: {e}")
        return _generate_error_message(band_name, f"Unexpected error: {e}")


def _generate_band_markdown(metadata: BandMetadata) -> str:
    """
    Generate detailed markdown for band with complete metadata.
    
    Args:
        metadata: BandMetadata instance with complete band information
        
    Returns:
        Formatted markdown string
    """
    markdown_parts = []
    
    # Header and basic information
    markdown_parts.append(_generate_header_section(metadata))
    
    # Band details
    markdown_parts.append(_generate_details_section(metadata))
    
    # Albums section
    markdown_parts.append(_generate_albums_section(metadata))
    
    # Missing albums section (if any)
    missing_albums = metadata.get_missing_albums()
    if missing_albums:
        markdown_parts.append(_generate_missing_albums_section(missing_albums))
    
    # Analysis section (if available)
    if metadata.analyze:
        markdown_parts.append(_generate_analysis_section(metadata.analyze))
    
    # Collection statistics
    markdown_parts.append(_generate_statistics_section(metadata))
    
    # Metadata information
    markdown_parts.append(_generate_metadata_section(metadata))
    
    return "\n\n".join(markdown_parts)


def _generate_header_section(metadata: BandMetadata) -> str:
    """Generate the header section with band name and key stats."""
    completion_percentage = _calculate_completion_percentage(metadata)
    
    header = f"# {metadata.band_name}"
    
    if metadata.formed:
        header += f" ({metadata.formed})"
    
    # Add status badges
    badges = []
    if metadata.analyze and metadata.analyze.rate > 0:
        badges.append(f"⭐ **{metadata.analyze.rate}/10**")
    
    if completion_percentage < 100:
        missing_count = len(metadata.get_missing_albums())
        badges.append(f"⚠️ **{missing_count} missing albums**")
    else:
        badges.append("✅ **Complete collection**")
    
    if metadata.analyze:
        badges.append("📊 **Analyzed**")
    
    if badges:
        header += f"\n\n{' • '.join(badges)}"
    
    return header


def _generate_details_section(metadata: BandMetadata) -> str:
    """Generate the band details section with formation, genre, origin, members."""
    details = ["## Band Information"]
    
    if metadata.description:
        details.append(f"*{metadata.description}*")
        details.append("")  # Add spacing
    
    info_table = ["| | |", "|---|---|"]
    
    if metadata.formed:
        info_table.append(f"| **Formed** | {metadata.formed} |")
    
    if metadata.genres:
        genres_str = ", ".join(metadata.genres)
        info_table.append(f"| **Genres** | {genres_str} |")
    
    if metadata.origin:
        info_table.append(f"| **Origin** | {metadata.origin} |")
    
    if metadata.members:
        members_str = ", ".join(metadata.members)
        info_table.append(f"| **Members** | {members_str} |")
    
    info_table.append(f"| **Total Albums** | {metadata.albums_count} |")
    
    completion_percentage = _calculate_completion_percentage(metadata)
    info_table.append(f"| **Collection Status** | {completion_percentage:.1f}% complete |")
    
    details.extend(info_table)
    
    return "\n".join(details)


def _generate_albums_section(metadata: BandMetadata) -> str:
    """Generate the albums section with detailed album information organized by type."""
    albums = ["## Albums"]
    
    # Get local albums (not missing)
    local_albums = metadata.get_local_albums()
    missing_albums = metadata.get_missing_albums()
    
    if not metadata.albums:
        albums.append("*No album information available.*")
        return "\n".join(albums)
    
    # Add folder structure information if available
    if metadata.folder_structure:
        structure_info = []
        structure_info.append(f"**Organization:** {metadata.folder_structure.structure_type.value.title()}")
        structure_info.append(f"**Health:** {metadata.folder_structure.get_organization_health().title()}")
        structure_info.append(f"**Score:** {metadata.folder_structure.structure_score}/100")
        
        if metadata.folder_structure.is_migration_recommended():
            structure_info.append("⚠️ **Migration recommended**")
        
        albums.append("### 📁 Folder Organization")
        albums.append(" • ".join(structure_info))
        albums.append("")
    
    # Local albums section organized by type
    if local_albums:
        albums.append("### 🎵 Available Albums")
        albums.append("")
        
        # Group albums by type
        albums_by_type = {}
        for album in local_albums:
            album_type = album.type.value if hasattr(album.type, 'value') else str(album.type)
            if album_type not in albums_by_type:
                albums_by_type[album_type] = []
            albums_by_type[album_type].append(album)
        
        # Define type order and icons
        type_order = ["Album", "EP", "Single", "Live", "Demo", "Compilation", "Instrumental", "Split"]
        type_icons = {
            "Album": "💿", "EP": "💽", "Single": "🎵", "Live": "🎤",
            "Demo": "🔧", "Compilation": "📦", "Instrumental": "🎼", "Split": "🤝"
        }
        
        # Display albums by type
        for album_type in type_order:
            if album_type in albums_by_type:
                type_albums = albums_by_type[album_type]
                icon = type_icons.get(album_type, "📀")
                albums.append(f"#### {icon} {album_type}s ({len(type_albums)})")
                albums.append("")
                
                for album in sorted(type_albums, key=lambda a: a.year or "0000"):
                    album_info = _format_album_info_enhanced(album, metadata.analyze)
                    albums.append(album_info)
                albums.append("")
        
        # Handle any albums with types not in the standard list
        other_types = [t for t in albums_by_type.keys() if t not in type_order]
        for album_type in sorted(other_types):
            type_albums = albums_by_type[album_type]
            albums.append(f"#### 📀 {album_type}s ({len(type_albums)})")
            albums.append("")
            
            for album in sorted(type_albums, key=lambda a: a.year or "0000"):
                album_info = _format_album_info_enhanced(album, metadata.analyze)
                albums.append(album_info)
            albums.append("")
    
    return "\n".join(albums)


def _generate_missing_albums_section(missing_albums: List[Album]) -> str:
    """Generate the missing albums section."""
    section = ["## 🔍 Missing Albums"]
    section.append(f"*{len(missing_albums)} albums not found in local collection*")
    section.append("")
    
    for album in missing_albums:
        album_info = _format_album_info(album, None, is_missing=True)
        section.append(album_info)
    
    return "\n".join(section)


def _generate_analysis_section(analysis) -> str:
    """Generate the analysis section with reviews and ratings."""
    section = ["## 📊 Analysis & Reviews"]
    
    # Overall band analysis
    if analysis.review:
        section.append("### Overall Review")
        section.append("")
        section.append(f"**Rating: {analysis.rate}/10**")
        section.append("")
        section.append(analysis.review)
        section.append("")
    
    # Album-specific analysis
    if analysis.albums:
        section.append("### Album Reviews")
        section.append("")
        
        for album_analysis in analysis.albums:
            section.append(f"#### {album_analysis.album_name}")
            if album_analysis.rate > 0:
                section.append(f"**Rating: {album_analysis.rate}/10**")
            if album_analysis.review:
                section.append("")
                section.append(album_analysis.review)
            section.append("")
    
    # Similar bands
    if analysis.similar_bands:
        section.append("### Similar Artists")
        similar_bands_list = ", ".join(f"`{band}`" for band in analysis.similar_bands)
        section.append(similar_bands_list)
    
    return "\n".join(section)


def _generate_statistics_section(metadata: BandMetadata) -> str:
    """Generate collection statistics section with enhanced metadata."""
    section = ["## 📈 Collection Statistics"]
    
    local_albums = metadata.get_local_albums()
    missing_albums = metadata.get_missing_albums()
    
    # Basic statistics table
    stats_table = [
        "| Statistic | Value |",
        "|-----------|-------|",
        f"| Total Albums | {metadata.albums_count} |",
        f"| Available Locally | {len(local_albums)} |",
        f"| Missing | {len(missing_albums)} |",
        f"| Completion | {_calculate_completion_percentage(metadata):.1f}% |"
    ]
    
    # Add genre statistics
    if metadata.genres:
        stats_table.append(f"| Genres | {len(metadata.genres)} |")
    
    # Add member count
    if metadata.members:
        stats_table.append(f"| Members | {len(metadata.members)} |")
    
    # Add total tracks count
    total_tracks = sum(album.track_count for album in metadata.albums)
    if total_tracks > 0:
        stats_table.append(f"| Total Tracks | {total_tracks} |")
    
    # Add analysis status
    analysis_status = "✅ Yes" if metadata.analyze else "❌ No"
    stats_table.append(f"| Has Analysis | {analysis_status} |")
    
    section.extend(stats_table)
    
    # Add album types distribution if available
    if metadata.albums:
        section.append("")
        section.append("### 🎯 Album Types Distribution")
        
        # Calculate album types
        album_types = {}
        for album in metadata.albums:
            album_type = album.type.value if hasattr(album.type, 'value') else str(album.type)
            album_types[album_type] = album_types.get(album_type, 0) + 1
        
        # Create distribution table
        distribution_table = [
            "| Type | Count | Percentage |",
            "|------|-------|------------|"
        ]
        
        total_albums = len(metadata.albums)
        for album_type in sorted(album_types.keys()):
            count = album_types[album_type]
            percentage = (count / total_albums * 100) if total_albums > 0 else 0
            distribution_table.append(f"| {album_type} | {count} | {percentage:.1f}% |")
        
        section.extend(distribution_table)
    
    # Add compliance statistics if available
    compliance_scores = []
    for album in metadata.albums:
        if album.folder_compliance:
            compliance_scores.append(album.folder_compliance.compliance_score)
    
    if compliance_scores:
        section.append("")
        section.append("### 📁 Folder Compliance")
        
        avg_score = sum(compliance_scores) / len(compliance_scores)
        compliant_count = sum(1 for score in compliance_scores if score >= 75)
        
        # Determine overall compliance level
        if avg_score >= 90:
            overall_level = "Excellent ✅"
        elif avg_score >= 75:
            overall_level = "Good 🟢"
        elif avg_score >= 50:
            overall_level = "Fair 🟡"
        elif avg_score >= 25:
            overall_level = "Poor 🟠"
        else:
            overall_level = "Critical 🔴"
        
        compliance_table = [
            "| Metric | Value |",
            "|--------|-------|",
            f"| Average Score | {avg_score:.1f}/100 |",
            f"| Overall Level | {overall_level} |",
            f"| Compliant Albums | {compliant_count}/{len(compliance_scores)} |",
            f"| Compliance Rate | {(compliant_count/len(compliance_scores)*100):.1f}% |"
        ]
        
        section.extend(compliance_table)
    
    # Add folder structure information if available
    if metadata.folder_structure:
        section.append("")
        section.append("### 🗂️ Folder Organization")
        
        structure_table = [
            "| Aspect | Status |",
            "|--------|--------|",
            f"| Structure Type | {metadata.folder_structure.structure_type.value.title()} |",
            f"| Consistency | {metadata.folder_structure.consistency.value.title()} |",
            f"| Organization Score | {metadata.folder_structure.structure_score}/100 |",
            f"| Health Assessment | {metadata.folder_structure.get_organization_health().title()} |",
            f"| Migration Needed | {'Yes ⚠️' if metadata.folder_structure.is_migration_recommended() else 'No ✅'} |"
        ]
        
        section.extend(structure_table)
        
        if metadata.folder_structure.recommendations:
            section.append("")
            section.append("**Recommendations:**")
            for i, rec in enumerate(metadata.folder_structure.recommendations[:3], 1):  # Show top 3
                section.append(f"{i}. {rec}")
            
            if len(metadata.folder_structure.recommendations) > 3:
                remaining = len(metadata.folder_structure.recommendations) - 3
                section.append(f"*...and {remaining} more recommendations*")
    
    return "\n".join(section)


def _generate_metadata_section(metadata: BandMetadata) -> str:
    """Generate metadata information section."""
    section = ["## ℹ️ Metadata Information"]
    
    # Parse last updated timestamp
    try:
        last_updated = datetime.fromisoformat(metadata.last_updated.replace('Z', '+00:00'))
        formatted_date = last_updated.strftime("%B %d, %Y at %I:%M %p")
    except:
        formatted_date = metadata.last_updated
    
    meta_table = [
        "| | |",
        "|---|---|",
        f"| **Last Updated** | {formatted_date} |",
        f"| **Data Source** | `.band_metadata.json` |",
        f"| **MCP Resource** | `band://info/{metadata.band_name}` |"
    ]
    
    section.extend(meta_table)
    
    return "\n".join(section)


def _format_album_info(album: Album, analysis=None, is_missing: bool = False) -> str:
    """
    Format individual album information.
    
    Args:
        album: Album instance
        analysis: BandAnalysis instance (optional)
        is_missing: Whether this is a missing album
        
    Returns:
        Formatted album information string
    """
    # Album header with year and tracks
    header_parts = []
    
    if album.year:
        header_parts.append(album.year)
    
    if album.track_count > 0:
        track_word = "track" if album.track_count == 1 else "tracks"
        header_parts.append(f"{album.track_count} {track_word}")
    
    if album.duration:
        header_parts.append(album.duration)
    
    header_suffix = f" ({', '.join(header_parts)})" if header_parts else ""
    
    # Status indicator
    status = "🔍 Missing" if is_missing else "🎵 Available"
    
    # Album title with status
    album_line = f"**{album.album_name}**{header_suffix} - {status}"
    
    # Add genres if available
    if album.genres:
        genres_str = ", ".join(album.genres)
        album_line += f"\n  *{genres_str}*"
    
    # Add album analysis if available
    if analysis and analysis.albums:
        for album_analysis in analysis.albums:
            if album_analysis.album_name == album.album_name:
                if album_analysis.rate > 0:
                    album_line += f"\n  ⭐ **{album_analysis.rate}/10**"
                if album_analysis.review:
                    # Truncate long reviews for album list
                    review_preview = album_analysis.review[:100]
                    if len(album_analysis.review) > 100:
                        review_preview += "..."
                    album_line += f"\n  *{review_preview}*"
                break
    
    return album_line


def _format_album_info_enhanced(album: Album, analysis=None) -> str:
    """
    Format individual album information with enhanced details.
    
    Args:
        album: Album instance
        analysis: BandAnalysis instance (optional)
        
    Returns:
        Formatted album information string
    """
    # Album header with year and tracks
    header_parts = []
    
    if album.year:
        header_parts.append(album.year)
    
    if album.track_count > 0:
        track_word = "track" if album.track_count == 1 else "tracks"
        header_parts.append(f"{album.track_count} {track_word}")
    
    if album.duration:
        header_parts.append(album.duration)
    
    header_suffix = f" ({', '.join(header_parts)})" if header_parts else ""
    
    # Album title with edition if available
    title = album.album_name
    if album.edition:
        title += f" ({album.edition})"
    
    album_line = f"**{title}**{header_suffix}"
    
    # Add compliance status if available
    if album.folder_compliance:
        compliance_level = album.folder_compliance.get_compliance_level()
        score = album.folder_compliance.compliance_score
        
        compliance_icons = {
            "excellent": "✅",
            "good": "🟢", 
            "fair": "🟡",
            "poor": "🟠",
            "critical": "🔴"
        }
        
        icon = compliance_icons.get(compliance_level, "❓")
        album_line += f"\n  {icon} **Compliance:** {compliance_level.title()} ({score}/100)"
        
        if album.folder_compliance.issues:
            issues_count = len(album.folder_compliance.issues)
            album_line += f" • {issues_count} issue{'s' if issues_count != 1 else ''}"
    
    # Add folder path information
    if album.folder_path:
        album_line += f"\n  📁 `{album.folder_path}`"
    
    # Add genres if available
    if album.genres:
        genres_str = ", ".join(album.genres)
        album_line += f"\n  🎼 *{genres_str}*"
    
    # Add album analysis if available
    if analysis and analysis.albums:
        for album_analysis in analysis.albums:
            if album_analysis.album_name == album.album_name:
                if album_analysis.rate > 0:
                    album_line += f"\n  ⭐ **{album_analysis.rate}/10**"
                if album_analysis.review:
                    # Truncate long reviews for album list
                    review_preview = album_analysis.review[:100]
                    if len(album_analysis.review) > 100:
                        review_preview += "..."
                    album_line += f"\n  💭 *{review_preview}*"
                break
    
    return album_line


def _calculate_completion_percentage(metadata: BandMetadata) -> float:
    """Calculate collection completion percentage."""
    if metadata.albums_count == 0:
        return 100.0
    
    local_albums = len(metadata.get_local_albums())
    return (local_albums / metadata.albums_count) * 100


def _generate_no_metadata_message(band_name: str) -> str:
    """Generate message for bands without metadata."""
    return f"""# {band_name}

## ❌ No Metadata Available

No metadata file found for **{band_name}**.

### Next Steps

1. **Scan Collection**: Use the `scan_music_folders` tool to discover this band
2. **Fetch Information**: Use the `fetch_band_info` prompt to gather band details
3. **Save Metadata**: Use the `save_band_metadata` tool to store the information
4. **Analyze Band**: Use the `analyze_band` prompt for reviews and ratings

### Help

- Check if the band folder exists in your music collection
- Ensure the band name matches the folder name exactly
- Use the `get_band_list` tool to see all discovered bands
"""


def _generate_error_message(band_name: str, error: str) -> str:
    """Generate error message for failed operations."""
    return f"""# {band_name}

## ⚠️ Error Loading Band Information

An error occurred while loading metadata for **{band_name}**:

```
{error}
```

### Troubleshooting

1. **Check File Permissions**: Ensure the metadata file is readable
2. **Validate JSON**: The `.band_metadata.json` file may be corrupted
3. **Rescan Collection**: Use `scan_music_folders` to refresh the collection
4. **Check Path**: Verify the music root path is correctly configured

### Support

- Use the `validate_band_metadata` tool to check metadata integrity
- Review the `schema://band_metadata` resource for correct format
- Contact support if the error persists
""" 