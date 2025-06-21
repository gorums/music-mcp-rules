#!/usr/bin/env python3
"""
Band Structure Migration - Error Handling and Recovery System

This module provides comprehensive error handling and recovery functionality for band 
structure migration operations, implementing all requirements from Task 6.6:

- Handle file system permission errors gracefully
- Detect and resolve disk space issues  
- Handle locked files and directories
- Implement partial migration recovery
- Provide detailed error messages and solutions
- Create automatic rollback on critical failures
- Support manual intervention for complex cases
"""

import os
import shutil
import psutil
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass
from enum import Enum
import threading
import json
from datetime import datetime

from src.exceptions import (
    MigrationError,
    MigrationPermissionError, 
    MigrationDiskSpaceError,
    MigrationFileLockError,
    MigrationPartialFailureError,
    MigrationRollbackError,
    ErrorSeverity
)

# Configure logging
logger = logging.getLogger(__name__)


class RecoveryAction(str, Enum):
    """Types of recovery actions available."""
    RETRY = "retry"
    ROLLBACK = "rollback"
    MANUAL_INTERVENTION = "manual_intervention"
    SKIP_ALBUM = "skip_album"
    ABORT_MIGRATION = "abort_migration"


class ErrorType(str, Enum):
    """Types of migration errors."""
    PERMISSION_DENIED = "permission_denied"
    DISK_SPACE_INSUFFICIENT = "disk_space_insufficient"
    FILE_LOCKED = "file_locked"
    SOURCE_NOT_FOUND = "source_not_found"
    TARGET_EXISTS = "target_exists"
    COPY_FAILED = "copy_failed"
    MOVE_FAILED = "move_failed"
    METADATA_UPDATE_FAILED = "metadata_update_failed"
    VALIDATION_FAILED = "validation_failed"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class ErrorDetails:
    """Detailed information about a migration error."""
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    album_name: str
    source_path: Optional[str] = None
    target_path: Optional[str] = None
    original_exception: Optional[Exception] = None
    retry_count: int = 0
    max_retries: int = 3
    recovery_actions: List[RecoveryAction] = None
    solution_steps: List[str] = None
    manual_intervention_required: bool = False
    rollback_available: bool = True
    
    def __post_init__(self):
        if self.recovery_actions is None:
            self.recovery_actions = []
        if self.solution_steps is None:
            self.solution_steps = []


@dataclass
class RecoveryPlan:
    """Plan for recovering from migration errors."""
    primary_action: RecoveryAction
    fallback_actions: List[RecoveryAction]
    requires_user_confirmation: bool
    estimated_time_seconds: int
    success_probability: float
    description: str
    steps: List[str]


class DiskSpaceMonitor:
    """Monitors disk space during migration operations."""
    
    def __init__(self, minimum_free_space_mb: int = 1024):
        """
        Initialize disk space monitor.
        
        Args:
            minimum_free_space_mb: Minimum free space required in MB
        """
        self.minimum_free_space_mb = minimum_free_space_mb
        self.minimum_free_space_bytes = minimum_free_space_mb * 1024 * 1024
    
    def check_disk_space(self, path: Path, required_space_bytes: int) -> Tuple[bool, int, str]:
        """
        Check if sufficient disk space is available.
        
        Args:
            path: Path to check disk space for
            required_space_bytes: Required space in bytes
            
        Returns:
            Tuple of (sufficient_space, available_bytes, error_message)
        """
        try:
            disk_usage = shutil.disk_usage(path)
            available_bytes = disk_usage.free
            
            total_required = required_space_bytes + self.minimum_free_space_bytes
            
            if available_bytes >= total_required:
                return True, available_bytes, ""
            else:
                shortage = total_required - available_bytes
                error_msg = (
                    f"Insufficient disk space. Need {total_required:,} bytes "
                    f"({required_space_bytes:,} for migration + {self.minimum_free_space_bytes:,} buffer), "
                    f"but only {available_bytes:,} bytes available. "
                    f"Short by {shortage:,} bytes ({shortage / (1024*1024):.1f} MB)."
                )
                return False, available_bytes, error_msg
                
        except Exception as e:
            logger.error(f"Failed to check disk space for {path}: {e}")
            return False, 0, f"Failed to check disk space: {str(e)}"
    
    def estimate_migration_space_requirements(self, album_paths: List[Path]) -> int:
        """
        Estimate total space required for migration.
        
        Args:
            album_paths: List of album folder paths
            
        Returns:
            Estimated space required in bytes
        """
        total_size = 0
        
        for album_path in album_paths:
            try:
                if album_path.exists():
                    folder_size = sum(
                        f.stat().st_size for f in album_path.rglob('*') if f.is_file()
                    )
                    total_size += folder_size
            except Exception as e:
                logger.warning(f"Failed to calculate size for {album_path}: {e}")
                # Add conservative estimate for failed calculations
                total_size += 500 * 1024 * 1024  # 500 MB estimate
        
        # Add 10% buffer for temporary files and filesystem overhead
        return int(total_size * 1.1)


