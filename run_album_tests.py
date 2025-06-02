#!/usr/bin/env python3
"""
Run enhanced album tests with clear output.
"""

import sys
import subprocess

def run_test_class(test_class):
    """Run a specific test class and report results."""
    print(f"\n{'='*60}")
    print(f"Running {test_class}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            f"tests/test_album_enhancements.py::{test_class}",
            "-v", "--tb=short"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"✅ {test_class} - ALL TESTS PASSED")
            # Extract and show test names
            for line in result.stdout.split('\n'):
                if '::test_' in line and ('PASSED' in line or 'FAILED' in line):
                    test_name = line.split('::')[-1].split()[0]
                    status = 'PASSED' if 'PASSED' in line else 'FAILED'
                    print(f"   - {test_name}: {status}")
        else:
            print(f"❌ {test_class} - SOME TESTS FAILED")
            print("STDOUT:", result.stdout[-500:])  # Last 500 chars
            if result.stderr:
                print("STDERR:", result.stderr[-300:])  # Last 300 chars
                
    except subprocess.TimeoutExpired:
        print(f"⏰ {test_class} - TIMEOUT")
    except Exception as e:
        print(f"💥 {test_class} - EXCEPTION: {e}")

def main():
    """Run all album enhancement test classes."""
    test_classes = [
        "TestAlbumType",
        "TestEnhancedAlbumModel", 
        "TestAlbumTypeDetector",
        "TestAlbumDataMigrator",
        "TestAlbumValidator",
        "TestAlbumUtilityFunctions",
        "TestBackwardCompatibility",
        "TestAlbumModelSerialization"
    ]
    
    print("🎵 Running Enhanced Album Model Tests")
    print(f"Testing {len(test_classes)} test classes...")
    
    passed = 0
    failed = 0
    
    for test_class in test_classes:
        run_test_class(test_class)
        # Simple pass/fail tracking (could be improved)
        passed += 1  # Assume passed for now
    
    print(f"\n{'='*60}")
    print(f"📊 SUMMARY: {len(test_classes)} test classes executed")
    print(f"{'='*60}")

if __name__ == "__main__":
    main() 