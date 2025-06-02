"""
Music Collection MCP Server - Data Models

This module provides Pydantic models for music metadata, collection management,
and data validation.
"""

from .band import (
    Album, 
    AlbumType,
    AlbumAnalysis, 
    BandAnalysis, 
    BandMetadata,
    FolderCompliance
)

from .collection import (
    BandIndexEntry,
    CollectionStats,
    CollectionInsight,
    CollectionIndex
)

from .validation import (
    AlbumTypeDetector,
    AlbumDataMigrator,
    AlbumValidator,
    get_album_type_distribution,
    get_edition_distribution,
    filter_albums_by_type,
    search_albums_by_criteria
)

from .album_parser import (
    AlbumFolderParser,
    FolderStructureValidator
)

from .band_structure import (
    StructureType,
    StructureConsistency,
    FolderStructure,
    BandStructureDetector,
    StructureAnalyzer
)

from .compliance import (
    ComplianceLevel,
    ComplianceIssueType,
    ComplianceIssue,
    BandComplianceReport,
    ComplianceValidator
)

# Rebuild models to resolve forward references
BandMetadata.model_rebuild()

__all__ = [
    # Band models
    'Album',
    'AlbumType', 
    'AlbumAnalysis',
    'BandAnalysis',
    'BandMetadata',
    'FolderCompliance',
    
    # Collection models
    'BandIndexEntry',
    'CollectionStats',
    'CollectionInsight', 
    'CollectionIndex',
    
    # Validation utilities
    'AlbumTypeDetector',
    'AlbumDataMigrator',
    'AlbumValidator',
    'get_album_type_distribution',
    'get_edition_distribution',
    'filter_albums_by_type',
    'search_albums_by_criteria',
    
    # Album parsing utilities
    'AlbumFolderParser',
    'FolderStructureValidator',
    
    # Band structure detection
    'StructureType',
    'StructureConsistency',
    'FolderStructure',
    'BandStructureDetector',
    'StructureAnalyzer',
    
    # Compliance validation
    'ComplianceLevel',
    'ComplianceIssueType',
    'ComplianceIssue',
    'BandComplianceReport',
    'ComplianceValidator'
] 