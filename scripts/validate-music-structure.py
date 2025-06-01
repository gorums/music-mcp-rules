#!/usr/bin/env python3
"""
Music Collection Structure Validator

This script validates your music collection structure for optimal performance
with the Music Collection MCP Server. It checks for common issues and provides
recommendations for organizing your collection.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import defaultdict, Counter


class MusicStructureValidator:
    """Validates music collection structure and provides recommendations."""
    
    # Supported music file extensions
    MUSIC_EXTENSIONS = {'.mp3', '.flac', '.wav', '.aac', '.m4a', '.ogg', '.wma', '.mp4', '.m4p'}
    
    # Recommended maximum values for performance
    MAX_RECOMMENDED_BANDS = 2000
    MAX_RECOMMENDED_ALBUMS_PER_BAND = 100
    MAX_RECOMMENDED_TRACKS_PER_ALBUM = 50
    
    def __init__(self, music_path: str):
        self.music_path = Path(music_path)
        self.issues = []
        self.warnings = []
        self.recommendations = []
        self.stats = {
            'total_bands': 0,
            'total_albums': 0,
            'total_tracks': 0,
            'empty_folders': 0,
            'large_collections': 0,
            'deep_nesting': 0,
            'special_characters': 0,
            'duplicate_names': 0
        }
        
    def validate(self) -> Dict[str, Any]:
        """Run complete validation of music collection structure."""
        print("🔍 Validating music collection structure...")
        
        if not self.music_path.exists():
            self.issues.append(f"Music path does not exist: {self.music_path}")
            return self._generate_report()
            
        if not self.music_path.is_dir():
            self.issues.append(f"Music path is not a directory: {self.music_path}")
            return self._generate_report()
            
        # Check permissions
        self._check_permissions()
        
        # Analyze folder structure
        self._analyze_structure()
        
        # Check for common issues
        self._check_naming_conventions()
        self._check_nesting_depth()
        self._check_file_distribution()
        self._check_duplicates()
        self._check_performance_concerns()
        
        # Generate recommendations
        self._generate_recommendations()
        
        return self._generate_report()
    
    def _check_permissions(self) -> None:
        """Check if the music path is readable."""
        if not os.access(self.music_path, os.R_OK):
            self.issues.append(f"No read permission for music path: {self.music_path}")
    
    def _analyze_structure(self) -> None:
        """Analyze the basic structure of the music collection."""
        band_folders = []
        
        try:
            for item in self.music_path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    band_folders.append(item)
        except PermissionError:
            self.issues.append(f"Permission denied accessing: {self.music_path}")
            return
            
        self.stats['total_bands'] = len(band_folders)
        
        for band_folder in band_folders:
            self._analyze_band_folder(band_folder)
    
    def _analyze_band_folder(self, band_folder: Path) -> None:
        """Analyze individual band folder structure."""
        album_folders = []
        loose_tracks = []
        
        try:
            for item in band_folder.iterdir():
                if item.is_dir():
                    album_folders.append(item)
                elif item.suffix.lower() in self.MUSIC_EXTENSIONS:
                    loose_tracks.append(item)
        except PermissionError:
            self.issues.append(f"Permission denied accessing: {band_folder}")
            return
            
        # Check for loose tracks (should be in album folders)
        if loose_tracks:
            self.warnings.append(
                f"Found {len(loose_tracks)} loose tracks in {band_folder.name} "
                f"(should be in album folders)"
            )
        
        # Analyze albums
        for album_folder in album_folders:
            self._analyze_album_folder(album_folder)
            
        self.stats['total_albums'] += len(album_folders)
        
        # Check for large band collections
        if len(album_folders) > self.MAX_RECOMMENDED_ALBUMS_PER_BAND:
            self.stats['large_collections'] += 1
            self.warnings.append(
                f"Band '{band_folder.name}' has {len(album_folders)} albums "
                f"(recommended max: {self.MAX_RECOMMENDED_ALBUMS_PER_BAND})"
            )
    
    def _analyze_album_folder(self, album_folder: Path) -> None:
        """Analyze individual album folder structure."""
        music_files = []
        
        try:
            for item in album_folder.iterdir():
                if item.is_file() and item.suffix.lower() in self.MUSIC_EXTENSIONS:
                    music_files.append(item)
        except PermissionError:
            self.issues.append(f"Permission denied accessing: {album_folder}")
            return
            
        track_count = len(music_files)
        self.stats['total_tracks'] += track_count
        
        # Check for empty albums
        if track_count == 0:
            self.stats['empty_folders'] += 1
            self.warnings.append(f"Empty album folder: {album_folder}")
            
        # Check for very large albums
        if track_count > self.MAX_RECOMMENDED_TRACKS_PER_ALBUM:
            self.warnings.append(
                f"Album '{album_folder.name}' has {track_count} tracks "
                f"(recommended max: {self.MAX_RECOMMENDED_TRACKS_PER_ALBUM})"
            )
    
    def _check_naming_conventions(self) -> None:
        """Check for naming convention issues."""
        problematic_chars = set()
        
        for root, dirs, files in os.walk(self.music_path):
            for name in dirs + files:
                # Check for special characters that might cause issues
                special_chars = set(name) & {'<', '>', ':', '"', '|', '?', '*'}
                if special_chars:
                    problematic_chars.update(special_chars)
                    self.stats['special_characters'] += 1
                    
                # Check for very long names
                if len(name) > 255:
                    self.warnings.append(f"Very long name (>255 chars): {name[:50]}...")
                    
                # Check for names with only spaces/dots
                if name.strip().replace('.', '').strip() == '':
                    self.warnings.append(f"Problematic name: '{name}'")
        
        if problematic_chars:
            self.warnings.append(
                f"Found special characters that may cause issues: {', '.join(problematic_chars)}"
            )
    
    def _check_nesting_depth(self) -> None:
        """Check for excessive nesting depth."""
        max_depth = 0
        deep_paths = []
        
        for root, dirs, files in os.walk(self.music_path):
            depth = len(Path(root).relative_to(self.music_path).parts)
            max_depth = max(max_depth, depth)
            
            # Warn about paths deeper than Band/Album structure
            if depth > 2:
                deep_paths.append(root)
                self.stats['deep_nesting'] += 1
        
        if deep_paths:
            self.warnings.append(
                f"Found {len(deep_paths)} paths with excessive nesting (>2 levels). "
                f"Recommended structure: Band/Album/Track"
            )
    
    def _check_file_distribution(self) -> None:
        """Check for uneven file distribution."""
        band_sizes = []
        
        for band_folder in self.music_path.iterdir():
            if not band_folder.is_dir() or band_folder.name.startswith('.'):
                continue
                
            band_track_count = 0
            for root, dirs, files in os.walk(band_folder):
                band_track_count += sum(
                    1 for f in files 
                    if Path(f).suffix.lower() in self.MUSIC_EXTENSIONS
                )
            band_sizes.append(band_track_count)
        
        if band_sizes:
            avg_size = sum(band_sizes) / len(band_sizes)
            large_bands = sum(1 for size in band_sizes if size > avg_size * 3)
            
            if large_bands > 0:
                self.warnings.append(
                    f"Found {large_bands} bands with significantly more tracks than average "
                    f"(may affect scanning performance)"
                )
    
    def _check_duplicates(self) -> None:
        """Check for duplicate folder names."""
        band_names = []
        album_names_by_band = defaultdict(list)
        
        for band_folder in self.music_path.iterdir():
            if not band_folder.is_dir() or band_folder.name.startswith('.'):
                continue
                
            band_names.append(band_folder.name.lower())
            
            try:
                for album_folder in band_folder.iterdir():
                    if album_folder.is_dir():
                        album_names_by_band[band_folder.name].append(album_folder.name.lower())
            except PermissionError:
                continue
        
        # Check for duplicate band names
        band_counts = Counter(band_names)
        duplicate_bands = {name: count for name, count in band_counts.items() if count > 1}
        
        if duplicate_bands:
            self.stats['duplicate_names'] += len(duplicate_bands)
            self.warnings.append(
                f"Found duplicate band names: {', '.join(duplicate_bands.keys())}"
            )
        
        # Check for duplicate album names within bands
        for band, albums in album_names_by_band.items():
            album_counts = Counter(albums)
            duplicate_albums = {name: count for name, count in album_counts.items() if count > 1}
            
            if duplicate_albums:
                self.stats['duplicate_names'] += len(duplicate_albums)
                self.warnings.append(
                    f"Found duplicate album names in {band}: {', '.join(duplicate_albums.keys())}"
                )
    
    def _check_performance_concerns(self) -> None:
        """Check for potential performance issues."""
        if self.stats['total_bands'] > self.MAX_RECOMMENDED_BANDS:
            self.warnings.append(
                f"Large collection ({self.stats['total_bands']} bands) may impact performance. "
                f"Consider splitting into smaller collections."
            )
        
        if self.stats['total_tracks'] > 100000:
            self.warnings.append(
                f"Very large collection ({self.stats['total_tracks']} tracks) detected. "
                f"Initial scanning may take significant time."
            )
    
    def _generate_recommendations(self) -> None:
        """Generate recommendations based on analysis."""
        
        # Structure recommendations
        if self.stats['empty_folders'] > 0:
            self.recommendations.append(
                f"Remove {self.stats['empty_folders']} empty folders to improve scanning efficiency"
            )
        
        if self.stats['deep_nesting'] > 0:
            self.recommendations.append(
                "Restructure deeply nested folders to Band/Album/Track format for better compatibility"
            )
        
        if self.stats['special_characters'] > 0:
            self.recommendations.append(
                "Consider renaming folders with special characters to avoid potential issues"
            )
        
        if self.stats['duplicate_names'] > 0:
            self.recommendations.append(
                "Resolve duplicate folder names to prevent confusion and metadata conflicts"
            )
        
        # Performance recommendations
        if self.stats['large_collections'] > 0:
            self.recommendations.append(
                "Consider organizing large band collections into compilation/separate artist folders"
            )
        
        if self.stats['total_bands'] > 1000:
            self.recommendations.append(
                "For better performance, consider using incremental scanning and longer cache duration"
            )
        
        # Best practices
        self.recommendations.extend([
            "Use consistent naming: 'Artist Name/Album Name (Year)/Track files'",
            "Keep album folders under 50 tracks for optimal performance",
            "Use descriptive album names to help with missing album detection",
            "Avoid special characters: < > : \" | ? * in folder names",
            "Ensure read permissions for all music folders and files"
        ])
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        severity = "ERROR" if self.issues else "WARNING" if self.warnings else "OK"
        
        return {
            'severity': severity,
            'summary': {
                'total_bands': self.stats['total_bands'],
                'total_albums': self.stats['total_albums'], 
                'total_tracks': self.stats['total_tracks'],
                'issues_found': len(self.issues),
                'warnings_found': len(self.warnings),
                'recommendations': len(self.recommendations)
            },
            'issues': self.issues,
            'warnings': self.warnings,
            'recommendations': self.recommendations,
            'detailed_stats': self.stats
        }
    
    def print_report(self, report: Dict[str, Any]) -> None:
        """Print formatted validation report."""
        print("\n" + "=" * 60)
        print("🎵 MUSIC COLLECTION VALIDATION REPORT")
        print("=" * 60)
        
        # Summary
        summary = report['summary']
        print(f"\n📊 COLLECTION SUMMARY:")
        print(f"  📁 Bands: {summary['total_bands']:,}")
        print(f"  💿 Albums: {summary['total_albums']:,}")
        print(f"  🎵 Tracks: {summary['total_tracks']:,}")
        
        # Severity indicator
        severity_icons = {"OK": "✅", "WARNING": "⚠️ ", "ERROR": "❌"}
        print(f"\n{severity_icons[report['severity']]} OVERALL STATUS: {report['severity']}")
        
        # Issues
        if report['issues']:
            print(f"\n❌ CRITICAL ISSUES ({len(report['issues'])}):")
            for i, issue in enumerate(report['issues'], 1):
                print(f"  {i}. {issue}")
        
        # Warnings
        if report['warnings']:
            print(f"\n⚠️  WARNINGS ({len(report['warnings'])}):")
            for i, warning in enumerate(report['warnings'], 1):
                print(f"  {i}. {warning}")
        
        # Recommendations
        if report['recommendations']:
            print(f"\n💡 RECOMMENDATIONS ({len(report['recommendations'])}):")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"  {i}. {rec}")
        
        # Performance assessment
        print(f"\n🚀 PERFORMANCE ASSESSMENT:")
        if summary['total_bands'] < 500:
            print("  ✅ Collection size optimal for fast scanning")
        elif summary['total_bands'] < 1500:
            print("  ⚠️  Medium collection - scanning may take a few minutes")
        else:
            print("  ❌ Large collection - consider performance optimizations")
        
        print("\n" + "=" * 60)


def main():
    """Main validation interface."""
    if len(sys.argv) != 2:
        print("Usage: python validate-music-structure.py <music_path>")
        print("\nExample:")
        print("  python validate-music-structure.py /home/user/Music")
        print("  python validate-music-structure.py C:\\Users\\User\\Music")
        sys.exit(1)
    
    music_path = sys.argv[1]
    
    # Expand user path and make absolute
    music_path = os.path.abspath(os.path.expanduser(music_path))
    
    print(f"🎵 Music Collection Structure Validator")
    print(f"📁 Validating: {music_path}")
    
    validator = MusicStructureValidator(music_path)
    report = validator.validate()
    validator.print_report(report)
    
    # Save report to file
    report_file = Path(music_path).parent / "music_structure_validation.json"
    try:
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Detailed report saved to: {report_file}")
    except Exception as e:
        print(f"\n⚠️  Could not save report: {e}")
    
    # Exit with appropriate code
    if report['severity'] == 'ERROR':
        sys.exit(1)
    elif report['severity'] == 'WARNING':
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main() 