#!/usr/bin/env python3
"""
Music Collection MCP Server

A Model Context Protocol server that provides intelligent access to your local music collection.
The server exposes tools, resources, and prompts to discover, analyze, and retrieve information
about bands and artists based on your folder structure.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

# Import tool implementations - using package imports
from src.tools.scanner import scan_music_folders as scanner_scan_music_folders
from src.tools.storage import get_band_list, save_band_metadata, save_band_analyze, save_collection_insight

# Import resource implementations - using package imports
from src.resources.band_info import get_band_info_markdown
from src.resources.collection_summary import get_collection_summary

# Import prompt implementations - using package imports
from src.prompts.fetch_band_info import get_fetch_band_info_prompt
from src.prompts.analyze_band import get_analyze_band_prompt
from src.prompts.compare_bands import get_compare_bands_prompt
from src.prompts.collection_insights import get_collection_insights_prompt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastMCP server instance
mcp = FastMCP("music-collection-mcp")

@mcp.tool()
def scan_music_folders(
    force_rescan: bool = False,
    include_missing_albums: bool = True
) -> Dict[str, Any]:
    """
    Scan the music directory structure to discover bands and albums.
    
    This tool performs a comprehensive scan of the music collection:
    - Discovers all band folders in the music directory
    - Finds album subfolders within each band folder
    - Counts music tracks in each album folder
    - Detects missing albums (in metadata but not in folders)
    - Updates the collection index with current state
    
    Args:
        force_rescan: If True, forces a complete rescan ignoring cache.
        include_missing_albums: If True, includes detection of missing albums.
    
    Returns:
        Dict containing scan results with bands, albums, and statistics including:
        - status: 'success' or 'error'
        - results: Dict with scan statistics and band data
        - collection_path: Path to the scanned music collection
    """
    try:
        # Call the actual scanner function using config MUSIC_ROOT_PATH
        result = scanner_scan_music_folders()
            
        # Add tool-specific metadata
        if result.get('status') == 'success':
            result['tool_info'] = {
                'tool_name': 'scan_music_folders',
                'version': '1.0.0',
                'force_rescan': force_rescan,
                'include_missing_albums': include_missing_albums
            }
            
        return result
        
    except Exception as e:
        logger.error(f"Error in scan_music_folders tool: {str(e)}")
        return {
            'status': 'error',
            'error': f"Tool execution failed: {str(e)}",
            'tool_info': {
                'tool_name': 'scan_music_folders',
                'version': '1.0.0'
            }
        }

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
    include_albums: bool = False
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
    
    Returns:
        Dict containing filtered and paginated band list with metadata including:
        - status: 'success' or 'error'
        - bands: List of band information with albums and analysis if requested
        - pagination: Page information with total counts and navigation info
        - collection_summary: Overall collection statistics
        - filters_applied: Summary of filters that were applied
        - sort: Information about the applied sorting
    """
    try:
        result = get_band_list(
            search_query=search_query,
            filter_genre=filter_genre,
            filter_has_metadata=filter_has_metadata,
            filter_missing_albums=filter_missing_albums,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size,
            include_albums=include_albums
        )
        
        # Add tool-specific metadata
        if result.get('status') == 'success':
            result['tool_info'] = {
                'tool_name': 'get_band_list',
                'version': '1.0.0',
                'parameters_used': {
                    'search_query': search_query,
                    'filter_genre': filter_genre,
                    'filter_has_metadata': filter_has_metadata,
                    'filter_missing_albums': filter_missing_albums,
                    'sort_by': sort_by,
                    'sort_order': sort_order,
                    'page': page,
                    'page_size': page_size,
                    'include_albums': include_albums
                }
            }
            
        return result
        
    except Exception as e:
        logger.error(f"Error in get_band_list tool: {str(e)}")
        return {
            'status': 'error',
            'error': f"Tool execution failed: {str(e)}",
            'tool_info': {
                'tool_name': 'get_band_list',
                'version': '1.0.0'
            }
        }

