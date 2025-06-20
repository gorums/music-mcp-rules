"""
Basic test for band structure detection to verify core functionality.
"""

import tempfile
import shutil
from pathlib import Path

from src.models.band_structure import (
    StructureType,
    BandStructureDetector
)

def test_basic_functionality():
    """Test basic band structure detection functionality."""
    
    detector = BandStructureDetector()
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create a simple test band with default structure
        band_path = Path(temp_dir) / "TestBand"
        band_path.mkdir()
        
        # Create some albums with default structure
        (band_path / "2010 - Album One").mkdir()
        (band_path / "2012 - Album Two (Deluxe Edition)").mkdir()
        (band_path / "2015 - Album Three").mkdir()
        
        # Add some music files to make it realistic
        for album_folder in band_path.iterdir():
            if album_folder.is_dir():
                for i in range(5):
                    (album_folder / f"track_{i+1}.mp3").touch()
        
        # Test detection
        result = detector.detect_band_structure(str(band_path))
        
        print(f"Structure Type: {result.structure_type}")
        print(f"Consistency: {result.consistency}")
        print(f"Albums Analyzed: {result.albums_analyzed}")
        print(f"Albums with Year: {result.albums_with_year_prefix}")
        print(f"Structure Score: {result.structure_score}")
        print(f"Detected Patterns: {result.detected_patterns}")
        print(f"Recommendations: {result.recommendations}")
        
        # Basic assertions
        assert result.structure_type in [StructureType.DEFAULT, StructureType.LEGACY, StructureType.MIXED, StructureType.ENHANCED]
        assert result.albums_analyzed == 3
        assert result.structure_score >= 0
        
        print("✅ Basic band structure detection is working!")
        
    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    test_basic_functionality() 
