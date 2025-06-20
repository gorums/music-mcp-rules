#!/usr/bin/env python3
"""
Tests for Band Structure Migration System

This module tests the comprehensive migration functionality for band folder organization patterns,
including dry-run mode, backup/rollback functionality, and progress tracking.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from src.models.migration import (
    BandStructureMigrator,
    MigrationType,
    MigrationStatus,
    MigrationResult,
    AlbumMigrationOperation,
    MigrationBackup
)
from src.models.band import AlbumType
from src.models.band_structure import StructureType


class TestBandStructureMigrator:
    """Test the BandStructureMigrator class."""
    
    def setup_method(self):
        """Set up test environment."""
        self.migrator = BandStructureMigrator()
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

    def test_migrator_initialization(self):
        """Test migrator initialization."""
        assert self.migrator is not None
        assert self.migrator.parser is not None
        assert self.migrator.detector is not None
        assert self.migrator.progress_callback is None

    def test_set_progress_callback(self):
        """Test setting progress callback."""
        callback = Mock()
        self.migrator.set_progress_callback(callback)
        assert self.migrator.progress_callback == callback

    def test_resolve_folder_conflicts_no_conflict(self):
        """Test folder conflict resolution when no conflict exists."""
        band_path = self._create_test_band_structure()
        target_path = band_path / "New Album"
        
        resolved_path = self.migrator._resolve_folder_conflicts(target_path)
        assert resolved_path == target_path

    def test_resolve_folder_conflicts_with_conflict(self):
        """Test folder conflict resolution when conflict exists."""
        band_path = self._create_test_band_structure()
        existing_album = band_path / "2010 - First Album"
        
        resolved_path = self.migrator._resolve_folder_conflicts(existing_album)
        assert resolved_path == band_path / "2010 - First Album (Conflict 1)"

    def test_resolve_folder_conflicts_with_edition(self):
        """Test folder conflict resolution with edition information."""
        band_path = self._create_test_band_structure()
        existing_album = band_path / "2012 - Second Album (Deluxe Edition)"
        
        resolved_path = self.migrator._resolve_folder_conflicts(existing_album)
        expected = band_path / "2012 - Second Album (Conflict 1) (Deluxe Edition)"
        assert resolved_path == expected

    def test_safe_move_with_permissions(self):
        """Test safe move operation with permission preservation."""
        band_path = self._create_test_band_structure()
        source = band_path / "2010 - First Album"
        target = band_path / "Album" / "2010 - First Album"
        
        # Create target directory
        target.parent.mkdir(parents=True, exist_ok=True)
        
        # Perform move
        self.migrator._safe_move_with_permissions(source, target)
        
        # Verify move
        assert not source.exists()
        assert target.exists()
        assert (target / "track1.mp3").exists()
        assert (target / "track2.mp3").exists()

    def test_safe_copy_with_permissions(self):
        """Test safe copy operation with permission preservation."""
        band_path = self._create_test_band_structure()
        source = band_path / "2010 - First Album"
        target = band_path / "Album" / "2010 - First Album Copy"
        
        # Create target directory
        target.parent.mkdir(parents=True, exist_ok=True)
        
        # Perform copy
        self.migrator._safe_copy_with_permissions(source, target)
        
        # Verify copy
        assert source.exists()
        assert target.exists()
        assert (target / "track1.mp3").exists()
        assert (target / "track2.mp3").exists()

    def test_format_album_name_for_enhanced(self):
        """Test album name formatting for enhanced structure."""
        parsed = {
            'year': '2010',
            'album_name': 'Test Album',
            'edition': 'Deluxe Edition'
        }
        
        result = self.migrator._format_album_name_for_enhanced(parsed)
        assert result == "2010 - Test Album (Deluxe Edition)"

    def test_format_album_name_for_enhanced_no_edition(self):
        """Test album name formatting for enhanced structure without edition."""
        parsed = {
            'year': '2010',
            'album_name': 'Test Album',
            'edition': ''
        }
        
        result = self.migrator._format_album_name_for_enhanced(parsed)
        assert result == "2010 - Test Album"

    def test_format_album_name_for_default(self):
        """Test album name formatting for default structure."""
        parsed = {
            'year': '2010',
            'album_name': 'Test Album',
            'edition': 'Deluxe Edition'
        }
        
        result = self.migrator._format_album_name_for_default(parsed)
        assert result == "2010 - Test Album (Deluxe Edition)"

    def test_format_album_name_for_default_no_year(self):
        """Test album name formatting for default structure without year."""
        from datetime import datetime
        current_year = str(datetime.now().year)
        
        parsed = {
            'year': '',
            'album_name': 'Test Album',
            'edition': ''
        }
        
        result = self.migrator._format_album_name_for_default(parsed)
        assert result == f"{current_year} - Test Album"

    def test_generate_target_path_default_to_enhanced(self):
        """Test target path generation for default to enhanced migration."""
        band_path = self._create_test_band_structure()
        album_folder = band_path / "2010 - First Album"
        
        parsed = {
            'year': '2010',
            'album_name': 'First Album',
            'edition': ''
        }
        
        target_path = self.migrator._generate_target_path(
            band_path, album_folder, MigrationType.DEFAULT_TO_ENHANCED, 
            AlbumType.ALBUM, parsed
        )
        
        expected = band_path / "Album" / "2010 - First Album"
        assert target_path == expected

    def test_generate_target_path_legacy_to_default(self):
        """Test target path generation for legacy to default migration."""
        band_path = self._create_test_band_structure("legacy")
        album_folder = band_path / "First Album"
        
        parsed = {
            'year': '',
            'album_name': 'First Album',
            'edition': ''
        }
        
        target_path = self.migrator._generate_target_path(
            band_path, album_folder, MigrationType.LEGACY_TO_DEFAULT, 
            AlbumType.ALBUM, parsed
        )
        
        # Should add current year
        from datetime import datetime
        current_year = str(datetime.now().year)
        expected = band_path / f"{current_year} - First Album"
        assert target_path == expected

    @patch('src.models.migration.BandStructureMigrator._get_band_info')
    def test_migrate_band_structure_dry_run(self, mock_get_band_info):
        """Test migration in dry-run mode."""
        band_path = self._create_test_band_structure()
        
        # Mock band info
        mock_get_band_info.return_value = {
            'band_name': 'Test Band',
            'folder_path': str(band_path)
        }
        
        # Mock structure detection
        with patch.object(self.migrator.detector, 'detect_band_structure') as mock_detect:
            mock_structure = Mock()
            mock_structure.structure_type = StructureType.DEFAULT
            mock_detect.return_value = mock_structure
            
            # Perform dry run migration
            result = self.migrator.migrate_band_structure(
                band_name="Test Band",
                migration_type=MigrationType.DEFAULT_TO_ENHANCED,
                dry_run=True
            )
        
        # Verify dry run results
        assert result.status == MigrationStatus.COMPLETED
        assert result.dry_run is True
        assert len(result.operations) > 0
        assert result.backup_info is None
        
        # Verify no actual changes were made
        assert (band_path / "2010 - First Album").exists()
        assert not (band_path / "Album").exists()

    def test_create_backup(self):
        """Test backup creation functionality."""
        band_path = self._create_test_band_structure()
        
        # Mock structure
        mock_structure = Mock()
        mock_structure.structure_type = StructureType.DEFAULT
        
        # Create some test operations
        operations = [
            AlbumMigrationOperation(
                album_name="First Album",
                source_path=str(band_path / "2010 - First Album"),
                target_path=str(band_path / "Album" / "2010 - First Album"),
                album_type=AlbumType.ALBUM,
                operation_type="move"
            )
        ]
        
        # Create metadata file
        metadata_file = band_path / ".band_metadata.json"
        metadata_file.write_text('{"band_name": "Test Band"}')
        
        # Create backup
        backup = self.migrator._create_backup(band_path, mock_structure, operations)
        
        # Verify backup
        assert backup is not None
        assert backup.band_name == "Test Band"
        assert backup.original_structure_type == StructureType.DEFAULT
        assert len(backup.operations) == 1
        
        backup_path = Path(backup.backup_folder_path)
        assert backup_path.exists()
        assert (backup_path / "Test Band").exists()
        assert backup.metadata_backup_path is not None


class TestMigrationIntegration:
    """Integration tests for migration functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_migration_operation_execution(self):
        """Test execution of migration operation."""
        migrator = BandStructureMigrator()
        
        # Create test structure
        band_path = self.temp_dir / "Test Band"
        band_path.mkdir(parents=True)
        source_album = band_path / "2010 - Test Album"
        source_album.mkdir()
        (source_album / "track1.mp3").touch()
        
        # Create operation
        operation = AlbumMigrationOperation(
            album_name="Test Album",
            source_path=str(source_album),
            target_path=str(band_path / "Album" / "2010 - Test Album"),
            album_type=AlbumType.ALBUM,
            operation_type="move"
        )
        
        # Execute operation
        migrator._execute_migration_operation(operation)
        
        # Verify operation
        assert not source_album.exists()
        target_path = Path(operation.target_path)
        assert target_path.exists()
        assert (target_path / "track1.mp3").exists()


