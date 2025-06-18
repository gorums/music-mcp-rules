#!/usr/bin/env python3
"""
Music Collection MCP Server - Advanced Search Albums Tool

This module contains the advanced_search_albums_tool implementation.
"""

import logging
from typing import Any, Dict, List, Optional

from ..mcp_instance import mcp
from ..base_handlers import BaseToolHandler

# Import required modules and functions
from src.tools.storage import load_collection_index, load_band_metadata

# Configure logging
logger = logging.getLogger(__name__)


class AdvancedSearchAlbumsHandler(BaseToolHandler):
    """Handler for the advanced_search_albums tool."""
    
    def __init__(self):
        super().__init__("advanced_search_albums", "1.0.0")
    
    def _execute_tool(self, **kwargs) -> Dict[str, Any]:
        """Execute the advanced search albums tool logic."""
        # Extract all the search parameters
        album_types = kwargs.get('album_types')
        year_min = kwargs.get('year_min')
        year_max = kwargs.get('year_max')
        decades = kwargs.get('decades')
        editions = kwargs.get('editions')
        genres = kwargs.get('genres')
        bands = kwargs.get('bands')
        has_rating = kwargs.get('has_rating')
        min_rating = kwargs.get('min_rating')
        max_rating = kwargs.get('max_rating')
        is_local = kwargs.get('is_local')
        track_count_min = kwargs.get('track_count_min')
        track_count_max = kwargs.get('track_count_max')
        
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
                raise ValueError(f"Invalid album type: {str(e)}. Valid types are: {[t.value for t in AlbumType]}")
        
        # Validate year ranges
        if year_min is not None:
            if not isinstance(year_min, int) or year_min < 1950 or year_min > 2030:
                raise ValueError("year_min must be an integer between 1950 and 2030")
        if year_max is not None:
            if not isinstance(year_max, int) or year_max < 1950 or year_max > 2030:
                raise ValueError("year_max must be an integer between 1950 and 2030")
        if year_min is not None and year_max is not None and year_min > year_max:
            raise ValueError("year_min cannot be greater than year_max")
        
        # Validate rating ranges
        if min_rating is not None:
            if not isinstance(min_rating, int) or min_rating < 1 or min_rating > 10:
                raise ValueError("min_rating must be an integer between 1 and 10")
        if max_rating is not None:
            if not isinstance(max_rating, int) or max_rating < 1 or max_rating > 10:
                raise ValueError("max_rating must be an integer between 1 and 10")
        if min_rating is not None and max_rating is not None and min_rating > max_rating:
            raise ValueError("min_rating cannot be greater than max_rating")
        
        # Validate track count ranges
        if track_count_min is not None:
            if not isinstance(track_count_min, int) or track_count_min < 0:
                raise ValueError("track_count_min must be a non-negative integer")
        if track_count_max is not None:
            if not isinstance(track_count_max, int) or track_count_max < 0:
                raise ValueError("track_count_max must be a non-negative integer")
        if track_count_min is not None and track_count_max is not None and track_count_min > track_count_max:
            raise ValueError("track_count_min cannot be greater than track_count_max")
        
        # Create search filters
        search_filters = AlbumSearchFilters(
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
        
        # Load collection data
        collection_index = load_collection_index()
        if not collection_index:
            raise ValueError("Collection index not found. Please run scan_music_folders first.")
        
        # Initialize search engine and perform search
        search_engine = AdvancedSearchEngine(collection_index, load_band_metadata)
        search_results = search_engine.search_albums(search_filters)
        
        # Count total matching albums
        total_matching_albums = sum(len(albums) for albums in search_results.results.values())
        
        # Build comprehensive response
        return {
            'status': 'success',
            'message': f"Found {total_matching_albums} albums across {search_results.total_matching_bands} bands",
            'results': search_results.results,
            'filters_applied': search_results.filters_applied,
            'total_matching_albums': total_matching_albums,
            'total_matching_bands': search_results.total_matching_bands,
            'search_statistics': search_results.search_statistics,
            'tool_info': self._create_tool_info(
                parameters_used={k: v for k, v in kwargs.items() if v is not None}
            )
        }


# Create handler instance
_handler = AdvancedSearchAlbumsHandler()

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
    return _handler.execute(
        album_types=album_types,
        year_min=year_min,
        year_max=year_max,
        decades=decades,
        editions=editions,
        genres=genres,
        bands=bands,
        has_rating=has_rating,
        min_rating=min_rating,
        max_rating=max_rating,
        is_local=is_local,
        track_count_min=track_count_min,
        track_count_max=track_count_max
    ) 