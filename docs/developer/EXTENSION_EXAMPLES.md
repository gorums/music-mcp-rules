# Extension Examples for Music Collection MCP Server with Album Type Classification

## Overview

The Music Collection MCP Server is designed with extensibility in mind. This document provides practical examples of how to extend the server with custom tools, resources, prompts, and integrations, focusing on the new album type classification and folder structure analysis features.

## Custom Tool Examples with Album Type Support

### 1. Export Tool - CSV/JSON Export with Album Types

Create a custom tool to export collection data including album types and structure analysis:

```python
# src/tools/export.py
import csv
import json
from pathlib import Path
from typing import Dict, Any, List, Literal
from datetime import datetime

from ..models.collection import CollectionIndex
from ..models.band import BandMetadata
from ..models.album import Album, AlbumType
from ..models.structure import StructureType
from ..config import Config

class CollectionExporter:
    """Export collection data with album type and structure information."""
    
    def __init__(self, config: Config):
        self.config = config
    
    def export_collection_with_types(
        self,
        format: Literal["csv", "json", "xml"],
        include_analysis: bool = True,
        include_type_stats: bool = True,
        include_structure_analysis: bool = True,
        output_path: str = None
    ) -> Dict[str, Any]:
        """
        Export complete collection data including album types and structure analysis.
        
        Args:
            format: Export format (csv, json, xml)
            include_analysis: Include analysis data in export
            include_type_stats: Include album type distribution statistics
            include_structure_analysis: Include folder structure analysis
            output_path: Custom output path (optional)
            
        Returns:
            Export result with file path and statistics
        """
        try:
            # Load collection data
            collection_index = self._load_collection_index()
            
            # Generate export data with type information
            export_data = self._prepare_export_data_with_types(
                collection_index, 
                include_analysis,
                include_type_stats,
                include_structure_analysis
            )
            
            # Determine output path
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"collection_export_with_types_{timestamp}.{format}"
            
            # Export based on format
            if format == "csv":
                self._export_csv_with_types(export_data, output_path)
            elif format == "json":
                self._export_json_with_types(export_data, output_path)
            elif format == "xml":
                self._export_xml_with_types(export_data, output_path)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            return {
                "success": True,
                "message": f"Collection exported to {format.upper()} with album type data",
                "output_file": output_path,
                "records_exported": len(export_data),
                "format": format,
                "include_analysis": include_analysis,
                "include_type_stats": include_type_stats,
                "type_summary": self._generate_type_summary(export_data)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "format": format
            }
    
    def _prepare_export_data_with_types(
        self, 
        collection_index: CollectionIndex, 
        include_analysis: bool,
        include_type_stats: bool,
        include_structure_analysis: bool
    ) -> List[Dict[str, Any]]:
        """Prepare export data with album type information."""
        export_data = []
        
        for band_entry in collection_index.bands:
            band_metadata = self._load_band_metadata(band_entry.band_name)
            
            band_data = {
                "band_name": band_entry.band_name,
                "formed": band_metadata.formed if band_metadata else None,
                "genres": band_metadata.genres if band_metadata else [],
                "origin": band_metadata.origin if band_metadata else None,
                "albums_count": band_entry.albums_count,
                "local_albums": band_entry.local_albums,
                "missing_albums": band_entry.missing_albums,
                "completion_percentage": band_entry.completion_percentage
            }
            
            # Add album type distribution
            if include_type_stats and band_metadata:
                type_distribution = self._calculate_type_distribution(band_metadata.albums)
                band_data.update({
                    f"type_{album_type.value.lower()}_count": count 
                    for album_type, count in type_distribution.items()
                })
                band_data["type_diversity_score"] = len([c for c in type_distribution.values() if c > 0])
            
            # Add structure analysis
            if include_structure_analysis and band_metadata and band_metadata.folder_structure:
                structure = band_metadata.folder_structure
                band_data.update({
                    "structure_type": structure.structure_type,
                    "structure_score": structure.structure_score,
                    "consistency_score": structure.consistency_score,
                    "compliance_level": structure.consistency,
                    "albums_with_type_folders": structure.albums_with_type_folders,
                    "type_folders_found_count": len(structure.type_folders_found),
                    "structure_recommendations_count": len(structure.recommendations),
                    "structure_issues_count": len(structure.issues)
                })
            
            # Add analysis data
            if include_analysis and band_metadata and band_metadata.analyze:
                band_data.update({
                    "overall_rating": band_metadata.analyze.rate,
                    "has_review": bool(band_metadata.analyze.review),
                    "similar_bands_count": len(band_metadata.analyze.similar_bands or []),
                    "album_ratings_count": len(band_metadata.analyze.albums or [])
                })
            
            export_data.append(band_data)
        
        return export_data
    
    def _calculate_type_distribution(self, albums: List[Album]) -> Dict[AlbumType, int]:
        """Calculate album type distribution for a band."""
        type_counts = {album_type: 0 for album_type in AlbumType}
        
        for album in albums:
            album_type = AlbumType(album.type) if album.type else AlbumType.ALBUM
            type_counts[album_type] += 1
        
        return type_counts
    
    def _export_csv_with_types(self, data: List[Dict[str, Any]], output_path: str) -> None:
        """Export data to CSV format with type information."""
        if not data:
            return
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in data:
                # Flatten complex fields for CSV
                flattened_row = self._flatten_dict_for_types(row)
                writer.writerow(flattened_row)
    
    def _export_json_with_types(self, data: List[Dict[str, Any]], output_path: str) -> None:
        """Export data to JSON format with type metadata."""
        export_metadata = {
            "export_date": datetime.now().isoformat(),
            "format": "json",
            "record_count": len(data),
            "includes_album_types": True,
            "includes_structure_analysis": True,
            "album_type_legend": {
                album_type.value: album_type.value for album_type in AlbumType
            },
            "structure_type_legend": {
                structure_type.value: structure_type.value for structure_type in StructureType
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as jsonfile:
            json.dump({
                "export_metadata": export_metadata,
                "bands": data
            }, jsonfile, indent=2, ensure_ascii=False)

# Register as MCP tool
@app.tool()
def export_collection_with_types(
    format: Literal["csv", "json", "xml"] = "json",
    include_analysis: bool = True,
    include_type_stats: bool = True,
    include_structure_analysis: bool = True,
    output_path: str = None
) -> Dict[str, Any]:
    """
    Export music collection data with album type classification and structure analysis.
    
    Args:
        format: Export format (csv, json, xml)
        include_analysis: Include analysis data in export
        include_type_stats: Include album type distribution statistics
        include_structure_analysis: Include folder structure analysis data
        output_path: Custom output path for export file
        
    Returns:
        Export operation result with type and structure information
    """
    config = get_config()
    exporter = CollectionExporter(config)
    
    return exporter.export_collection_with_types(
        format, include_analysis, include_type_stats, include_structure_analysis, output_path
    )
```

