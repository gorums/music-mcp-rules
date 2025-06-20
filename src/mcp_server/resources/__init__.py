#!/usr/bin/env python3
"""
Music Collection MCP Server - Resources Package

This package contains all individual MCP resource implementations.
Each resource is in its own dedicated file for better maintainability.
"""

# Import all individual resource functions
from .band_info_resource import band_info_resource
from .collection_summary_resource import collection_summary_resource
from .advanced_analytics_resource import advanced_analytics_resource

# Export all resources for easy importing
__all__ = [
    'band_info_resource',
    'collection_summary_resource',
    'advanced_analytics_resource'
] 