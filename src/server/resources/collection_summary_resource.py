#!/usr/bin/env python3
"""
Music Collection MCP Server - Collection Summary Resource

This module contains the collection_summary_resource implementation.
"""

import logging
from typing import Any, Dict, List, Optional

from ..core import mcp

# Import resource implementation - using absolute imports
from src.resources.collection_summary import get_collection_summary

# Configure logging
logger = logging.getLogger(__name__)

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
    try:
        return get_collection_summary()
    except Exception as e:
        logger.error(f"Error in collection_summary resource: {str(e)}")
        return f"# Error Retrieving Collection Summary\n\n**Error:** {str(e)}\n\nPlease ensure your music collection has been scanned and that the collection index is accessible." 