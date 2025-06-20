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
import os
import logging
from datetime import datetime
from pydantic import BaseModel, Field

from .band import AlbumType, Album
from .band_structure import StructureType, BandStructureDetector
from .album_parser import AlbumFolderParser


# Configure logging for migration operations
logger = logging.getLogger(__name__)


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


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationIssue(BaseModel):
    """Represents a single validation issue."""
    severity: ValidationSeverity = Field(description="Issue severity")
    message: str = Field(description="Issue description")
    album_name: Optional[str] = Field(default=None, description="Affected album")
    source_path: Optional[str] = Field(default=None, description="Source path")
    target_path: Optional[str] = Field(default=None, description="Target path")
    suggestion: Optional[str] = Field(default=None, description="Resolution suggestion")


class MigrationValidationResult(BaseModel):
    """Result of migration validation checks."""
    is_valid: bool = Field(description="Whether migration can proceed")
    issues: List[ValidationIssue] = Field(default_factory=list, description="Validation issues")
    warnings_count: int = Field(default=0, description="Number of warnings")
    errors_count: int = Field(default=0, description="Number of errors")
    critical_count: int = Field(default=0, description="Number of critical issues")
    
    def add_issue(self, severity: ValidationSeverity, message: str, **kwargs):
        """Add a validation issue."""
        issue = ValidationIssue(severity=severity, message=message, **kwargs)
        self.issues.append(issue)
        
        if severity == ValidationSeverity.CRITICAL:
            self.critical_count += 1
            self.is_valid = False
        elif severity == ValidationSeverity.ERROR:
            self.errors_count += 1
            self.is_valid = False
        elif severity == ValidationSeverity.WARNING:
            self.warnings_count += 1


class MigrationLogEntry(BaseModel):
    """Single entry in migration log."""
    timestamp: str = Field(description="Timestamp")
    level: str = Field(description="Log level")
    operation: str = Field(description="Operation performed")
    album_name: Optional[str] = Field(default=None, description="Album name")
    source_path: Optional[str] = Field(default=None, description="Source path")
    target_path: Optional[str] = Field(default=None, description="Target path")
    message: str = Field(description="Log message")
    success: bool = Field(description="Operation success")
    error_details: Optional[str] = Field(default=None, description="Error details")


class MigrationLog(BaseModel):
    """Comprehensive migration log."""
    migration_id: str = Field(description="Migration identifier")
    band_name: str = Field(description="Band name")
    migration_type: MigrationType = Field(description="Migration type")
    start_time: str = Field(description="Start timestamp")
    end_time: Optional[str] = Field(default=None, description="End timestamp")
    status: MigrationStatus = Field(description="Migration status")
    entries: List[MigrationLogEntry] = Field(default_factory=list, description="Log entries")
    validation_result: Optional[MigrationValidationResult] = Field(default=None, description="Validation result")
    rollback_available: bool = Field(default=False, description="Rollback available")
    
    def add_entry(self, level: str, operation: str, message: str, success: bool = True, **kwargs):
        """Add log entry."""
        entry = MigrationLogEntry(
            timestamp=datetime.now().isoformat(),
            level=level,
            operation=operation,
            message=message,
            success=success,
            **kwargs
        )
        self.entries.append(entry)
        logger.log(getattr(logging, level.upper(), logging.INFO), message)


class MigrationIntegrityCheck(BaseModel):
    """Post-migration integrity check result."""
    passed: bool = Field(description="Whether integrity check passed")
    albums_verified: int = Field(default=0, description="Albums verified")
    files_missing: int = Field(default=0, description="Missing files")
    permission_issues: int = Field(default=0, description="Permission issues")
    folder_structure_valid: bool = Field(default=True, description="Folder structure validity")
    metadata_consistent: bool = Field(default=True, description="Metadata consistency")
    issues: List[str] = Field(default_factory=list, description="Integrity issues found")


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
    validation_result: Optional[MigrationValidationResult] = Field(default=None, description="Validation result")
    migration_log: Optional[MigrationLog] = Field(default=None, description="Migration log")
    integrity_check: Optional[MigrationIntegrityCheck] = Field(default=None, description="Integrity check result")