### 2. Album Type Statistics Tool - Advanced Analytics

```python
# src/tools/type_statistics.py
from typing import Dict, Any, List
from collections import defaultdict
import statistics
from datetime import datetime, timedelta

from ..models.album import AlbumType
from ..models.structure import StructureType
from ..config import Config

class AlbumTypeStatistics:
    """Generate advanced album type and structure statistics."""
    
    def __init__(self, config: Config):
        self.config = config
    
    def generate_type_statistics(self) -> Dict[str, Any]:
        """Generate comprehensive album type statistics."""
        collection_index = self._load_collection_index()
        
        stats = {
            "overview": self._calculate_overview_stats(collection_index),
            "type_distribution": self._calculate_type_distribution_stats(collection_index),
            "structure_analysis": self._calculate_structure_stats(collection_index),
            "type_diversity": self._calculate_type_diversity_stats(collection_index),
            "compliance_analysis": self._calculate_compliance_stats(collection_index),
            "recommendations": self._generate_type_recommendations(collection_index)
        }
        
        return {
            "success": True,
            "statistics": stats,
            "generated_at": datetime.now().isoformat()
        }
    
    def _calculate_type_distribution_stats(self, collection_index) -> Dict[str, Any]:
        """Calculate detailed album type distribution statistics."""
        type_counts = defaultdict(int)
        band_type_presence = defaultdict(int)
        type_by_decade = defaultdict(lambda: defaultdict(int))
        
        for band_entry in collection_index.bands:
            band_metadata = self._load_band_metadata(band_entry.band_name)
            if not band_metadata or not band_metadata.albums:
                continue
            
            band_types = set()
            
            for album in band_metadata.albums:
                album_type = AlbumType(album.type) if album.type else AlbumType.ALBUM
                type_counts[album_type.value] += 1
                band_types.add(album_type.value)
                
                # Track by decade if year available
                if album.year and len(album.year) == 4:
                    decade = f"{album.year[:3]}0s"
                    type_by_decade[decade][album_type.value] += 1
            
            # Track band type presence
            for band_type in band_types:
                band_type_presence[band_type] += 1
        
        total_albums = sum(type_counts.values())
        total_bands = len(collection_index.bands)
        
        return {
            "total_albums_by_type": dict(type_counts),
            "percentage_by_type": {
                album_type: (count / total_albums * 100) if total_albums > 0 else 0
                for album_type, count in type_counts.items()
            },
            "bands_with_type": dict(band_type_presence),
            "type_penetration": {
                album_type: (count / total_bands * 100) if total_bands > 0 else 0
                for album_type, count in band_type_presence.items()
            },
            "average_per_band": {
                album_type: (count / total_bands) if total_bands > 0 else 0
                for album_type, count in type_counts.items()
            },
            "type_by_decade": dict(type_by_decade)
        }
    
    def _calculate_structure_stats(self, collection_index) -> Dict[str, Any]:
        """Calculate folder structure statistics."""
        structure_counts = defaultdict(int)
        compliance_scores = []
        structure_scores = []
        
        for band_entry in collection_index.bands:
            band_metadata = self._load_band_metadata(band_entry.band_name)
            if not band_metadata or not band_metadata.folder_structure:
                continue
            
            structure = band_metadata.folder_structure
            structure_counts[structure.structure_type] += 1
            
            if structure.consistency_score is not None:
                compliance_scores.append(structure.consistency_score)
            if structure.structure_score is not None:
                structure_scores.append(structure.structure_score)
        
        return {
            "structure_type_distribution": dict(structure_counts),
            "compliance_statistics": {
                "average_score": statistics.mean(compliance_scores) if compliance_scores else 0,
                "median_score": statistics.median(compliance_scores) if compliance_scores else 0,
                "min_score": min(compliance_scores) if compliance_scores else 0,
                "max_score": max(compliance_scores) if compliance_scores else 0,
                "std_deviation": statistics.stdev(compliance_scores) if len(compliance_scores) > 1 else 0
            },
            "structure_quality": {
                "average_score": statistics.mean(structure_scores) if structure_scores else 0,
                "median_score": statistics.median(structure_scores) if structure_scores else 0,
                "excellent_count": len([s for s in structure_scores if s >= 90]),
                "good_count": len([s for s in structure_scores if 70 <= s < 90]),
                "poor_count": len([s for s in structure_scores if s < 70])
            }
        }
    
    def _calculate_type_diversity_stats(self, collection_index) -> Dict[str, Any]:
        """Calculate type diversity statistics across bands."""
        diversity_scores = []
        most_diverse_bands = []
        missing_type_analysis = defaultdict(list)
        
        for band_entry in collection_index.bands:
            band_metadata = self._load_band_metadata(band_entry.band_name)
            if not band_metadata or not band_metadata.albums:
                continue
            
            # Calculate type diversity for this band
            band_types = set()
            for album in band_metadata.albums:
                album_type = AlbumType(album.type) if album.type else AlbumType.ALBUM
                band_types.add(album_type)
            
            diversity_score = len(band_types)
            diversity_scores.append(diversity_score)
            
            if diversity_score >= 4:  # Highly diverse bands
                most_diverse_bands.append({
                    "band_name": band_entry.band_name,
                    "type_count": diversity_score,
                    "types": [t.value for t in band_types]
                })
            
            # Track missing types
            missing_types = set(AlbumType) - band_types
            for missing_type in missing_types:
                missing_type_analysis[missing_type.value].append(band_entry.band_name)
        
        return {
            "diversity_statistics": {
                "average_types_per_band": statistics.mean(diversity_scores) if diversity_scores else 0,
                "median_types_per_band": statistics.median(diversity_scores) if diversity_scores else 0,
                "max_diversity": max(diversity_scores) if diversity_scores else 0,
                "min_diversity": min(diversity_scores) if diversity_scores else 0
            },
            "most_diverse_bands": sorted(most_diverse_bands, key=lambda x: x["type_count"], reverse=True)[:10],
            "missing_type_opportunities": {
                album_type: {
                    "band_count": len(bands),
                    "percentage": len(bands) / len(collection_index.bands) * 100
                }
                for album_type, bands in missing_type_analysis.items()
            }
        }

# Register as MCP tool
@app.tool()
def analyze_album_type_statistics() -> Dict[str, Any]:
    """
    Generate comprehensive album type and structure statistics for the collection.
    
    Returns:
        Detailed statistics including type distribution, structure analysis, 
        diversity metrics, and recommendations
    """
    config = get_config()
    analyzer = AlbumTypeStatistics(config)
    
    return analyzer.generate_type_statistics()
```

