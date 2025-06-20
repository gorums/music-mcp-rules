"""
Music Collection MCP Server - Prompts Package

This package provides MCP prompt templates for band information fetching,
analysis, comparison, and collection insights.
"""

from .analyze_band import get_analyze_band_prompt
from .fetch_band_info import get_fetch_band_info_prompt
from .compare_bands import get_compare_bands_prompt
from .collection_insights import get_collection_insights_prompt

__all__ = [
    # Prompt functions
    'get_analyze_band_prompt',
    'get_fetch_band_info_prompt',
    'get_compare_bands_prompt',
    'get_collection_insights_prompt'
] 