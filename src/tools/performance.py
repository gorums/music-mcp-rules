"""
Performance monitoring and optimization utilities for Music Collection MCP Server.

This module provides tools for tracking file system operations, memory usage,
and performance benchmarks to optimize large collection handling.
"""

import functools
import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, TypeVar
import threading

# Try to import psutil for memory monitoring
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

F = TypeVar('F', bound=Callable[..., Any])

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    memory_start: Optional[float] = None
    memory_end: Optional[float] = None
    memory_delta: Optional[float] = None
    items_processed: int = 0
    file_operations: int = 0
    directory_operations: int = 0
    errors: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def finish(self) -> None:
        """Mark operation as finished and calculate duration."""
        if self.end_time is None:
            self.end_time = time.time()
            self.duration = self.end_time - self.start_time
            
            # Calculate memory delta if available
            if HAS_PSUTIL and self.memory_start is not None:
                current_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                self.memory_end = current_memory
                self.memory_delta = current_memory - self.memory_start
    
    @property
    def items_per_second(self) -> Optional[float]:
        """Calculate items processed per second."""
        if self.duration and self.duration > 0 and self.items_processed > 0:
            return self.items_processed / self.duration
        return None
    
    @property
    def files_per_second(self) -> Optional[float]:
        """Calculate file operations per second."""
        if self.duration and self.duration > 0 and self.file_operations > 0:
            return self.file_operations / self.duration
        return None


class PerformanceTracker:
    """
    Thread-safe performance tracking for file system operations.
    """
    
    def __init__(self):
        self._metrics: List[PerformanceMetrics] = []
        self._lock = threading.Lock()
        self._current_operation: Optional[PerformanceMetrics] = None
    
    def start_operation(self, operation_name: str, **metadata) -> PerformanceMetrics:
        """Start tracking a new operation."""
        with self._lock:
            metrics = PerformanceMetrics(
                operation_name=operation_name,
                start_time=time.time(),
                metadata=metadata
            )
            
            # Add memory tracking if available
            if HAS_PSUTIL:
                try:
                    metrics.memory_start = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                except Exception:
                    pass  # Ignore memory tracking errors
            
            self._current_operation = metrics
            return metrics
    
    def finish_operation(self, metrics: PerformanceMetrics) -> None:
        """Finish tracking an operation."""
        with self._lock:
            metrics.finish()
            self._metrics.append(metrics)
            if self._current_operation is metrics:
                self._current_operation = None
    
    def get_current_operation(self) -> Optional[PerformanceMetrics]:
        """Get the currently tracked operation."""
        with self._lock:
            return self._current_operation
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all tracked operations."""
        with self._lock:
            if not self._metrics:
                return {"total_operations": 0}
            
            total_duration = sum(m.duration for m in self._metrics if m.duration)
            total_items = sum(m.items_processed for m in self._metrics)
            total_files = sum(m.file_operations for m in self._metrics)
            total_dirs = sum(m.directory_operations for m in self._metrics)
            total_errors = sum(m.errors for m in self._metrics)
            
            # Memory statistics if available
            memory_stats = {}
            if HAS_PSUTIL:
                memory_deltas = [m.memory_delta for m in self._metrics if m.memory_delta is not None]
                if memory_deltas:
                    memory_stats = {
                        "max_memory_increase_mb": max(memory_deltas),
                        "total_memory_delta_mb": sum(memory_deltas),
                        "avg_memory_delta_mb": sum(memory_deltas) / len(memory_deltas)
                    }
            
            return {
                "total_operations": len(self._metrics),
                "total_duration_seconds": total_duration,
                "total_items_processed": total_items,
                "total_file_operations": total_files,
                "total_directory_operations": total_dirs,
                "total_errors": total_errors,
                "avg_items_per_second": total_items / total_duration if total_duration > 0 else 0,
                "avg_files_per_second": total_files / total_duration if total_duration > 0 else 0,
                **memory_stats
            }
    
    def clear_metrics(self) -> None:
        """Clear all tracked metrics."""
        with self._lock:
            self._metrics.clear()
            self._current_operation = None


# Global performance tracker instance
_global_tracker = PerformanceTracker()


@contextmanager
def track_operation(operation_name: str, **metadata) -> Generator[PerformanceMetrics, None, None]:
    """
    Context manager for tracking operation performance.
    
    Args:
        operation_name: Name of the operation being tracked
        **metadata: Additional metadata to store with metrics
        
    Yields:
        PerformanceMetrics: Metrics object for the operation
    """
    metrics = _global_tracker.start_operation(operation_name, **metadata)
    try:
        yield metrics
    finally:
        _global_tracker.finish_operation(metrics)


def performance_monitor(operation_name: Optional[str] = None, track_memory: bool = True):
    """
    Decorator for monitoring function performance.
    
    Args:
        operation_name: Name for the operation (defaults to function name)
        track_memory: Whether to track memory usage
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            name = operation_name or f"{func.__module__}.{func.__name__}"
            with track_operation(name, track_memory=track_memory) as metrics:
                try:
                    result = func(*args, **kwargs)
                    # Try to extract item count from result if it's a dict/list
                    if isinstance(result, dict):
                        if 'bands_discovered' in result:
                            metrics.items_processed = result['bands_discovered']
                        elif 'albums_discovered' in result:
                            metrics.items_processed = result['albums_discovered']
                        elif 'bands' in result and isinstance(result['bands'], list):
                            metrics.items_processed = len(result['bands'])
                    elif isinstance(result, (list, tuple)):
                        metrics.items_processed = len(result)
                    return result
                except Exception as e:
                    metrics.errors += 1
                    raise
        return wrapper
    return decorator