### 3. Structure Migration Tool - Automated Organization

```python
# src/tools/structure_migration.py
from pathlib import Path
from typing import Dict, Any, List, Optional
import shutil
import os

from ..models.album import Album, AlbumType
from ..models.structure import StructureType
from ..models.band import BandMetadata
from ..utils.album_parser import AlbumFolderParser
from ..config import Config

class StructureMigrationTool:
    """Tool for migrating folder structures to enhanced organization."""
    
    def __init__(self, config: Config):
        self.config = config
    
    def analyze_migration_opportunities(self, band_name: str) -> Dict[str, Any]:
        """
        Analyze a band's folder structure for migration opportunities.
        
        Args:
            band_name: Name of the band to analyze
            
        Returns:
            Migration analysis with recommendations and planned operations
        """
        try:
            band_path = Path(self.config.music_root_path) / band_name
            if not band_path.exists():
                return {"success": False, "error": "Band folder not found"}
            
            # Load current metadata
            band_metadata = self._load_band_metadata(band_name)
            if not band_metadata:
                return {"success": False, "error": "Band metadata not found"}
            
            # Analyze current structure
            current_analysis = self._analyze_current_structure(band_path, band_metadata)
            
            # Generate migration plan
            migration_plan = self._generate_migration_plan(band_path, band_metadata, current_analysis)
            
            # Calculate benefits
            benefits = self._calculate_migration_benefits(current_analysis, migration_plan)
            
            return {
                "success": True,
                "band_name": band_name,
                "current_structure": current_analysis,
                "migration_plan": migration_plan,
                "estimated_benefits": benefits,
                "can_migrate": migration_plan["can_migrate"],
                "risk_assessment": migration_plan["risk_assessment"]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def execute_migration(
        self, 
        band_name: str, 
        target_structure: StructureType = StructureType.ENHANCED,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Execute folder structure migration for a band.
        
        Args:
            band_name: Name of the band to migrate
            target_structure: Target structure type (enhanced, default)
            dry_run: If True, only simulate the migration
            
        Returns:
            Migration execution result
        """
        try:
            # Get migration plan
            analysis = self.analyze_migration_opportunities(band_name)
            if not analysis["success"] or not analysis["can_migrate"]:
                return {"success": False, "error": "Migration not possible or advisable"}
            
            migration_plan = analysis["migration_plan"]
            operations = migration_plan["operations"]
            
            if dry_run:
                return {
                    "success": True,
                    "dry_run": True,
                    "planned_operations": operations,
                    "operations_count": len(operations),
                    "estimated_improvement": analysis["estimated_benefits"]["compliance_improvement"]
                }
            
            # Execute actual migration
            results = []
            successful_operations = 0
            
            for operation in operations:
                result = self._execute_operation(operation)
                results.append(result)
                if result["success"]:
                    successful_operations += 1
            
            # Update metadata if migration successful
            if successful_operations == len(operations):
                self._update_metadata_after_migration(band_name, target_structure)
            
            return {
                "success": successful_operations == len(operations),
                "operations_executed": successful_operations,
                "total_operations": len(operations),
                "results": results,
                "target_structure": target_structure.value
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _generate_migration_plan(
        self, 
        band_path: Path, 
        band_metadata: BandMetadata, 
        current_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate detailed migration plan."""
        operations = []
        can_migrate = True
        risk_factors = []
        
        # Check if albums need type folder organization
        if current_analysis["structure_type"] != StructureType.ENHANCED:
            for album in band_metadata.albums:
                if album.missing:
                    continue
                
                current_path = band_path / album.folder_path if album.folder_path else band_path / album.album_name
                album_type = AlbumType(album.type) if album.type else AlbumType.ALBUM
                
                # Determine target path
                if album_type == AlbumType.ALBUM:
                    type_folder = "Album"
                else:
                    type_folder = album_type.value
                
                year_prefix = f"{album.year} - " if album.year else ""
                edition_suffix = f" ({album.edition})" if album.edition else ""
                new_folder_name = f"{year_prefix}{album.album_name}{edition_suffix}"
                target_path = band_path / type_folder / new_folder_name
                
                if current_path != target_path:
                    operations.append({
                        "type": "move_album",
                        "album_name": album.album_name,
                        "source_path": str(current_path),
                        "target_path": str(target_path),
                        "create_type_folder": type_folder,
                        "album_type": album_type.value
                    })
        
        # Risk assessment
        if len(operations) > 20:
            risk_factors.append("Large number of operations (>20)")
        
        total_size_mb = sum(self._get_folder_size(Path(op["source_path"])) for op in operations if Path(op["source_path"]).exists())
        if total_size_mb > 10000:  # 10GB
            risk_factors.append(f"Large data volume ({total_size_mb:.1f}MB)")
        
        return {
            "operations": operations,
            "can_migrate": can_migrate and len(risk_factors) == 0,
            "risk_assessment": {
                "risk_level": "high" if len(risk_factors) > 0 else "low",
                "risk_factors": risk_factors,
                "total_operations": len(operations),
                "estimated_time_minutes": len(operations) * 0.5  # Estimate 30s per operation
            }
        }

# Register as MCP tool  
@app.tool()
def analyze_structure_migration(band_name: str) -> Dict[str, Any]:
    """
    Analyze folder structure migration opportunities for a band.
    
    Args:
        band_name: Name of the band to analyze for migration
        
    Returns:
        Migration analysis with recommendations and planned operations
    """
    config = get_config()
    migrator = StructureMigrationTool(config)
    
    return migrator.analyze_migration_opportunities(band_name)

@app.tool()
def execute_structure_migration(
    band_name: str,
    target_structure: str = "enhanced",
    dry_run: bool = True
) -> Dict[str, Any]:
    """
    Execute folder structure migration for a band.
    
    Args:
        band_name: Name of the band to migrate
        target_structure: Target structure type (enhanced, default)
        dry_run: If True, only simulate the migration
        
    Returns:
        Migration execution result
    """
    config = get_config()
    migrator = StructureMigrationTool(config)
    
    target_type = StructureType(target_structure) if target_structure in [s.value for s in StructureType] else StructureType.ENHANCED
    
    return migrator.execute_migration(band_name, target_type, dry_run)
```

