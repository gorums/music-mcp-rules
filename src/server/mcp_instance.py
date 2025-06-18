#!/usr/bin/env python3
"""
Music Collection MCP Server - MCP Instance

This module contains the FastMCP server instance to avoid circular imports.
"""

from fastmcp import FastMCP

# Create FastMCP server instance
mcp = FastMCP("music-collection-mcp") 