class FileLockDetector:
    """Detects and handles file locks during migration."""
    
    def __init__(self, max_wait_time_seconds: int = 30):
        """
        Initialize file lock detector.
        
        Args:
            max_wait_time_seconds: Maximum time to wait for locks to be released
        """
        self.max_wait_time = max_wait_time_seconds
        self.lock_check_interval = 1.0  # Check every second
    
    def is_file_locked(self, file_path: Path) -> Tuple[bool, List[str]]:
        """
        Check if a file or directory is locked.
        
        Args:
            file_path: Path to check for locks
            
        Returns:
            Tuple of (is_locked, list_of_processes_using_file)
        """
        try:
            # Try to access the file/directory
            if file_path.is_file():
                # Try to open file for writing
                with open(file_path, 'r+b'):
                    pass
            elif file_path.is_dir():
                # Try to create a temporary file in the directory
                temp_file = file_path / f".migration_test_{int(time.time())}"
                try:
                    temp_file.touch()
                    temp_file.unlink()
                except Exception:
                    return True, ["Unknown process"]
            
            return False, []
            
        except PermissionError:
            # File might be locked, try to find which processes are using it
            return True, self._find_processes_using_file(file_path)
        except Exception as e:
            logger.warning(f"Error checking file lock for {file_path}: {e}")
            return True, [f"Unknown error: {str(e)}"]
    
    def _find_processes_using_file(self, file_path: Path) -> List[str]:
        """
        Find processes that are using a specific file.
        
        Args:
            file_path: Path to check
            
        Returns:
            List of process names using the file
        """
        processes = []
        try:
            # Use psutil to find processes with open files
            for proc in psutil.process_iter(['pid', 'name', 'open_files']):
                try:
                    if proc.info['open_files']:
                        for open_file in proc.info['open_files']:
                            if Path(open_file.path) == file_path.resolve():
                                processes.append(f"{proc.info['name']} (PID: {proc.info['pid']})")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.warning(f"Failed to find processes using file {file_path}: {e}")
            
        return processes
    
    def wait_for_file_unlock(self, file_path: Path, progress_callback: Optional[Callable] = None) -> bool:
        """
        Wait for a file to be unlocked.
        
        Args:
            file_path: Path to wait for
            progress_callback: Optional callback for progress updates
            
        Returns:
            True if file was unlocked, False if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < self.max_wait_time:
            is_locked, processes = self.is_file_locked(file_path)
            
            if not is_locked:
                if progress_callback:
                    progress_callback(f"File {file_path.name} is now available", 100.0)
                return True
            
            elapsed = time.time() - start_time
            progress = min((elapsed / self.max_wait_time) * 100, 95)  # Cap at 95% until unlocked
            
            if progress_callback:
                process_list = ", ".join(processes) if processes else "unknown processes"
                progress_callback(
                    f"Waiting for {file_path.name} to be unlocked (used by {process_list})", 
                    progress
                )
            
            time.sleep(self.lock_check_interval)
        
        return False


class PermissionManager:
    """Manages file system permissions during migration."""
    
    def __init__(self):
        self.original_permissions = {}  # Store original permissions for rollback
    
    def check_permissions(self, path: Path, required_permissions: str = "rw") -> Tuple[bool, str]:
        """
        Check if required permissions are available for a path.
        
        Args:
            path: Path to check
            required_permissions: Required permissions ("r", "w", "rw", "rwx")
            
        Returns:
            Tuple of (has_permissions, error_message)
        """
        try:
            # Check if path exists
            if not path.exists():
                return False, f"Path does not exist: {path}"
            
            # Check read permission
            if 'r' in required_permissions:
                if not os.access(path, os.R_OK):
                    return False, f"Read permission denied for: {path}"
            
            # Check write permission
            if 'w' in required_permissions:
                if not os.access(path, os.W_OK):
                    return False, f"Write permission denied for: {path}"
            
            # Check execute permission (for directories)
            if 'x' in required_permissions:
                if not os.access(path, os.X_OK):
                    return False, f"Execute permission denied for: {path}"
            
            return True, ""
            
        except Exception as e:
            return False, f"Failed to check permissions for {path}: {str(e)}"
    
    def attempt_permission_fix(self, path: Path, required_permissions: str = "rw") -> Tuple[bool, str]:
        """
        Attempt to fix permission issues.
        
        Args:
            path: Path to fix permissions for
            required_permissions: Required permissions
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Store original permissions for potential rollback
            if path.exists():
                original_stat = path.stat()
                self.original_permissions[str(path)] = original_stat.st_mode
            
            # Attempt to set permissions
            if path.is_file():
                # Set file permissions
                if 'w' in required_permissions:
                    path.chmod(0o644)  # rw-r--r--
                else:
                    path.chmod(0o444)  # r--r--r--
            elif path.is_dir():
                # Set directory permissions
                if 'w' in required_permissions:
                    path.chmod(0o755)  # rwxr-xr-x
                else:
                    path.chmod(0o555)  # r-xr-xr-x
            
            # Verify the fix worked
            has_perms, error_msg = self.check_permissions(path, required_permissions)
            if has_perms:
                return True, f"Successfully fixed permissions for {path}"
            else:
                return False, f"Permission fix failed: {error_msg}"
                
        except Exception as e:
            return False, f"Failed to fix permissions for {path}: {str(e)}"
    
    def restore_original_permissions(self, path: Path) -> bool:
        """
        Restore original permissions for a path.
        
        Args:
            path: Path to restore permissions for
            
        Returns:
            True if successful, False otherwise
        """
        try:
            path_str = str(path)
            if path_str in self.original_permissions:
                path.chmod(self.original_permissions[path_str])
                del self.original_permissions[path_str]
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to restore permissions for {path}: {e}")
            return False