## Custom Resource Examples

### 1. Genre Overview Resource

```python
# src/resources/genre_overview.py
from typing import Dict, Any
from collections import defaultdict

class GenreOverviewResource:
    """Resource for genre-specific collection overview."""
    
    def __init__(self, config: Config):
        self.config = config
    
    def get_genre_overview(self, genre_name: str) -> str:
        """
        Generate markdown overview for a specific genre.
        
        Args:
            genre_name: Name of the genre to overview
            
        Returns:
            Markdown-formatted genre overview
        """
        try:
            # Load collection data
            collection_index = self._load_collection_index()
            
            # Filter bands by genre
            genre_bands = self._filter_bands_by_genre(collection_index, genre_name)
            
            if not genre_bands:
                return f"# {genre_name}\n\n❌ **No bands found for genre '{genre_name}'**"
            
            # Generate markdown content
            markdown = self._generate_genre_markdown(genre_name, genre_bands)
            
            return markdown
            
        except Exception as e:
            return f"# {genre_name}\n\n❌ **Error**: {str(e)}"
    
    def _generate_genre_markdown(self, genre_name: str, bands: List[Any]) -> str:
        """Generate comprehensive genre overview markdown."""
        total_albums = sum(band.albums_count for band in bands)
        total_missing = sum(band.missing_albums for band in bands)
        completion_rate = ((total_albums - total_missing) / total_albums * 100) if total_albums > 0 else 0
        
        # Header
        markdown = [
            f"# {genre_name} Collection Overview",
            "",
            "## 📊 Statistics",
            f"- **Total Bands**: {len(bands)}",
            f"- **Total Albums**: {total_albums}",
            f"- **Missing Albums**: {total_missing}",
            f"- **Completion Rate**: {completion_rate:.1f}%",
            ""
        ]
        
        # Top bands by album count
        sorted_bands = sorted(bands, key=lambda b: b.albums_count, reverse=True)[:10]
        
        markdown.extend([
            "## 🏆 Top Bands by Collection Size",
            "",
            "| Band | Albums | Missing | Completion |",
            "|------|--------|---------|------------|"
        ])
        
        for band in sorted_bands:
            completion = ((band.albums_count - band.missing_albums) / band.albums_count * 100) if band.albums_count > 0 else 0
            status = "✅" if completion == 100 else "⚠️" if completion >= 80 else "❌"
            
            markdown.append(
                f"| {status} {band.band_name} | {band.albums_count} | {band.missing_albums} | {completion:.1f}% |"
            )
        
        # Missing albums section
        bands_with_missing = [b for b in bands if b.missing_albums > 0]
        if bands_with_missing:
            markdown.extend([
                "",
                f"## 📋 Incomplete Collections ({len(bands_with_missing)} bands)",
                ""
            ])
            
            for band in sorted(bands_with_missing, key=lambda b: b.missing_albums, reverse=True)[:5]:
                markdown.append(f"- **{band.band_name}**: {band.missing_albums} missing albums")
        
        return "\n".join(markdown)

# Register as MCP resource
@app.resource("genre://overview/{genre_name}")
def get_genre_overview_resource(genre_name: str) -> str:
    """Get comprehensive overview for a specific genre."""
    config = get_config()
    resource = GenreOverviewResource(config)
    
    # URL decode genre name
    from urllib.parse import unquote
    decoded_genre = unquote(genre_name)
    
    return resource.get_genre_overview(decoded_genre)
```

