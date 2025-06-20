"""
Band Structure Migration System

This module provides comprehensive migration functionality for band folder organization patterns,
supporting migration between different folder structure types with rollback functionality
and progress tracking.
"""

from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from enum import Enum
import json
import shutil
import time
from datetime import datetime
from pydantic import BaseModel, Field

from .band import AlbumType, Album
from .band_structure import StructureType, BandStructureDetector
from .album_parser import AlbumFolderParser


class MigrationType(str, Enum):
    """
    Enumeration of supported migration types.
    
    Values:
        DEFAULT_TO_ENHANCED: Migrate from default flat structure to enhanced type-based structure
        LEGACY_TO_DEFAULT: Migrate from legacy (no year) to default (with year prefix)
        MIXED_TO_ENHANCED: Migrate from mixed patterns to consistent enhanced structure
        ENHANCED_TO_DEFAULT: Rollback from enhanced to default structure
    """
    DEFAULT_TO_ENHANCED = "default_to_enhanced"
    LEGACY_TO_DEFAULT = "legacy_to_default"
    MIXED_TO_ENHANCED = "mixed_to_enhanced"
    ENHANCED_TO_DEFAULT = "enhanced_to_default"


class MigrationStatus(str, Enum):
    """
    Enumeration of migration operation status.
    
    Values:
        PENDING: Migration not yet started
        IN_PROGRESS: Migration currently running
        COMPLETED: Migration completed successfully
        FAILED: Migration failed with errors
        ROLLED_BACK: Migration was rolled back due to failure
    """
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class AlbumMigrationOperation(BaseModel):
    """
    Information about a single album migration operation.
    
    Attributes:
        album_name: Name of the album being migrated
        source_path: Original folder path
        target_path: Destination folder path
        album_type: Detected or assigned album type
        operation_type: Type of operation (move, copy, rename)
        completed: Whether the operation was completed successfully
        error_message: Error message if operation failed
    """
    album_name: str = Field(description="Album name")
    source_path: str = Field(description="Source folder path")
    target_path: str = Field(description="Target folder path")
    album_type: AlbumType = Field(description="Album type")
    operation_type: str = Field(description="Operation type")
    completed: bool = Field(default=False, description="Completion status")
    error_message: Optional[str] = Field(default=None, description="Error message")


class MigrationBackup(BaseModel):
    """
    Backup information for rollback functionality.
    
    Attributes:
        timestamp: Backup creation timestamp
        band_name: Name of the band
        original_structure_type: Original folder structure type
        backup_folder_path: Path to backup folder
        operations: List of all migration operations performed
        metadata_backup_path: Path to backed up metadata file
    """
    timestamp: str = Field(description="Backup timestamp")
    band_name: str = Field(description="Band name")
    original_structure_type: StructureType = Field(description="Original structure type")
    backup_folder_path: str = Field(description="Backup folder path")
    operations: List[AlbumMigrationOperation] = Field(description="Migration operations")
    metadata_backup_path: Optional[str] = Field(default=None, description="Metadata backup path")


class MigrationResult(BaseModel):
    """
    Result of a band structure migration operation.
    
    Attributes:
        status: Migration status
        band_name: Name of the migrated band
        migration_type: Type of migration performed
        albums_migrated: Number of albums successfully migrated
        albums_failed: Number of albums that failed to migrate
        operations: List of all migration operations
        backup_info: Backup information for rollback
        error_messages: List of error messages
        migration_time_seconds: Time taken for migration
        dry_run: Whether this was a dry run
    """
    status: MigrationStatus = Field(description="Migration status")
    band_name: str = Field(description="Band name")
    migration_type: MigrationType = Field(description="Migration type")
    albums_migrated: int = Field(default=0, description="Albums migrated")
    albums_failed: int = Field(default=0, description="Albums failed")
    operations: List[AlbumMigrationOperation] = Field(description="Migration operations")
    backup_info: Optional[MigrationBackup] = Field(default=None, description="Backup information")
    error_messages: List[str] = Field(default_factory=list, description="Error messages")
    migration_time_seconds: float = Field(default=0.0, description="Migration time")
    dry_run: bool = Field(default=False, description="Dry run flag")


