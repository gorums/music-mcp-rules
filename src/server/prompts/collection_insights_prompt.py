#!/usr/bin/env python3
"""
Music Collection MCP Server - Collection Insights Prompt

This module contains the collection_insights_prompt implementation.
"""

import logging
from typing import Any, Dict

from ..core import mcp
from ..base_handlers import BasePromptHandler

# Import prompt implementation - using absolute imports
from src.prompts.collection_insights import get_collection_insights_prompt

# Configure logging
logger = logging.getLogger(__name__)


class CollectionInsightsPromptHandler(BasePromptHandler):
    """Handler for the collection_insights prompt."""
    
    def __init__(self):
        super().__init__("collection_insights", "1.0.0")
    
    def _generate_prompt(self, **kwargs) -> Dict[str, Any]:
        """Generate the collection insights prompt template."""
        return get_collection_insights_prompt()


# Create handler instance
_handler = CollectionInsightsPromptHandler()

@mcp.prompt()
def collection_insights_prompt() -> Dict[str, Any]:
    """
    Prompt template for generating collection insights.
    
    Returns:
        Prompt template for collection insights
    """
    return _handler.generate() 