#!/usr/bin/env python3
"""
Music Collection MCP Server - Scan Music Folders Tool

This module contains the scan_music_folders tool implementation.
"""

import logging
from typing import Any, Dict

from ..core import mcp

# Import tool implementation - using absolute imports
from src.tools.scanner import scan_music_folders as scanner_scan_music_folders

# Configure logging
logger = logging.getLogger(__name__)

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
    try:
        # Call the scanner to perform comprehensive change detection
        # Reason: Always perform full scan to detect all types of changes
        result = scanner_scan_music_folders()
            
        # Add tool-specific metadata
        if result.get('status') == 'success':
            result['tool_info'] = {
                'tool_name': 'scan_music_folders',
                'version': '3.0.0',  # Updated version for always-scan behavior
                'scan_mode': 'comprehensive_change_detection',
                'change_detection': 'enabled'
            }
            
        return result
        
    except Exception as e:
        logger.error(f"Error in scan_music_folders tool: {str(e)}")
        return {
            'status': 'error',
            'error': f"Tool execution failed: {str(e)}",
            'tool_info': {
                'tool_name': 'scan_music_folders',
                'version': '3.0.0'
            }
        } 