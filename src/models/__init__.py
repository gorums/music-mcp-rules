"""
Music Collection MCP Server - Data Models

This module provides Pydantic models for music metadata, collection management,
and data validation.
"""

# Standard library imports
from typing import TYPE_CHECKING

# Local imports
from .band import (
    Album, 
    AlbumAnalysis, 
    AlbumType,
    BandAnalysis, 
    BandMetadata,
    FolderCompliance,
)

from .album_parser import (
    AlbumFolderParser,
    FolderStructureValidator,
)
from .analytics import (
    AdvancedCollectionInsights,
    AdvancedSearchEngine,
    AlbumSearchFilters,
    CollectionAnalyzer,
    CollectionHealthMetrics,
    CollectionMaturityLevel,
    EditionAnalysis,
    EditionUpgrade,
    RecommendationType,
    TypeAnalysis,
    TypeRecommendation,
)
from .band_structure import (
    BandStructureDetector,
    FolderStructure,
    StructureAnalyzer,
    StructureConsistency,
    StructureType,
)
from .collection import (
    BandIndexEntry,
    CollectionIndex,
    CollectionInsight,
    CollectionStats,
)
from .compliance import (
    BandComplianceReport,
    ComplianceIssue,
    ComplianceIssueType,
    ComplianceLevel,
    ComplianceValidator,
)
from .validation import (
    AlbumDataMigrator,
    AlbumTypeDetector,
    AlbumValidator,
    filter_albums_by_type,
    get_album_type_distribution,
    get_edition_distribution,
    search_albums_by_criteria,
)

# Rebuild models to resolve forward references
BandMetadata.model_rebuild()

__all__ = [
    # Band models
    'Album',
    'AlbumAnalysis',
    'AlbumType',
    'BandAnalysis',
    'BandMetadata',
    'FolderCompliance',
    
    # Collection models
    'BandIndexEntry',
    'CollectionIndex',
    'CollectionInsight',
    'CollectionStats',
    
    # Validation utilities
    'AlbumDataMigrator',
    'AlbumTypeDetector',
    'AlbumValidator',
    'filter_albums_by_type',
    'get_album_type_distribution',
    'get_edition_distribution',
    'search_albums_by_criteria',
    
    # Album parsing utilities
    'AlbumFolderParser',
    'FolderStructureValidator',
    
    # Band structure detection
    'BandStructureDetector',
    'FolderStructure',
    'StructureAnalyzer',
    'StructureConsistency',
    'StructureType',
    
    # Compliance validation
    'BandComplianceReport',
    'ComplianceIssue',
    'ComplianceIssueType',
    'ComplianceLevel',
    'ComplianceValidator',
    
    # Advanced analytics
    'AdvancedCollectionInsights',
    'AdvancedSearchEngine',
    'AlbumSearchFilters',
    'CollectionAnalyzer',
    'CollectionHealthMetrics',
    'CollectionMaturityLevel',
    'EditionAnalysis',
    'EditionUpgrade',
    'RecommendationType',
    'TypeAnalysis',
    'TypeRecommendation',
] 