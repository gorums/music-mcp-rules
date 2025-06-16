#!/usr/bin/env python3
"""
Music Collection MCP Server - Fetch Band Info Prompt

This module contains the fetch_band_info_prompt implementation.
"""

import logging
from typing import Any, Dict, List, Optional

from ..core import mcp

# Import prompt implementation - using absolute imports
from src.prompts.fetch_band_info import get_fetch_band_info_prompt

# Configure logging
logger = logging.getLogger(__name__)

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
    try:
        return get_fetch_band_info_prompt(band_name, existing_albums, information_scope)
    except Exception as e:
        logger.error(f"Error in fetch_band_info prompt: {str(e)}")
        return {
            'name': 'fetch_band_info',
            'description': 'Error loading prompt template',
            'messages': [{'role': 'user', 'content': f'Error: {str(e)}'}],
            'arguments': []
        } 