#!/usr/bin/env python3
"""
Music Collection MCP Server - Migration Reporting Tool

This module contains the migration_reporting tool implementation for accessing
migration history, statistics, and detailed reports.
"""

import logging
from typing import Any, Dict, List, Optional

from ..mcp_instance import mcp
from ..base_handlers import BaseToolHandler

# Import migration analytics functionality
from src.models.migration_analytics import migration_analytics

# Configure logging
logger = logging.getLogger(__name__)


class MigrationReportingHandler(BaseToolHandler):
    """Handler for the migration_reporting tool."""
    
    def __init__(self):
        super().__init__("migration_reporting", "1.0.0")
    
    def _execute_tool(self, **kwargs) -> Dict[str, Any]:
        """Execute the migration reporting tool logic."""
        # Extract and validate parameters
        report_type = kwargs.get('report_type', 'history').strip().lower()
        band_name = kwargs.get('band_name', '').strip()
        limit = kwargs.get('limit', 50)
        
        # Validate limit
        if not isinstance(limit, int) or limit < 1 or limit > 1000:
            raise ValueError("Limit must be an integer between 1 and 1000")
        
        try:
            if report_type == 'history':
                # Get migration history
                history = migration_analytics.get_migration_history(
                    band_name=band_name if band_name else None,
                    limit=limit
                )
                
                response = {
                    'status': 'success',
                    'report_type': 'migration_history',
                    'band_name': band_name if band_name else 'all',
                    'total_entries': len(history),
                    'migration_history': [
                        {
                            'migration_id': entry.migration_id,
                            'timestamp': entry.timestamp,
                            'band_name': entry.band_name,
                            'migration_type': entry.migration_type.value,
                            'status': entry.status.value,
                            'albums_migrated': entry.albums_migrated,
                            'duration_seconds': entry.duration_seconds,
                            'success_rate': entry.success_rate
                        }
                        for entry in history
                    ]
                }
                
            elif report_type == 'statistics':
                # Get overall migration statistics
                stats = migration_analytics.get_migration_statistics()
                
                response = {
                    'status': 'success',
                    'report_type': 'migration_statistics',
                    'statistics': stats
                }
                
            elif report_type == 'summary':
                # Get summary combining history and statistics
                history = migration_analytics.get_migration_history(limit=10)
                stats = migration_analytics.get_migration_statistics()
                
                # Recent activity analysis
                recent_activity = {
                    'recent_migrations': len([h for h in history if h.timestamp]),
                    'recent_success_rate': sum(h.success_rate for h in history) / max(1, len(history)),
                    'most_migrated_band': max(stats.get('migration_types', {}).items(), 
                                            key=lambda x: x[1], default=('None', 0))[0],
                    'average_recent_duration': sum(h.duration_seconds for h in history) / max(1, len(history))
                }
                
                response = {
                    'status': 'success',
                    'report_type': 'migration_summary',
                    'overall_statistics': stats,
                    'recent_activity': recent_activity,
                    'recent_migrations': [
                        {
                            'migration_id': entry.migration_id,
                            'timestamp': entry.timestamp,
                            'band_name': entry.band_name,
                            'migration_type': entry.migration_type.value,
                            'status': entry.status.value,
                            'success_rate': entry.success_rate
                        }
                        for entry in history[:5]  # Last 5 migrations
                    ]
                }
                
            else:
                raise ValueError(f"Invalid report type '{report_type}'. Valid types: 'history', 'statistics', 'summary'")
            
            # Add tool-specific metadata
            response['tool_info'] = self._create_handler_info(
                report_type=report_type,
                band_filter=band_name if band_name else 'none',
                limit=limit
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Migration reporting failed: {str(e)}")
            raise


# Create handler instance
_handler = MigrationReportingHandler()

@mcp.tool()
def migration_reporting(
    report_type: str = "history",
    band_name: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Access migration reporting and analytics information.
    
    This tool provides comprehensive access to migration history, statistics,
    and analytics for understanding migration patterns and success rates.
    
    Report Types:
    - history: Detailed migration history with timestamps and results
    - statistics: Overall migration statistics and success rates
    - summary: Combined overview with recent activity and key metrics
    
    Args:
        report_type: Type of report to generate ('history', 'statistics', 'summary')
        band_name: Optional band name filter for history reports
        limit: Maximum number of history entries to return (1-1000, default: 50)
    
    Returns:
        Dict containing migration reporting data including:
        - status: 'success' or 'error'
        - report_type: Type of report generated
        - migration_history: List of migration history entries (for history reports)
        - statistics: Overall migration statistics (for statistics reports)
        - recent_activity: Recent migration activity analysis (for summary reports)
        - tool_info: Reporting metadata and parameters
    
    Example Usage:
        # Get migration history for all bands
        migration_reporting(report_type="history", limit=100)
        
        # Get migration history for specific band
        migration_reporting(report_type="history", band_name="Metallica", limit=20)
        
        # Get overall migration statistics
        migration_reporting(report_type="statistics")
        
        # Get summary with recent activity
        migration_reporting(report_type="summary")
    """
    return _handler.execute_tool(
        report_type=report_type,
        band_name=band_name,
        limit=limit
    ) 