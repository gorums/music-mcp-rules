#!/usr/bin/env python3
"""
Tests for Migration Validation and Safety Components

This module tests the comprehensive migration validation functionality including:
- Source structure validation
- Type folder conflict detection  
- Album type assignment verification
- Destination path validation
- Disk space checking
- File permissions validation
- Migration conflict detection
- Prerequisites validation
- Comprehensive validation orchestration
- Atomic operations safety
- Integrity checks
"""

import pytest
import tempfile
import shutil
import os
import stat
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.models.migration import (
    MigrationValidator,
    MigrationSafetyManager,
    MigrationIntegrityChecker,
    MigrationType,
    MigrationStatus,
    ValidationSeverity,
    ValidationIssue,
    MigrationValidationResult,
    AlbumMigrationOperation,
    MigrationLogEntry,
    MigrationLog,
    MigrationIntegrityCheck
)
from src.models.band import AlbumType
from src.models.band_structure import StructureType


class TestMigrationValidator:
    """Test the MigrationValidator class for comprehensive validation."""
    
    def setup_method(self):
        """Set up test environment."""
        self.validator = MigrationValidator()
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def _create_test_band_structure(self, structure_type: str = "default"):
        """Create a test band folder structure."""
        band_path = self.temp_dir / "Test Band"
        band_path.mkdir(parents=True, exist_ok=True)
        
        if structure_type == "default":
            # Default structure: Band/YYYY - Album Name (Edition?)
            (band_path / "2010 - First Album").mkdir()
            (band_path / "2012 - Second Album (Deluxe Edition)").mkdir()
            (band_path / "2015 - Live Concert (Live)").mkdir()
            
        elif structure_type == "legacy":
            # Legacy structure: Band/Album Name
            (band_path / "First Album").mkdir()
            (band_path / "Second Album").mkdir()
            (band_path / "Live Concert").mkdir()
            
        elif structure_type == "enhanced":
            # Enhanced structure: Band/Type/YYYY - Album Name (Edition?)
            album_dir = band_path / "Album"
            album_dir.mkdir()
            (album_dir / "2010 - First Album").mkdir()
            (album_dir / "2012 - Second Album (Deluxe Edition)").mkdir()
            
            live_dir = band_path / "Live"
            live_dir.mkdir()
            (live_dir / "2015 - Live Concert (Live)").mkdir()
        
        # Add some test files to albums
        for album_folder in band_path.rglob("*"):
            if album_folder.is_dir() and album_folder.parent != self.temp_dir:
                (album_folder / "track1.mp3").touch()
                (album_folder / "track2.mp3").touch()
        
        return band_path

    def _create_test_operations(self, band_path: Path) -> list[AlbumMigrationOperation]:
        """Create test migration operations."""
        return [
            AlbumMigrationOperation(
                album_name="First Album",
                source_path=str(band_path / "2010 - First Album"),
                target_path=str(band_path / "Album" / "2010 - First Album"),
                album_type=AlbumType.ALBUM,
                operation_type="move"
            ),
            AlbumMigrationOperation(
                album_name="Live Concert",
                source_path=str(band_path / "2015 - Live Concert (Live)"),
                target_path=str(band_path / "Live" / "2015 - Live Concert"),
                album_type=AlbumType.LIVE,
                operation_type="move"
            )
        ]

    def test_validator_initialization(self):
        """Test validator initialization."""
        assert self.validator is not None
        assert self.validator.detector is not None
        assert self.validator.parser is not None

    def test_validate_source_structure_success(self):
        """Test successful source structure validation."""
        band_path = self._create_test_band_structure("default")
        
        result = self.validator.validate_source_structure(band_path, MigrationType.DEFAULT_TO_ENHANCED)
        
        assert result.is_valid
        assert result.critical_count == 0
        assert result.errors_count == 0

    def test_validate_source_structure_nonexistent_folder(self):
        """Test source structure validation with nonexistent folder."""
        nonexistent_path = self.temp_dir / "NonexistentBand"
        
        result = self.validator.validate_source_structure(nonexistent_path, MigrationType.DEFAULT_TO_ENHANCED)
        
        assert not result.is_valid
        assert result.critical_count == 1
        assert "does not exist" in result.issues[0].message

    @patch('os.access')
    def test_validate_source_structure_permission_denied(self, mock_access):
        """Test source structure validation with permission denied."""
        band_path = self._create_test_band_structure("default")
        mock_access.return_value = False
        
        result = self.validator.validate_source_structure(band_path, MigrationType.DEFAULT_TO_ENHANCED)
        
        assert not result.is_valid
        assert result.critical_count == 1
        assert "Insufficient permissions" in result.issues[0].message

    def test_validate_source_structure_inappropriate_migration(self):
        """Test source structure validation with inappropriate migration type."""
        band_path = self._create_test_band_structure("enhanced")
        
        result = self.validator.validate_source_structure(band_path, MigrationType.LEGACY_TO_DEFAULT)
        
        assert not result.is_valid
        assert result.errors_count >= 1
        assert "not appropriate for current structure" in result.issues[0].message

    def test_check_existing_type_folders_no_conflicts(self):
        """Test existing type folders check with no conflicts."""
        band_path = self._create_test_band_structure("default")
        
        result = self.validator.check_existing_type_folders(band_path, MigrationType.DEFAULT_TO_ENHANCED)
        
        assert result.is_valid
        assert result.warnings_count == 0

    def test_check_existing_type_folders_with_conflicts(self):
        """Test existing type folders check with conflicts."""
        band_path = self._create_test_band_structure("enhanced")
        
        result = self.validator.check_existing_type_folders(band_path, MigrationType.DEFAULT_TO_ENHANCED)
        
        assert result.is_valid
        # Should have info about existing type folders
        assert any("existing type folders" in issue.message for issue in result.issues)

    def test_check_existing_type_folders_permission_error(self):
        """Test existing type folders check with permission errors."""
        band_path = self._create_test_band_structure("default")
        type_folder = band_path / "Album"
        type_folder.mkdir()
        
        # Create a file that we can't access
        protected_file = type_folder / "protected"
        protected_file.touch()
        
        # Make directory unreadable (on systems that support it)
        if os.name != 'nt':  # Skip on Windows due to different permission model
            os.chmod(type_folder, 0o000)
            
            result = self.validator.check_existing_type_folders(band_path, MigrationType.DEFAULT_TO_ENHANCED)
            
            # Should have permission error
            assert any("Permission denied" in issue.message for issue in result.issues)
            
            # Restore permissions for cleanup
            os.chmod(type_folder, 0o755)

    def test_verify_album_type_assignments_success(self):
        """Test successful album type assignment verification."""
        band_path = self._create_test_band_structure("default")
        operations = self._create_test_operations(band_path)
        
        result = self.validator.verify_album_type_assignments(operations)
        
        assert result.is_valid
        assert result.errors_count == 0

    def test_verify_album_type_assignments_invalid_type(self):
        """Test album type assignment verification with invalid type."""
        band_path = self._create_test_band_structure("default")
        
        # Create operation with valid AlbumType first, then manually modify to test validation
        operation = AlbumMigrationOperation(
            album_name="Invalid Album",
            source_path=str(band_path / "2010 - First Album"),
            target_path=str(band_path / "Invalid" / "2010 - First Album"),
            album_type=AlbumType.ALBUM,  # Valid initially
            operation_type="move"
        )
        
        # Manually set invalid type to bypass Pydantic validation
        operation.__dict__['album_type'] = "InvalidType"
        
        result = self.validator.verify_album_type_assignments([operation])
        
        assert not result.is_valid
        assert result.errors_count == 1
        assert "Invalid album type" in result.issues[0].message

    def test_verify_album_type_assignments_type_mismatch(self):
        """Test album type assignment verification with type mismatch."""
        band_path = self._create_test_band_structure("default")
        operations = [
            AlbumMigrationOperation(
                album_name="Live Concert",
                source_path=str(band_path / "2015 - Live Concert (Live)"),
                target_path=str(band_path / "Album" / "2015 - Live Concert"),
                album_type=AlbumType.ALBUM,  # Mismatch: should be LIVE
                operation_type="move"
            )
        ]
        
        result = self.validator.verify_album_type_assignments(operations)
        
        # Should have warning about type mismatch
        assert any("differs from detected type" in issue.message for issue in result.issues)

    def test_validate_destination_paths_success(self):
        """Test successful destination path validation."""
        band_path = self._create_test_band_structure("default")
        operations = self._create_test_operations(band_path)
        
        result = self.validator.validate_destination_paths(operations, band_path)
        
        assert result.is_valid
        assert result.errors_count == 0

    def test_validate_destination_paths_duplicate_targets(self):
        """Test destination path validation with duplicate targets."""
        band_path = self._create_test_band_structure("default")
        operations = [
            AlbumMigrationOperation(
                album_name="Album 1",
                source_path=str(band_path / "2010 - First Album"),
                target_path=str(band_path / "Album" / "Same Target"),
                album_type=AlbumType.ALBUM,
                operation_type="move"
            ),
            AlbumMigrationOperation(
                album_name="Album 2",
                source_path=str(band_path / "2012 - Second Album"),
                target_path=str(band_path / "Album" / "Same Target"),  # Duplicate
                album_type=AlbumType.ALBUM,
                operation_type="move"
            )
        ]
        
        result = self.validator.validate_destination_paths(operations, band_path)
        
        assert not result.is_valid
        assert result.errors_count >= 1
        assert "Duplicate target path" in result.issues[0].message

    def test_validate_destination_paths_existing_target(self):
        """Test destination path validation with existing target."""
        band_path = self._create_test_band_structure("enhanced")
        existing_target = band_path / "Album" / "2010 - First Album"
        
        operations = [
            AlbumMigrationOperation(
                album_name="New Album",
                source_path=str(band_path / "2020 - New Album"),
                target_path=str(existing_target),  # Already exists
                album_type=AlbumType.ALBUM,
                operation_type="move"
            )
        ]
        
        result = self.validator.validate_destination_paths(operations, band_path)
        
        # Should have warning about existing target
        assert any("already exists" in issue.message for issue in result.issues)

    def test_check_disk_space_sufficient(self):
        """Test disk space check with sufficient space."""
        band_path = self._create_test_band_structure("default")
        operations = self._create_test_operations(band_path)
        
        result = self.validator.check_disk_space(operations, band_path)
        
        assert result.is_valid
        assert result.critical_count == 0

    @patch('shutil.disk_usage')
    def test_check_disk_space_insufficient(self, mock_disk_usage):
        """Test disk space check with insufficient space."""
        band_path = self._create_test_band_structure("default")
        operations = [
            AlbumMigrationOperation(
                album_name="Large Album",
                source_path=str(band_path / "2010 - First Album"),
                target_path=str(band_path / "Album" / "2010 - First Album"),
                album_type=AlbumType.ALBUM,
                operation_type="copy"  # Copy requires additional space
            )
        ]
        
        # Mock very small available space
        mock_disk_usage.return_value = Mock(free=1024)  # 1KB available
        
        result = self.validator.check_disk_space(operations, band_path)
        
        assert not result.is_valid
        assert result.critical_count >= 1
        assert "Insufficient disk space" in result.issues[0].message

    def test_validate_file_permissions_success(self):
        """Test successful file permissions validation."""
        band_path = self._create_test_band_structure("default")
        operations = self._create_test_operations(band_path)
        
        result = self.validator.validate_file_permissions(operations)
        
        assert result.is_valid
        assert result.critical_count == 0

    @patch('os.access')
    def test_validate_file_permissions_no_read_permission(self, mock_access):
        """Test file permissions validation with no read permission."""
        band_path = self._create_test_band_structure("default")
        operations = self._create_test_operations(band_path)
        
        # Mock no read permission
        def mock_access_func(path, mode):
            if mode == os.R_OK:
                return False
            return True
        
        mock_access.side_effect = mock_access_func
        
        result = self.validator.validate_file_permissions(operations)
        
        assert not result.is_valid
        assert result.critical_count >= 1
        assert "No read permission" in result.issues[0].message

    @patch('os.access')
    def test_validate_file_permissions_no_write_permission(self, mock_access):
        """Test file permissions validation with no write permission."""
        band_path = self._create_test_band_structure("default")
        operations = self._create_test_operations(band_path)
        
        # Mock no write permission
        def mock_access_func(path, mode):
            if mode == os.W_OK:
                return False
            return True
        
        mock_access.side_effect = mock_access_func
        
        result = self.validator.validate_file_permissions(operations)
        
        assert not result.is_valid
        assert result.critical_count >= 1
        assert any("No write permission" in issue.message for issue in result.issues)

    def test_check_migration_conflicts_no_conflicts(self):
        """Test migration conflicts check with no conflicts."""
        band_path = self._create_test_band_structure("default")
        operations = self._create_test_operations(band_path)
        
        result = self.validator.check_migration_conflicts(operations)
        
        assert result.is_valid
        assert result.errors_count == 0

    def test_check_migration_conflicts_target_conflict(self):
        """Test migration conflicts check with target path conflicts."""
        band_path = self._create_test_band_structure("default")
        operations = [
            AlbumMigrationOperation(
                album_name="Album 1",
                source_path=str(band_path / "2010 - First Album"),
                target_path=str(band_path / "Album" / "Same Target"),
                album_type=AlbumType.ALBUM,
                operation_type="move"
            ),
            AlbumMigrationOperation(
                album_name="Album 2",
                source_path=str(band_path / "2012 - Second Album"),
                target_path=str(band_path / "Album" / "Same Target"),  # Conflict
                album_type=AlbumType.ALBUM,
                operation_type="move"
            )
        ]
        
        result = self.validator.check_migration_conflicts(operations)
        
        assert not result.is_valid
        assert result.errors_count >= 1
        assert "Target path conflict" in result.issues[0].message

    def test_check_migration_conflicts_source_duplicate(self):
        """Test migration conflicts check with duplicate source paths."""
        band_path = self._create_test_band_structure("default")
        operations = [
            AlbumMigrationOperation(
                album_name="Album 1",
                source_path=str(band_path / "2010 - First Album"),
                target_path=str(band_path / "Album" / "Target 1"),
                album_type=AlbumType.ALBUM,
                operation_type="move"
            ),
            AlbumMigrationOperation(
                album_name="Album 2",
                source_path=str(band_path / "2010 - First Album"),  # Duplicate
                target_path=str(band_path / "Album" / "Target 2"),
                album_type=AlbumType.ALBUM,
                operation_type="move"
            )
        ]
        
        result = self.validator.check_migration_conflicts(operations)
        
        assert not result.is_valid
        assert result.errors_count >= 1
        assert "Duplicate source path" in result.issues[0].message

    def test_validate_migration_prerequisites_success(self):
        """Test successful migration prerequisites validation."""
        band_path = self._create_test_band_structure("default")
        
        result = self.validator.validate_migration_prerequisites(band_path, MigrationType.DEFAULT_TO_ENHANCED)
        
        assert result.is_valid
        assert result.warnings_count == 0

    def test_validate_migration_prerequisites_no_albums(self):
        """Test migration prerequisites validation with no albums."""
        empty_band_path = self.temp_dir / "EmptyBand"
        empty_band_path.mkdir()
        
        result = self.validator.validate_migration_prerequisites(empty_band_path, MigrationType.DEFAULT_TO_ENHANCED)
        
        assert result.warnings_count >= 1
        assert "No album folders found" in result.issues[0].message

    def test_validate_migration_prerequisites_no_valid_albums(self):
        """Test migration prerequisites validation with no valid albums."""
        band_path = self.temp_dir / "InvalidBand"
        band_path.mkdir()
        # Create folders that don't match album patterns
        (band_path / "not_an_album").mkdir()
        (band_path / "also_not_album").mkdir()
        
        result = self.validator.validate_migration_prerequisites(band_path, MigrationType.DEFAULT_TO_ENHANCED)
        
        assert result.warnings_count >= 1
        assert any("No albums with valid naming patterns" in issue.message for issue in result.issues)

    def test_validate_migration_prerequisites_legacy_migration(self):
        """Test migration prerequisites validation for legacy migration."""
        band_path = self._create_test_band_structure("default")  # All have year prefixes
        
        result = self.validator.validate_migration_prerequisites(band_path, MigrationType.LEGACY_TO_DEFAULT)
        
        # Should have info that no legacy albums found
        assert any("No legacy albums" in issue.message for issue in result.issues)

    def test_perform_comprehensive_validation_success(self):
        """Test comprehensive validation with all checks passing."""
        band_path = self._create_test_band_structure("default")
        operations = self._create_test_operations(band_path)
        
        result = self.validator.perform_comprehensive_validation(
            band_path, MigrationType.DEFAULT_TO_ENHANCED, operations, force=False, dry_run=False
        )
        
        assert result.is_valid
        assert result.critical_count == 0

    def test_perform_comprehensive_validation_with_force(self):
        """Test comprehensive validation with force flag."""
        band_path = self._create_test_band_structure("default")
        operations = self._create_test_operations(band_path)
        
        result = self.validator.perform_comprehensive_validation(
            band_path, MigrationType.DEFAULT_TO_ENHANCED, operations, force=True, dry_run=False
        )
        
        # Force should allow validation to pass even with warnings
        assert result.is_valid or result.critical_count == 0

    def test_perform_comprehensive_validation_dry_run(self):
        """Test comprehensive validation in dry run mode."""
        band_path = self._create_test_band_structure("default")
        operations = self._create_test_operations(band_path)
        
        result = self.validator.perform_comprehensive_validation(
            band_path, MigrationType.DEFAULT_TO_ENHANCED, operations, force=False, dry_run=True
        )
        
        # Dry run should skip some validations
        assert isinstance(result, MigrationValidationResult)


