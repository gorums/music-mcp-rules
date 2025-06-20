#!/usr/bin/env python3
"""
Music Collection MCP Server - Scan Music Folders Tool

This module contains the scan_music_folders tool implementation.
"""

import logging
from typing import Any, Dict

from ..mcp_instance import mcp
from ..base_handlers import BaseToolHandler

# Import tool implementation - using absolute imports
from src.core.tools.scanner import scan_music_folders as scanner_scan_music_folders

# Configure logging
logger = logging.getLogger(__name__)


class ScanMusicFoldersHandler(BaseToolHandler):
    """Handler for the scan_music_folders tool."""
    
    def __init__(self):
        super().__init__("scan_music_folders", "3.0.0")
    
    def _execute_tool(self, **kwargs) -> Dict[str, Any]:
        """Execute the scan music folders tool logic."""
        # Call the scanner to perform comprehensive change detection
        # Reason: Always perform full scan to detect all types of changes
        result = scanner_scan_music_folders()
        
        # Add tool-specific metadata
        if result.get('status') == 'success':
            result['tool_info'] = self._create_tool_info(
                scan_mode='comprehensive_change_detection',
                change_detection='enabled'
            )
        
        return result


# Create handler instance
_handler = ScanMusicFoldersHandler()

@mcp.tool()
def scan_music_folders() -> Dict[str, Any]:
    """
    Scan the music directory structure to discover bands and albums, detecting all changes.
    
    This tool performs a comprehensive scan of the music collection:
    - Detects new bands that have been added to the collection
    - Identifies bands that have been removed from the collection  
    - Discovers changes in album structure (new albums, removed albums, renamed albums)
    - Updates collection index with all detected changes
    - Preserves existing metadata and analysis data during scanning
    - Optimized for performance while ensuring complete change detection
    
    Returns:
        Dict containing scan results including:
        - status: 'success' or 'error'
        - results: Dict with scan statistics and detailed change information
        - collection_path: Path to the scanned music collection
        - changes_made: True if any changes were detected and saved
        - bands_added: Number of new bands discovered
        - bands_removed: Number of bands no longer found
        - albums_changed: Number of bands with album structure changes
    """
    return _handler.execute() 