#!/usr/bin/env python3
"""
Music Collection MCP Server Package

This package contains the refactored MCP server components organized by function:
- core.py: Server initialization and FastMCP instance
- tools/: Individual tool implementations (8 tools)
- resources/: Individual resource implementations (3 resources)
- prompts/: Individual prompt implementations (4 prompts)
"""

from .core import create_server
from .mcp_instance import mcp

# Import all tools to ensure they are registered
from .tools import (
    scan_music_folders,
    get_band_list_tool,
    save_band_metadata_tool,
    save_band_analyze_tool,
    save_collection_insight_tool,
    validate_band_metadata_tool,
    advanced_search_albums_tool,
    analyze_collection_insights_tool
)

# Import all resources to ensure they are registered
from .resources import (
    band_info_resource,
    collection_summary_resource,
    advanced_analytics_resource
)

# Import all prompts to ensure they are registered
from .prompts import (
    fetch_band_info_prompt,
    analyze_band_prompt,
    compare_bands_prompt,
    collection_insights_prompt
)

__all__ = [
    "create_server",
    "mcp",
    # Tools
    "scan_music_folders",
    "get_band_list_tool",
    "save_band_metadata_tool",
    "save_band_analyze_tool",
    "save_collection_insight_tool",
    "validate_band_metadata_tool",
    "advanced_search_albums_tool",
    "analyze_collection_insights_tool",
    # Resources
    "band_info_resource",
    "collection_summary_resource",
    "advanced_analytics_resource",
    # Prompts
    "fetch_band_info_prompt",
    "analyze_band_prompt",
    "compare_bands_prompt",
    "collection_insights_prompt"
] 