class TestMigrationSafetyManager:
    """Test the MigrationSafetyManager class for atomic operations."""
    
    def setup_method(self):
        """Set up test environment."""
        self.safety_manager = MigrationSafetyManager()
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        self.safety_manager.cleanup_temp_directory()

    def _create_test_operation(self) -> AlbumMigrationOperation:
        """Create a test migration operation."""
        source_path = self.temp_dir / "source" / "Test Album"
        source_path.mkdir(parents=True)
        (source_path / "track1.mp3").touch()
        
        return AlbumMigrationOperation(
            album_name="Test Album",
            source_path=str(source_path),
            target_path=str(self.temp_dir / "target" / "Test Album"),
            album_type=AlbumType.ALBUM,
            operation_type="move"
        )

    def test_safety_manager_initialization(self):
        """Test safety manager initialization."""
        assert self.safety_manager is not None
        assert len(self.safety_manager.operation_locks) == 0
        assert len(self.safety_manager.active_operations) == 0

    def test_begin_atomic_operation_success(self):
        """Test successful atomic operation start."""
        operation = self._create_test_operation()
        
        result = self.safety_manager.begin_atomic_operation(operation)
        
        assert result is True
        assert operation.album_name in self.safety_manager.operation_locks
        assert operation in self.safety_manager.active_operations

    def test_begin_atomic_operation_already_locked(self):
        """Test atomic operation start when already locked."""
        operation = self._create_test_operation()
        
        # First operation should succeed
        result1 = self.safety_manager.begin_atomic_operation(operation)
        assert result1 is True
        
        # Second operation with same album should fail
        result2 = self.safety_manager.begin_atomic_operation(operation)
        assert result2 is False

    def test_commit_atomic_operation_success(self):
        """Test successful atomic operation commit."""
        operation = self._create_test_operation()
        
        # Begin operation
        assert self.safety_manager.begin_atomic_operation(operation)
        
        # Commit operation
        result = self.safety_manager.commit_atomic_operation(operation)
        
        assert result is True
        assert operation.album_name not in self.safety_manager.operation_locks
        assert operation not in self.safety_manager.active_operations

    def test_commit_atomic_operation_not_started(self):
        """Test atomic operation commit when not started."""
        operation = self._create_test_operation()
        
        result = self.safety_manager.commit_atomic_operation(operation)
        
        assert result is True  # Operation not started, consider success

    def test_rollback_operation_success(self):
        """Test successful operation rollback."""
        operation = self._create_test_operation()
        
        # Begin operation
        assert self.safety_manager.begin_atomic_operation(operation)
        
        # Simulate partial move by creating target and removing source
        target_path = Path(operation.target_path)
        target_path.mkdir(parents=True)
        source_path = Path(operation.source_path)
        
        # Rollback operation
        result = self.safety_manager.rollback_operation(operation)
        
        assert result is True

    def test_rollback_all_operations(self):
        """Test rollback of all operations."""
        operations = [self._create_test_operation()]
        
        for op in operations:
            self.safety_manager.begin_atomic_operation(op)
        
        count = self.safety_manager.rollback_all_operations()
        
        assert count == len(operations)
        assert len(self.safety_manager.active_operations) == 0

    def test_acquire_operation_lock_success(self):
        """Test successful operation lock acquisition."""
        result = self.safety_manager.acquire_operation_lock("Test Album")
        
        assert result is True
        assert "Test Album" in self.safety_manager.operation_locks

    def test_acquire_operation_lock_already_locked(self):
        """Test operation lock acquisition when already locked."""
        # First lock should succeed
        result1 = self.safety_manager.acquire_operation_lock("Test Album")
        assert result1 is True
        
        # Second lock should fail
        result2 = self.safety_manager.acquire_operation_lock("Test Album")
        assert result2 is False

    def test_release_operation_lock(self):
        """Test operation lock release."""
        # Acquire lock
        assert self.safety_manager.acquire_operation_lock("Test Album")
        
        # Release lock
        self.safety_manager.release_operation_lock("Test Album")
        
        assert "Test Album" not in self.safety_manager.operation_locks

    def test_validate_operation_safety_success(self):
        """Test successful operation safety validation."""
        operation = self._create_test_operation()
        
        issues = self.safety_manager.validate_operation_safety(operation)
        
        assert len(issues) == 0

    def test_validate_operation_safety_source_not_exists(self):
        """Test operation safety validation with nonexistent source."""
        operation = AlbumMigrationOperation(
            album_name="Nonexistent Album",
            source_path=str(self.temp_dir / "nonexistent" / "album"),
            target_path=str(self.temp_dir / "target" / "album"),
            album_type=AlbumType.ALBUM,
            operation_type="move"
        )
        
        issues = self.safety_manager.validate_operation_safety(operation)
        
        assert len(issues) > 0
        assert "does not exist" in issues[0]

    def test_create_safe_temp_directory(self):
        """Test safe temporary directory creation."""
        temp_dir = self.safety_manager.create_safe_temp_directory(self.temp_dir)
        
        assert temp_dir is not None
        assert temp_dir.exists()
        assert temp_dir.is_dir()
        assert ".migration_temp" in str(temp_dir.parent)

    def test_cleanup_temp_directory(self):
        """Test temporary directory cleanup."""
        temp_dir = self.safety_manager.create_safe_temp_directory(self.temp_dir)
        assert temp_dir.exists()
        
        self.safety_manager.cleanup_temp_directory()
        
        assert not temp_dir.exists()


