#!/usr/bin/env python3
"""
Tests for Migration Analytics System

This module tests the migration reporting and analytics functionality,
ensuring comprehensive test coverage and business logic preservation.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

from src.models.migration_analytics import (
    MigrationAnalytics,
    MigrationReport,
    MigrationMetric,
    AlbumTypeDistribution,
    StructureComparisonResult,
    MigrationSuccessRate,
    OrganizationImprovement,
    UnmigratedAlbumRecommendation,
    MigrationHistoryEntry,
    migration_analytics
)
from src.models.migration import (
    MigrationResult,
    MigrationStatus,
    MigrationType,
    AlbumMigrationOperation
)
from src.models.band import AlbumType
from src.models.band_structure import StructureType


class TestMigrationAnalytics:
    """Test migration analytics functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.analytics = MigrationAnalytics()
        self.temp_dir = tempfile.mkdtemp()
        self.band_folder_path = Path(self.temp_dir) / "Test Band"
        self.band_folder_path.mkdir(parents=True, exist_ok=True)
    
    def create_sample_migration_result(self) -> MigrationResult:
        """Create a sample migration result for testing."""
        operations = [
            AlbumMigrationOperation(
                album_name="Album 1",
                source_path="Test Band/2010 - Album 1",
                target_path="Test Band/Album/2010 - Album 1",
                album_type=AlbumType.ALBUM,
                operation_type="move",
                completed=True
            ),
            AlbumMigrationOperation(
                album_name="Live Album",
                source_path="Test Band/2011 - Live Album (Live)",
                target_path="Test Band/Live/2011 - Live Album (Live)",
                album_type=AlbumType.LIVE,
                operation_type="move",
                completed=True
            ),
            AlbumMigrationOperation(
                album_name="Failed Album",
                source_path="Test Band/2012 - Failed Album",
                target_path="Test Band/Album/2012 - Failed Album",
                album_type=AlbumType.ALBUM,
                operation_type="move",
                completed=False,
                error_message="Permission denied"
            )
        ]
        
        return MigrationResult(
            status=MigrationStatus.COMPLETED,
            band_name="Test Band",
            migration_type=MigrationType.DEFAULT_TO_ENHANCED,
            albums_migrated=2,
            albums_failed=1,
            operations=operations,
            migration_time_seconds=45.5
        )
    
    def test_generate_migration_report(self):
        """Test migration report generation."""
        migration_result = self.create_sample_migration_result()
        
        report = self.analytics.generate_migration_report(
            migration_result, 
            self.band_folder_path
        )
        
        # Verify report structure
        assert isinstance(report, MigrationReport)
        assert report.band_name == "Test Band"
        assert report.migration_result == migration_result
        assert report.report_id.startswith("Test Band_")
        
        # Verify structure comparison
        assert report.structure_comparison.before_structure == StructureType.DEFAULT
        assert report.structure_comparison.after_structure == StructureType.ENHANCED
        assert report.structure_comparison.albums_reorganized == 2
        
        # Verify type distribution
        assert len(report.type_distribution_analysis) > 0
        album_dist = next((d for d in report.type_distribution_analysis 
                          if d.album_type == AlbumType.ALBUM), None)
        assert album_dist is not None
        assert album_dist.before_count == 2  # 2 albums that would be Album type
        
        # Verify success metrics
        assert report.success_metrics.total_operations == 3
        assert report.success_metrics.successful_operations == 2
        assert report.success_metrics.failed_operations == 1
        assert abs(report.success_metrics.success_rate - 66.67) < 0.1
        
        # Verify performance metrics
        assert len(report.performance_metrics) > 0
        duration_metric = next((m for m in report.performance_metrics 
                               if m.name == "Migration Duration"), None)
        assert duration_metric is not None
        assert duration_metric.value == 45.5
        
        # Verify unmigrated recommendations
        assert len(report.unmigrated_recommendations) == 1
        rec = report.unmigrated_recommendations[0]
        assert rec.album_name == "Failed Album"
        assert "Permission denied" in rec.reason
    
    def test_analyze_type_distribution(self):
        """Test album type distribution analysis."""
        migration_result = self.create_sample_migration_result()
        
        distributions = self.analytics._analyze_type_distribution(migration_result)
        
        # Should have distributions for all album types
        assert len(distributions) == len(AlbumType)
        
        # Check specific distributions
        album_dist = next(d for d in distributions if d.album_type == AlbumType.ALBUM)
        assert album_dist.before_count == 2
        assert album_dist.after_count == 1  # One failed
        assert album_dist.change == -1
        
        live_dist = next(d for d in distributions if d.album_type == AlbumType.LIVE)
        assert live_dist.before_count == 1
        assert live_dist.after_count == 1
        assert live_dist.change == 0
    
    def test_calculate_success_metrics(self):
        """Test success metrics calculation."""
        migration_result = self.create_sample_migration_result()
        
        success_metrics = self.analytics._calculate_success_metrics(migration_result)
        
        assert success_metrics.total_operations == 3
        assert success_metrics.successful_operations == 2
        assert success_metrics.failed_operations == 1
        assert abs(success_metrics.success_rate - 66.67) < 0.1
        assert success_metrics.average_operation_time > 0
        assert "Permission Error" in success_metrics.error_breakdown
    
    def test_generate_performance_metrics(self):
        """Test performance metrics generation."""
        migration_result = self.create_sample_migration_result()
        
        metrics = self.analytics._generate_performance_metrics(migration_result)
        
        # Should have multiple metrics
        assert len(metrics) >= 3
        
        # Check specific metrics
        metric_names = [m.name for m in metrics]
        assert "Migration Duration" in metric_names
        assert "Migration Throughput" in metric_names
        assert "Success Rate" in metric_names
        
        # Verify metric values
        duration_metric = next(m for m in metrics if m.name == "Migration Duration")
        assert duration_metric.value == 45.5
        assert duration_metric.unit == "seconds"
    
    def test_generate_unmigrated_recommendations(self):
        """Test unmigrated album recommendations."""
        migration_result = self.create_sample_migration_result()
        
        recommendations = self.analytics._generate_unmigrated_recommendations(
            migration_result, 
            self.band_folder_path
        )
        
        assert len(recommendations) == 1
        rec = recommendations[0]
        assert rec.album_name == "Failed Album"
        assert rec.recommended_type == AlbumType.ALBUM
        assert "permission denied" in rec.reason.lower()
    
    def test_migration_history_tracking(self):
        """Test migration history tracking."""
        migration_result = self.create_sample_migration_result()
        
        # Generate report to add to history
        self.analytics.generate_migration_report(migration_result, self.band_folder_path)
        
        # Check history
        history = self.analytics.get_migration_history()
        assert len(history) == 1
        
        entry = history[0]
        assert entry.band_name == "Test Band"
        assert entry.migration_type == MigrationType.DEFAULT_TO_ENHANCED
        assert entry.status == MigrationStatus.COMPLETED
        assert entry.albums_migrated == 2
    
    def test_get_migration_statistics(self):
        """Test migration statistics generation."""
        # Initially empty
        stats = self.analytics.get_migration_statistics()
        assert stats["total_migrations"] == 0
        
        # Add some migration history
        migration_result = self.create_sample_migration_result()
        self.analytics.generate_migration_report(migration_result, self.band_folder_path)
        
        # Check updated statistics
        stats = self.analytics.get_migration_statistics()
        assert stats["total_migrations"] == 1
        assert stats["successful_migrations"] == 1
        assert stats["failed_migrations"] == 0
        assert stats["overall_success_rate"] == 100.0
        assert stats["bands_migrated"] == 1
    
    def test_generate_markdown_report(self):
        """Test markdown report generation."""
        migration_result = self.create_sample_migration_result()
        report = self.analytics.generate_migration_report(migration_result, self.band_folder_path)
        
        markdown = self.analytics.generate_markdown_report(report)
        
        # Verify markdown content
        assert "# Migration Report: Test Band" in markdown
        assert "Migration Type:** default_to_enhanced" in markdown
        assert "Total Albums Processed:** 3" in markdown
        assert "Successfully Migrated:** 2" in markdown
        assert "## 🎵 Album Type Distribution" in markdown
        assert "## ⚡ Performance Metrics" in markdown
        assert "## 🔄 Recommendations for Unmigrated Albums" in markdown
        assert "Failed Album" in markdown
    
    def test_categorize_error(self):
        """Test error categorization."""
        assert self.analytics._categorize_error("Permission denied") == "Permission Error"
        assert self.analytics._categorize_error("Not enough disk space") == "Disk Space Error"
        assert self.analytics._categorize_error("Invalid path") == "Path Error"
        assert self.analytics._categorize_error("File not found") == "File Error"
        assert self.analytics._categorize_error("Unknown error") == "Unknown Error"
    
    def test_structure_type_mapping(self):
        """Test structure type mapping."""
        # Test original structure detection
        assert self.analytics._determine_original_structure(
            MigrationType.DEFAULT_TO_ENHANCED) == StructureType.DEFAULT
        assert self.analytics._determine_original_structure(
            MigrationType.LEGACY_TO_DEFAULT) == StructureType.LEGACY
        
        # Test target structure detection
        assert self.analytics._determine_target_structure(
            MigrationType.DEFAULT_TO_ENHANCED) == StructureType.ENHANCED
        assert self.analytics._determine_target_structure(
            MigrationType.LEGACY_TO_DEFAULT) == StructureType.DEFAULT
    
    def test_identify_new_type_folders(self):
        """Test new type folder identification."""
        migration_result = self.create_sample_migration_result()
        
        type_folders = self.analytics._identify_new_type_folders(migration_result)
        
        # Should identify Live folder (Album is default, so not "new")
        assert "Live" in type_folders
        assert len(type_folders) >= 1
    
    def test_compliance_score_calculation(self):
        """Test compliance score calculation."""
        migration_result = self.create_sample_migration_result()
        
        before_score, after_score = self.analytics._calculate_compliance_scores(
            migration_result, 
            self.band_folder_path
        )
        
        # Should show improvement
        assert after_score > before_score
        assert before_score >= 0
        assert after_score <= 100
    
    def test_migration_history_filtering(self):
        """Test migration history filtering by band."""
        # Add multiple migrations for different bands
        result1 = self.create_sample_migration_result()
        result1.band_name = "Band A"
        
        result2 = self.create_sample_migration_result()
        result2.band_name = "Band B"
        
        self.analytics.generate_migration_report(result1, self.band_folder_path)
        self.analytics.generate_migration_report(result2, self.band_folder_path)
        
        # Test filtering
        all_history = self.analytics.get_migration_history()
        assert len(all_history) == 2
        
        band_a_history = self.analytics.get_migration_history(band_name="Band A")
        assert len(band_a_history) == 1
        assert band_a_history[0].band_name == "Band A"
        
        band_b_history = self.analytics.get_migration_history(band_name="Band B")
        assert len(band_b_history) == 1
        assert band_b_history[0].band_name == "Band B"
    
    def test_migration_history_limit(self):
        """Test migration history limit functionality."""
        # Add multiple migrations
        for i in range(5):
            result = self.create_sample_migration_result()
            result.band_name = f"Band {i}"
            self.analytics.generate_migration_report(result, self.band_folder_path)
        
        # Test limit
        limited_history = self.analytics.get_migration_history(limit=3)
        assert len(limited_history) == 3
        
        # Should be sorted by timestamp (most recent first)
        timestamps = [entry.timestamp for entry in limited_history]
        assert timestamps == sorted(timestamps, reverse=True)


