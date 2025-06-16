#!/usr/bin/env python3
"""
Music Collection MCP Server - Collection Insights Prompt

This module contains the collection_insights_prompt implementation.
"""

import logging
from typing import Any, Dict

from ..core import mcp

# Import prompt implementation - using absolute imports
from src.prompts.collection_insights import get_collection_insights_prompt

# Configure logging
logger = logging.getLogger(__name__)

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