class TestMigrationIntegrityChecker:
    """Test the MigrationIntegrityChecker class for post-migration verification."""
    
    def setup_method(self):
        """Set up test environment."""
        self.integrity_checker = MigrationIntegrityChecker()
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def _create_test_band_structure(self):
        """Create a test band folder structure."""
        band_path = self.temp_dir / "Test Band"
        band_path.mkdir(parents=True, exist_ok=True)
        
        # Create enhanced structure
        album_dir = band_path / "Album"
        album_dir.mkdir()
        album1 = album_dir / "2010 - First Album"
        album1.mkdir()
        (album1 / "track1.mp3").touch()
        (album1 / "track2.mp3").touch()
        
        live_dir = band_path / "Live"
        live_dir.mkdir()
        live_album = live_dir / "2015 - Live Concert"
        live_album.mkdir()
        (live_album / "live1.mp3").touch()
        
        return band_path

    def _create_test_operations(self, band_path: Path) -> list[AlbumMigrationOperation]:
        """Create test migration operations."""
        return [
            AlbumMigrationOperation(
                album_name="First Album",
                source_path=str(band_path / "2010 - First Album"),
                target_path=str(band_path / "Album" / "2010 - First Album"),
                album_type=AlbumType.ALBUM,
                operation_type="move",
                completed=True
            ),
            AlbumMigrationOperation(
                album_name="Live Concert",
                source_path=str(band_path / "2015 - Live Concert"),
                target_path=str(band_path / "Live" / "2015 - Live Concert"),
                album_type=AlbumType.LIVE,
                operation_type="move",
                completed=True
            )
        ]

    def test_integrity_checker_initialization(self):
        """Test integrity checker initialization."""
        assert self.integrity_checker is not None

    def test_perform_integrity_check_success(self):
        """Test successful integrity check."""
        band_path = self._create_test_band_structure()
        operations = self._create_test_operations(band_path)
        
        result = self.integrity_checker.perform_integrity_check(operations, band_path)
        
        assert result.passed
        assert result.albums_verified == len(operations)
        assert result.files_missing == 0
        assert result.permission_issues == 0

    def test_perform_integrity_check_missing_files(self):
        """Test integrity check with missing files."""
        band_path = self._create_test_band_structure()
        operations = self._create_test_operations(band_path)
        
        # Mark operations as completed to trigger verification
        for op in operations:
            op.completed = True
        
        # Remove all files from the target directory to simulate migration failure
        target_path = Path(operations[0].target_path)
        if target_path.exists():
            for file in target_path.iterdir():
                if file.is_file():
                    file.unlink()
        else:
            target_path.mkdir(parents=True, exist_ok=True)
        
        result = self.integrity_checker.perform_integrity_check(operations, band_path)
        
        assert not result.passed
        assert result.files_missing > 0 or len(result.issues) > 0

    def test_perform_integrity_check_missing_albums(self):
        """Test integrity check with missing albums."""
        band_path = self._create_test_band_structure()
        operations = self._create_test_operations(band_path)
        
        # Remove an album folder
        missing_album = band_path / "Live" / "2015 - Live Concert"
        if missing_album.exists():
            shutil.rmtree(missing_album)
        
        result = self.integrity_checker.perform_integrity_check(operations, band_path)
        
        assert not result.passed
        assert len(result.issues) > 0

    def test_perform_integrity_check_invalid_metadata(self):
        """Test integrity check with invalid metadata."""
        band_path = self._create_test_band_structure()
        operations = self._create_test_operations(band_path)
        
        # Create invalid metadata file
        metadata_file = band_path / ".band_metadata.json"
        metadata_file.write_text("invalid json content")
        
        result = self.integrity_checker.perform_integrity_check(operations, band_path)
        
        assert not result.metadata_consistent


