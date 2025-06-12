"""
Metadata management functions for Music Collection MCP Server.

This module provides high-level functions for saving and managing band metadata,
analysis data, and collection insights using the storage module.
"""

from typing import Dict, Any
from models import BandMetadata, BandAnalysis, CollectionInsight
from .storage import save_band_metadata as _save_band_metadata
from .storage import save_band_analyze as _save_band_analyze
from .storage import save_collection_insight as _save_collection_insight
from .storage import StorageError


def save_band_metadata(band_name: str, metadata: BandMetadata) -> Dict[str, Any]:
    """
    Save complete band metadata to .band_metadata.json file.
    
    Args:
        band_name: Name of the band
        metadata: BandMetadata instance to save
        
    Returns:
        Dict with operation status and details
        
    Raises:
        StorageError: If save operation fails
    """
    return _save_band_metadata(band_name, metadata)


def save_band_analyze(band_name: str, analysis: BandAnalysis) -> Dict[str, Any]:
    """
    Save band analysis data with reviews and ratings.
    
    Args:
        band_name: Name of the band
        analysis: BandAnalysis instance to save
        
    Returns:
        Dict with operation status and details
        
    Raises:
        StorageError: If save operation fails
    """
    return _save_band_analyze(band_name, analysis)


def save_collection_insight(insights: CollectionInsight) -> Dict[str, Any]:
    """
    Save collection-wide insights and analytics.
    
    Args:
        insights: CollectionInsight instance to save
        
    Returns:
        Dict with operation status and details
        
    Raises:
        StorageError: If save operation fails
    """
    return _save_collection_insight(insights) 