class BandStructureMigrator:
    """
    Main class for performing band structure migrations.
    
    Handles migration operations between different folder structure types
    with backup, rollback, and progress tracking functionality.
    """
    
    def __init__(self):
        """Initialize the migrator."""
        self.parser = AlbumFolderParser()
        self.detector = BandStructureDetector()
        self.progress_callback = None
    
    def set_progress_callback(self, callback):
        """Set a callback function for progress reporting."""
        self.progress_callback = callback
    
    def migrate_band_structure(
        self,
        band_name: str,
        migration_type: MigrationType,
        dry_run: bool = False,
        album_type_overrides: Optional[Dict[str, str]] = None,
        backup_original: bool = True,
        force: bool = False,
        exclude_albums: Optional[List[str]] = None
    ) -> MigrationResult:
        """
        Migrate a band's folder structure.
        
        Args:
            band_name: Name of the band to migrate
            migration_type: Type of migration to perform
            dry_run: If True, preview migration without making changes
            album_type_overrides: Manual album type assignments
            backup_original: Whether to create backup before migration
            force: Override safety checks
            exclude_albums: Albums to skip during migration
            
        Returns:
            MigrationResult with detailed operation information
        """
        start_time = time.time()
        
        # Initialize result
        result = MigrationResult(
            status=MigrationStatus.PENDING,
            band_name=band_name,
            migration_type=migration_type,
            operations=[],
            dry_run=dry_run
        )
        
        try:
            # Progress: Starting migration
            self._report_progress(f"Starting {migration_type} migration for {band_name}", 0)
            
            # Validate band exists and get current structure
            band_info = self._get_band_info(band_name)
            if not band_info:
                raise ValueError(f"Band '{band_name}' not found in collection")
            
            band_folder_path = Path(band_info['folder_path'])
            if not band_folder_path.exists():
                raise ValueError(f"Band folder not found: {band_folder_path}")
            
            # Progress: Analyzing current structure
            self._report_progress("Analyzing current folder structure", 10)
            
            # Detect current structure
            current_structure = self.detector.detect_band_structure(str(band_folder_path))
            
            # Validate migration is appropriate
            if not force:
                self._validate_migration(current_structure, migration_type)
            
            # Progress: Planning migration
            self._report_progress("Planning migration operations", 20)
            
            # Plan migration operations
            operations = self._plan_migration_operations(
                band_folder_path,
                migration_type,
                album_type_overrides or {},
                exclude_albums or []
            )
            
            result.operations = operations
            
            if dry_run:
                result.status = MigrationStatus.COMPLETED
                result.migration_time_seconds = time.time() - start_time
                self._report_progress("Dry run completed", 100)
                return result
            
            # Progress: Creating backup
            self._report_progress("Creating backup", 30)
            
            # Create backup if requested
            backup_info = None
            if backup_original:
                backup_info = self._create_backup(band_folder_path, current_structure, operations)
                result.backup_info = backup_info
            
            # Progress: Executing migration
            self._report_progress("Executing migration operations", 40)
            
            # Execute migration operations
            result.status = MigrationStatus.IN_PROGRESS
            
            success_count = 0
            for i, operation in enumerate(operations):
                try:
                    progress = 40 + (50 * (i + 1) / len(operations))
                    self._report_progress(f"Migrating album: {operation.album_name}", progress)
                    
                    self._execute_migration_operation(operation)
                    operation.completed = True
                    success_count += 1
                    
                except Exception as e:
                    operation.completed = False
                    operation.error_message = str(e)
                    result.error_messages.append(f"Failed to migrate {operation.album_name}: {e}")
            
            result.albums_migrated = success_count
            result.albums_failed = len(operations) - success_count
            
            # Progress: Updating metadata
            self._report_progress("Updating band metadata", 90)
            
            # Update band metadata with new structure information
            self._update_band_metadata_after_migration(band_name, migration_type)
            
            # Determine final status
            if result.albums_failed == 0:
                result.status = MigrationStatus.COMPLETED
            else:
                result.status = MigrationStatus.FAILED
                if not force and result.albums_failed > len(operations) / 2:
                    # More than half failed, attempt rollback
                    self._report_progress("Migration failed, attempting rollback", 95)
                    self._rollback_migration(backup_info)
                    result.status = MigrationStatus.ROLLED_BACK
            
            result.migration_time_seconds = time.time() - start_time
            self._report_progress("Migration completed", 100)
            
        except Exception as e:
            result.status = MigrationStatus.FAILED
            result.error_messages.append(str(e))
            result.migration_time_seconds = time.time() - start_time
            
            # Attempt rollback if backup exists
            if result.backup_info and not dry_run:
                try:
                    self._rollback_migration(result.backup_info)
                    result.status = MigrationStatus.ROLLED_BACK
                except Exception as rollback_error:
                    result.error_messages.append(f"Rollback failed: {rollback_error}")
        
        return result
    
    def _get_band_info(self, band_name: str) -> Optional[Dict[str, Any]]:
        """Get band information from collection."""
        try:
            # Import here to avoid circular imports
            from ..core.tools.storage import get_band_list
            
            band_list_result = get_band_list(
                search_query=band_name,
                page=1,
                page_size=1
            )
            
            if band_list_result.get('status') == 'success':
                bands = band_list_result.get('results', {}).get('bands', [])
                for band in bands:
                    if band.get('band_name', '').lower() == band_name.lower():
                        return band
            
            return None
        except Exception:
            return None
    
    def _validate_migration(self, current_structure, migration_type: MigrationType):
        """Validate that the migration is appropriate for the current structure."""
        current_type = current_structure.structure_type
        
        # Define valid migration paths
        valid_migrations = {
            StructureType.DEFAULT: [MigrationType.DEFAULT_TO_ENHANCED],
            StructureType.LEGACY: [MigrationType.LEGACY_TO_DEFAULT],
            StructureType.MIXED: [MigrationType.MIXED_TO_ENHANCED],
            StructureType.ENHANCED: [MigrationType.ENHANCED_TO_DEFAULT]
        }
        
        if migration_type not in valid_migrations.get(current_type, []):
            raise ValueError(
                f"Migration type '{migration_type}' is not appropriate for "
                f"current structure type '{current_type}'"
            )
    
    def _plan_migration_operations(
        self,
        band_folder_path: Path,
        migration_type: MigrationType,
        album_type_overrides: Dict[str, str],
        exclude_albums: List[str]
    ) -> List[AlbumMigrationOperation]:
        """Plan all migration operations for the band."""
        operations = []
        
        # Get all album folders
        album_folders = []
        for item in band_folder_path.iterdir():
            if item.is_dir() and item.name not in exclude_albums:
                # Skip type folders in enhanced structure
                if item.name.lower() not in [t.value.lower() for t in AlbumType]:
                    album_folders.append(item)
                else:
                    # This is a type folder, get albums inside it
                    for album_item in item.iterdir():
                        if album_item.is_dir() and album_item.name not in exclude_albums:
                            album_folders.append(album_item)
        
        for album_folder in album_folders:
            # Parse album information
            parsed = self.parser.parse_enhanced_folder_structure(str(album_folder))
            
            # Determine album type
            album_type = AlbumType.ALBUM
            if album_folder.name in album_type_overrides:
                album_type = AlbumType(album_type_overrides[album_folder.name])
            elif 'album_type' in parsed:
                album_type = AlbumType(parsed['album_type'])
            else:
                album_type = self.parser.detect_album_type_from_folder(
                    parsed['album_name'], 
                    album_folder.parent.name if album_folder.parent != band_folder_path else ''
                )
            
            # Generate target path based on migration type
            target_path = self._generate_target_path(
                band_folder_path, album_folder, migration_type, album_type, parsed
            )
            
            # Create operation
            operation = AlbumMigrationOperation(
                album_name=parsed['album_name'],
                source_path=str(album_folder),
                target_path=str(target_path),
                album_type=album_type,
                operation_type="move"
            )
            
            operations.append(operation)
        
        return operations
    
    def _generate_target_path(
        self,
        band_folder_path: Path,
        album_folder: Path,
        migration_type: MigrationType,
        album_type: AlbumType,
        parsed: Dict[str, str]
    ) -> Path:
        """Generate target path for album based on migration type."""
        if migration_type == MigrationType.DEFAULT_TO_ENHANCED:
            # Create type-based structure: Band/Type/YYYY - Album Name (Edition)
            type_folder = band_folder_path / album_type.value.title()
            album_name = self._format_album_name_for_enhanced(parsed)
            return type_folder / album_name
            
        elif migration_type == MigrationType.LEGACY_TO_DEFAULT:
            # Add year prefix: Band/YYYY - Album Name (Edition)
            album_name = self._format_album_name_for_default(parsed)
            return band_folder_path / album_name
            
        elif migration_type == MigrationType.MIXED_TO_ENHANCED:
            # Convert to enhanced structure
            type_folder = band_folder_path / album_type.value.title()
            album_name = self._format_album_name_for_enhanced(parsed)
            return type_folder / album_name
            
        elif migration_type == MigrationType.ENHANCED_TO_DEFAULT:
            # Convert back to flat structure
            album_name = self._format_album_name_for_enhanced(parsed)
            return band_folder_path / album_name
            
        else:
            # Default: no change
            return album_folder
    
    def _format_album_name_for_enhanced(self, parsed: Dict[str, str]) -> str:
        """Format album name for enhanced structure."""
        year = parsed.get('year', '')
        album_name = parsed.get('album_name', '')
        edition = parsed.get('edition', '')
        
        if year and album_name:
            if edition:
                return f"{year} - {album_name} ({edition})"
            else:
                return f"{year} - {album_name}"
        else:
            if edition:
                return f"{album_name} ({edition})"
            else:
                return album_name
    
    def _format_album_name_for_default(self, parsed: Dict[str, str]) -> str:
        """Format album name for default structure with year prefix."""
        year = parsed.get('year', '')
        album_name = parsed.get('album_name', '')
        edition = parsed.get('edition', '')
        
        # Use current year if no year available
        if not year:
            year = str(datetime.now().year)
        
        if edition:
            return f"{year} - {album_name} ({edition})"
        else:
            return f"{year} - {album_name}"
    
    def _create_backup(
        self,
        band_folder_path: Path,
        current_structure,
        operations: List[AlbumMigrationOperation]
    ) -> MigrationBackup:
        """Create backup of current structure for rollback."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_folder = band_folder_path.parent / f"{band_folder_path.name}_backup_{timestamp}"
        
        # Create backup folder
        backup_folder.mkdir(exist_ok=True)
        
        # Copy entire band folder
        shutil.copytree(
            band_folder_path,
            backup_folder / band_folder_path.name,
            dirs_exist_ok=True
        )
        
        # Backup metadata file if it exists
        metadata_file = band_folder_path / ".band_metadata.json"
        metadata_backup_path = None
        if metadata_file.exists():
            metadata_backup_path = str(backup_folder / ".band_metadata.json")
            shutil.copy2(metadata_file, metadata_backup_path)
        
        return MigrationBackup(
            timestamp=timestamp,
            band_name=band_folder_path.name,
            original_structure_type=current_structure.structure_type,
            backup_folder_path=str(backup_folder),
            operations=operations,
            metadata_backup_path=metadata_backup_path
        )
    
    def _execute_migration_operation(self, operation: AlbumMigrationOperation):
        """Execute a single migration operation."""
        source_path = Path(operation.source_path)
        target_path = Path(operation.target_path)
        
        # Skip if source and target are the same
        if source_path == target_path:
            return
        
        # Create target directory if it doesn't exist
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Perform the move operation
        if operation.operation_type == "move":
            shutil.move(str(source_path), str(target_path))
        elif operation.operation_type == "copy":
            shutil.copytree(str(source_path), str(target_path), dirs_exist_ok=True)
    
    def _update_band_metadata_after_migration(self, band_name: str, migration_type: MigrationType):
        """Update band metadata after successful migration."""
        try:
            # Import here to avoid circular imports
            from ..core.tools.storage import load_band_metadata, save_band_metadata
            
            # Load existing metadata
            metadata = load_band_metadata(band_name)
            if metadata:
                # Update folder structure information
                if hasattr(metadata, 'folder_structure'):
                    if migration_type in [MigrationType.DEFAULT_TO_ENHANCED, MigrationType.MIXED_TO_ENHANCED]:
                        metadata.folder_structure.structure_type = StructureType.ENHANCED
                    elif migration_type == MigrationType.LEGACY_TO_DEFAULT:
                        metadata.folder_structure.structure_type = StructureType.DEFAULT
                    elif migration_type == MigrationType.ENHANCED_TO_DEFAULT:
                        metadata.folder_structure.structure_type = StructureType.DEFAULT
                
                # Update timestamp
                metadata.update_timestamp()
                
                # Save updated metadata
                save_band_metadata(metadata.model_dump())
        except Exception:
            # Non-critical error, just continue
            pass
    
    def _rollback_migration(self, backup_info: MigrationBackup):
        """Rollback migration using backup information."""
        if not backup_info:
            raise ValueError("No backup information available for rollback")
        
        backup_path = Path(backup_info.backup_folder_path)
        if not backup_path.exists():
            raise ValueError(f"Backup folder not found: {backup_path}")
        
        # Restore from backup
        band_folder_path = backup_path.parent / backup_info.band_name
        
        # Remove current (failed) structure
        if band_folder_path.exists():
            shutil.rmtree(band_folder_path)
        
        # Restore from backup
        shutil.move(
            str(backup_path / backup_info.band_name),
            str(band_folder_path)
        )
        
        # Restore metadata if available
        if backup_info.metadata_backup_path:
            metadata_backup = Path(backup_info.metadata_backup_path)
            if metadata_backup.exists():
                shutil.copy2(
                    metadata_backup,
                    band_folder_path / ".band_metadata.json"
                )
        
        # Clean up backup folder
        shutil.rmtree(backup_path)
    
    def _report_progress(self, message: str, percentage: float):
        """Report migration progress."""
        if self.progress_callback:
            self.progress_callback(message, percentage) 