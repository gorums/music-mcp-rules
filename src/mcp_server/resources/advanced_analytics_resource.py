#!/usr/bin/env python3
"""
Music Collection MCP Server - Advanced Analytics Resource

This module contains the advanced_analytics_resource implementation.
"""

from ..mcp_instance import mcp
from ..base_handlers import BaseResourceHandler

# Import resource implementation - using absolute imports
from src.core.resources.advanced_analytics import get_advanced_analytics_markdown

class AdvancedAnalyticsResourceHandler(BaseResourceHandler):
    """Handler for the advanced_analytics resource."""
    
    def __init__(self):
        super().__init__("advanced_analytics", "1.0.0")
    
    def _get_resource_content(self, **kwargs) -> str:
        """Get advanced analytics in markdown format."""
        return get_advanced_analytics_markdown()

# Create handler instance
_handler = AdvancedAnalyticsResourceHandler()

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
    return _handler.get_content() 