class MigrationValidator:
    """Comprehensive migration validation and safety checker."""
    
    def __init__(self):
        self.detector = BandStructureDetector()
        self.parser = AlbumFolderParser()
    
    def validate_source_structure(self, band_folder_path: Path, migration_type: MigrationType) -> MigrationValidationResult:
        """
        Validate source band structure before migration.
        
        Args:
            band_folder_path: Path to band folder
            migration_type: Intended migration type
            
        Returns:
            MigrationValidationResult with validation findings
        """
        result = MigrationValidationResult(is_valid=True)
        
        # Check if band folder exists
        if not band_folder_path.exists():
            result.add_issue(
                ValidationSeverity.CRITICAL,
                f"Band folder does not exist: {band_folder_path}",
                source_path=str(band_folder_path)
            )
            return result
        
        # Check folder permissions
        if not os.access(band_folder_path, os.R_OK | os.W_OK):
            result.add_issue(
                ValidationSeverity.CRITICAL,
                f"Insufficient permissions for band folder: {band_folder_path}",
                source_path=str(band_folder_path)
            )
            return result
        
        # Detect current structure
        try:
            current_structure = self.detector.detect_band_structure(str(band_folder_path))
            current_type = current_structure.structure_type
            
            # Validate migration is appropriate for current structure
            valid_migrations = {
                StructureType.DEFAULT: [MigrationType.DEFAULT_TO_ENHANCED],
                StructureType.LEGACY: [MigrationType.LEGACY_TO_DEFAULT],
                StructureType.MIXED: [MigrationType.MIXED_TO_ENHANCED],
                StructureType.ENHANCED: [MigrationType.ENHANCED_TO_DEFAULT]
            }
            
            if migration_type not in valid_migrations.get(current_type, []):
                result.add_issue(
                    ValidationSeverity.ERROR,
                    f"Migration type '{migration_type}' is not appropriate for current structure type '{current_type}'",
                    suggestion=f"Valid migrations for {current_type}: {valid_migrations.get(current_type, [])}"
                )
            
        except Exception as e:
            result.add_issue(
                ValidationSeverity.ERROR,
                f"Failed to detect current structure: {str(e)}",
                source_path=str(band_folder_path)
            )
        
        return result
    
    def check_existing_type_folders(self, band_folder_path: Path, migration_type: MigrationType) -> MigrationValidationResult:
        """
        Check for existing type folders and handle conflicts.
        
        Args:
            band_folder_path: Path to band folder
            migration_type: Migration type
            
        Returns:
            MigrationValidationResult with conflict findings
        """
        result = MigrationValidationResult(is_valid=True)
        
        if migration_type not in [MigrationType.DEFAULT_TO_ENHANCED, MigrationType.MIXED_TO_ENHANCED]:
            return result
        
        # Check for existing type folders
        type_folders = ['Album', 'Compilation', 'EP', 'Live', 'Single', 'Demo', 'Instrumental', 'Split']
        existing_type_folders = []
        
        for type_folder in type_folders:
            type_path = band_folder_path / type_folder
            if type_path.exists():
                existing_type_folders.append(type_folder)
                
                # Check if type folder has albums
                try:
                    albums_in_type = list(type_path.iterdir())
                    if albums_in_type:
                        result.add_issue(
                            ValidationSeverity.WARNING,
                            f"Type folder '{type_folder}' already exists with {len(albums_in_type)} album(s)",
                            source_path=str(type_path),
                            suggestion="Consider merging or renaming existing albums"
                        )
                except PermissionError:
                    result.add_issue(
                        ValidationSeverity.ERROR,
                        f"Permission denied accessing type folder: {type_path}",
                        source_path=str(type_path)
                    )
        
        if existing_type_folders:
            result.add_issue(
                ValidationSeverity.INFO,
                f"Found existing type folders: {', '.join(existing_type_folders)}",
                suggestion="Migration will merge with existing type-based structure"
            )
        
        return result
    
    def verify_album_type_assignments(self, operations: List[AlbumMigrationOperation]) -> MigrationValidationResult:
        """
        Verify album type assignments before moving files.
        
        Args:
            operations: List of planned migration operations
            
        Returns:
            MigrationValidationResult with type assignment findings
        """
        result = MigrationValidationResult(is_valid=True)
        
        for operation in operations:
            # Verify album type is valid
            try:
                album_type = AlbumType(operation.album_type)
            except ValueError:
                result.add_issue(
                    ValidationSeverity.ERROR,
                    f"Invalid album type '{operation.album_type}' for album '{operation.album_name}'",
                    album_name=operation.album_name,
                    suggestion="Use valid album type: Album, Compilation, EP, Live, Single, Demo, Instrumental, Split"
                )
                continue
            
            # Check if album name matches detected type
            source_path = Path(operation.source_path)
            try:
                detected_type = self.parser.detect_album_type_from_folder(source_path.name)
                if detected_type != album_type and detected_type != AlbumType.ALBUM:
                    result.add_issue(
                        ValidationSeverity.WARNING,
                        f"Assigned type '{album_type}' differs from detected type '{detected_type}' for album '{operation.album_name}'",
                        album_name=operation.album_name,
                        source_path=operation.source_path,
                        suggestion="Verify album type assignment is correct"
                    )
            except Exception as e:
                result.add_issue(
                    ValidationSeverity.WARNING,
                    f"Could not verify type assignment for album '{operation.album_name}': {str(e)}",
                    album_name=operation.album_name
                )
        
        return result
    
    def validate_destination_paths(self, operations: List[AlbumMigrationOperation], band_folder_path: Path) -> MigrationValidationResult:
        """
        Validate destination paths and folder creation.
        
        Args:
            operations: List of planned migration operations
            band_folder_path: Band folder path
            
        Returns:
            MigrationValidationResult with path validation findings
        """
        result = MigrationValidationResult(is_valid=True)
        
        target_paths = set()
        
        for operation in operations:
            target_path = Path(operation.target_path)
            
            # Check for duplicate target paths
            if str(target_path) in target_paths:
                result.add_issue(
                    ValidationSeverity.ERROR,
                    f"Duplicate target path detected: {target_path}",
                    album_name=operation.album_name,
                    target_path=operation.target_path,
                    suggestion="Resolve naming conflicts before migration"
                )
                continue
            
            target_paths.add(str(target_path))
            
            # Check if target already exists
            if target_path.exists():
                result.add_issue(
                    ValidationSeverity.WARNING,
                    f"Target path already exists: {target_path}",
                    album_name=operation.album_name,
                    target_path=operation.target_path,
                    suggestion="Target will be renamed with suffix"
                )
            
            # Check if parent directory can be created (but don't actually create it)
            parent_dir = target_path.parent
            try:
                # Find the closest existing parent directory
                current_parent = parent_dir
                while not current_parent.exists() and current_parent.parent != current_parent:
                    current_parent = current_parent.parent
                
                # Check write permissions on the existing parent
                if current_parent.exists() and not os.access(current_parent, os.W_OK):
                    result.add_issue(
                        ValidationSeverity.ERROR,
                        f"No write permission to create target directory structure in: {current_parent}",
                        album_name=operation.album_name,
                        target_path=operation.target_path
                    )
                elif parent_dir.exists() and not os.access(parent_dir, os.W_OK):
                    result.add_issue(
                        ValidationSeverity.ERROR,
                        f"No write permission for target directory: {parent_dir}",
                        album_name=operation.album_name,
                        target_path=operation.target_path
                    )
            except Exception as e:
                result.add_issue(
                    ValidationSeverity.WARNING,
                    f"Cannot verify target directory permissions for {parent_dir}: {str(e)}",
                    album_name=operation.album_name,
                    target_path=operation.target_path
                )
        
        return result
    
    def check_disk_space(self, operations: List[AlbumMigrationOperation], band_folder_path: Path) -> MigrationValidationResult:
        """
        Check available disk space for migration operations.
        
        Args:
            operations: List of planned migration operations
            band_folder_path: Band folder path
            
        Returns:
            MigrationValidationResult with disk space findings
        """
        result = MigrationValidationResult(is_valid=True)
        
        try:
            # Get disk usage info
            stat = shutil.disk_usage(band_folder_path)
            available_space = stat.free
            
            # For move operations, no additional space is needed
            # For copy operations (backup), calculate required space
            required_space = 0
            for operation in operations:
                if operation.operation_type == "copy":
                    source_path = Path(operation.source_path)
                    if source_path.exists():
                        try:
                            # Calculate folder size
                            folder_size = sum(f.stat().st_size for f in source_path.rglob('*') if f.is_file())
                            required_space += folder_size
                        except Exception:
                            # Conservative estimate if we can't calculate exact size
                            required_space += 100 * 1024 * 1024  # 100MB per album
            
            # Add a minimum buffer (10MB) for safety
            buffer_space = 10 * 1024 * 1024
            if (required_space + buffer_space) > available_space:
                result.add_issue(
                    ValidationSeverity.CRITICAL,
                    f"Insufficient disk space. Required: {(required_space + buffer_space) / (1024**3):.2f}GB, Available: {available_space / (1024**3):.2f}GB",
                    suggestion="Free up disk space before migration"
                )
        
        except Exception as e:
            result.add_issue(
                ValidationSeverity.WARNING,
                f"Could not check disk space: {str(e)}",
                suggestion="Verify sufficient disk space manually"
            )
        
        return result

    def validate_file_permissions(self, operations: List[AlbumMigrationOperation]) -> MigrationValidationResult:
        """
        Validate file system permissions for migration operations.
        
        Args:
            operations: List of planned migration operations
            
        Returns:
            MigrationValidationResult with permission findings
        """
        result = MigrationValidationResult(is_valid=True)
        
        for operation in operations:
            source_path = Path(operation.source_path)
            target_path = Path(operation.target_path)
            
            # Check source permissions
            if source_path.exists():
                if not os.access(source_path, os.R_OK):
                    result.add_issue(
                        ValidationSeverity.CRITICAL,
                        f"No read permission for source: {source_path}",
                        album_name=operation.album_name,
                        source_path=operation.source_path
                    )
                
                if operation.operation_type == "move" and not os.access(source_path.parent, os.W_OK):
                    result.add_issue(
                        ValidationSeverity.CRITICAL,
                        f"No write permission for source parent directory: {source_path.parent}",
                        album_name=operation.album_name,
                        source_path=operation.source_path
                    )
            
            # Check target permissions
            target_parent = target_path.parent
            if target_parent.exists():
                if not os.access(target_parent, os.W_OK):
                    result.add_issue(
                        ValidationSeverity.CRITICAL,
                        f"No write permission for target parent directory: {target_parent}",
                        album_name=operation.album_name,
                        target_path=operation.target_path
                    )
            else:
                # Check if target parent can be created
                try:
                    # Check permission of the closest existing parent
                    current_parent = target_path.parent
                    while not current_parent.exists() and current_parent.parent != current_parent:
                        current_parent = current_parent.parent
                    
                    if current_parent.exists() and not os.access(current_parent, os.W_OK):
                        result.add_issue(
                            ValidationSeverity.CRITICAL,
                            f"No write permission to create target directory structure in: {current_parent}",
                            album_name=operation.album_name,
                            target_path=operation.target_path
                        )
                except Exception:
                    # If we can't check permissions, it's a warning not a critical error
                    result.add_issue(
                        ValidationSeverity.WARNING,
                        f"Could not verify write permissions for target path: {target_path}",
                        album_name=operation.album_name,
                        target_path=operation.target_path
                    )
            
        return result

    def check_migration_conflicts(self, operations: List[AlbumMigrationOperation]) -> MigrationValidationResult:
        """
        Check for potential conflicts between migration operations.
        
        Args:
            operations: List of planned migration operations
            
        Returns:
            MigrationValidationResult with conflict findings
        """
        result = MigrationValidationResult(is_valid=True)
        
        target_paths = {}
        source_paths = set()
        
        for operation in operations:
            # Check for duplicate target paths
            target_key = str(Path(operation.target_path).resolve())
            if target_key in target_paths:
                existing_op = target_paths[target_key]
                result.add_issue(
                    ValidationSeverity.ERROR,
                    f"Target path conflict: '{operation.album_name}' and '{existing_op.album_name}' both target '{operation.target_path}'",
                    album_name=operation.album_name,
                    target_path=operation.target_path,
                    suggestion="Rename one of the conflicting albums"
                )
            else:
                target_paths[target_key] = operation
            
            # Check for source path conflicts (shouldn't happen but safety check)
            source_key = str(Path(operation.source_path).resolve())
            if source_key in source_paths:
                result.add_issue(
                    ValidationSeverity.ERROR,
                    f"Duplicate source path detected: {operation.source_path}",
                    album_name=operation.album_name,
                    source_path=operation.source_path
                )
            source_paths.add(source_key)
        
        return result

    def validate_migration_prerequisites(self, band_folder_path: Path, migration_type: MigrationType) -> MigrationValidationResult:
        """
        Validate prerequisites for migration are met.
        
        Args:
            band_folder_path: Path to band folder
            migration_type: Type of migration
            
        Returns:
            MigrationValidationResult with prerequisite findings
        """
        result = MigrationValidationResult(is_valid=True)
        
        # Check if band has albums to migrate
        try:
            album_folders = [f for f in band_folder_path.iterdir() 
                           if f.is_dir() and not f.name.startswith('.')]
            
            if not album_folders:
                result.add_issue(
                    ValidationSeverity.WARNING,
                    "No album folders found to migrate",
                    suggestion="Ensure band folder contains album subdirectories"
                )
                return result
            
            # Check if any albums match the expected pattern for migration type
            valid_albums = 0
            for album_folder in album_folders:
                try:
                    parsed = self.parser.parse_album_folder(album_folder.name)
                    # Check if this looks like a valid album folder name
                    # Valid albums should have:
                    # 1. A meaningful album name (not just generic words)
                    # 2. Either year information or reasonable pattern
                    if parsed['album_name'] and self._is_reasonable_album_name(parsed['album_name'], parsed.get('year', '')):
                        valid_albums += 1
                except Exception:
                    continue
            
            if valid_albums == 0:
                result.add_issue(
                    ValidationSeverity.WARNING,
                    "No albums with valid naming patterns found",
                    suggestion="Ensure album folders follow expected naming conventions"
                )
            
            # Migration-specific prerequisites
            if migration_type == MigrationType.LEGACY_TO_DEFAULT:
                # Check if albums are missing year prefixes
                legacy_albums = [f for f in album_folders 
                               if not f.name.startswith(('19', '20')) and ' - ' not in f.name[:6]]
                if not legacy_albums:
                    result.add_issue(
                        ValidationSeverity.INFO,
                        "No legacy albums (without year prefix) found for migration",
                        suggestion="Migration may not be necessary"
                    )
            
        except Exception as e:
            result.add_issue(
                ValidationSeverity.ERROR,
                f"Failed to validate migration prerequisites: {str(e)}",
                source_path=str(band_folder_path)
            )
        
        return result

    def perform_comprehensive_validation(self, band_folder_path: Path, migration_type: MigrationType, 
                                       operations: List[AlbumMigrationOperation], force: bool = False, dry_run: bool = False) -> MigrationValidationResult:
        """
        Perform all validation checks in sequence.
        
        Args:
            band_folder_path: Path to band folder
            migration_type: Type of migration
            operations: Planned migration operations
            force: Whether to override validation warnings
            
        Returns:
            Comprehensive MigrationValidationResult
        """
        # Combine all validation results (skip some validations for dry-run)
        validations = [
            self.validate_source_structure(band_folder_path, migration_type),
            self.validate_migration_prerequisites(band_folder_path, migration_type),
            self.check_existing_type_folders(band_folder_path, migration_type),
            self.verify_album_type_assignments(operations),
            self.validate_destination_paths(operations, band_folder_path),
            self.check_migration_conflicts(operations)
        ]
        
        # Skip intensive validations for dry-run mode
        if not dry_run:
            validations.extend([
                self.validate_file_permissions(operations),
                self.check_disk_space(operations, band_folder_path)
            ])
        
        # Merge all results
        combined_result = MigrationValidationResult(is_valid=True)
        for validation in validations:
            combined_result.issues.extend(validation.issues)
            combined_result.warnings_count += validation.warnings_count
            combined_result.errors_count += validation.errors_count
            combined_result.critical_count += validation.critical_count
            
            # If any validation failed and not forced, mark as invalid
            if not validation.is_valid and not force:
                combined_result.is_valid = False
        
        return combined_result

    def _is_reasonable_album_name(self, album_name: str, year: str = '') -> bool:
        """
        Check if a folder name appears to be a reasonable album name.
        
        Args:
            album_name: The album name to check
            year: Optional year string
            
        Returns:
            bool: Whether the name seems like a valid album name
        """
        if not album_name or len(album_name.strip()) < 2:
            return False
        
        name_lower = album_name.lower().strip()
        
        # Reject obvious non-album names
        invalid_patterns = [
            'not_an_album', 'not an album', 'also_not_album', 'also not album',
            'temp', 'temporary', 'test', 'testing', 'dummy', 'placeholder',
            'untitled', 'new folder', 'folder', 'album folder', 'music',
            'unknown', 'misc', 'miscellaneous', 'various', 'other'
        ]
        
        if name_lower in invalid_patterns:
            return False
        
        # If it has a year, it's more likely to be valid
        if year and year.isdigit() and len(year) == 4:
            return True
        
        # Check for reasonable album characteristics
        # Albums usually have some length and reasonable characters
        if len(name_lower) >= 3 and not name_lower.startswith('test') and not name_lower.startswith('tmp'):
            # Should contain at least one letter
            if any(c.isalpha() for c in name_lower):
                return True
        
        return False