class TestMigrationLogAndValidationResult:
    """Test migration logging and validation result classes."""
    
    def test_validation_issue_creation(self):
        """Test validation issue creation."""
        issue = ValidationIssue(
            severity=ValidationSeverity.ERROR,
            message="Test error message",
            album_name="Test Album",
            source_path="/source/path",
            target_path="/target/path",
            suggestion="Fix the issue"
        )
        
        assert issue.severity == ValidationSeverity.ERROR
        assert issue.message == "Test error message"
        assert issue.album_name == "Test Album"
        assert issue.suggestion == "Fix the issue"

    def test_migration_validation_result_add_issue(self):
        """Test adding issues to validation result."""
        result = MigrationValidationResult(is_valid=True)
        
        # Add critical issue
        result.add_issue(ValidationSeverity.CRITICAL, "Critical error")
        assert not result.is_valid
        assert result.critical_count == 1
        
        # Add error
        result.add_issue(ValidationSeverity.ERROR, "Error message")
        assert not result.is_valid
        assert result.errors_count == 1
        
        # Add warning
        result.add_issue(ValidationSeverity.WARNING, "Warning message")
        assert result.warnings_count == 1

    def test_migration_log_add_entry(self):
        """Test adding entries to migration log."""
        log = MigrationLog(
            migration_id="test-123",
            band_name="Test Band",
            migration_type=MigrationType.DEFAULT_TO_ENHANCED,
            start_time=datetime.now().isoformat(),
            status=MigrationStatus.IN_PROGRESS
        )
        
        log.add_entry("INFO", "MIGRATION_START", "Migration started", success=True)
        
        assert len(log.entries) == 1
        assert log.entries[0].level == "INFO"
        assert log.entries[0].operation == "MIGRATION_START"
        assert log.entries[0].success is True

    def test_migration_integrity_check_creation(self):
        """Test migration integrity check creation."""
        check = MigrationIntegrityCheck(
            passed=False,
            albums_verified=5,
            files_missing=2,
            permission_issues=1,
            folder_structure_valid=True,
            metadata_consistent=False,
            issues=["File missing", "Metadata corrupted"]
        )
        
        assert not check.passed
        assert check.albums_verified == 5
        assert check.files_missing == 2
        assert len(check.issues) == 2


