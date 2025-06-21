#!/usr/bin/env python3
"""
Tests for Migration Reporting Tool

This module tests the migration_reporting MCP tool functionality,
ensuring it properly integrates with the analytics system.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.mcp_server.tools.migration_reporting_tool import (
    MigrationReportingHandler,
    migration_reporting
)
from src.models.migration_analytics import MigrationHistoryEntry
from src.models.migration import MigrationStatus, MigrationType


class TestMigrationReportingHandler:
    """Test migration reporting handler."""
    
    def setup_method(self):
        """Set up test environment."""
        self.handler = MigrationReportingHandler()
    
    def test_handler_initialization(self):
        """Test handler initialization."""
        assert self.handler.handler_name == "migration_reporting"
        assert self.handler.version == "1.0.0"
    
    @patch('src.mcp_server.tools.migration_reporting_tool.migration_analytics')
    def test_execute_tool_history_report(self, mock_analytics):
        """Test history report generation."""
        # Mock migration history
        mock_entries = [
            MigrationHistoryEntry(
                migration_id="test_1",
                timestamp="2025-01-31T10:00:00",
                band_name="Test Band",
                migration_type=MigrationType.DEFAULT_TO_ENHANCED,
                status=MigrationStatus.COMPLETED,
                albums_migrated=5,
                duration_seconds=30.0,
                success_rate=100.0
            )
        ]
        mock_analytics.get_migration_history.return_value = mock_entries
        
        # Execute tool
        result = self.handler._execute_tool(
            report_type="history",
            band_name="Test Band",
            limit=50
        )
        
        # Verify response
        assert result["status"] == "success"
        assert result["report_type"] == "migration_history"
        assert result["band_name"] == "Test Band"
        assert result["total_entries"] == 1
        assert len(result["migration_history"]) == 1
        
        # Verify history entry
        entry = result["migration_history"][0]
        assert entry["migration_id"] == "test_1"
        assert entry["band_name"] == "Test Band"
        assert entry["migration_type"] == "default_to_enhanced"
        assert entry["status"] == "completed"
        assert entry["albums_migrated"] == 5
        
        # Verify analytics was called correctly
        mock_analytics.get_migration_history.assert_called_once_with(
            band_name="Test Band",
            limit=50
        )
    
    @patch('src.mcp_server.tools.migration_reporting_tool.migration_analytics')
    def test_execute_tool_history_report_all_bands(self, mock_analytics):
        """Test history report for all bands."""
        mock_analytics.get_migration_history.return_value = []
        
        result = self.handler._execute_tool(
            report_type="history",
            band_name="",
            limit=100
        )
        
        assert result["band_name"] == "all"
        mock_analytics.get_migration_history.assert_called_once_with(
            band_name=None,
            limit=100
        )
    
    @patch('src.mcp_server.tools.migration_reporting_tool.migration_analytics')
    def test_execute_tool_statistics_report(self, mock_analytics):
        """Test statistics report generation."""
        # Mock statistics
        mock_stats = {
            "total_migrations": 10,
            "successful_migrations": 8,
            "failed_migrations": 2,
            "overall_success_rate": 80.0,
            "average_duration": 45.5,
            "migration_types": {"default_to_enhanced": 5, "legacy_to_default": 3},
            "bands_migrated": 8
        }
        mock_analytics.get_migration_statistics.return_value = mock_stats
        
        # Execute tool
        result = self.handler._execute_tool(report_type="statistics")
        
        # Verify response
        assert result["status"] == "success"
        assert result["report_type"] == "migration_statistics"
        assert result["statistics"] == mock_stats
        
        # Verify analytics was called
        mock_analytics.get_migration_statistics.assert_called_once()
    
    @patch('src.mcp_server.tools.migration_reporting_tool.migration_analytics')
    def test_execute_tool_summary_report(self, mock_analytics):
        """Test summary report generation."""
        # Mock history and statistics
        mock_history = [
            MigrationHistoryEntry(
                migration_id="test_1",
                timestamp="2025-01-31T10:00:00",
                band_name="Band A",
                migration_type=MigrationType.DEFAULT_TO_ENHANCED,
                status=MigrationStatus.COMPLETED,
                albums_migrated=5,
                duration_seconds=30.0,
                success_rate=100.0
            ),
            MigrationHistoryEntry(
                migration_id="test_2",
                timestamp="2025-01-31T09:00:00",
                band_name="Band B",
                migration_type=MigrationType.LEGACY_TO_DEFAULT,
                status=MigrationStatus.COMPLETED,
                albums_migrated=3,
                duration_seconds=20.0,
                success_rate=100.0
            )
        ]
        mock_stats = {
            "total_migrations": 2,
            "migration_types": {"default_to_enhanced": 1, "legacy_to_default": 1}
        }
        
        mock_analytics.get_migration_history.return_value = mock_history
        mock_analytics.get_migration_statistics.return_value = mock_stats
        
        # Execute tool
        result = self.handler._execute_tool(report_type="summary")
        
        # Verify response structure
        assert result["status"] == "success"
        assert result["report_type"] == "migration_summary"
        assert "overall_statistics" in result
        assert "recent_activity" in result
        assert "recent_migrations" in result
        
        # Verify recent activity
        recent_activity = result["recent_activity"]
        assert recent_activity["recent_migrations"] == 2
        assert recent_activity["recent_success_rate"] == 100.0
        assert recent_activity["average_recent_duration"] == 25.0  # (30 + 20) / 2
        
        # Verify recent migrations (should be limited to 5)
        assert len(result["recent_migrations"]) == 2
    
    def test_execute_tool_invalid_report_type(self):
        """Test invalid report type handling."""
        with pytest.raises(ValueError, match="Invalid report type 'invalid'"):
            self.handler._execute_tool(report_type="invalid")
    
    def test_execute_tool_invalid_limit(self):
        """Test invalid limit handling."""
        # Test negative limit
        with pytest.raises(ValueError, match="Limit must be an integer between 1 and 1000"):
            self.handler._execute_tool(report_type="history", limit=-1)
        
        # Test zero limit
        with pytest.raises(ValueError, match="Limit must be an integer between 1 and 1000"):
            self.handler._execute_tool(report_type="history", limit=0)
        
        # Test too large limit
        with pytest.raises(ValueError, match="Limit must be an integer between 1 and 1000"):
            self.handler._execute_tool(report_type="history", limit=1001)
        
        # Test non-integer limit
        with pytest.raises(ValueError, match="Limit must be an integer between 1 and 1000"):
            self.handler._execute_tool(report_type="history", limit="invalid")
    
    @patch('src.mcp_server.tools.migration_reporting_tool.migration_analytics')
    def test_execute_tool_with_tool_info(self, mock_analytics):
        """Test that tool info is included in response."""
        mock_analytics.get_migration_history.return_value = []
        
        result = self.handler._execute_tool(
            report_type="history",
            band_name="Test Band",
            limit=25
        )
        
        # Verify tool_info is present
        assert "tool_info" in result
        tool_info = result["tool_info"]
        assert tool_info["handler_name"] == "migration_reporting"
        assert tool_info["version"] == "1.0.0"
    
    @patch('src.mcp_server.tools.migration_reporting_tool.migration_analytics')
    def test_execute_tool_exception_handling(self, mock_analytics):
        """Test exception handling in tool execution."""
        # Mock exception
        mock_analytics.get_migration_history.side_effect = Exception("Test error")
        
        with pytest.raises(Exception, match="Test error"):
            self.handler._execute_tool(report_type="history")


class TestMigrationReportingFunction:
    """Test migration_reporting function."""
    
    @patch('src.mcp_server.tools.migration_reporting_tool._handler')
    def test_migration_reporting_function(self, mock_handler):
        """Test migration_reporting function calls handler correctly."""
        # Mock handler response
        mock_response = {"status": "success", "report_type": "history"}
        mock_handler.execute_tool.return_value = mock_response
        
        # Call function
        result = migration_reporting(
            report_type="history",
            band_name="Test Band",
            limit=100
        )
        
        # Verify handler was called correctly
        mock_handler.execute_tool.assert_called_once_with(
            report_type="history",
            band_name="Test Band",
            limit=100
        )
        
        # Verify result
        assert result == mock_response
    
    @patch('src.mcp_server.tools.migration_reporting_tool._handler')
    def test_migration_reporting_default_parameters(self, mock_handler):
        """Test migration_reporting function with default parameters."""
        mock_handler.execute_tool.return_value = {"status": "success"}
        
        result = migration_reporting()
        
        mock_handler.execute_tool.assert_called_once_with(
            report_type="history",
            band_name=None,
            limit=50
        )


class TestMigrationReportingIntegration:
    """Integration tests for migration reporting."""
    
    def test_tool_registration(self):
        """Test that the tool is properly registered."""
        # This tests that the @mcp.tool() decorator works
        # The function should be callable
        assert callable(migration_reporting)
        assert migration_reporting.__name__ == "migration_reporting"
    
    def test_tool_docstring(self):
        """Test that the tool has proper documentation."""
        assert migration_reporting.__doc__ is not None
        assert "Access migration reporting and analytics" in migration_reporting.__doc__
        assert "Args:" in migration_reporting.__doc__
        assert "Returns:" in migration_reporting.__doc__
        assert "Example Usage:" in migration_reporting.__doc__


if __name__ == "__main__":
    pytest.main([__file__]) 