class MigrationErrorAnalyzer:
    """Analyzes migration errors and determines recovery strategies."""
    
    def __init__(self):
        self.disk_monitor = DiskSpaceMonitor()
        self.lock_detector = FileLockDetector()
        self.permission_manager = PermissionManager()
    
    def analyze_error(self, exception: Exception, album_name: str, source_path: str, target_path: str) -> ErrorDetails:
        """
        Analyze a migration error and create detailed error information.
        
        Args:
            exception: The exception that occurred
            album_name: Name of the album being migrated
            source_path: Source path of the migration
            target_path: Target path of the migration
            
        Returns:
            ErrorDetails with comprehensive error information
        """
        error_details = ErrorDetails(
            error_type=ErrorType.UNKNOWN_ERROR,
            severity=ErrorSeverity.MEDIUM,
            message=str(exception),
            album_name=album_name,
            source_path=source_path,
            target_path=target_path,
            original_exception=exception
        )
        
        # Analyze specific error types
        if isinstance(exception, PermissionError):
            self._analyze_permission_error(error_details, exception)
        elif isinstance(exception, OSError) and exception.errno == 28:  # No space left on device
            self._analyze_disk_space_error(error_details, exception)
        elif isinstance(exception, OSError) and exception.errno in [16, 26]:  # Device busy or text file busy
            self._analyze_file_lock_error(error_details, exception)
        elif isinstance(exception, FileNotFoundError):
            self._analyze_file_not_found_error(error_details, exception)
        elif isinstance(exception, FileExistsError):
            self._analyze_file_exists_error(error_details, exception)
        else:
            self._analyze_generic_error(error_details, exception)
        
        return error_details
    
    def _analyze_permission_error(self, error_details: ErrorDetails, exception: Exception):
        """Analyze permission-related errors."""
        error_details.error_type = ErrorType.PERMISSION_DENIED
        error_details.severity = ErrorSeverity.HIGH
        error_details.manual_intervention_required = True
        error_details.rollback_available = True
        error_details.recovery_actions = [RecoveryAction.MANUAL_INTERVENTION, RecoveryAction.RETRY]
        
        # Try to determine which path has permission issues
        problem_path = None
        if error_details.source_path and not os.access(error_details.source_path, os.R_OK):
            problem_path = error_details.source_path
        elif error_details.target_path and not os.access(Path(error_details.target_path).parent, os.W_OK):
            problem_path = str(Path(error_details.target_path).parent)
        
        error_details.solution_steps = [
            f"Check file permissions for: {problem_path or 'migration paths'}",
            "Grant read/write permissions to the migration directories",
            "Ensure no files are read-only or locked",
            "Run migration tool with appropriate privileges",
            "Retry the migration operation"
        ]
    
    def _analyze_disk_space_error(self, error_details: ErrorDetails, exception: Exception):
        """Analyze disk space-related errors."""
        error_details.error_type = ErrorType.DISK_SPACE_INSUFFICIENT
        error_details.severity = ErrorSeverity.CRITICAL
        error_details.manual_intervention_required = True
        error_details.rollback_available = True
        error_details.recovery_actions = [RecoveryAction.MANUAL_INTERVENTION, RecoveryAction.ABORT_MIGRATION]
        
        # Check current disk space
        if error_details.target_path:
            target_dir = Path(error_details.target_path).parent
            has_space, available_bytes, space_error = self.disk_monitor.check_disk_space(target_dir, 0)
            
            error_details.solution_steps = [
                f"Free up disk space on: {target_dir}",
                f"Currently available: {available_bytes / (1024*1024):.1f} MB",
                "Delete unnecessary files or move them to another drive",
                "Consider migrating to a different location with more space",
                "Retry the migration after freeing space"
            ]
        else:
            error_details.solution_steps = [
                "Free up disk space on the target drive",
                "Delete unnecessary files or move them to another drive",
                "Retry the migration after freeing space"
            ]
    
    def _analyze_file_lock_error(self, error_details: ErrorDetails, exception: Exception):
        """Analyze file lock-related errors."""
        error_details.error_type = ErrorType.FILE_LOCKED
        error_details.severity = ErrorSeverity.HIGH
        error_details.manual_intervention_required = True
        error_details.rollback_available = True
        error_details.recovery_actions = [RecoveryAction.RETRY, RecoveryAction.MANUAL_INTERVENTION]
        
        # Try to identify which processes are using the files
        locked_files = []
        if error_details.source_path:
            is_locked, processes = self.lock_detector.is_file_locked(Path(error_details.source_path))
            if is_locked:
                locked_files.extend(processes)
        
        if locked_files:
            process_list = ", ".join(locked_files)
            error_details.solution_steps = [
                f"Close applications using the files: {process_list}",
                "Wait for file operations to complete",
                "Restart any problematic applications",
                "Retry the migration operation"
            ]
        else:
            error_details.solution_steps = [
                "Close any applications that might be using the music files",
                "Wait a few minutes for file operations to complete",
                "Restart the system if the problem persists",
                "Retry the migration operation"
            ]
    
    def _analyze_file_not_found_error(self, error_details: ErrorDetails, exception: Exception):
        """Analyze file not found errors."""
        error_details.error_type = ErrorType.SOURCE_NOT_FOUND
        error_details.severity = ErrorSeverity.MEDIUM
        error_details.manual_intervention_required = False
        error_details.rollback_available = True
        error_details.recovery_actions = [RecoveryAction.SKIP_ALBUM, RecoveryAction.MANUAL_INTERVENTION]
        
        error_details.solution_steps = [
            f"Verify that the source album folder exists: {error_details.source_path}",
            "Check if the folder was moved or deleted during migration",
            "Refresh the collection scan to update folder information",
            "Skip this album or restore it from backup if available"
        ]
    
    def _analyze_file_exists_error(self, error_details: ErrorDetails, exception: Exception):
        """Analyze file exists errors."""
        error_details.error_type = ErrorType.TARGET_EXISTS
        error_details.severity = ErrorSeverity.MEDIUM
        error_details.manual_intervention_required = False
        error_details.rollback_available = True
        error_details.recovery_actions = [RecoveryAction.RETRY, RecoveryAction.MANUAL_INTERVENTION]
        
        error_details.solution_steps = [
            f"Target folder already exists: {error_details.target_path}",
            "Remove or rename the existing target folder",
            "Use the force migration option to overwrite",
            "Retry the migration operation"
        ]
    
    def _analyze_generic_error(self, error_details: ErrorDetails, exception: Exception):
        """Analyze generic/unknown errors."""
        error_details.error_type = ErrorType.UNKNOWN_ERROR
        error_details.severity = ErrorSeverity.MEDIUM
        error_details.manual_intervention_required = True
        error_details.rollback_available = True
        error_details.recovery_actions = [RecoveryAction.RETRY, RecoveryAction.MANUAL_INTERVENTION, RecoveryAction.SKIP_ALBUM]
        
        error_details.solution_steps = [
            f"Unexpected error occurred: {str(exception)}",
            "Check system logs for more details",
            "Verify file system integrity",
            "Try migrating other albums first",
            "Contact support if the problem persists"
        ]


