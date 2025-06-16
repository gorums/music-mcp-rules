#!/usr/bin/env python3
"""
Music Collection MCP Server - Advanced Analytics Resource

This module contains the advanced_analytics_resource implementation.
"""

import logging
from typing import Any, Dict, List, Optional

from ..core import mcp

# Import resource implementation - using absolute imports
from src.resources.advanced_analytics import get_advanced_analytics_markdown

# Configure logging
logger = logging.getLogger(__name__)

@mcp.resource("collection://analytics")
def advanced_analytics_resource() -> str:
    """
    Get advanced collection analytics with comprehensive insights in markdown format.
    
    This resource provides deep collection analysis including:
    - Collection maturity assessment (Beginner to Master levels)
    - Album type distribution analysis vs. ideal distributions
    - Edition prevalence and upgrade opportunities
    - Collection health metrics with multi-factor scoring
    - Type-specific recommendations for missing albums
    - Discovery potential and value assessment
    - Organization recommendations and folder structure analysis
    - Decade distribution and genre trend analysis
    - Advanced insights with pattern recognition
    
    Returns:
        Markdown-formatted advanced analytics with:
        - Collection maturity section with level assessment
        - Type analysis with distribution vs. ideal ratios
        - Edition analysis with upgrade recommendations
        - Health metrics with scoring breakdown
        - Recommendations section with actionable insights
        - Value assessment with rarity factors
        - Discovery section with potential opportunities
        - Advanced insights with collection patterns
        - Organization analysis with compliance scoring
        
    URI Format:
        collection://analytics
        
    Features:
        - Maturity level assessment (5 levels from Beginner to Master)
        - Health scoring with multiple factors
        - Type distribution vs. ideal analysis
        - Edition tracking and upgrade suggestions
        - Value scoring based on rarity
        - Discovery potential assessment
        - Pattern recognition and insights
        - Organization health analysis
    """
    try:
        return get_advanced_analytics_markdown()
    except Exception as e:
        logger.error(f"Error in advanced_analytics resource: {str(e)}")
        return f"# Error Retrieving Advanced Analytics\n\n**Error:** {str(e)}\n\nPlease ensure your music collection has been scanned and analyzed. Advanced analytics require collection data and may need collection insights to be generated first." 