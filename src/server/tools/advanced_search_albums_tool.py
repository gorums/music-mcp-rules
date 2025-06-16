#!/usr/bin/env python3
"""
Music Collection MCP Server - Advanced Search Albums Tool

This module contains the advanced_search_albums_tool implementation.
"""

import logging
from typing import Any, Dict, List, Optional

from ..core import mcp

# Import required modules and functions
from src.tools.storage import load_collection_index, load_band_metadata

# Configure logging
logger = logging.getLogger(__name__)

@mcp.tool()
def advanced_search_albums_tool(
    album_types: Optional[str] = None,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    decades: Optional[str] = None,
    editions: Optional[str] = None,
    genres: Optional[str] = None,
    bands: Optional[str] = None,
    has_rating: Optional[bool] = None,
    min_rating: Optional[int] = None,
    max_rating: Optional[int] = None,
    is_local: Optional[bool] = None,
    track_count_min: Optional[int] = None,
    track_count_max: Optional[int] = None
) -> Dict[str, Any]:
    """
    Perform advanced search across all albums with comprehensive filtering options.
    
    This tool provides powerful search capabilities across your entire music collection.
    You can combine multiple filters to find exactly what you're looking for.
    All parameters are optional - omit any you don't need.
    
    PARAMETER DETAILS WITH EXAMPLES:
    
    album_types (str, optional):
        Valid values: "Album", "EP", "Live", "Demo", "Compilation", "Instrumental", "Split", "Single"
        Use comma-separated values for multiple types
        Examples:
        - "EP" - Find only EPs
        - "Live,Demo" - Find Live albums and Demo recordings
        - "Album,Compilation" - Find standard albums and compilations
        
    year_min/year_max (int, optional):
        Range: 1950-2030
        Examples:
        - year_min=1980 - Albums from 1980 onwards
        - year_max=1990 - Albums up to 1990
        - year_min=1975, year_max=1985 - Albums from 1975-1985
        
    decades (str, optional):
        Valid formats: "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"
        Use comma-separated values for multiple decades
        Examples:
        - "1980s" - All albums from the 1980s
        - "1970s,1980s" - Albums from 70s and 80s
        
    editions (str, optional):
        Common values: "Deluxe Edition", "Limited Edition", "Remastered", "Anniversary Edition", "Special Edition"
        Use comma-separated values for multiple editions
        Examples:
        - "Deluxe Edition" - Only Deluxe editions
        - "Limited Edition,Special Edition" - Limited or Special editions
        - "Remastered" - Remastered albums
        
    genres (str, optional):
        Use exact genre names from your collection
        Use comma-separated values for multiple genres
        Examples:
        - "Heavy Metal" - Only Heavy Metal bands
        - "Rock,Hard Rock" - Rock and Hard Rock bands
        - "Thrash Metal,Death Metal" - Metal subgenres
        
    bands (str, optional):
        Use exact band names from your collection
        Use comma-separated values for multiple bands
        Examples:
        - "Metallica" - Only Metallica albums
        - "Iron Maiden,Judas Priest" - Albums from both bands
        - "Pink Floyd,Led Zeppelin,The Beatles" - Classic rock bands
        
    has_rating (bool, optional):
        Examples:
        - has_rating=true - Only albums that have been rated
        - has_rating=false - Only albums without ratings
        - Omit to include both rated and unrated albums
        
    min_rating/max_rating (int, optional):
        Range: 1-10
        Examples:
        - min_rating=8 - Albums rated 8 or higher
        - max_rating=6 - Albums rated 6 or lower
        - min_rating=7, max_rating=9 - Albums rated 7, 8, or 9
        
    is_local (bool, optional):
        Examples:
        - is_local=true - Only albums you have locally
        - is_local=false - Only missing albums (in metadata but not found)
        - Omit to include both local and missing albums
        
    track_count_min/track_count_max (int, optional):
        Examples:
        - track_count_min=10 - Albums with 10+ tracks
        - track_count_max=6 - Albums with 6 or fewer tracks (EPs/Singles)
        - track_count_min=8, track_count_max=12 - Albums with 8-12 tracks
    
    USAGE EXAMPLES:
    
    1. Find all EPs from the 1980s:
       album_types="EP", decades="1980s"
       
    2. Find highly rated live albums:
       album_types="Live", min_rating=8
       
    3. Find missing deluxe editions:
       editions="Deluxe Edition", is_local=false
       
    4. Find short albums (likely EPs) by specific bands:
       bands="Metallica,Iron Maiden", track_count_max=7
       
    5. Find unrated albums from the 90s to review:
       decades="1990s", has_rating=false
       
    6. Find all demo recordings:
       album_types="Demo"
       
    7. Complex search - Metal EPs from 80s with good ratings:
       album_types="EP", decades="1980s", genres="Heavy Metal,Thrash Metal", min_rating=7
     
     EXACT JSON EXAMPLE FOR MCP CLIENT:
     To find all EPs and Live albums from the 1980s with ratings of 7 or higher, send:
     {
       "album_types": "EP,Live",
       "decades": "1980s",
       "min_rating": 7
     }
     
     To find missing Deluxe editions by Metallica:
     {
       "bands": "Metallica",
       "editions": "Deluxe Edition",
       "is_local": false
     }
     
     To find all demo recordings:
     {
       "album_types": "Demo"
     }
     
     To find albums from 1975-1985 with 8+ tracks:
     {
       "year_min": 1975,
       "year_max": 1985,
       "track_count_min": 8
     }
     
     Returns:
        Dict containing search results:
        - status: 'success' or 'error'
        - results: Dict mapping band names to matching albums (empty dict if no matches)
        - filters_applied: Summary of filters used in the search
        - total_matching_albums: Total number of albums found across all bands
        - total_matching_bands: Number of bands that had matching albums
        - search_statistics: Detailed statistics about search performance and results
        - tool_info: Metadata about the tool execution
    """
    try:
        from src.models.analytics import AdvancedSearchEngine, AlbumSearchFilters
        from src.models.band import AlbumType
        
        # Parse comma-separated strings into lists
        def parse_comma_separated(value: Optional[str]) -> Optional[List[str]]:
            if not value:
                return None
            return [item.strip() for item in value.split(',') if item.strip()]
        
        # Convert comma-separated strings to lists
        album_types_list = parse_comma_separated(album_types)
        decades_list = parse_comma_separated(decades)
        editions_list = parse_comma_separated(editions)
        genres_list = parse_comma_separated(genres)
        bands_list = parse_comma_separated(bands)
        
        # Convert string album types to AlbumType enums
        album_type_enums = None
        if album_types_list:
            try:
                album_type_enums = [AlbumType(album_type) for album_type in album_types_list]
            except ValueError as e:
                return {
                    'status': 'error',
                    'error': f"Invalid album type: {str(e)}. Valid types are: {[t.value for t in AlbumType]}"
                }
        
        # Create search filters
        filters = AlbumSearchFilters(
            album_types=album_type_enums,
            year_min=year_min,
            year_max=year_max,
            decades=decades_list,
            editions=editions_list,
            genres=genres_list,
            bands=bands_list,
            has_rating=has_rating,
            min_rating=min_rating,
            max_rating=max_rating,
            is_local=is_local,
            track_count_min=track_count_min,
            track_count_max=track_count_max
        )
        
        # Load all band metadata for searching
        collection_index = load_collection_index()
        band_metadata = {}
        
        for band_entry in collection_index.bands:
            try:
                metadata = load_band_metadata(band_entry.name)
                if metadata:
                    band_metadata[band_entry.name] = metadata
            except Exception as e:
                logger.warning(f"Could not load metadata for band {band_entry.name}: {str(e)}")
        
        # Perform search
        search_results = AdvancedSearchEngine.search_albums(band_metadata, filters)
        
        # Calculate statistics
        total_matching_albums = sum(len(albums) for albums in search_results.values())
        total_matching_bands = len(search_results)
        
        # Generate search statistics
        search_statistics = {
            'total_albums_searched': sum(
                len(metadata.albums) + len(metadata.albums_missing) 
                for metadata in band_metadata.values()
            ),
            'total_bands_searched': len(band_metadata),
            'match_rate': round((total_matching_albums / max(sum(len(metadata.albums) + len(metadata.albums_missing) for metadata in band_metadata.values()), 1)) * 100, 2),
            'bands_with_matches': total_matching_bands,
            'albums_per_band': round(total_matching_albums / max(total_matching_bands, 1), 2) if total_matching_bands > 0 else 0
        }
        
        # Summarize filters applied
        filters_applied = {}
        if album_types:
            filters_applied['album_types'] = album_types
        if year_min or year_max:
            filters_applied['year_range'] = f"{year_min or 'any'} - {year_max or 'any'}"
        if decades:
            filters_applied['decades'] = decades
        if editions:
            filters_applied['editions'] = editions
        if genres:
            filters_applied['genres'] = genres
        if bands:
            filters_applied['bands'] = bands
        if has_rating is not None:
            filters_applied['has_rating'] = has_rating
        if min_rating or max_rating:
            filters_applied['rating_range'] = f"{min_rating or 1} - {max_rating or 10}"
        if is_local is not None:
            filters_applied['album_status'] = 'local' if is_local else 'missing'
        if track_count_min or track_count_max:
            filters_applied['track_count_range'] = f"{track_count_min or 'any'} - {track_count_max or 'any'}"
        
        # Convert results to serializable format
        serializable_results = {}
        for band_name, albums in search_results.items():
            serializable_results[band_name] = [album.model_dump() for album in albums]
        
        return {
            'status': 'success',
            'results': serializable_results,
            'filters_applied': filters_applied,
            'total_matching_albums': total_matching_albums,
            'total_matching_bands': total_matching_bands,
            'search_statistics': search_statistics,
            'tool_info': {
                'tool_name': 'advanced_search_albums',
                'version': '1.0.0',
                'search_timestamp': load_collection_index().last_scan
            }
        }
        
    except Exception as e:
        logger.error(f"Error in advanced_search_albums tool: {str(e)}")
        return {
            'status': 'error',
            'error': f"Advanced search failed: {str(e)}",
            'tool_info': {
                'tool_name': 'advanced_search_albums',
                'version': '1.0.0'
            }
        } 