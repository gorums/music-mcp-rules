"""
Tools module for Music Collection MCP Server.

This module provides tools for scanning, storage, metadata management, and cache management.
"""

from .scanner import scan_music_folders
from .storage import (
    save_band_metadata,
    save_band_analyze, 
    save_collection_insight,
    get_band_list,
    load_band_metadata,
    load_collection_index,
    update_collection_index,
    cleanup_backups
)
from .cache import (
    CacheManager,
    CacheStatus,
    CacheStats,
    CacheEntry,
    CacheError,
    is_metadata_cache_valid,
    cleanup_expired_caches,
    get_collection_cache_stats
)
from .performance import (
    PerformanceMetrics,
    PerformanceTracker,
    BatchFileOperations,
    ProgressReporter,
    performance_monitor,
    track_operation,
    get_performance_summary,
    clear_performance_metrics
)

__all__ = [
    # Scanner functions
    'scan_music_folders',
    
    # Storage functions
    'save_band_metadata',
    'save_band_analyze',
    'save_collection_insight', 
    'get_band_list',
    'load_band_metadata',
    'load_collection_index',
    'update_collection_index',
    'cleanup_backups',
    
    # Metadata functions
    'metadata_save_band_metadata',
    'metadata_save_band_analyze',
    'metadata_save_collection_insight',
    
    # Cache management
    'CacheManager',
    'CacheStatus',
    'CacheStats', 
    'CacheEntry',
    'CacheError',
    'is_metadata_cache_valid',
    'cleanup_expired_caches',
    'get_collection_cache_stats',
    
    # Performance monitoring
    'PerformanceMetrics',
    'PerformanceTracker',
    'BatchFileOperations', 
    'ProgressReporter',
    'performance_monitor',
    'track_operation',
    'get_performance_summary',
    'clear_performance_metrics'
] 