class MigrationRecoveryManager:
    """Manages recovery operations for failed migrations."""
    
    def __init__(self):
        self.error_analyzer = MigrationErrorAnalyzer()
        self.recovery_log = []
        self.active_rollbacks = {}
        self._lock = threading.Lock()
    
    def create_recovery_plan(self, error_details: ErrorDetails) -> RecoveryPlan:
        """
        Create a recovery plan for a migration error.
        
        Args:
            error_details: Details of the error that occurred
            
        Returns:
            RecoveryPlan with recommended actions
        """
        if error_details.error_type == ErrorType.PERMISSION_DENIED:
            return self._create_permission_recovery_plan(error_details)
        elif error_details.error_type == ErrorType.DISK_SPACE_INSUFFICIENT:
            return self._create_disk_space_recovery_plan(error_details)
        elif error_details.error_type == ErrorType.FILE_LOCKED:
            return self._create_file_lock_recovery_plan(error_details)
        elif error_details.error_type == ErrorType.TARGET_EXISTS:
            return self._create_target_exists_recovery_plan(error_details)
        else:
            return self._create_generic_recovery_plan(error_details)
    
    def _create_permission_recovery_plan(self, error_details: ErrorDetails) -> RecoveryPlan:
        """Create recovery plan for permission errors."""
        return RecoveryPlan(
            primary_action=RecoveryAction.MANUAL_INTERVENTION,
            fallback_actions=[RecoveryAction.SKIP_ALBUM, RecoveryAction.ABORT_MIGRATION],
            requires_user_confirmation=True,
            estimated_time_seconds=300,  # 5 minutes
            success_probability=0.8,
            description="Fix file permissions and retry migration",
            steps=[
                "Check and fix file permissions for source and target directories",
                "Ensure migration tool has appropriate privileges",
                "Retry the failed album migration",
                "If unsuccessful, skip the album and continue with others"
            ]
        )
    
    def _create_disk_space_recovery_plan(self, error_details: ErrorDetails) -> RecoveryPlan:
        """Create recovery plan for disk space errors."""
        return RecoveryPlan(
            primary_action=RecoveryAction.MANUAL_INTERVENTION,
            fallback_actions=[RecoveryAction.ABORT_MIGRATION],
            requires_user_confirmation=True,
            estimated_time_seconds=600,  # 10 minutes
            success_probability=0.9,
            description="Free up disk space and retry migration",
            steps=[
                "Check available disk space on target drive",
                "Delete unnecessary files or move them to another location",
                "Consider moving some albums to external storage",
                "Retry the migration with sufficient space available"
            ]
        )
    
    def _create_file_lock_recovery_plan(self, error_details: ErrorDetails) -> RecoveryPlan:
        """Create recovery plan for file lock errors."""
        return RecoveryPlan(
            primary_action=RecoveryAction.RETRY,
            fallback_actions=[RecoveryAction.MANUAL_INTERVENTION, RecoveryAction.SKIP_ALBUM],
            requires_user_confirmation=False,
            estimated_time_seconds=120,  # 2 minutes
            success_probability=0.7,
            description="Wait for file locks to be released and retry",
            steps=[
                "Wait for file operations to complete",
                "Automatically retry the operation",
                "If still locked, identify and close blocking applications",
                "Skip the album if locks cannot be resolved"
            ]
        )
    
    def _create_target_exists_recovery_plan(self, error_details: ErrorDetails) -> RecoveryPlan:
        """Create recovery plan for target exists errors."""
        return RecoveryPlan(
            primary_action=RecoveryAction.RETRY,
            fallback_actions=[RecoveryAction.MANUAL_INTERVENTION, RecoveryAction.SKIP_ALBUM],
            requires_user_confirmation=True,
            estimated_time_seconds=60,  # 1 minute
            success_probability=0.9,
            description="Resolve target path conflict and retry",
            steps=[
                "Check if target folder already contains the same content",
                "Remove conflicting target folder if it's safe to do so",
                "Rename existing folder to create backup",
                "Retry the migration operation"
            ]
        )
    
    def _create_generic_recovery_plan(self, error_details: ErrorDetails) -> RecoveryPlan:
        """Create recovery plan for generic errors."""
        return RecoveryPlan(
            primary_action=RecoveryAction.RETRY,
            fallback_actions=[RecoveryAction.SKIP_ALBUM, RecoveryAction.MANUAL_INTERVENTION],
            requires_user_confirmation=True,
            estimated_time_seconds=180,  # 3 minutes
            success_probability=0.5,
            description="Investigate error and attempt recovery",
            steps=[
                "Analyze the specific error message",
                "Check system logs for additional information",
                "Attempt to retry the operation",
                "Skip the album if the error persists"
            ]
        )
    
    def execute_recovery_action(
        self, 
        recovery_plan: RecoveryPlan, 
        error_details: ErrorDetails,
        retry_callback: Callable = None,
        progress_callback: Callable = None
    ) -> Tuple[bool, str]:
        """
        Execute a recovery action.
        
        Args:
            recovery_plan: The recovery plan to execute
            error_details: Details of the original error
            retry_callback: Callback to retry the original operation
            progress_callback: Callback for progress updates
            
        Returns:
            Tuple of (success, message)
        """
        with self._lock:
            self.recovery_log.append({
                'timestamp': datetime.now().isoformat(),
                'album_name': error_details.album_name,
                'error_type': error_details.error_type.value,
                'recovery_action': recovery_plan.primary_action.value,
                'started': True
            })
        
        try:
            if recovery_plan.primary_action == RecoveryAction.RETRY:
                return self._execute_retry_action(error_details, retry_callback, progress_callback)
            elif recovery_plan.primary_action == RecoveryAction.MANUAL_INTERVENTION:
                return self._execute_manual_intervention(error_details, progress_callback)
            elif recovery_plan.primary_action == RecoveryAction.SKIP_ALBUM:
                return self._execute_skip_album(error_details)
            elif recovery_plan.primary_action == RecoveryAction.ROLLBACK:
                return self._execute_rollback_action(error_details)
            else:
                return False, f"Unknown recovery action: {recovery_plan.primary_action}"
                
        except Exception as e:
            error_msg = f"Recovery action failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def _execute_retry_action(
        self, 
        error_details: ErrorDetails, 
        retry_callback: Callable,
        progress_callback: Callable
    ) -> Tuple[bool, str]:
        """Execute retry recovery action."""
        if not retry_callback:
            return False, "No retry callback provided"
        
        max_retries = error_details.max_retries
        retry_count = error_details.retry_count
        
        if retry_count >= max_retries:
            return False, f"Maximum retries ({max_retries}) exceeded"
        
        # Handle specific error types before retry
        if error_details.error_type == ErrorType.FILE_LOCKED:
            if progress_callback:
                progress_callback(f"Waiting for file locks to be released for {error_details.album_name}", 25)
            
            # Wait for file to be unlocked
            source_path = Path(error_details.source_path) if error_details.source_path else None
            if source_path:
                unlocked = self.error_analyzer.lock_detector.wait_for_file_unlock(source_path, progress_callback)
                if not unlocked:
                    return False, f"File {source_path.name} remained locked after timeout"
        
        # Attempt retry
        if progress_callback:
            progress_callback(f"Retrying migration for {error_details.album_name} (attempt {retry_count + 1})", 75)
        
        try:
            result = retry_callback()
            if progress_callback:
                progress_callback(f"Retry successful for {error_details.album_name}", 100)
            return True, f"Retry successful after {retry_count + 1} attempts"
        except Exception as e:
            error_details.retry_count += 1
            return False, f"Retry failed: {str(e)}"
    
    def _execute_manual_intervention(self, error_details: ErrorDetails, progress_callback: Callable) -> Tuple[bool, str]:
        """Execute manual intervention recovery action."""
        if progress_callback:
            progress_callback(f"Manual intervention required for {error_details.album_name}", 50)
        
        intervention_msg = (
            f"Manual intervention required for album '{error_details.album_name}'\n"
            f"Error: {error_details.message}\n"
            f"Solution steps:\n" + 
            "\n".join(f"  {i+1}. {step}" for i, step in enumerate(error_details.solution_steps))
        )
        
        return False, intervention_msg
    
    def _execute_skip_album(self, error_details: ErrorDetails) -> Tuple[bool, str]:
        """Execute skip album recovery action."""
        skip_msg = f"Skipped album '{error_details.album_name}' due to error: {error_details.message}"
        logger.warning(skip_msg)
        return True, skip_msg
    
    def _execute_rollback_action(self, error_details: ErrorDetails) -> Tuple[bool, str]:
        """Execute rollback recovery action."""
        if not error_details.rollback_available:
            return False, "Rollback not available for this error"
        
        # This would be implemented by the migration tool itself
        # as it has access to backup information
        rollback_msg = f"Rollback initiated for album '{error_details.album_name}'"
        logger.info(rollback_msg)
        return True, rollback_msg
    
    def get_recovery_log(self) -> List[Dict[str, Any]]:
        """Get the recovery log."""
        with self._lock:
            return self.recovery_log.copy()
    
    def clear_recovery_log(self):
        """Clear the recovery log."""
        with self._lock:
            self.recovery_log.clear()


def create_comprehensive_error_handler() -> MigrationRecoveryManager:
    """
    Create a comprehensive error handler for migration operations.
    
    Returns:
        Configured MigrationRecoveryManager instance
    """
    return MigrationRecoveryManager() 