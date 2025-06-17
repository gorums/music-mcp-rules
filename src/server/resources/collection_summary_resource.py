#!/usr/bin/env python3
"""
Music Collection MCP Server - Collection Summary Resource

This module contains the collection_summary_resource implementation.
"""

import logging
from typing import Any, Dict, List, Optional

from ..core import mcp
from ..base_handlers import BaseResourceHandler

# Import resource implementation - using absolute imports
from src.resources.collection_summary import get_collection_summary

# Configure logging
logger = logging.getLogger(__name__)


class CollectionSummaryResourceHandler(BaseResourceHandler):
    """Handler for the collection_summary resource."""
    
    def __init__(self):
        super().__init__("collection_summary", "1.0.0")
    
    def _get_resource_content(self, **kwargs) -> str:
        """Get collection summary in markdown format."""
        return get_collection_summary()


# Create handler instance
_handler = CollectionSummaryResourceHandler()

@mcp.resource("collection://summary")
def collection_summary_resource() -> str:
    """
    Get collection summary statistics in markdown format.
    
    This resource provides comprehensive collection overview including:
    - Collection overview with total counts and statistics
    - Band distribution analysis (large/medium/small collections)
    - Genre distribution and diversity metrics
    - Missing albums analysis across the collection
    - Top-rated content and rating statistics
    - Collection health assessment with recommendations
    - Recent activity and scanning information
    - Enhanced statistics with album types and compliance
    
    Returns:
        Markdown-formatted collection summary with:
        - Header with collection status badges
        - Collection overview section with key metrics
        - Band analysis with distribution breakdown
        - Genre diversity and distribution charts
        - Missing albums section with acquisition priorities
        - Rating analysis and top-rated content
        - Collection health assessment
        - Enhanced statistics including album types, editions, and compliance
        - Metadata information with timestamps and scan details
        
    URI Format:
        collection://summary
        
    Features:
        - Real-time collection statistics
        - Health assessment scoring
        - Missing albums prioritization
        - Genre and type distribution analysis
        - Collection maturity indicators
        - Actionable recommendations
    """
    return _handler.get_content() 