### 2. Timeline Resource

```python
# src/resources/timeline.py
from datetime import datetime
from typing import Dict, List, Any

class TimelineResource:
    """Resource for chronological collection timeline."""
    
    def get_collection_timeline(self) -> str:
        """Generate chronological timeline of collection."""
        try:
            # Load all band metadata
            timeline_data = self._build_timeline_data()
            
            # Generate timeline markdown
            markdown = self._generate_timeline_markdown(timeline_data)
            
            return markdown
            
        except Exception as e:
            return f"# Collection Timeline\n\n❌ **Error**: {str(e)}"
    
    def _build_timeline_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Build chronological timeline data."""
        timeline = defaultdict(list)
        
        collection_index = self._load_collection_index()
        
        for band_entry in collection_index.bands:
            # Load band metadata
            band_metadata = self._load_band_metadata(band_entry.band_name)
            
            if band_metadata and band_metadata.formed:
                try:
                    year = int(band_metadata.formed)
                    decade = f"{year//10*10}s"
                    
                    timeline[decade].append({
                        "year": year,
                        "band_name": band_metadata.band_name,
                        "genres": band_metadata.genres,
                        "albums_count": band_metadata.albums_count,
                        "origin": band_metadata.origin
                    })
                except ValueError:
                    continue
        
        return timeline
    
    def _generate_timeline_markdown(self, timeline_data: Dict[str, List[Dict[str, Any]]]) -> str:
        """Generate timeline markdown from data."""
        markdown = [
            "# Collection Timeline",
            "",
            "A chronological overview of bands in your collection by formation decade.",
            ""
        ]
        
        # Sort decades
        sorted_decades = sorted(timeline_data.keys())
        
        for decade in sorted_decades:
            bands = sorted(timeline_data[decade], key=lambda b: b["year"])
            
            markdown.extend([
                f"## 🎵 {decade}",
                f"*{len(bands)} bands formed in this decade*",
                ""
            ])
            
            for band in bands:
                genres_str = ", ".join(band["genres"][:3]) if band["genres"] else "Unknown"
                origin_str = f" ({band['origin']})" if band['origin'] else ""
                
                markdown.append(
                    f"- **{band['year']}**: {band['band_name']}{origin_str} - "
                    f"{genres_str} - {band['albums_count']} albums"
                )
            
            markdown.append("")
        
        return "\n".join(markdown)

# Register as MCP resource
@app.resource("collection://timeline")
def get_collection_timeline_resource() -> str:
    """Get chronological timeline of collection."""
    config = get_config()
    resource = TimelineResource(config)
    
    return resource.get_collection_timeline()
```

## Custom Prompt Examples

### 1. Music Discovery Prompt

