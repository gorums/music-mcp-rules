"""
Tests for performance optimizations to ensure business logic is preserved.

This module verifies that the performance optimizations in scanner.py and storage.py
maintain the same functionality while improving performance.
"""

import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

from src.tools.scanner import scan_music_folders
from src.tools.storage import get_band_list, load_collection_index
from src.tools.performance import (
    get_performance_summary,
    clear_performance_metrics,
    BatchFileOperations,
    ProgressReporter,
    track_operation
)


class TestPerformanceOptimizations(unittest.TestCase):
    """Test that performance optimizations preserve business logic."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        # Clear performance metrics before each test
        clear_performance_metrics()
        
        # Mock config to use our test directory
        self.config_patcher = patch('src.di.get_config')
        self.mock_config = self.config_patcher.start()
        self.mock_config.return_value.MUSIC_ROOT_PATH = self.temp_dir
        self.mock_config.return_value.CACHE_DURATION_DAYS = 30
        
        # Also patch the scanner module's get_config calls
        self.scanner_config_patcher = patch('src.tools.scanner.get_config')
        self.mock_scanner_config = self.scanner_config_patcher.start()
        self.mock_scanner_config.return_value.MUSIC_ROOT_PATH = self.temp_dir
        self.mock_scanner_config.return_value.CACHE_DURATION_DAYS = 30
        
        # Patch storage module's get_config calls
        self.storage_config_patcher = patch('src.tools.storage.get_config')
        self.mock_storage_config = self.storage_config_patcher.start()
        self.mock_storage_config.return_value.MUSIC_ROOT_PATH = self.temp_dir
        self.mock_storage_config.return_value.CACHE_DURATION_DAYS = 30

    def tearDown(self):
        """Clean up test environment."""
        self.config_patcher.stop()
        self.scanner_config_patcher.stop()
        self.storage_config_patcher.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        clear_performance_metrics()

    def _create_test_collection(self, num_bands=5, albums_per_band=3):
        """Create a test music collection."""
        collection_path = Path(self.temp_dir)
        
        for i in range(num_bands):
            band_name = f"Test Band {i:02d}"
            band_path = collection_path / band_name
            band_path.mkdir()
            
            # Create albums
            for j in range(albums_per_band):
                album_name = f"2020 - Album {j:02d}"
                album_path = band_path / album_name
                album_path.mkdir()
                
                # Create some music files
                for k in range(5):  # 5 tracks per album
                    track_file = album_path / f"track_{k:02d}.mp3"
                    track_file.write_text("fake music file")

    def test_batch_file_operations_functionality(self):
        """Test that BatchFileOperations preserves directory scanning functionality."""
        # Create test structure
        test_dir = Path(self.temp_dir) / "test_dir"
        test_dir.mkdir()
        
        # Create some files and directories
        (test_dir / "file1.txt").write_text("test")
        (test_dir / "file2.mp3").write_text("music")
        (test_dir / ".hidden").write_text("hidden")
        (test_dir / "subdir").mkdir()
        
        # Test batch scanning
        results = BatchFileOperations.scan_directory_batch(test_dir)
        
        # Should find files and directories, but not hidden files
        self.assertGreater(len(results), 0)
        filenames = [r.name for r in results]
        self.assertIn("file1.txt", filenames)
        self.assertIn("file2.mp3", filenames)
        self.assertIn("subdir", filenames)
        self.assertNotIn(".hidden", filenames)

    def test_batch_file_counting_functionality(self):
        """Test that BatchFileOperations file counting works correctly."""
        # Create test structure
        test_dir = Path(self.temp_dir) / "test_dir"
        test_dir.mkdir()
        
        # Create music files
        music_extensions = {'.mp3', '.flac', '.wav'}
        (test_dir / "song1.mp3").write_text("music")
        (test_dir / "song2.flac").write_text("music")
        (test_dir / "song3.wav").write_text("music")
        (test_dir / "document.txt").write_text("not music")
        
        # Test file counting
        count = BatchFileOperations.count_files_in_directory(test_dir, music_extensions)
        
        # Should count only music files
        self.assertEqual(count, 3)

    def test_scan_with_performance_monitoring(self):
        """Test that scan_music_folders works with performance monitoring."""
        # Create test collection
        self._create_test_collection(num_bands=3, albums_per_band=2)
        
        # Clear metrics before test
        clear_performance_metrics()
        
        # Run scan with performance monitoring
        result = scan_music_folders()
        
        # Verify scan works correctly
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['results']['bands_discovered'], 3)
        self.assertGreater(result['results']['albums_discovered'], 0)
        
        # Verify performance metrics are included
        self.assertIn('performance_metrics', result)
        metrics = result['performance_metrics']
        self.assertIn('total_operations', metrics)
        self.assertGreater(metrics['total_operations'], 0)

    def test_get_band_list_with_performance_monitoring(self):
        """Test that get_band_list works with performance monitoring."""
        # Create test collection and scan it first
        self._create_test_collection(num_bands=2, albums_per_band=2)
        scan_result = scan_music_folders()
        self.assertEqual(scan_result['status'], 'success')
        
        # Clear metrics before test
        clear_performance_metrics()
        
        # Run get_band_list with performance monitoring
        result = get_band_list(page_size=10)
        
        # Verify function works correctly
        self.assertEqual(result['status'], 'success')
        self.assertIn('bands', result)
        self.assertLessEqual(len(result['bands']), 10)  # Should respect page_size
        
        # Verify performance was tracked
        metrics = get_performance_summary()
        self.assertGreater(metrics['total_operations'], 0)

    def test_progress_reporter_functionality(self):
        """Test ProgressReporter functionality."""
        # Create progress reporter
        reporter = ProgressReporter(total_items=10, operation_name="Test Operation")
        
        # Simulate progress updates
        for i in range(5):
            reporter.update()
        
        # Check progress
        self.assertEqual(reporter.processed_items, 5)
        self.assertEqual(reporter.total_items, 10)
        
        # Finish and check completion
        reporter.finish()
        # Should not raise any exceptions

    def test_track_operation_context_manager(self):
        """Test track_operation context manager."""
        clear_performance_metrics()
        
        # Use track_operation context manager
        with track_operation("test_operation") as metrics:
            # Simulate some work
            metrics.items_processed = 5
            metrics.file_operations = 10
        
        # Verify metrics were recorded
        summary = get_performance_summary()
        self.assertEqual(summary['total_operations'], 1)
        self.assertEqual(summary['total_items_processed'], 5)
        self.assertEqual(summary['total_file_operations'], 10)

    def test_caching_preserves_functionality(self):
        """Test that caching in storage operations preserves functionality."""
        # Create test collection and scan it
        self._create_test_collection(num_bands=2)
        scan_result = scan_music_folders()
        self.assertEqual(scan_result['status'], 'success')
        
        # First call to get_band_list (should load from file)
        result1 = get_band_list()
        self.assertEqual(result1['status'], 'success')
        
        # Second call to get_band_list (should use cache)
        result2 = get_band_list()
        self.assertEqual(result2['status'], 'success')
        
        # Results should be identical
        self.assertEqual(result1['total_bands'], result2['total_bands'])
        self.assertEqual(len(result1['bands']), len(result2['bands']))

    def test_performance_optimizations_preserve_scan_results(self):
        """Test that performance optimizations don't change scan results."""
        # Create test collection
        self._create_test_collection(num_bands=3, albums_per_band=2)
        
        # Run optimized scan
        result = scan_music_folders()
        
        # Verify all expected results are present
        self.assertEqual(result['status'], 'success')
        
        # Check scan results structure
        scan_results = result['results']
        self.assertIn('bands_discovered', scan_results)
        self.assertIn('albums_discovered', scan_results)
        self.assertIn('total_tracks', scan_results)
        self.assertIn('bands', scan_results)
        
        # Verify band data is complete
        self.assertEqual(scan_results['bands_discovered'], 3)
        self.assertEqual(len(scan_results['bands']), 3)
        
        # Each band should have expected structure
        for band in scan_results['bands']:
            self.assertIn('band_name', band)
            self.assertIn('albums_count', band)
            self.assertIn('total_tracks', band)
            self.assertIn('folder_path', band)

    def test_large_collection_performance_improvement(self):
        """Test performance with larger collection (simulated)."""
        # Create slightly larger test collection
        self._create_test_collection(num_bands=10, albums_per_band=3)
        
        clear_performance_metrics()
        
        # Run scan and measure performance
        result = scan_music_folders()
        
        # Verify scan completed successfully
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['results']['bands_discovered'], 10)
        
        # Verify performance metrics are available
        metrics = get_performance_summary()
        self.assertGreater(metrics['total_operations'], 0)
        self.assertGreater(metrics['total_items_processed'], 0)
        
        # Performance should complete in reasonable time (this is more of a smoke test)
        if 'total_duration_seconds' in metrics:
            # Should complete within 30 seconds for this size collection
            self.assertLess(metrics['total_duration_seconds'], 30)

    def test_optimized_file_operations_preserve_counts(self):
        """Test that optimized file operations preserve accurate counts."""
        # Create test album with known file count
        album_dir = Path(self.temp_dir) / "test_album"
        album_dir.mkdir()
        
        # Create specific number of music files
        music_extensions = {'.mp3', '.flac', '.wav', '.aac', '.m4a', '.ogg', '.wma'}
        expected_count = 7
        
        for i, ext in enumerate(music_extensions):
            (album_dir / f"track_{i:02d}{ext}").write_text("music file")
        
        # Also create non-music files (should not be counted)
        (album_dir / "artwork.jpg").write_text("image")
        (album_dir / "info.txt").write_text("text")
        
        # Import optimized function
        from src.tools.scanner import _count_music_files
        
        # Test optimized file counting
        count = _count_music_files(album_dir)
        
        # Should count only music files
        self.assertEqual(count, expected_count)


if __name__ == '__main__':
    unittest.main() 