class MigrationSafetyManager:
    """Manages atomic operations and safety measures during migration."""
    
    def __init__(self):
        self.active_operations = []
        self.rollback_info = {}
        self.temp_directory = None
        self.operation_locks = {}
    
    def begin_atomic_operation(self, operation: AlbumMigrationOperation) -> bool:
        """
        Begin an atomic migration operation.
        
        Args:
            operation: Migration operation to begin
            
        Returns:
            bool: Success status
        """
        try:
            # Check if already locked
            if operation.album_name in self.operation_locks:
                return False
            
            # Acquire lock
            if not self.acquire_operation_lock(operation.album_name):
                return False
            
            # Record operation start
            self.active_operations.append(operation)
            
            # Store original state for rollback
            source_path = Path(operation.source_path)
            if source_path.exists():
                self.rollback_info[operation.album_name] = {
                    'original_path': str(source_path),
                    'operation_type': operation.operation_type,
                    'started': datetime.now().isoformat()
                }
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to begin atomic operation for {operation.album_name}: {str(e)}")
            return False
    
    def commit_atomic_operation(self, operation: AlbumMigrationOperation) -> bool:
        """
        Commit an atomic migration operation.
        
        Args:
            operation: Migration operation to commit
            
        Returns:
            bool: Success status
        """
        try:
            # Check if operation was started
            if operation.album_name not in self.operation_locks:
                return True  # Operation not started, consider success
            
            # Mark operation as completed
            operation.completed = True
            
            # Remove from active operations
            if operation in self.active_operations:
                self.active_operations.remove(operation)
            
            # Clean up rollback info
            if operation.album_name in self.rollback_info:
                del self.rollback_info[operation.album_name]
            
            # Release lock
            self.release_operation_lock(operation.album_name)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to commit atomic operation for {operation.album_name}: {str(e)}")
            return False
    
    def rollback_operation(self, operation: AlbumMigrationOperation) -> bool:
        """
        Rollback a failed migration operation.
        
        Args:
            operation: Migration operation to rollback
            
        Returns:
            bool: Success status
        """
        try:
            rollback_data = self.rollback_info.get(operation.album_name)
            if not rollback_data:
                logger.warning(f"No rollback data found for {operation.album_name}")
                return False
            
            target_path = Path(operation.target_path)
            source_path = Path(rollback_data['original_path'])
            
            if target_path.exists():
                if operation.operation_type == "move":
                    # Move back to original location
                    shutil.move(str(target_path), str(source_path))
                    logger.info(f"Rolled back move operation for {operation.album_name}")
                elif operation.operation_type == "copy":
                    # Remove the copy
                    shutil.rmtree(target_path)
                    logger.info(f"Rolled back copy operation for {operation.album_name}")
            
            # Clean up
            if operation in self.active_operations:
                self.active_operations.remove(operation)
            del self.rollback_info[operation.album_name]
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to rollback operation for {operation.album_name}: {str(e)}")
            return False
    
    def rollback_all_operations(self) -> int:
        """
        Rollback all active operations.
        
        Returns:
            int: Number of operations rolled back
        """
        rolled_back = 0
        
        for operation in self.active_operations.copy():
            if self.rollback_operation(operation):
                rolled_back += 1
        
        return rolled_back

    def create_safe_temp_directory(self, base_path: Path) -> Path:
        """
        Create a safe temporary directory for staging operations.
        
        Args:
            base_path: Base path for temporary directory
            
        Returns:
            Path to temporary directory
        """
        import tempfile
        
        if self.temp_directory is None:
            temp_parent = base_path.parent / ".migration_temp"
            temp_parent.mkdir(exist_ok=True)
            self.temp_directory = Path(tempfile.mkdtemp(dir=temp_parent, prefix="migration_"))
        
        return self.temp_directory

    def cleanup_temp_directory(self):
        """Clean up temporary directory after migration."""
        if self.temp_directory and self.temp_directory.exists():
            try:
                shutil.rmtree(self.temp_directory)
                self.temp_directory = None
            except Exception as e:
                logger.warning(f"Failed to cleanup temp directory: {str(e)}")

    def acquire_operation_lock(self, album_name: str) -> bool:
        """
        Acquire a lock for an album operation to prevent concurrent access.
        
        Args:
            album_name: Name of album to lock
            
        Returns:
            bool: Whether lock was acquired
        """
        if album_name in self.operation_locks:
            return False  # Already locked
        
        self.operation_locks[album_name] = True
        return True

    def release_operation_lock(self, album_name: str):
        """
        Release operation lock for an album.
        
        Args:
            album_name: Name of album to unlock
        """
        if album_name in self.operation_locks:
            del self.operation_locks[album_name]

    def validate_operation_safety(self, operation: AlbumMigrationOperation) -> List[str]:
        """
        Validate that an operation can be safely performed.
        
        Args:
            operation: Migration operation to validate
            
        Returns:
            List of safety issues (empty if safe)
        """
        issues = []
        
        source_path = Path(operation.source_path)
        target_path = Path(operation.target_path)
        
        # Check if source exists
        if not source_path.exists():
            issues.append(f"Source path does not exist: {source_path}")
            return issues
        
        # Check if already locked (but don't acquire lock, this is just validation)
        if operation.album_name in self.operation_locks:
            issues.append(f"Album '{operation.album_name}' is already being processed")
            return issues
        
        # Check target path safety
        if target_path.exists() and operation.operation_type == "move":
            # Check if target is empty or can be safely replaced
            if target_path.is_dir():
                try:
                    target_contents = list(target_path.iterdir())
                    if target_contents:
                        issues.append(f"Target directory is not empty: {target_path}")
                except PermissionError:
                    issues.append(f"Cannot access target directory: {target_path}")
        
        # Check path safety (no dangerous operations)
        try:
            source_resolved = source_path.resolve()
            target_resolved = target_path.resolve()
            
            # Ensure we're not moving to a subdirectory of itself
            if str(target_resolved).startswith(str(source_resolved) + os.sep):
                issues.append("Cannot move folder to its own subdirectory")
            
        except Exception as e:
            issues.append(f"Path resolution error: {str(e)}")
        
        return issues