```python
# src/prompts/discover_music.py
from typing import Dict, Any, List

class MusicDiscoveryPrompt:
    """Prompt for discovering new music based on collection."""
    
    def get_discovery_prompt(
        self,
        discovery_type: str = "similar",
        genres: List[str] = None,
        favorite_bands: List[str] = None,
        era: str = None
    ) -> Dict[str, Any]:
        """
        Generate music discovery prompt based on collection analysis.
        
        Args:
            discovery_type: Type of discovery (similar, new_genres, era_exploration)
            genres: Preferred genres for discovery
            favorite_bands: User's favorite bands for similarity matching
            era: Specific era to explore
            
        Returns:
            Structured prompt for music discovery
        """
        # Analyze current collection
        collection_analysis = self._analyze_current_collection()
        
        # Generate prompt based on discovery type
        if discovery_type == "similar":
            return self._generate_similar_discovery_prompt(collection_analysis, favorite_bands)
        elif discovery_type == "new_genres":
            return self._generate_genre_exploration_prompt(collection_analysis, genres)
        elif discovery_type == "era_exploration":
            return self._generate_era_exploration_prompt(collection_analysis, era)
        else:
            return self._generate_general_discovery_prompt(collection_analysis)
    
    def _generate_similar_discovery_prompt(self, analysis: Dict, favorites: List[str]) -> Dict[str, Any]:
        """Generate prompt for finding similar artists."""
        prompt_content = f"""
Based on this music collection analysis, suggest new artists to explore:

## Current Collection Profile
- **Total Bands**: {analysis['total_bands']}
- **Top Genres**: {', '.join(analysis['top_genres'][:5])}
- **Collection Strength**: {analysis['collection_focus']}

## Favorite Bands for Reference
{chr(10).join(f'- {band}' for band in (favorites or analysis['top_rated_bands'][:5]))}

## Discovery Request
Find 10 new artists that would complement this collection, focusing on:
1. Artists similar to the favorite bands listed
2. Artists that fill gaps in the current collection
3. Both classic and contemporary recommendations

For each recommendation, provide:
- Artist name
- Primary genre
- Key albums to start with
- Relationship to existing collection (why it fits)
- Availability status (active/disbanded)

Format as a structured list with brief explanations.
"""
        
        return {
            "role": "user",
            "content": prompt_content.strip()
        }

# Register as MCP prompt
@app.prompt("discover_music")
def discover_music_prompt(
    discovery_type: str = "similar",
    genres: List[str] = None,
    favorite_bands: List[str] = None,
    era: str = None
) -> Dict[str, Any]:
    """
    Generate music discovery prompt based on collection.
    
    Args:
        discovery_type: Type of discovery to perform
        genres: Preferred genres for discovery
        favorite_bands: Favorite bands for similarity matching
        era: Specific era to explore
    """
    config = get_config()
    prompt_generator = MusicDiscoveryPrompt(config)
    
    return prompt_generator.get_discovery_prompt(
        discovery_type, genres, favorite_bands, era
    )
```

### 2. Collection Curation Prompt

```python
# src/prompts/curate_collection.py

class CollectionCurationPrompt:
    """Prompt for collection curation and improvement suggestions."""
    
    def get_curation_prompt(
        self,
        focus_area: str = "gaps",
        budget_range: str = "medium",
        priority_level: str = "high"
    ) -> Dict[str, Any]:
        """
        Generate collection curation prompt.
        
        Args:
            focus_area: Area to focus on (gaps, duplicates, upgrades, completion)
            budget_range: Budget consideration (low, medium, high, unlimited)
            priority_level: Priority level (high, medium, low)
        """
        collection_analysis = self._perform_curation_analysis()
        
        prompt_content = f"""
# Collection Curation Analysis

Analyze this music collection and provide curation recommendations:

## Current Collection Status
- **Total Collection**: {collection_analysis['total_bands']} bands, {collection_analysis['total_albums']} albums
- **Completion Rate**: {collection_analysis['completion_rate']:.1f}%
- **Missing Albums**: {collection_analysis['missing_albums']} across {collection_analysis['incomplete_bands']} bands
- **Genre Distribution**: {collection_analysis['genre_summary']}

## Focus Area: {focus_area.title()}
Budget Range: {budget_range.title()}
Priority Level: {priority_level.title()}

## Detailed Analysis Needed
Please provide recommendations for:

1. **Priority Acquisitions**: Most important missing albums to acquire first
2. **Collection Gaps**: Genres or eras that are underrepresented
3. **Completion Opportunities**: Bands where acquiring a few albums would complete the collection
4. **Quality Upgrades**: Older releases that might benefit from remastering or better editions
5. **Discovery Potential**: New artists that would enhance the collection's coherence

## Output Format
Structure your response as:
- **Immediate Actions** (top 5 recommendations)
- **Medium-term Goals** (next 10-15 acquisitions)
- **Long-term Strategy** (collection development plan)
- **Budget Optimization** (best value acquisitions)

Consider the specified budget range and provide realistic, actionable advice.
"""
        
        return {
            "role": "user", 
            "content": prompt_content.strip()
        }

# Register as MCP prompt
@app.prompt("curate_collection")
def curate_collection_prompt(
    focus_area: str = "gaps",
    budget_range: str = "medium", 
    priority_level: str = "high"
) -> Dict[str, Any]:
    """Generate collection curation and improvement prompt."""
    config = get_config()
    prompt_generator = CollectionCurationPrompt(config)
    
    return prompt_generator.get_curation_prompt(focus_area, budget_range, priority_level)
```

## External Integration Examples

### 1. Last.fm Integration