class TestMigrationEdgeCases:
    """Test edge cases for migration functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.migrator = BandStructureMigrator()
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_migrate_same_source_and_target(self):
        """Test migration when source and target paths are the same."""
        band_path = self.temp_dir / "Test Band"
        band_path.mkdir(parents=True)
        album_path = band_path / "2010 - Test Album"
        album_path.mkdir()
        
        operation = AlbumMigrationOperation(
            album_name="Test Album",
            source_path=str(album_path),
            target_path=str(album_path),  # Same path
            album_type=AlbumType.ALBUM,
            operation_type="move"
        )
        
        # Should not raise an error and should do nothing
        self.migrator._execute_migration_operation(operation)
        assert album_path.exists()

    def test_preserve_folder_attributes_error_handling(self):
        """Test error handling in folder attribute preservation."""
        # Create a test folder
        test_folder = self.temp_dir / "test_folder"
        test_folder.mkdir()
        
        # Mock stat object with proper numeric attributes for os.utime
        mock_stat = Mock()
        mock_stat.st_atime = 1234567890.0  # Mock timestamp as float
        mock_stat.st_mtime = 1234567890.0  # Mock timestamp as float
        
        # Test case 1: Missing st_mode attribute
        if hasattr(mock_stat, 'st_mode'):
            delattr(mock_stat, 'st_mode')
        
        # Should not raise an error
        self.migrator._preserve_folder_attributes(test_folder, mock_stat)
        
        # Test case 2: Invalid st_mode value
        mock_stat.st_mode = "invalid"  # Non-integer value
        
        # Should not raise an error
        self.migrator._preserve_folder_attributes(test_folder, mock_stat)
        
        # Folder should still exist
        assert test_folder.exists()

    def test_conflict_resolution_max_conflicts(self):
        """Test conflict resolution with maximum conflicts."""
        band_path = self.temp_dir / "Test Band"
        band_path.mkdir(parents=True)
        
        # Create a folder
        base_folder = band_path / "Test Album"
        base_folder.mkdir()
        
        # Mock the exists method to always return True
        with patch.object(Path, 'exists', return_value=True):
            with pytest.raises(ValueError, match="Too many conflicts"):
                self.migrator._resolve_folder_conflicts(base_folder) 