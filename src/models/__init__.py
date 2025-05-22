"""
Music Collection MCP Server - Data Models

This module contains all data models for the music collection metadata system,
including Pydantic models for validation, JSON serialization/deserialization,
and data migration utilities.
"""

from .band import (
    Album,
    AlbumAnalysis,
    BandAnalysis,
    BandMetadata
)

from .collection import (
    BandIndexEntry,
    CollectionStats,
    CollectionInsight,
    CollectionIndex
)

# Migration utilities will be added when needed
# from .migration import (
#     DataMigration,
#     DataValidator
# )

__all__ = [
    # Band models
    'Album',
    'AlbumAnalysis', 
    'BandAnalysis',
    'BandMetadata',
    
    # Collection models
    'BandIndexEntry',
    'CollectionStats',
    'CollectionInsight',
    'CollectionIndex',
    
    # Migration utilities (commented out until implemented)
    # 'DataMigration',
    # 'DataValidator'
] 