```python
# src/integrations/lastfm.py
import requests
from typing import Dict, Any, Optional

class LastFmIntegration:
    """Integration with Last.fm API for scrobbling and recommendations."""
    
    def __init__(self, api_key: str, api_secret: str = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "http://ws.audioscrobbler.com/2.0/"
    
    def get_artist_info(self, artist_name: str) -> Optional[Dict[str, Any]]:
        """Get artist information from Last.fm."""
        try:
            params = {
                "method": "artist.getinfo",
                "artist": artist_name,
                "api_key": self.api_key,
                "format": "json"
            }
            
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if "artist" in data:
                artist_data = data["artist"]
                return {
                    "name": artist_data.get("name"),
                    "listeners": int(artist_data.get("stats", {}).get("listeners", 0)),
                    "playcount": int(artist_data.get("stats", {}).get("playcount", 0)),
                    "bio": artist_data.get("bio", {}).get("summary", ""),
                    "tags": [tag["name"] for tag in artist_data.get("tags", {}).get("tag", [])],
                    "similar": [similar["name"] for similar in artist_data.get("similar", {}).get("artist", [])]
                }
            
            return None
            
        except Exception as e:
            print(f"Error fetching Last.fm data for {artist_name}: {e}")
            return None

# Custom tool using Last.fm integration
@app.tool()
def enrich_with_lastfm(
    band_name: str,
    lastfm_api_key: str,
    update_metadata: bool = True
) -> Dict[str, Any]:
    """
    Enrich band metadata with Last.fm information.
    
    Args:
        band_name: Name of the band to enrich
        lastfm_api_key: Last.fm API key
        update_metadata: Whether to update local metadata with Last.fm data
        
    Returns:
        Enrichment result with Last.fm data
    """
    try:
        # Initialize Last.fm integration
        lastfm = LastFmIntegration(lastfm_api_key)
        
        # Get Last.fm data
        lastfm_data = lastfm.get_artist_info(band_name)
        
        if not lastfm_data:
            return {
                "success": False,
                "error": f"No Last.fm data found for '{band_name}'"
            }
        
        result = {
            "success": True,
            "band_name": band_name,
            "lastfm_data": lastfm_data,
            "enrichment_applied": False
        }
        
        # Update local metadata if requested
        if update_metadata:
            # Load existing metadata
            config = get_config()
            existing_metadata = load_band_metadata(config, band_name)
            
            if existing_metadata:
                # Merge Last.fm data
                updated_metadata = merge_lastfm_data(existing_metadata, lastfm_data)
                
                # Save updated metadata
                save_result = save_band_metadata(config, band_name, updated_metadata)
                
                result["enrichment_applied"] = save_result["success"]
                result["save_result"] = save_result
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

### 2. Spotify Integration

```python
# src/integrations/spotify.py
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from typing import Dict, Any, List, Optional

