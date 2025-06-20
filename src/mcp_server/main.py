#!/usr/bin/env python3
"""
Music Collection MCP Server Core

Core module for the Music Collection MCP Server that handles:
- Server initialization and configuration
- FastMCP server instance creation
- Main entry point and lifecycle management
- Logger configuration
"""

# Standard library imports
import logging
from typing import Any, Dict, List, Optional

# Third-party imports
from fastmcp import FastMCP

# Local imports - Import MCP instance first to avoid circular imports
from .mcp_instance import mcp

# Configure logging
logger = logging.getLogger(__name__)

# Local imports - Import handlers to register decorators
from . import prompts, resources
from .tools import (
    advanced_search_albums_tool,
    analyze_collection_insights_tool,
    get_band_list_tool,
    save_band_analyze_tool,
    save_band_metadata_tool,
    save_collection_insight_tool,
    scan_music_folders,
    validate_band_metadata_tool,
)

def create_server() -> FastMCP:
    """Create and configure the MCP server instance"""
    logger.info("Initializing Music Collection MCP Server...")
    
    # Import handlers to register with the server
    # NOTE: These imports are required to register @mcp.tool(), @mcp.resource(), @mcp.prompt() decorators
    # Removing these imports will prevent the MCP tools from being available to clients
    logger.info("All MCP handlers initialized successfully")
    
    return mcp

def main():
    """Main entry point for the MCP server."""
    logger.info("Starting Music Collection MCP Server...")
    
    try:
        # Run server directly - tools are already registered through imports
        logger.info("MCP Server initialized successfully")
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        raise
    finally:
        logger.info("Music Collection MCP Server stopped")

if __name__ == "__main__":
    main() 