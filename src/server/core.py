#!/usr/bin/env python3
"""
Music Collection MCP Server Core

Core module for the Music Collection MCP Server that handles:
- Server initialization and configuration
- FastMCP server instance creation
- Main entry point and lifecycle management
- Logger configuration
"""

import logging
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

# Configure logging
logger = logging.getLogger(__name__)

# Create FastMCP server instance with ERROR log level to fix MCP client visibility
mcp = FastMCP("music-collection-mcp")

# Import all tool modules to register the @mcp.tool() decorators
# Individual tool files are loaded to register the MCP tools
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

# Import individual resource and prompt handlers
from . import resources
from . import prompts

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