class SpotifyIntegration:
    """Integration with Spotify API for music discovery and playlist creation."""
    
    def __init__(self, client_id: str, client_secret: str):
        client_credentials_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    
    def create_collection_playlist(
        self,
        user_id: str,
        collection_data: Dict[str, Any],
        playlist_type: str = "top_rated"
    ) -> Dict[str, Any]:
        """
        Create Spotify playlist based on collection data.
        
        Args:
            user_id: Spotify user ID
            collection_data: Music collection data
            playlist_type: Type of playlist (top_rated, recent_additions, genre_mix)
            
        Returns:
            Playlist creation result
        """
        try:
            # Generate track list based on playlist type
            if playlist_type == "top_rated":
                tracks = self._get_top_rated_tracks(collection_data)
                playlist_name = "Music Collection - Top Rated"
                description = "Top rated albums from your music collection"
            elif playlist_type == "recent_additions":
                tracks = self._get_recent_additions(collection_data)
                playlist_name = "Music Collection - Recent Additions"
                description = "Recently added albums to your collection"
            else:
                tracks = self._get_genre_mix(collection_data)
                playlist_name = "Music Collection - Genre Mix"
                description = "A mix of genres from your collection"
            
            # Create playlist
            playlist = self.spotify.user_playlist_create(
                user=user_id,
                name=playlist_name,
                description=description,
                public=False
            )
            
            # Add tracks to playlist
            if tracks:
                track_uris = self._find_spotify_tracks(tracks)
                if track_uris:
                    self.spotify.playlist_add_items(playlist["id"], track_uris)
            
            return {
                "success": True,
                "playlist_id": playlist["id"],
                "playlist_url": playlist["external_urls"]["spotify"],
                "tracks_added": len(track_uris) if tracks else 0,
                "playlist_name": playlist_name
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# Custom tool for Spotify integration
@app.tool()
def create_spotify_playlist(
    spotify_client_id: str,
    spotify_client_secret: str,
    spotify_user_id: str,
    playlist_type: str = "top_rated"
) -> Dict[str, Any]:
    """
    Create Spotify playlist from collection data.
    
    Args:
        spotify_client_id: Spotify application client ID
        spotify_client_secret: Spotify application client secret
        spotify_user_id: Spotify user ID
        playlist_type: Type of playlist to create
        
    Returns:
        Playlist creation result
    """
    try:
        # Initialize Spotify integration
        spotify = SpotifyIntegration(spotify_client_id, spotify_client_secret)
        
        # Load collection data
        config = get_config()
        collection_data = load_collection_data(config)
        
        # Create playlist
        result = spotify.create_collection_playlist(
            spotify_user_id,
            collection_data,
            playlist_type
        )
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

## Plugin Architecture Example

### 1. Plugin Base Class

```python
# src/plugins/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class MusicMCPPlugin(ABC):
    """Base class for Music MCP Server plugins."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = self.__class__.__name__
        self.version = "1.0.0"
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the plugin. Return True if successful."""
        pass
    
    @abstractmethod
    def get_tools(self) -> List[Dict[str, Any]]:
        """Return list of tools provided by this plugin."""
        pass
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Return list of resources provided by this plugin."""
        return []
    
    def get_prompts(self) -> List[Dict[str, Any]]:
        """Return list of prompts provided by this plugin."""
        return []
    
    def cleanup(self) -> None:
        """Cleanup plugin resources."""
        pass

class PluginManager:
    """Manager for loading and coordinating plugins."""
    
    def __init__(self):
        self.plugins: List[MusicMCPPlugin] = []
        self.plugin_tools: Dict[str, Any] = {}
    
    def load_plugin(self, plugin_class: type, config: Dict[str, Any]) -> bool:
        """Load and initialize a plugin."""
        try:
            plugin = plugin_class(config)
            
            if plugin.initialize():
                self.plugins.append(plugin)
                
                # Register plugin tools
                for tool in plugin.get_tools():
                    tool_name = f"{plugin.name.lower()}_{tool['name']}"
                    self.plugin_tools[tool_name] = tool
                
                return True
            
            return False
            
        except Exception as e:
            print(f"Error loading plugin {plugin_class.__name__}: {e}")
            return False
    
    def get_all_tools(self) -> Dict[str, Any]:
        """Get all tools from all loaded plugins."""
        return self.plugin_tools
```

### 2. Example Plugin Implementation

```python
# src/plugins/discogs_plugin.py
import requests
from typing import Dict, Any, List

class DiscogsPlugin(MusicMCPPlugin):
    """Plugin for Discogs API integration."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_token = config.get("discogs_api_token")
        self.base_url = "https://api.discogs.com"
    
    def initialize(self) -> bool:
        """Initialize Discogs plugin."""
        if not self.api_token:
            print("Discogs API token not provided")
            return False
        
        # Test API connection
        try:
            response = requests.get(f"{self.base_url}/database/search?q=test&token={self.api_token}")
            return response.status_code == 200
        except:
            return False
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Return Discogs-specific tools."""
        return [
            {
                "name": "search_discogs",
                "description": "Search Discogs database for releases",
                "function": self.search_discogs,
                "parameters": {
                    "query": {"type": "string", "description": "Search query"},
                    "type": {"type": "string", "description": "Search type (artist, release, master)"}
                }
            },
            {
                "name": "get_release_info",
                "description": "Get detailed release information from Discogs",
                "function": self.get_release_info,
                "parameters": {
                    "release_id": {"type": "integer", "description": "Discogs release ID"}
                }
            }
        ]
    
    def search_discogs(self, query: str, type: str = "release") -> Dict[str, Any]:
        """Search Discogs database."""
        try:
            params = {
                "q": query,
                "type": type,
                "token": self.api_token
            }
            
            response = requests.get(f"{self.base_url}/database/search", params=params)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "success": True,
                "results": data.get("results", []),
                "total_results": data.get("pagination", {}).get("items", 0)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_release_info(self, release_id: int) -> Dict[str, Any]:
        """Get detailed release information."""
        try:
            response = requests.get(
                f"{self.base_url}/releases/{release_id}",
                params={"token": self.api_token}
            )
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "success": True,
                "release_info": {
                    "title": data.get("title"),
                    "artists": [artist["name"] for artist in data.get("artists", [])],
                    "year": data.get("year"),
                    "genres": data.get("genres", []),
                    "styles": data.get("styles", []),
                    "tracklist": [
                        {"position": track.get("position"), "title": track.get("title")}
                        for track in data.get("tracklist", [])
                    ],
                    "discogs_url": f"https://www.discogs.com/release/{release_id}"
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
```

## Usage Examples

### 1. Registering Custom Extensions

```python
# In main.py or plugin loader
from src.plugins.discogs_plugin import DiscogsPlugin
from src.plugins.base import PluginManager

# Initialize plugin manager
plugin_manager = PluginManager()

# Load plugins
plugin_manager.load_plugin(DiscogsPlugin, {
    "discogs_api_token": os.getenv("DISCOGS_API_TOKEN")
})

# Register plugin tools with FastMCP
for tool_name, tool_config in plugin_manager.get_all_tools().items():
    @app.tool(name=tool_name)
    def plugin_tool(**kwargs):
        return tool_config["function"](**kwargs)
```

### 2. Configuration for Extensions

```python
# Extended configuration for plugins
class ExtendedConfig(Config):
    """Extended configuration with plugin support."""
    
    # Plugin configurations
    enable_plugins: bool = Field(False, env="ENABLE_PLUGINS")
    
    # External service API keys
    lastfm_api_key: Optional[str] = Field(None, env="LASTFM_API_KEY")
    spotify_client_id: Optional[str] = Field(None, env="SPOTIFY_CLIENT_ID")
    spotify_client_secret: Optional[str] = Field(None, env="SPOTIFY_CLIENT_SECRET")
    discogs_api_token: Optional[str] = Field(None, env="DISCOGS_API_TOKEN")
    
    # Export settings
    default_export_format: str = Field("json", env="DEFAULT_EXPORT_FORMAT")
    export_directory: Optional[str] = Field(None, env="EXPORT_DIRECTORY")
```

These extension examples demonstrate how the Music Collection MCP Server can be extended with additional functionality while maintaining clean separation of concerns and consistent API patterns. The plugin architecture allows for easy addition of new integrations and features without modifying the core server code. 