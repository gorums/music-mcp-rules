"""
Test collection statistics calculation.

This module tests that collection statistics are correctly calculated
when the collection index is updated, ensuring the fix for the stats
calculation bug is working properly.
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from pathlib import Path

from src.models.collection import CollectionIndex, CollectionStats, BandIndexEntry
from src.tools.storage import update_collection_index


class TestCollectionStats(unittest.TestCase):
    """Test collection statistics calculation."""

    def test_stats_calculation_on_update(self):
        """Test that stats are recalculated when collection index is updated."""
        # Create test band entries
        band1 = BandIndexEntry(
            name="Test Band 1",
            albums_count=10,
            local_albums_count=7,
            folder_path="Test Band 1",
            missing_albums_count=3,
            has_metadata=True,
            last_updated=datetime.now().isoformat()
        )
        
        band2 = BandIndexEntry(
            name="Test Band 2", 
            albums_count=15,
            local_albums_count=10,
            folder_path="Test Band 2",
            missing_albums_count=5,
            has_metadata=True,
            last_updated=datetime.now().isoformat()
        )
        
        # Create collection index with bands
        collection_index = CollectionIndex(bands=[band1, band2])
        
        # Verify initial stats are correct
        self.assertEqual(collection_index.stats.total_bands, 2)
        self.assertEqual(collection_index.stats.total_albums, 25)  # 10 + 15
        self.assertEqual(collection_index.stats.total_local_albums, 17)  # 7 + 10
        self.assertEqual(collection_index.stats.total_missing_albums, 8)  # 3 + 5
        self.assertEqual(collection_index.stats.bands_with_metadata, 2)
        self.assertEqual(collection_index.stats.avg_albums_per_band, 12.5)  # 25/2
        
        # Calculate expected completion percentage
        expected_completion = (17 / 25) * 100  # (17/25) * 100 = 68%
        self.assertEqual(collection_index.stats.completion_percentage, 68.0)
        
        # Mock the storage operations
        with patch('src.tools.storage.JSONStorage.save_json') as mock_save, \
             patch('src.tools.storage.Config') as mock_config:
            
            # Setup mocks
            mock_config.return_value.MUSIC_ROOT_PATH = "/test/music"
            
            # Update collection index (this should trigger _update_stats)
            result = update_collection_index(collection_index)
            
            # Verify update was successful
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["total_bands"], 2)
            self.assertEqual(result["total_albums"], 25)
            
            # Verify save was called
            mock_save.assert_called_once()

    def test_stats_calculation_with_no_bands(self):
        """Test stats calculation with empty collection."""
        collection_index = CollectionIndex(bands=[])
        
        self.assertEqual(collection_index.stats.total_bands, 0)
        self.assertEqual(collection_index.stats.total_albums, 0)
        self.assertEqual(collection_index.stats.total_missing_albums, 0)
        self.assertEqual(collection_index.stats.bands_with_metadata, 0)
        self.assertEqual(collection_index.stats.avg_albums_per_band, 0.0)
        self.assertEqual(collection_index.stats.completion_percentage, 100.0)

    def test_stats_calculation_with_no_missing_albums(self):
        """Test stats calculation when no albums are missing."""
        band = BandIndexEntry(
            name="Complete Band",
            albums_count=5,
            local_albums_count=5,
            folder_path="Complete Band",
            missing_albums_count=0,
            has_metadata=True,
            last_updated=datetime.now().isoformat()
        )
        
        collection_index = CollectionIndex(bands=[band])
        
        self.assertEqual(collection_index.stats.total_albums, 5)
        self.assertEqual(collection_index.stats.total_local_albums, 5)
        self.assertEqual(collection_index.stats.total_missing_albums, 0)
        self.assertEqual(collection_index.stats.completion_percentage, 100.0)

    def test_stats_calculation_with_all_missing_albums(self):
        """Test stats calculation when all albums are missing."""
        band = BandIndexEntry(
            name="Missing Band",
            albums_count=8,
            local_albums_count=0,
            folder_path="Missing Band", 
            missing_albums_count=8,
            has_metadata=True,
            last_updated=datetime.now().isoformat()
        )
        
        collection_index = CollectionIndex(bands=[band])
        
        self.assertEqual(collection_index.stats.total_albums, 8)
        self.assertEqual(collection_index.stats.total_local_albums, 0)
        self.assertEqual(collection_index.stats.total_missing_albums, 8)
        self.assertEqual(collection_index.stats.completion_percentage, 0.0)

    def test_add_band_updates_stats(self):
        """Test that adding a band updates statistics."""
        collection_index = CollectionIndex()
        
        # Initially empty
        self.assertEqual(collection_index.stats.total_bands, 0)
        self.assertEqual(collection_index.stats.total_albums, 0)
        
        # Add a band
        band = BandIndexEntry(
            name="New Band",
            albums_count=7,
            local_albums_count=5,
            folder_path="New Band",
            missing_albums_count=2,
            has_metadata=True,
            last_updated=datetime.now().isoformat()
        )
        
        collection_index.add_band(band)
        
        # Stats should be updated
        self.assertEqual(collection_index.stats.total_bands, 1)
        self.assertEqual(collection_index.stats.total_albums, 7)
        self.assertEqual(collection_index.stats.total_local_albums, 5)
        self.assertEqual(collection_index.stats.total_missing_albums, 2)
        self.assertEqual(collection_index.stats.completion_percentage, round((5/7) * 100, 2))

    def test_remove_band_updates_stats(self):
        """Test that removing a band updates statistics."""
        band1 = BandIndexEntry(
            name="Band 1",
            albums_count=5,
            local_albums_count=4,
            folder_path="Band 1",
            missing_albums_count=1,
            has_metadata=True,
            last_updated=datetime.now().isoformat()
        )
        
        band2 = BandIndexEntry(
            name="Band 2",
            albums_count=3,
            local_albums_count=3,
            folder_path="Band 2", 
            missing_albums_count=0,
            has_metadata=False,
            last_updated=datetime.now().isoformat()
        )
        
        collection_index = CollectionIndex(bands=[band1, band2])
        
        # Initial stats
        self.assertEqual(collection_index.stats.total_bands, 2)
        self.assertEqual(collection_index.stats.total_albums, 8)
        self.assertEqual(collection_index.stats.total_local_albums, 7)
        self.assertEqual(collection_index.stats.bands_with_metadata, 1)
        
        # Remove a band
        removed = collection_index.remove_band("Band 2")
        self.assertTrue(removed)
        
        # Stats should be updated
        self.assertEqual(collection_index.stats.total_bands, 1)
        self.assertEqual(collection_index.stats.total_albums, 5)
        self.assertEqual(collection_index.stats.total_local_albums, 4)
        self.assertEqual(collection_index.stats.total_missing_albums, 1)
        self.assertEqual(collection_index.stats.bands_with_metadata, 1)


if __name__ == '__main__':
    unittest.main() 