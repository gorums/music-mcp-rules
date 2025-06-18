#!/usr/bin/env python3
"""
Music Collection MCP Server - Get Band List Tool

This module contains the get_band_list_tool implementation.
"""

import logging
from typing import Any, Dict, List, Optional

from ..mcp_instance import mcp
from ..base_handlers import BaseToolHandler, validate_pagination_params, validate_sort_params

# Import tool implementation - using absolute imports
from src.tools.storage import get_band_list

# Configure logging
logger = logging.getLogger(__name__)


class GetBandListHandler(BaseToolHandler):
    """Handler for the get_band_list tool."""
    
    def __init__(self):
        super().__init__("get_band_list", "1.1.0")
    
    def _execute_tool(self, **kwargs) -> Dict[str, Any]:
        """Execute the get band list tool logic."""
        # Extract parameters with defaults
        search_query = kwargs.get('search_query')
        filter_genre = kwargs.get('filter_genre')
        filter_has_metadata = kwargs.get('filter_has_metadata')
        filter_missing_albums = kwargs.get('filter_missing_albums')
        sort_by = kwargs.get('sort_by', 'name')
        sort_order = kwargs.get('sort_order', 'asc')
        page = kwargs.get('page', 1)
        page_size = kwargs.get('page_size', 50)
        include_albums = kwargs.get('include_albums', False)
        album_details_filter = kwargs.get('album_details_filter')
        
        # Validate pagination parameters
        pagination_error = validate_pagination_params(page, page_size)
        if pagination_error:
            raise ValueError(pagination_error)
        
        # Validate sort parameters
        allowed_sort_fields = ['name', 'albums_count', 'last_updated', 'completion']
        sort_error = validate_sort_params(sort_by, sort_order, allowed_sort_fields)
        if sort_error:
            raise ValueError(sort_error)
        
        # Call the storage function
        result = get_band_list(
            search_query=search_query,
            filter_genre=filter_genre,
            filter_has_metadata=filter_has_metadata,
            filter_missing_albums=filter_missing_albums,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size,
            include_albums=include_albums,
            album_details_filter=album_details_filter
        )
        
        # Add tool-specific metadata
        if result.get('status') == 'success':
            result['tool_info'] = self._create_tool_info(
                parameters_used={
                    'search_query': search_query,
                    'filter_genre': filter_genre,
                    'filter_has_metadata': filter_has_metadata,
                    'filter_missing_albums': filter_missing_albums,
                    'sort_by': sort_by,
                    'sort_order': sort_order,
                    'page': page,
                    'page_size': page_size,
                    'include_albums': include_albums,
                    'album_details_filter': album_details_filter
                }
            )
            result['album_details_filter'] = album_details_filter
        
        return result


# Create handler instance
_handler = GetBandListHandler()

@mcp.tool()
def get_band_list_tool(
    search_query: Optional[str] = None,
    filter_genre: Optional[str] = None,
    filter_has_metadata: Optional[bool] = None,
    filter_missing_albums: Optional[bool] = None,
    sort_by: str = "name",
    sort_order: str = "asc", 
    page: int = 1,
    page_size: int = 50,
    include_albums: bool = False,
    album_details_filter: Optional[str] = None  # 'local', 'missing', or None
) -> Dict[str, Any]:
    """
    Get a list of all discovered bands with enhanced filtering, sorting, and pagination.
    
    This tool provides comprehensive band listing functionality:
    - Search bands by name or album names
    - Filter by genre, metadata availability, or missing albums
    - Sort by name, album count, last update, or completion percentage
    - Paginate results for large collections
    - Include detailed album information and analysis data
    - Show cached metadata status and last updated info
    - Filter album details to show only local or only missing albums
    
    Args:
        search_query: Search term to filter bands by name or album name
        filter_genre: Filter bands by genre (requires metadata to be available)
        filter_has_metadata: If True, show only bands with metadata; if False, only without
        filter_missing_albums: If True, show only bands with missing albums; if False, only complete bands
        sort_by: Field to sort by - 'name', 'albums_count', 'last_updated', or 'completion'
        sort_order: Sort order - 'asc' for ascending or 'desc' for descending
        page: Page number for pagination (starts at 1)
        page_size: Number of results per page (1-100)
        include_albums: If True, include detailed album information for each band
        album_details_filter: If 'local', only include local albums in album details; if 'missing', only missing albums; None for all
    
    Returns:
        Dict containing filtered and paginated band list with metadata including:
        - status: 'success' or 'error'
        - bands: List of band information with albums and analysis if requested
        - pagination: Page information with total counts and navigation info
        - collection_summary: Overall collection statistics
        - filters_applied: Summary of filters that were applied
        - sort: Information about the applied sorting
        - album_details_filter: Album details filter applied
    """
    return _handler.execute(
        search_query=search_query,
        filter_genre=filter_genre,
        filter_has_metadata=filter_has_metadata,
        filter_missing_albums=filter_missing_albums,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
        include_albums=include_albums,
        album_details_filter=album_details_filter
    ) 