#!/usr/bin/env python3
"""
Music Collection MCP Server - Compare Bands Prompt

This module contains the compare_bands_prompt implementation.
"""

import logging
from typing import Any, Dict, List, Optional

from ..core import mcp

# Import prompt implementation - using absolute imports
from src.prompts.compare_bands import get_compare_bands_prompt

# Configure logging
logger = logging.getLogger(__name__)

@mcp.prompt()
def compare_bands_prompt(
    band_names: List[str] = None,
    comparison_aspects: List[str] = None,
    comparison_scope: str = "full"
) -> Dict[str, Any]:
    """
    Prompt template for comparing multiple bands.
    
    This prompt guides the creation of comprehensive band comparisons across multiple
    dimensions including musical style, discography, influence, and commercial success.
    It supports focused comparison aspects and different scope levels.
    
    Args:
        band_names: List of band names to compare (minimum 2 required)
        comparison_aspects: Specific aspects to focus on: style, discography, influence, legacy, innovation, commercial, critical
        comparison_scope: Scope of comparison - "basic", "full", or "summary"
    
    Returns:
        Prompt template dictionary with:
        - name: Prompt identifier
        - description: Prompt description
        - messages: List of prompt messages with comparison instructions
        - arguments: Prompt arguments schema
        
    Comparison Aspects:
        - "style": Musical style and genre evolution
        - "discography": Album quality and progression
        - "influence": Impact on other artists and genres
        - "legacy": Long-term cultural significance
        - "innovation": Technical and artistic innovation
        - "commercial": Commercial success and popularity
        - "critical": Critical acclaim and reviews
        
    Comparison Scopes:
        - "basic": Essential comparison with key differences
        - "full": Comprehensive multi-dimensional analysis
        - "summary": Concise comparison with rankings
        
    Output Format:
        The prompt generates instructions for creating comparison data in JSON format
        with rankings, assessments, and detailed analysis for each comparison dimension.
    """
    try:
        return get_compare_bands_prompt(band_names, comparison_aspects, comparison_scope)
    except Exception as e:
        logger.error(f"Error in compare_bands prompt: {str(e)}")
        return {
            'name': 'compare_bands',
            'description': 'Error loading prompt template',
            'messages': [{'role': 'user', 'content': f'Error: {str(e)}'}],
            'arguments': []
        } 