class TestMigrationAnalyticsModels:
    """Test migration analytics data models."""
    
    def test_migration_metric_model(self):
        """Test MigrationMetric model."""
        metric = MigrationMetric(
            name="Test Metric",
            value=42.5,
            unit="units",
            description="Test description"
        )
        
        assert metric.name == "Test Metric"
        assert metric.value == 42.5
        assert metric.unit == "units"
        assert metric.description == "Test description"
    
    def test_album_type_distribution_model(self):
        """Test AlbumTypeDistribution model."""
        distribution = AlbumTypeDistribution(
            album_type=AlbumType.ALBUM,
            before_count=10,
            after_count=8,
            change=-2,
            percentage_before=50.0,
            percentage_after=40.0
        )
        
        assert distribution.album_type == AlbumType.ALBUM
        assert distribution.before_count == 10
        assert distribution.after_count == 8
        assert distribution.change == -2
    
    def test_structure_comparison_result_model(self):
        """Test StructureComparisonResult model."""
        comparison = StructureComparisonResult(
            before_structure=StructureType.DEFAULT,
            after_structure=StructureType.ENHANCED,
            albums_reorganized=5,
            new_type_folders_created=["Live", "Demo"],
            compliance_score_before=60.0,
            compliance_score_after=90.0,
            compliance_improvement=30.0
        )
        
        assert comparison.before_structure == StructureType.DEFAULT
        assert comparison.after_structure == StructureType.ENHANCED
        assert comparison.albums_reorganized == 5
        assert len(comparison.new_type_folders_created) == 2
        assert comparison.compliance_improvement == 30.0
    
    def test_migration_success_rate_model(self):
        """Test MigrationSuccessRate model."""
        success_rate = MigrationSuccessRate(
            total_operations=10,
            successful_operations=8,
            failed_operations=2,
            success_rate=80.0,
            average_operation_time=2.5,
            error_breakdown={"Permission Error": 1, "Disk Space Error": 1}
        )
        
        assert success_rate.total_operations == 10
        assert success_rate.successful_operations == 8
        assert success_rate.failed_operations == 2
        assert success_rate.success_rate == 80.0
        assert len(success_rate.error_breakdown) == 2
    
    def test_organization_improvement_model(self):
        """Test OrganizationImprovement model."""
        improvement = OrganizationImprovement(
            metric_name="Structure Consistency",
            before_value=40.0,
            after_value=90.0,
            improvement_percentage=125.0,
            improvement_description="Migrated to enhanced structure"
        )
        
        assert improvement.metric_name == "Structure Consistency"
        assert improvement.before_value == 40.0
        assert improvement.after_value == 90.0
        assert improvement.improvement_percentage == 125.0
    
    def test_unmigrated_album_recommendation_model(self):
        """Test UnmigratedAlbumRecommendation model."""
        recommendation = UnmigratedAlbumRecommendation(
            album_name="Failed Album",
            current_path="/current/path",
            recommended_type=AlbumType.LIVE,
            recommended_path="/recommended/path",
            confidence_score=0.85,
            reason="Permission denied during migration"
        )
        
        assert recommendation.album_name == "Failed Album"
        assert recommendation.recommended_type == AlbumType.LIVE
        assert recommendation.confidence_score == 0.85
    
    def test_migration_history_entry_model(self):
        """Test MigrationHistoryEntry model."""
        entry = MigrationHistoryEntry(
            migration_id="test_migration_123",
            timestamp="2025-01-31T10:00:00",
            band_name="Test Band",
            migration_type=MigrationType.DEFAULT_TO_ENHANCED,
            status=MigrationStatus.COMPLETED,
            albums_migrated=5,
            duration_seconds=30.0,
            success_rate=100.0
        )
        
        assert entry.migration_id == "test_migration_123"
        assert entry.band_name == "Test Band"
        assert entry.migration_type == MigrationType.DEFAULT_TO_ENHANCED
        assert entry.status == MigrationStatus.COMPLETED


class TestGlobalMigrationAnalytics:
    """Test global migration analytics instance."""
    
    def test_global_instance_exists(self):
        """Test that global migration analytics instance exists."""
        assert migration_analytics is not None
        assert isinstance(migration_analytics, MigrationAnalytics)
    
    def test_global_instance_methods(self):
        """Test global instance methods work."""
        # Should not raise errors
        history = migration_analytics.get_migration_history()
        stats = migration_analytics.get_migration_statistics()
        
        assert isinstance(history, list)
        assert isinstance(stats, dict)
        assert "total_migrations" in stats


if __name__ == "__main__":
    pytest.main([__file__]) 