def get_performance_summary() -> Dict[str, Any]:
    """Get summary of all tracked performance metrics."""
    return _global_tracker.get_metrics_summary()


def clear_performance_metrics() -> None:
    """Clear all tracked performance metrics."""
    _global_tracker.clear_metrics()


class BatchFileOperations:
    """
    Optimized batch file system operations.
    """
    
    @staticmethod
    def scan_directory_batch(directory: Path, pattern: str = "*", 
                           recursive: bool = False, exclude_hidden: bool = True) -> List[Path]:
        """
        Efficiently scan directory using os.scandir for better performance.
        
        Args:
            directory: Directory to scan
            pattern: File pattern to match (not implemented yet, for future use)
            recursive: Whether to scan recursively
            exclude_hidden: Whether to exclude hidden files/directories
            
        Returns:
            List of paths matching criteria
        """
        results = []
        
        try:
            with track_operation("batch_directory_scan", 
                               directory=str(directory), recursive=recursive) as metrics:
                
                # Use os.scandir for better performance than pathlib
                import os
                with os.scandir(directory) as entries:
                    for entry in entries:
                        metrics.directory_operations += 1
                        
                        # Skip hidden files if requested
                        if exclude_hidden and entry.name.startswith('.'):
                            continue
                        
                        if entry.is_dir():
                            results.append(Path(entry.path))
                            
                            # Recursive scanning if requested
                            if recursive:
                                try:
                                    sub_results = BatchFileOperations.scan_directory_batch(
                                        Path(entry.path), pattern, recursive, exclude_hidden
                                    )
                                    results.extend(sub_results)
                                except (PermissionError, OSError) as e:
                                    logger.warning(f"Skipping inaccessible directory {entry.path}: {e}")
                                    metrics.errors += 1
                        elif entry.is_file():
                            results.append(Path(entry.path))
                            metrics.file_operations += 1
                
                metrics.items_processed = len(results)
                
        except (PermissionError, OSError) as e:
            logger.error(f"Error scanning directory {directory}: {e}")
            raise
        
        return results
    
    @staticmethod
    def count_files_in_directory(directory: Path, extensions: set = None) -> int:
        """
        Efficiently count files in directory with optional extension filtering.
        
        Args:
            directory: Directory to scan
            extensions: Set of allowed extensions (e.g., {'.mp3', '.flac'})
            
        Returns:
            Number of matching files
        """
        count = 0
        
        try:
            with track_operation("count_files", directory=str(directory)) as metrics:
                import os
                with os.scandir(directory) as entries:
                    for entry in entries:
                        if entry.is_file():
                            metrics.file_operations += 1
                            if extensions is None:
                                count += 1
                            else:
                                # Check extension efficiently
                                _, ext = os.path.splitext(entry.name.lower())
                                if ext in extensions:
                                    count += 1
                
                metrics.items_processed = count
                
        except (PermissionError, OSError):
            # Return 0 for inaccessible directories
            pass
        
        return count


class ProgressReporter:
    """
    Progress reporting for long-running operations.
    """
    
    def __init__(self, total_items: int, operation_name: str = "Operation"):
        self.total_items = total_items
        self.operation_name = operation_name
        self.processed_items = 0
        self.start_time = time.time()
        self.last_report_time = self.start_time
        self.report_interval = 1.0  # Report every second
    
    def update(self, increment: int = 1) -> None:
        """Update progress and log if needed."""
        self.processed_items += increment
        current_time = time.time()
        
        # Report progress at intervals
        if current_time - self.last_report_time >= self.report_interval:
            self._report_progress()
            self.last_report_time = current_time
    
    def _report_progress(self) -> None:
        """Log current progress."""
        if self.total_items > 0:
            percentage = (self.processed_items / self.total_items) * 100
            elapsed = time.time() - self.start_time
            
            if self.processed_items > 0 and elapsed > 0:
                rate = self.processed_items / elapsed
                eta_seconds = (self.total_items - self.processed_items) / rate if rate > 0 else 0
                eta_str = f", ETA: {eta_seconds:.0f}s" if eta_seconds > 0 else ""
            else:
                eta_str = ""
            
            logger.info(f"{self.operation_name}: {self.processed_items}/{self.total_items} "
                       f"({percentage:.1f}%) - {elapsed:.1f}s elapsed{eta_str}")
    
    def finish(self) -> None:
        """Log completion."""
        elapsed = time.time() - self.start_time
        rate = self.processed_items / elapsed if elapsed > 0 else 0
        logger.info(f"{self.operation_name} completed: {self.processed_items} items "
                   f"in {elapsed:.1f}s ({rate:.1f} items/sec)") 