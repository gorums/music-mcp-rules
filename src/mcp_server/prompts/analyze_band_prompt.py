#!/usr/bin/env python3
"""
Music Collection MCP Server - Analyze Band Prompt

This module contains the analyze_band_prompt implementation.
"""

import logging
from typing import Any, Dict, List, Optional

from ..mcp_instance import mcp
from ..base_handlers import BasePromptHandler

# Import prompt implementation - using absolute imports
from src.core.prompts.analyze_band import get_analyze_band_prompt

# Configure logging
logger = logging.getLogger(__name__)


class AnalyzeBandPromptHandler(BasePromptHandler):
    """Handler for the analyze_band prompt."""
    
    def __init__(self):
        super().__init__("analyze_band", "1.0.0")
    
    def _generate_prompt(self, **kwargs) -> Dict[str, Any]:
        """Generate the analyze band prompt template."""
        band_name = kwargs.get('band_name', '')
        albums = kwargs.get('albums')
        analyze_missing_albums = kwargs.get('analyze_missing_albums', False)
        analysis_scope = kwargs.get('analysis_scope', 'full')
        
        return get_analyze_band_prompt(band_name, albums, analyze_missing_albums, analysis_scope)


# Create handler instance
_handler = AnalyzeBandPromptHandler()

@mcp.prompt()
def analyze_band_prompt(
    band_name: str = "",
    albums: List[str] = None,
    analyze_missing_albums: bool = False,
    analysis_scope: str = "full"
) -> Dict[str, Any]:
    """
    Prompt template for comprehensive band analysis.
    
    This prompt guides the creation of detailed band analysis including reviews,
    ratings, and similar bands identification. It supports different analysis scopes
    and can include both local and missing albums in the analysis.
    
    Args:
        band_name: Name of the band to analyze (optional parameter for dynamic prompts)
        albums: List of albums to include in analysis (optional)
        analyze_missing_albums: If True, include analysis for missing albums too
        analysis_scope: Scope of analysis - "basic", "full", or "albums_only"
    
    Returns:
        Prompt template dictionary with:
        - name: Prompt identifier
        - description: Prompt description
        - messages: List of prompt messages with analysis instructions
        - arguments: Prompt arguments schema
        
    Analysis Scopes:
        - "basic": Essential analysis (overall band review and rating)
        - "full": Complete analysis including album-by-album reviews and ratings
        - "albums_only": Focus on album-specific analysis only
        
    Output Format:
        The prompt generates instructions for creating analysis data in JSON format
        compatible with the BandAnalysis schema, including 1-10 rating scale
        and similar bands identification with collection presence detection.
    """
    return _handler.generate(
        band_name=band_name,
        albums=albums,
        analyze_missing_albums=analyze_missing_albums,
        analysis_scope=analysis_scope
    ) 