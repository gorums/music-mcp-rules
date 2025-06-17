#!/usr/bin/env python3
"""
Music Collection MCP Server - Band Info Resource

This module contains the band_info_resource implementation.
"""

import logging
from typing import Any, Dict, List, Optional

from ..core import mcp
from ..base_handlers import BaseResourceHandler

# Import resource implementation - using absolute imports
from src.resources.band_info import get_band_info_markdown

# Configure logging
logger = logging.getLogger(__name__)


class BandInfoResourceHandler(BaseResourceHandler):
    """Handler for the band_info resource."""
    
    def __init__(self):
        super().__init__("band_info", "1.0.0")
    
    def _get_resource_content(self, **kwargs) -> str:
        """Get band information in markdown format."""
        band_name = kwargs.get('band_name')
        if not band_name:
            raise ValueError("Band name is required")
        
        return get_band_info_markdown(band_name)
    
    def _format_error_content(self, error_message: str, **kwargs) -> str:
        """Format error message for band info resource."""
        band_name = kwargs.get('band_name', 'Unknown')
        return f"""# Error Retrieving Band Information

**Band:** {band_name}
**Error:** {error_message}

Please check that the band name is correct and that the band has been scanned into your collection.

**Suggestions:**
- Run the `scan_music_folders` tool to discover new bands
- Check the spelling of the band name
- Use the `get_band_list` tool to see available bands

**Timestamp:** {self._get_timestamp()}
"""


# Create handler instance
_handler = BandInfoResourceHandler()

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
    return _handler.get_content(band_name=band_name) 