#!/usr/bin/env python3
"""
Music Collection MCP Server - Fetch Band Info Prompt

This module contains the fetch_band_info_prompt implementation.
"""

from typing import Any, Dict, List

from ..mcp_instance import mcp
from ..base_handlers import BasePromptHandler

# Import prompt implementation - using absolute imports
from src.core.prompts.fetch_band_info import get_fetch_band_info_prompt


class FetchBandInfoPromptHandler(BasePromptHandler):
    """Handler for the fetch_band_info prompt."""
    
    def __init__(self):
        super().__init__("fetch_band_info", "1.0.0")
    
    def _generate_prompt(self, **kwargs) -> Dict[str, Any]:
        """Generate the fetch band info prompt template."""
        band_name = kwargs.get('band_name')
        existing_albums = kwargs.get('existing_albums')
        information_scope = kwargs.get('information_scope', 'full')
        
        # Validate required parameters
        if not band_name:
            raise ValueError("band_name is required")
        
        return get_fetch_band_info_prompt(band_name, existing_albums, information_scope)


# Create handler instance
_handler = FetchBandInfoPromptHandler()

@mcp.prompt()
def fetch_band_info_prompt(
    band_name: str, 
    existing_albums: List[str] = None, 
    information_scope: str = "full"
) -> Dict[str, Any]:
    """
    Prompt template for fetching band information using external sources.
    
    This prompt guides the collection of comprehensive band information from external sources
    such as Wikipedia, AllMusic, and official band websites. It supports different information
    scopes and integrates with existing album data to identify missing albums.
    
    Args:
        band_name: Name of the band to fetch information for
        existing_albums: List of albums already in the collection (optional)
        information_scope: Scope of information to fetch - "basic", "full", or "albums_only"
    
    Returns:
        Prompt template dictionary with:
        - name: Prompt identifier
        - description: Prompt description
        - messages: List of prompt messages with instructions
        - arguments: Prompt arguments schema
        
    Information Scopes:
        - "basic": Essential band information (formed, genre, origin, key members)
        - "full": Complete band information including detailed discography
        - "albums_only": Focus on discovering missing albums from discography
        
    Output Format:
        The prompt generates instructions for collecting band information in JSON format
        compatible with the enhanced metadata schema, including album type detection
        and missing album identification.
    """
    return _handler.generate(
        band_name=band_name,
        existing_albums=existing_albums,
        information_scope=information_scope
    ) 