class MigrationIntegrityChecker:
    """Performs post-migration integrity checks."""
    
    def __init__(self):
        self.parser = AlbumFolderParser()
    
    def perform_integrity_check(self, operations: List[AlbumMigrationOperation], band_folder_path: Path) -> MigrationIntegrityCheck:
        """
        Perform comprehensive post-migration integrity check.
        
        Args:
            operations: Completed migration operations
            band_folder_path: Band folder path
            
        Returns:
            MigrationIntegrityCheck with findings
        """
        check = MigrationIntegrityCheck(passed=True)
        
        for operation in operations:
            if not operation.completed:
                continue
            
            try:
                self._verify_album_migration(operation, check)
                check.albums_verified += 1
                
            except Exception as e:
                check.issues.append(f"Failed to verify {operation.album_name}: {str(e)}")
                check.passed = False
        
        # Verify overall folder structure
        self._verify_folder_structure(band_folder_path, check)
        
        # Check metadata consistency
        self._verify_metadata_consistency(band_folder_path, check)
        
        # Additional comprehensive checks
        self._verify_file_integrity(operations, check)
        self._verify_permissions_integrity(operations, check)
        
        return check
    
    def _verify_album_migration(self, operation: AlbumMigrationOperation, check: MigrationIntegrityCheck):
        """Verify individual album migration."""
        target_path = Path(operation.target_path)
        
        # Check if target exists
        if not target_path.exists():
            check.files_missing += 1
            check.issues.append(f"Target path missing: {target_path}")
            check.passed = False
        
        # Check permissions
        if not os.access(target_path, os.R_OK):
            check.permission_issues += 1
            check.issues.append(f"Cannot read target path: {target_path}")
            check.passed = False
        
        # Verify source no longer exists (for move operations)
        if operation.operation_type == "move":
            source_path = Path(operation.source_path)
            if source_path.exists():
                check.issues.append(f"Source still exists after move: {source_path}")
                check.passed = False
    
    def _verify_folder_structure(self, band_folder_path: Path, check: MigrationIntegrityCheck):
        """Verify overall folder structure validity."""
        try:
            # Check if band folder exists and is accessible
            if not band_folder_path.exists():
                check.folder_structure_valid = False
                check.issues.append(f"Band folder missing: {band_folder_path}")
                check.passed = False
            
            # Check for proper type folder structure (if enhanced)
            type_folders = ['Album', 'Compilation', 'EP', 'Live', 'Single', 'Demo', 'Instrumental', 'Split']
            has_type_folders = any((band_folder_path / tf).exists() for tf in type_folders)
            
            if has_type_folders:
                # Verify no albums are in root folder (for enhanced structure)
                root_albums = [f for f in band_folder_path.iterdir() 
                              if f.is_dir() and f.name not in type_folders and not f.name.startswith('.')]
                if root_albums:
                    check.issues.append(f"Albums found in root folder in enhanced structure: {[f.name for f in root_albums]}")
                    check.folder_structure_valid = False
        
        except Exception as e:
            check.issues.append(f"Failed to verify folder structure: {str(e)}")
            check.folder_structure_valid = False
            check.passed = False
    
    def _verify_metadata_consistency(self, band_folder_path: Path, check: MigrationIntegrityCheck):
        """Verify metadata consistency after migration."""
        try:
            metadata_file = band_folder_path / ".band_metadata.json"
            
            if metadata_file.exists():
                # Load and verify metadata can be parsed
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # Check if metadata structure is valid
                if not isinstance(metadata, dict):
                    check.metadata_consistent = False
                    check.issues.append("Metadata file is not a valid JSON object")
                    check.passed = False
            
        except Exception as e:
            check.metadata_consistent = False
            check.issues.append(f"Failed to verify metadata consistency: {str(e)}")
            check.passed = False

    def _verify_file_integrity(self, operations: List[AlbumMigrationOperation], check: MigrationIntegrityCheck):
        """Verify file integrity after migration."""
        for operation in operations:
            if not operation.completed:
                continue
                
            target_path = Path(operation.target_path)
            
            if target_path.exists():
                try:
                    # Count files in migrated folder
                    all_files = [f for f in target_path.rglob('*') if f.is_file()]
                    file_count = len(all_files)
                    
                    if file_count == 0:
                        check.files_missing += 1
                        check.issues.append(f"No files found in migrated album: {operation.album_name}")
                        check.passed = False
                    
                    # Check for common music file extensions
                    music_files = [f for f in all_files 
                                 if f.suffix.lower() in ['.mp3', '.flac', '.wav', '.m4a', '.ogg']]
                    
                    if not music_files and file_count > 0:
                        check.files_missing += 1
                        check.issues.append(f"No music files found in migrated album: {operation.album_name}")
                        check.passed = False
                    
                    # For albums that should have specific files, verify they exist
                    # This helps catch cases where files were removed after migration
                    if operation.operation_type == "move":
                        source_path = Path(operation.source_path)
                        if source_path.exists():
                            # If source still exists (shouldn't for move), that's an issue
                            check.issues.append(f"Source path still exists after move: {source_path}")
                            check.passed = False
                        
                        # Check if we have reasonable number of files for an album
                        if file_count < 1:
                            check.files_missing += 1
                            check.issues.append(f"Insufficient files in migrated album: {operation.album_name}")
                            check.passed = False
                            
                except Exception as e:
                    check.issues.append(f"Failed to verify file integrity for {operation.album_name}: {str(e)}")
                    check.passed = False
            else:
                # Target path doesn't exist - definitely a problem
                check.files_missing += 1
                check.issues.append(f"Target path missing after migration: {target_path}")
                check.passed = False

    def _verify_permissions_integrity(self, operations: List[AlbumMigrationOperation], check: MigrationIntegrityCheck):
        """Verify file permissions after migration."""
        for operation in operations:
            if not operation.completed:
                continue
                
            target_path = Path(operation.target_path)
            
            if target_path.exists():
                try:
                    # Check read permission
                    if not os.access(target_path, os.R_OK):
                        check.permission_issues += 1
                        check.issues.append(f"Read permission issue for migrated album: {operation.album_name}")
                        check.passed = False
                    
                    # Check write permission for parent directory
                    if not os.access(target_path.parent, os.W_OK):
                        check.permission_issues += 1
                        check.issues.append(f"Write permission issue for parent directory: {target_path.parent}")
                        check.passed = False
                        
                except Exception as e:
                    check.permission_issues += 1
                    check.issues.append(f"Failed to verify permissions for {operation.album_name}: {str(e)}")
                    check.passed = False


