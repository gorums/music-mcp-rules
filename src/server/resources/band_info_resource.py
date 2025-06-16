#!/usr/bin/env python3
"""
Music Collection MCP Server - Band Info Resource

This module contains the band_info_resource implementation.
"""

import logging
from typing import Any, Dict, List, Optional

from ..core import mcp

# Import resource implementation - using absolute imports
from src.resources.band_info import get_band_info_markdown

# Configure logging
logger = logging.getLogger(__name__)

@mcp.resource("band://info/{band_name}")
def band_info_resource(band_name: str) -> str:
    """
    Get detailed band information in markdown format.
    
    This resource provides comprehensive band information including:
    - Basic band metadata (formed, genre, origin, members, description)
    - Complete album listing organized by type (Album, EP, Live, Demo, etc.)
    - Missing albums section with acquisition recommendations
    - Analysis section with reviews and ratings (band and album-level)
    - Similar bands information with collection presence indicators
    - Collection statistics and completion percentage
    - Folder structure analysis and compliance information
    
    Args:
        band_name: Name of the band to retrieve information for (extracted from URI)
        
    Returns:
        Markdown-formatted comprehensive band information with:
        - Header with band name and completion badge
        - Band overview section with key details
        - Albums organized by type with icons and status indicators
        - Missing albums section with recommendations
        - Analysis and ratings section
        - Similar bands with collection links
        - Collection statistics and metadata information
        
    URI Format:
        band://info/{band_name}
        
    Examples:
        - band://info/Pink Floyd
        - band://info/The Beatles
        - band://info/Iron Maiden
    """
    try:
        return get_band_info_markdown(band_name)
    except Exception as e:
        logger.error(f"Error in band_info resource for '{band_name}': {str(e)}")
        return f"# Error Retrieving Band Information\n\n**Band:** {band_name}\n\n**Error:** {str(e)}\n\nPlease check that the band name is correct and that the band has been scanned into your collection." 