# Extension Examples for Music Collection MCP Server

## Overview

The Music Collection MCP Server is designed with extensibility in mind. This document provides practical examples of how to extend the server with custom tools, resources, prompts, and integrations.

## Custom Tool Examples

### 1. Export Tool - CSV/JSON Export

Create a custom tool to export collection data in various formats:

```python
# src/tools/export.py
import csv
import json
from pathlib import Path
from typing import Dict, Any, List, Literal
from datetime import datetime

from ..models.collection import CollectionIndex
from ..models.band import BandMetadata
from ..config import Config

class CollectionExporter:
    """Export collection data to various formats."""
    
    def __init__(self, config: Config):
        self.config = config
    
    def export_collection(
        self,
        format: Literal["csv", "json", "xml"],
        include_analysis: bool = True,
        output_path: str = None
    ) -> Dict[str, Any]:
        """
        Export complete collection data.
        
        Args:
            format: Export format (csv, json, xml)
            include_analysis: Include analysis data in export
            output_path: Custom output path (optional)
            
        Returns:
            Export result with file path and statistics
        """
        try:
            # Load collection data
            collection_index = self._load_collection_index()
            
            # Generate export data
            export_data = self._prepare_export_data(collection_index, include_analysis)
            
            # Determine output path
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"collection_export_{timestamp}.{format}"
            
            # Export based on format
            if format == "csv":
                self._export_csv(export_data, output_path)
            elif format == "json":
                self._export_json(export_data, output_path)
            elif format == "xml":
                self._export_xml(export_data, output_path)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            return {
                "success": True,
                "message": f"Collection exported to {format.upper()}",
                "output_file": output_path,
                "records_exported": len(export_data),
                "format": format,
                "include_analysis": include_analysis
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "format": format
            }
    
    def _export_csv(self, data: List[Dict[str, Any]], output_path: str) -> None:
        """Export data to CSV format."""
        if not data:
            return
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in data:
                # Flatten complex fields for CSV
                flattened_row = self._flatten_dict(row)
                writer.writerow(flattened_row)
    
    def _export_json(self, data: List[Dict[str, Any]], output_path: str) -> None:
        """Export data to JSON format."""
        with open(output_path, 'w', encoding='utf-8') as jsonfile:
            json.dump({
                "export_metadata": {
                    "export_date": datetime.now().isoformat(),
                    "format": "json",
                    "record_count": len(data)
                },
                "bands": data
            }, jsonfile, indent=2, ensure_ascii=False)
    
    def _flatten_dict(self, d: Dict[str, Any], prefix: str = "") -> Dict[str, str]:
        """Flatten nested dictionaries for CSV export."""
        result = {}
        for key, value in d.items():
            new_key = f"{prefix}_{key}" if prefix else key
            
            if isinstance(value, dict):
                result.update(self._flatten_dict(value, new_key))
            elif isinstance(value, list):
                result[new_key] = "; ".join(str(item) for item in value)
            else:
                result[new_key] = str(value) if value is not None else ""
        
        return result

# Register as MCP tool
@app.tool()
def export_collection(
    format: Literal["csv", "json", "xml"] = "json",
    include_analysis: bool = True,
    output_path: str = None
) -> Dict[str, Any]:
    """
    Export music collection data to various formats.
    
    Args:
        format: Export format (csv, json, xml)
        include_analysis: Include analysis data in export
        output_path: Custom output path for export file
        
    Returns:
        Export operation result
    """
    config = get_config()
    exporter = CollectionExporter(config)
    
    return exporter.export_collection(format, include_analysis, output_path)
```

### 2. Statistics Tool - Advanced Analytics

```python
# src/tools/statistics.py
from typing import Dict, Any, List
from collections import defaultdict
import statistics
from datetime import datetime, timedelta

class CollectionStatistics:
    """Generate advanced statistics for music collection."""
    
    def __init__(self, config: Config):
        self.config = config
    
    def generate_comprehensive_stats(self) -> Dict[str, Any]:
        """Generate comprehensive collection statistics."""
        collection_index = self._load_collection_index()
        
        stats = {
            "overview": self._calculate_overview_stats(collection_index),
            "distribution": self._calculate_distribution_stats(collection_index),
            "ratings": self._calculate_rating_stats(collection_index),
            "genres": self._calculate_genre_stats(collection_index),
            "completion": self._calculate_completion_stats(collection_index),
            "trends": self._calculate_trend_stats(collection_index)
        }
        
        return {
            "success": True,
            "statistics": stats,
            "generated_at": datetime.now().isoformat()
        }
    
    def _calculate_distribution_stats(self, collection_index) -> Dict[str, Any]:
        """Calculate album distribution statistics."""
        album_counts = [band.albums_count for band in collection_index.bands]
        
        if not album_counts:
            return {"error": "No album data available"}
        
        return {
            "mean_albums_per_band": statistics.mean(album_counts),
            "median_albums_per_band": statistics.median(album_counts),
            "mode_albums_per_band": statistics.mode(album_counts),
            "std_dev": statistics.stdev(album_counts) if len(album_counts) > 1 else 0,
            "quartiles": {
                "q1": sorted(album_counts)[len(album_counts) // 4],
                "q2": statistics.median(album_counts),
                "q3": sorted(album_counts)[3 * len(album_counts) // 4]
            },
            "distribution": {
                "small_collections": len([c for c in album_counts if c <= 3]),
                "medium_collections": len([c for c in album_counts if 4 <= c <= 9]),
                "large_collections": len([c for c in album_counts if c >= 10])
            }
        }

# Register as MCP tool
@app.tool()
def get_collection_statistics() -> Dict[str, Any]:
    """Generate comprehensive collection statistics and analytics."""
    config = get_config()
    stats_calculator = CollectionStatistics(config)
    
    return stats_calculator.generate_comprehensive_stats()
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