class TestMigrationValidationIntegration:
    """Integration tests for migration validation components."""
    
    def setup_method(self):
        """Set up test environment."""
        self.validator = MigrationValidator()
        self.safety_manager = MigrationSafetyManager()
        self.integrity_checker = MigrationIntegrityChecker()
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        self.safety_manager.cleanup_temp_directory()

    def test_complete_validation_workflow(self):
        """Test complete validation workflow integration."""
        # Create test band structure
        band_path = self.temp_dir / "Integration Band"
        band_path.mkdir(parents=True)
        
        # Create albums
        album1 = band_path / "2010 - First Album"
        album1.mkdir()
        (album1 / "track1.mp3").touch()
        
        album2 = band_path / "2015 - Live Concert (Live)"
        album2.mkdir()
        (album2 / "live1.mp3").touch()
        
        # Plan operations
        operations = [
            AlbumMigrationOperation(
                album_name="First Album",
                source_path=str(album1),
                target_path=str(band_path / "Album" / "2010 - First Album"),
                album_type=AlbumType.ALBUM,
                operation_type="move"
            ),
            AlbumMigrationOperation(
                album_name="Live Concert",
                source_path=str(album2),
                target_path=str(band_path / "Live" / "2015 - Live Concert"),
                album_type=AlbumType.LIVE,
                operation_type="move"
            )
        ]
        
        # 1. Validate source structure
        source_result = self.validator.validate_source_structure(band_path, MigrationType.DEFAULT_TO_ENHANCED)
        assert source_result.is_valid
        
        # 2. Check existing type folders
        type_result = self.validator.check_existing_type_folders(band_path, MigrationType.DEFAULT_TO_ENHANCED)
        assert type_result.is_valid
        
        # 3. Verify album type assignments
        type_assignment_result = self.validator.verify_album_type_assignments(operations)
        assert type_assignment_result.is_valid
        
        # 4. Validate destination paths
        path_result = self.validator.validate_destination_paths(operations, band_path)
        assert path_result.is_valid
        
        # 5. Check disk space
        disk_result = self.validator.check_disk_space(operations, band_path)
        assert disk_result.is_valid
        
        # 6. Validate file permissions
        perm_result = self.validator.validate_file_permissions(operations)
        assert perm_result.is_valid
        
        # 7. Check migration conflicts
        conflict_result = self.validator.check_migration_conflicts(operations)
        assert conflict_result.is_valid
        
        # 8. Validate prerequisites
        prereq_result = self.validator.validate_migration_prerequisites(band_path, MigrationType.DEFAULT_TO_ENHANCED)
        assert prereq_result.is_valid
        
        # 9. Perform comprehensive validation
        comprehensive_result = self.validator.perform_comprehensive_validation(
            band_path, MigrationType.DEFAULT_TO_ENHANCED, operations, force=False
        )
        assert comprehensive_result.is_valid
        
        # 10. Simulate migration execution (create target structure)
        for operation in operations:
            target_path = Path(operation.target_path)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            if Path(operation.source_path).exists():
                shutil.move(operation.source_path, operation.target_path)
                operation.completed = True
        
        # 11. Perform integrity check
        integrity_result = self.integrity_checker.perform_integrity_check(operations, band_path)
        assert integrity_result.passed

    def test_validation_failure_handling(self):
        """Test validation failure handling."""
        # Create problematic band structure
        band_path = self.temp_dir / "Problem Band"
        band_path.mkdir(parents=True)
        
        # Create conflicting operations
        operations = [
            AlbumMigrationOperation(
                album_name="Album 1",
                source_path=str(band_path / "nonexistent1"),
                target_path=str(band_path / "Album" / "Same Target"),
                album_type=AlbumType.ALBUM,
                operation_type="move"
            ),
            AlbumMigrationOperation(
                album_name="Album 2",
                source_path=str(band_path / "nonexistent2"),
                target_path=str(band_path / "Album" / "Same Target"),  # Conflict
                album_type=AlbumType.ALBUM,
                operation_type="move"
            )
        ]
        
        # Comprehensive validation should fail
        result = self.validator.perform_comprehensive_validation(
            band_path, MigrationType.DEFAULT_TO_ENHANCED, operations, force=False
        )
        
        assert not result.is_valid
        assert result.errors_count > 0 or result.critical_count > 0

    def test_atomic_operations_safety(self):
        """Test atomic operations safety workflow."""
        # Create test operation
        source_path = self.temp_dir / "source" / "Test Album"
        source_path.mkdir(parents=True)
        (source_path / "track1.mp3").touch()
        
        operation = AlbumMigrationOperation(
            album_name="Test Album",
            source_path=str(source_path),
            target_path=str(self.temp_dir / "target" / "Test Album"),
            album_type=AlbumType.ALBUM,
            operation_type="move"
        )
        
        # 1. Validate operation safety
        issues = self.safety_manager.validate_operation_safety(operation)
        assert len(issues) == 0
        
        # 2. Begin atomic operation
        assert self.safety_manager.begin_atomic_operation(operation)
        
        # 3. Attempt to start same operation again (should fail)
        duplicate_operation = AlbumMigrationOperation(
            album_name="Test Album",  # Same album name should cause conflict
            source_path=str(self.temp_dir / "source2" / "Test Album"),
            target_path=str(self.temp_dir / "target2" / "Test Album"),
            album_type=AlbumType.ALBUM,
            operation_type="move"
        )
        assert not self.safety_manager.begin_atomic_operation(duplicate_operation)
        
        # 4. Commit operation
        assert self.safety_manager.commit_atomic_operation(operation)
        
        # 5. Verify operation is no longer locked
        assert operation.album_name not in self.safety_manager.operation_locks 