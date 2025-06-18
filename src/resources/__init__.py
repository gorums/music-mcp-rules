"""
Music Collection MCP Server - Resources Package

This package provides MCP resource implementations for band information,
collection summaries, and advanced analytics.
"""

from .band_info import get_band_info_markdown
from .collection_summary import get_collection_summary
from .advanced_analytics import get_advanced_analytics_markdown

__all__ = [
    # Resource functions
    'get_band_info_markdown',
    'get_collection_summary', 
    'get_advanced_analytics_markdown'
] 