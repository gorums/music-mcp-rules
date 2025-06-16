#!/usr/bin/env python3
"""
Music Collection MCP Server - Prompts Package

This package contains all individual MCP prompt implementations.
Each prompt is in its own dedicated file for better maintainability.
"""

# Import all individual prompt functions
from .fetch_band_info_prompt import fetch_band_info_prompt
from .analyze_band_prompt import analyze_band_prompt
from .compare_bands_prompt import compare_bands_prompt
from .collection_insights_prompt import collection_insights_prompt

# Export all prompts for easy importing
__all__ = [
    'fetch_band_info_prompt',
    'analyze_band_prompt', 
    'compare_bands_prompt',
    'collection_insights_prompt'
] 