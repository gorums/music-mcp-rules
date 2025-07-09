#!/usr/bin/env python3
"""
Music Collection MCP Server Tools Package

This package contains all individual MCP tool implementations.
Each tool is in its own file for better organization and maintainability.
"""

# Import all individual tool modules to register the @mcp.tool() decorators
from .scan_music_folders_tool import scan_music_folders
from .get_band_list_tool import get_band_list_tool
from .save_band_metadata_tool import save_band_metadata_tool
from .save_band_analyze_tool import save_band_analyze_tool
from .save_collection_insight_tool import save_collection_insight_tool
from .validate_band_metadata_tool import validate_band_metadata_tool
from .advanced_search_albums_tool import advanced_search_albums_tool
from .analyze_collection_insights_tool import analyze_collection_insights_tool
from .migrate_band_structure_tool import migrate_band_structure
from .generate_collection_web_navigator_tool import generate_collection_web_navigator_tool
from .generate_collection_theme_css_tool import generate_collection_theme_css_tool

__all__ = [
    "scan_music_folders",
    "get_band_list_tool",
    "save_band_metadata_tool", 
    "save_band_analyze_tool",
    "save_collection_insight_tool",
    "validate_band_metadata_tool",
    "advanced_search_albums_tool",
    "analyze_collection_insights_tool",
    "migrate_band_structure",
    "generate_collection_web_navigator_tool",
    "generate_collection_theme_css_tool"
] 