class BandStructureMigrator:
    """
    Handles migration of band folder structures between different organization patterns.
    
    Supports migration between:
    - Default structure (YYYY - Album Name)
    - Enhanced structure (Type/YYYY - Album Name)
    - Legacy structure (Album Name only)
    """

    def __init__(self):
        self.detector = BandStructureDetector()
        self.parser = AlbumFolderParser()
        self.validator = MigrationValidator()
        self.safety_manager = MigrationSafetyManager()
        self.integrity_checker = MigrationIntegrityChecker()
        self.progress_callback = None

    def set_progress_callback(self, callback):
        """Set callback function for progress reporting."""
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
        Migrate a band's folder structure to a different organization pattern.
        
        Args:
            band_name: Name of the band to migrate
            migration_type: Type of migration to perform
            dry_run: If True, only plan the migration without executing
            album_type_overrides: Manual album type assignments
            backup_original: Whether to create backup before migration
            force: Override validation warnings and proceed
            exclude_albums: List of album names to exclude from migration
            
        Returns:
            MigrationResult with migration outcome and details
        """
        start_time = time.time()
        migration_id = f"{band_name}_{migration_type}_{int(start_time)}"
        
        # Initialize result
        result = MigrationResult(
            status=MigrationStatus.PENDING,
            band_name=band_name,
            migration_type=migration_type,
            dry_run=dry_run,
            operations=[]  # Initialize with empty operations list
        )
        
        # Initialize migration log
        migration_log = MigrationLog(
            migration_id=migration_id,
            band_name=band_name,
            migration_type=migration_type,
            start_time=datetime.now().isoformat(),
            status=MigrationStatus.IN_PROGRESS
        )
        result.migration_log = migration_log
        
        try:
            # Progress: Starting migration
            self._report_progress(f"Starting {migration_type} migration for {band_name}", 0)
            migration_log.add_entry("INFO", "MIGRATION_START", f"Starting {migration_type} migration for {band_name}")
            
            # Validate band exists and get current structure
            band_info = self._get_band_info(band_name)
            if not band_info:
                raise ValueError(f"Band '{band_name}' not found in collection")
            
            band_folder_path = Path(band_info['folder_path'])
            if not band_folder_path.exists():
                raise ValueError(f"Band folder not found: {band_folder_path}")
            
            # Progress: Validation phase
            self._report_progress("Performing comprehensive validation", 10)
            migration_log.add_entry("INFO", "VALIDATION_START", "Starting migration validation")
            
            # Comprehensive validation
            validation_result = self._perform_comprehensive_validation(
                band_folder_path, migration_type, force, dry_run
            )
            result.validation_result = validation_result
            migration_log.validation_result = validation_result
            
            # Log validation results
            for issue in validation_result.issues:
                migration_log.add_entry(
                    issue.severity.upper(),
                    "VALIDATION_ISSUE",
                    issue.message,
                    success=issue.severity != ValidationSeverity.CRITICAL,
                    album_name=issue.album_name
                )
            
            if not validation_result.is_valid and not force:
                result.status = MigrationStatus.FAILED
                result.error_messages.append("Validation failed - use force=True to override")
                migration_log.add_entry("ERROR", "VALIDATION_FAILED", "Migration validation failed")
                migration_log.status = MigrationStatus.FAILED
                migration_log.end_time = datetime.now().isoformat()
                return result
            
            # Progress: Planning migration
            self._report_progress("Planning migration operations", 20)
            migration_log.add_entry("INFO", "PLANNING_START", "Planning migration operations")
            
            # Plan migration operations
            operations = self._plan_migration_operations(
                band_folder_path,
                migration_type,
                album_type_overrides or {},
                exclude_albums or []
            )
            
            result.operations = operations
            migration_log.add_entry("INFO", "PLANNING_COMPLETE", f"Planned {len(operations)} migration operations")
            
            if dry_run:
                result.status = MigrationStatus.COMPLETED
                result.migration_time_seconds = time.time() - start_time
                migration_log.add_entry("INFO", "DRY_RUN_COMPLETE", "Dry run completed successfully")
                migration_log.status = MigrationStatus.COMPLETED
                migration_log.end_time = datetime.now().isoformat()
                self._report_progress("Dry run completed", 100)
                return result
            
            # Progress: Creating backup
            self._report_progress("Creating backup", 30)
            migration_log.add_entry("INFO", "BACKUP_START", "Creating backup")
            
            # Create backup if requested
            backup_info = None
            if backup_original:
                current_structure = self.detector.detect_band_structure(str(band_folder_path))
                backup_info = self._create_backup(band_folder_path, current_structure, operations)
                result.backup_info = backup_info
                migration_log.rollback_available = True
                migration_log.add_entry("INFO", "BACKUP_COMPLETE", f"Backup created at {backup_info.backup_folder_path}")
            
            # Progress: Executing migration
            self._report_progress("Executing migration operations", 40)
            migration_log.add_entry("INFO", "EXECUTION_START", "Starting migration execution")
            
            # Execute migration operations with atomic safety
            albums_migrated = 0
            albums_failed = 0
            
            for i, operation in enumerate(operations):
                try:
                    # Validate operation safety before execution
                    safety_issues = self.safety_manager.validate_operation_safety(operation)
                    if safety_issues:
                        raise RuntimeError(f"Safety validation failed: {'; '.join(safety_issues)}")
                    
                    # Begin atomic operation
                    if not self.safety_manager.begin_atomic_operation(operation):
                        raise RuntimeError("Failed to begin atomic operation")
                    
                    migration_log.add_entry(
                        "INFO", "OPERATION_START",
                        f"Starting migration of {operation.album_name}",
                        album_name=operation.album_name,
                        source_path=operation.source_path,
                        target_path=operation.target_path
                    )
                    
                    # Execute the operation
                    self._execute_migration_operation(operation)
                    
                    # Commit atomic operation
                    if not self.safety_manager.commit_atomic_operation(operation):
                        raise RuntimeError("Failed to commit atomic operation")
                    
                    # Release operation lock
                    self.safety_manager.release_operation_lock(operation.album_name)
                    
                    albums_migrated += 1
                    migration_log.add_entry(
                        "INFO", "OPERATION_SUCCESS",
                        f"Successfully migrated {operation.album_name}",
                        album_name=operation.album_name
                    )
                    
                    # Update progress
                    progress = 40 + (50 * (i + 1) / len(operations))
                    self._report_progress(f"Migrated {operation.album_name}", progress)
                    
                except Exception as e:
                    operation.error_message = str(e)
                    albums_failed += 1
                    result.error_messages.append(f"Failed to migrate {operation.album_name}: {str(e)}")
                    
                    migration_log.add_entry(
                        "ERROR", "OPERATION_FAILED",
                        f"Failed to migrate {operation.album_name}: {str(e)}",
                        success=False,
                        album_name=operation.album_name,
                        error_details=str(e)
                    )
                    
                    # Release operation lock on failure
                    self.safety_manager.release_operation_lock(operation.album_name)
                    
                    # Attempt rollback
                    if self.safety_manager.rollback_operation(operation):
                        migration_log.add_entry(
                            "INFO", "OPERATION_ROLLBACK",
                            f"Rolled back failed migration of {operation.album_name}",
                            album_name=operation.album_name
                        )
            
            result.albums_migrated = albums_migrated
            result.albums_failed = albums_failed
            
            # Progress: Post-migration integrity check
            self._report_progress("Performing integrity check", 90)
            migration_log.add_entry("INFO", "INTEGRITY_CHECK_START", "Starting post-migration integrity check")
            
            # Perform integrity check
            integrity_check = self.integrity_checker.perform_integrity_check(operations, band_folder_path)
            result.integrity_check = integrity_check
            
            if integrity_check.passed:
                migration_log.add_entry("INFO", "INTEGRITY_CHECK_PASSED", "Integrity check passed")
            else:
                migration_log.add_entry("ERROR", "INTEGRITY_CHECK_FAILED", f"Integrity check failed: {', '.join(integrity_check.issues)}")
                
                # If integrity check fails, consider rollback
                if albums_failed == 0 and not integrity_check.passed:
                    result.status = MigrationStatus.FAILED
                    result.error_messages.append("Post-migration integrity check failed")
            
            # Update band metadata after successful migration
            if albums_migrated > 0 and integrity_check.passed:
                self._update_band_metadata_after_migration(band_name, migration_type)
                migration_log.add_entry("INFO", "METADATA_UPDATE", "Updated band metadata after migration")
            
            # Determine final status
            if albums_failed == 0 and integrity_check.passed:
                result.status = MigrationStatus.COMPLETED
                migration_log.status = MigrationStatus.COMPLETED
                migration_log.add_entry("INFO", "MIGRATION_COMPLETE", "Migration completed successfully")
            else:
                result.status = MigrationStatus.FAILED
                migration_log.status = MigrationStatus.FAILED
                migration_log.add_entry("ERROR", "MIGRATION_FAILED", f"Migration failed: {albums_failed} albums failed, integrity check: {integrity_check.passed}")
            
            result.migration_time_seconds = time.time() - start_time
            migration_log.end_time = datetime.now().isoformat()
            self._report_progress("Migration completed", 100)
            
            # Cleanup safety manager resources
            self.safety_manager.cleanup_temp_directory()
            
            return result
            
        except Exception as e:
            result.status = MigrationStatus.FAILED
            result.error_messages.append(str(e))
            result.migration_time_seconds = time.time() - start_time
            
            migration_log.status = MigrationStatus.FAILED
            migration_log.end_time = datetime.now().isoformat()
            migration_log.add_entry("ERROR", "MIGRATION_ERROR", f"Migration failed with error: {str(e)}", success=False, error_details=str(e))
            
            # Attempt to rollback all operations
            rolled_back = self.safety_manager.rollback_all_operations()
            if rolled_back > 0:
                migration_log.add_entry("INFO", "ROLLBACK_COMPLETE", f"Rolled back {rolled_back} operations")
                result.status = MigrationStatus.ROLLED_BACK
                migration_log.status = MigrationStatus.ROLLED_BACK
            
            logger.error(f"Migration failed for band '{band_name}': {str(e)}")
            raise
    
    def _perform_comprehensive_validation(self, band_folder_path: Path, migration_type: MigrationType, force: bool, dry_run: bool = False) -> MigrationValidationResult:
        """Perform comprehensive validation before migration."""
        # Plan operations for validation
        operations = self._plan_migration_operations(band_folder_path, migration_type, {}, [])
        
        # Use the enhanced comprehensive validation from MigrationValidator
        return self.validator.perform_comprehensive_validation(
            band_folder_path, migration_type, operations, force, dry_run
        )

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
        """
        Execute a single migration operation with enhanced file handling.
        
        Handles:
        - File permission preservation
        - Timestamp preservation 
        - Folder name conflict detection and resolution
        - Atomic operations with proper error handling
        """
        source_path = Path(operation.source_path)
        target_path = Path(operation.target_path)
        
        # Skip if source and target are the same
        if source_path == target_path:
            return
        
        # Check for folder name conflicts and resolve them
        target_path = self._resolve_folder_conflicts(target_path)
        operation.target_path = str(target_path)  # Update operation with resolved path
        
        # Create target directory if it doesn't exist
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Perform the move operation with enhanced file handling
        if operation.operation_type == "move":
            self._safe_move_with_permissions(source_path, target_path)
        elif operation.operation_type == "copy":
            self._safe_copy_with_permissions(source_path, target_path)
    
    def _resolve_folder_conflicts(self, target_path: Path) -> Path:
        """
        Detect and resolve folder name conflicts.
        
        Args:
            target_path: The intended target path
            
        Returns:
            Path: Resolved path without conflicts
        """
        if not target_path.exists():
            return target_path
        
        # Generate alternative name with counter
        counter = 1
        original_name = target_path.name
        parent_dir = target_path.parent
        
        while target_path.exists():
            # Extract the base name and extension/edition info
            if " (" in original_name and original_name.endswith(")"):
                # Handle names like "2010 - Album Name (Deluxe Edition)"
                base_part = original_name.rsplit(" (", 1)[0]
                edition_part = original_name.rsplit(" (", 1)[1]
                new_name = f"{base_part} (Conflict {counter}) ({edition_part}"
            else:
                # Handle names like "2010 - Album Name"
                new_name = f"{original_name} (Conflict {counter})"
            
            target_path = parent_dir / new_name
            counter += 1
            
            # Safety check to prevent infinite loops
            if counter > 999:
                raise ValueError(f"Too many conflicts for folder: {original_name}")
        
        return target_path

    def _safe_move_with_permissions(self, source_path: Path, target_path: Path):
        """
        Move folder while preserving permissions and timestamps.
        
        Args:
            source_path: Source folder path
            target_path: Target folder path
        """
        try:
            # Get original permissions and timestamps before move
            source_stat = source_path.stat()
            
            # Perform the move operation
            shutil.move(str(source_path), str(target_path))
            
            # Restore permissions and timestamps
            self._preserve_folder_attributes(target_path, source_stat)
            
        except Exception as e:
            raise RuntimeError(f"Failed to move folder from {source_path} to {target_path}: {e}")

    def _safe_copy_with_permissions(self, source_path: Path, target_path: Path):
        """
        Copy folder while preserving permissions and timestamps.
        
        Args:
            source_path: Source folder path
            target_path: Target folder path
        """
        try:
            # Use shutil.copytree with copy_function that preserves metadata
            shutil.copytree(
                str(source_path), 
                str(target_path), 
                copy_function=shutil.copy2,  # Preserves metadata including timestamps
                dirs_exist_ok=True
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to copy folder from {source_path} to {target_path}: {e}")

    def _preserve_folder_attributes(self, folder_path: Path, original_stat):
        """
        Preserve folder permissions and timestamps after move operation.
        
        Args:
            folder_path: Path to folder to update
            original_stat: Original stat object from source folder
        """
        try:
            # Preserve access and modification times
            os.utime(folder_path, (original_stat.st_atime, original_stat.st_mtime))
            
            # Preserve permissions (only on Unix-like systems)
            if hasattr(original_stat, 'st_mode') and isinstance(original_stat.st_mode, int):
                folder_path.chmod(original_stat.st_mode)
                
        except (OSError, AttributeError, TypeError):
            # Non-critical error, permissions/timestamps couldn't be preserved
            # This is common on Windows or with restricted permissions
            pass
    
    def _update_band_metadata_after_migration(self, band_name: str, migration_type: MigrationType):
        """
        Update band metadata after successful migration.
        
        Updates:
        - Folder structure type information
        - Album folder paths in metadata
        - Band timestamps
        """
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
                
                # Update album folder paths in metadata
                self._update_album_folder_paths_in_metadata(metadata, migration_type)
                
                # Update timestamp
                metadata.update_timestamp()
                
                # Save updated metadata
                save_band_metadata(metadata.model_dump())
        except Exception:
            # Non-critical error, just continue
            pass

    def _update_album_folder_paths_in_metadata(self, metadata, migration_type: MigrationType):
        """
        Update album folder paths in band metadata after migration.
        
        Args:
            metadata: Band metadata object
            migration_type: Type of migration performed
        """
        try:
            # Update paths for both local albums and missing albums if they have folder_path
            for album_list_name in ['albums', 'albums_missing']:
                if hasattr(metadata, album_list_name):
                    album_list = getattr(metadata, album_list_name)
                    if album_list:
                        for album in album_list:
                            if hasattr(album, 'folder_path') and album.folder_path:
                                # Update the folder path based on migration type
                                album.folder_path = self._calculate_new_album_path(
                                    album, migration_type
                                )
        except Exception:
            # Non-critical error, continue
            pass

    def _calculate_new_album_path(self, album, migration_type: MigrationType) -> str:
        """
        Calculate new album folder path after migration.
        
        Args:
            album: Album object from metadata
            migration_type: Type of migration performed
            
        Returns:
            str: New folder path for the album
        """
        try:
            current_path = Path(album.folder_path)
            band_folder = current_path.parent
            
            # Parse album information
            parsed = self.parser.parse_enhanced_folder_structure(str(current_path))
            
            # Determine album type
            album_type = getattr(album, 'type', AlbumType.ALBUM)
            if isinstance(album_type, str):
                album_type = AlbumType(album_type)
            
            # Generate new path based on migration type
            new_path = self._generate_target_path(
                band_folder, current_path, migration_type, album_type, parsed
            )
            
            return str(new_path)
            
        except Exception:
            # If path calculation fails, return original path
            return album.folder_path
    
    def _report_progress(self, message: str, percentage: float):
        """Report migration progress."""
        if self.progress_callback:
            self.progress_callback(message, percentage) 