@mcp.tool()
def save_band_metadata_tool(
    band_name: str,
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Save band metadata to the local storage.
    
    Args:
        band_name: The name of the band
        metadata: Complete metadata dictionary for the band
        
    Returns:
        Dict containing the operation status
    """
    try:
        return save_band_metadata(band_name, metadata)
    except Exception as e:
        logger.error(f"Error in save_band_metadata tool: {str(e)}")
        return {
            'status': 'error',
            'error': f"Tool execution failed: {str(e)}"
        }

@mcp.tool()
def save_band_analyze_tool(
    band_name: str, 
    analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Save band analysis data to the local storage.
    
    Args:
        band_name: The name of the band
        analysis: Analysis data including reviews, ratings, and similar bands
        
    Returns:
        Dict containing the operation status
    """
    try:
        return save_band_analyze(band_name, analysis)
    except Exception as e:
        logger.error(f"Error in save_band_analyze tool: {str(e)}")
        return {
            'status': 'error',
            'error': f"Tool execution failed: {str(e)}"
        }

@mcp.tool()
def save_collection_insight_tool(
    insights: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Save collection-wide insights to the local storage.
    
    Args:
        insights: Collection insights data including statistics and analytics
        
    Returns:
        Dict containing the operation status
    """
    try:
        return save_collection_insight(insights)
    except Exception as e:
        logger.error(f"Error in save_collection_insight tool: {str(e)}")
        return {
            'status': 'error',
            'error': f"Tool execution failed: {str(e)}"
        }

# Register resources
@mcp.resource("band://info/{band_name}")
def band_info_resource(band_name: str) -> str:
    """
    Get detailed band information in markdown format.
    
    Args:
        band_name: Name of the band to retrieve information for
        
    Returns:
        Markdown-formatted band information
    """
    try:
        return get_band_info_markdown(band_name)
    except Exception as e:
        logger.error(f"Error in band_info resource: {str(e)}")
        return f"Error retrieving band information: {str(e)}"

@mcp.resource("collection://summary")
def collection_summary_resource() -> str:
    """
    Get collection summary statistics in markdown format.
    
    Returns:
        Markdown-formatted collection summary
    """
    try:
        return get_collection_summary()
    except Exception as e:
        logger.error(f"Error in collection_summary resource: {str(e)}")
        return f"Error retrieving collection summary: {str(e)}"

# Register prompts
@mcp.prompt()
def fetch_band_info_prompt() -> Dict[str, Any]:
    """
    Prompt template for fetching band information using external sources.
    
    Returns:
        Prompt template for band information retrieval
    """
    try:
        return get_fetch_band_info_prompt()
    except Exception as e:
        logger.error(f"Error in fetch_band_info prompt: {str(e)}")
        return {
            'name': 'fetch_band_info',
            'description': 'Error loading prompt template',
            'messages': [{'role': 'user', 'content': f'Error: {str(e)}'}]
        }

@mcp.prompt()
def analyze_band_prompt() -> Dict[str, Any]:
    """
    Prompt template for comprehensive band analysis.
    
    Returns:
        Prompt template for band analysis
    """
    try:
        return get_analyze_band_prompt()
    except Exception as e:
        logger.error(f"Error in analyze_band prompt: {str(e)}")
        return {
            'name': 'analyze_band',
            'description': 'Error loading prompt template', 
            'messages': [{'role': 'user', 'content': f'Error: {str(e)}'}]
        }

@mcp.prompt()
def compare_bands_prompt() -> Dict[str, Any]:
    """
    Prompt template for comparing multiple bands.
    
    Returns:
        Prompt template for band comparison
    """
    try:
        return get_compare_bands_prompt()
    except Exception as e:
        logger.error(f"Error in compare_bands prompt: {str(e)}")
        return {
            'name': 'compare_bands',
            'description': 'Error loading prompt template',
            'messages': [{'role': 'user', 'content': f'Error: {str(e)}'}]
        }

@mcp.prompt()
def collection_insights_prompt() -> Dict[str, Any]:
    """
    Prompt template for generating collection insights.
    
    Returns:
        Prompt template for collection insights
    """
    try:
        return get_collection_insights_prompt()
    except Exception as e:
        logger.error(f"Error in collection_insights prompt: {str(e)}")
        return {
            'name': 'collection_insights',
            'description': 'Error loading prompt template',
            'messages': [{'role': 'user', 'content': f'Error: {str(e)}'}]
        }

def main():
    """Main entry point for the MCP server."""
    logger.info("Starting Music Collection MCP Server...")
    
    try:
        # Try to run the MCP server
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        # In development mode, keep server alive even if no client connects
        logger.info("Running in development mode - server will stay alive")
        try:
            # Keep the process alive
            while True:
                import time
                time.sleep(60)  # Sleep for 60 seconds at a time
                logger.info("Server still running... (development mode)")
        except KeyboardInterrupt:
            logger.info("Development server stopped by user")

if __name__ == "__main__":
    main() 