#!/usr/bin/env python3
"""
Collection Health Check System for Music Collection MCP Server

This script provides comprehensive health monitoring for:
- Metadata integrity and consistency
- Collection index synchronization
- File system consistency
- Performance monitoring
- Configuration validation
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import hashlib
from collections import defaultdict, Counter


class MusicCollectionHealthCheck:
    """Comprehensive health check system for Music Collection MCP Server."""
    
    def __init__(self, music_root: str):
        """
        Initialize health check system.
        
        Args:
            music_root: Root path of music collection
        """
        self.music_root = Path(music_root)
        self.start_time = time.time()
        
        # Health check results
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'music_root': str(self.music_root),
            'overall_health': 'unknown',
            'checks': {},
            'issues': [],
            'warnings': [],
            'recommendations': [],
            'metrics': {}
        }
        
        # Music file extensions
        self.music_extensions = {'.mp3', '.flac', '.wav', '.aac', '.m4a', '.ogg', '.wma', '.mp4', '.m4p'}
    
    def run_full_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check."""
        print("🏥 Running Music Collection Health Check...")
        print("=" * 50)
        
        # Core health checks
        self._check_filesystem_access()
        self._check_collection_index()
        self._check_metadata_integrity()
        self._check_file_synchronization()
        self._check_performance_metrics()
        self._check_cache_health()
        self._check_configuration()
        
        # Calculate overall health
        self._calculate_overall_health()
        
        # Generate recommendations
        self._generate_recommendations()
        
        # Calculate metrics
        self.results['metrics']['check_duration'] = time.time() - self.start_time
        
        print(f"\n🏥 Health check completed in {self.results['metrics']['check_duration']:.2f}s")
        return self.results
    
    def _check_filesystem_access(self) -> None:
        """Check filesystem access and permissions."""
        print("📁 Checking filesystem access...")
        
        check_result = {
            'status': 'pass',
            'details': {},
            'issues': []
        }
        
        # Check if music root exists
        if not self.music_root.exists():
            check_result['status'] = 'fail'
            check_result['issues'].append(f"Music root does not exist: {self.music_root}")
            self.results['issues'].append("Music collection root directory not found")
        else:
            # Check read permissions
            if not os.access(self.music_root, os.R_OK):
                check_result['status'] = 'fail'
                check_result['issues'].append("No read permission for music root")
                self.results['issues'].append("Insufficient read permissions for music collection")
            
            # Check write permissions for metadata
            try:
                test_file = self.music_root / ".health_check_test"
                test_file.touch()
                test_file.unlink()
                check_result['details']['write_access'] = True
            except (PermissionError, OSError):
                check_result['details']['write_access'] = False
                check_result['issues'].append("No write permission for metadata files")
                self.results['warnings'].append("Cannot write metadata files - server will be read-only")
            
            # Check space availability
            try:
                stat = os.statvfs(self.music_root)
                free_space = stat.f_bavail * stat.f_frsize
                total_space = stat.f_blocks * stat.f_frsize
                used_percentage = ((total_space - free_space) / total_space) * 100
                
                check_result['details']['free_space_gb'] = free_space / (1024**3)
                check_result['details']['used_percentage'] = used_percentage
                
                if used_percentage > 95:
                    check_result['status'] = 'warning'
                    check_result['issues'].append(f"Disk space critical: {used_percentage:.1f}% used")
                    self.results['warnings'].append("Disk space running low - may affect metadata operations")
                elif used_percentage > 85:
                    check_result['issues'].append(f"Disk space warning: {used_percentage:.1f}% used")
                    
            except (OSError, AttributeError):
                # Windows or other systems might not support statvfs
                check_result['details']['space_check'] = 'unsupported'
        
        self.results['checks']['filesystem_access'] = check_result
        print(f"  Status: {check_result['status'].upper()}")
    
    def _check_collection_index(self) -> None:
        """Check collection index integrity."""
        print("📚 Checking collection index...")
        
        check_result = {
            'status': 'pass',
            'details': {},
            'issues': []
        }
        
        collection_index_file = self.music_root / ".collection_index.json"
        
        if not collection_index_file.exists():
            check_result['status'] = 'warning'
            check_result['issues'].append("Collection index not found - needs initial scan")
            self.results['warnings'].append("Collection index missing - run scan_music_folders")
        else:
            try:
                with open(collection_index_file) as f:
                    collection_index = json.load(f)
                
                # Validate index structure
                required_fields = ['bands', 'collection_stats', 'last_updated']
                for field in required_fields:
                    if field not in collection_index:
                        check_result['status'] = 'fail'
                        check_result['issues'].append(f"Missing required field: {field}")
                        self.results['issues'].append(f"Collection index corrupted - missing {field}")
                
                if collection_index:
                    bands = collection_index.get('bands', {})
                    stats = collection_index.get('collection_stats', {})
                    
                    check_result['details']['total_bands'] = len(bands)
                    check_result['details']['total_albums'] = stats.get('total_albums', 0)
                    check_result['details']['total_missing_albums'] = stats.get('total_missing_albums', 0)
                    
                    # Check last updated
                    last_updated = collection_index.get('last_updated')
                    if last_updated:
                        try:
                            last_update_time = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                            days_since_update = (datetime.now() - last_update_time.replace(tzinfo=None)).days
                            check_result['details']['days_since_update'] = days_since_update
                            
                            if days_since_update > 30:
                                check_result['status'] = 'warning'
                                check_result['issues'].append(f"Collection index is {days_since_update} days old")
                                self.results['warnings'].append("Collection index may be outdated")
                                
                        except ValueError:
                            check_result['issues'].append("Invalid last_updated timestamp")
                    
                    # Check for inconsistencies in stats
                    calculated_albums = sum(band.get('albums_count', 0) for band in bands.values())
                    if calculated_albums != stats.get('total_albums', 0):
                        check_result['status'] = 'warning'
                        check_result['issues'].append("Album count mismatch in statistics")
                        self.results['warnings'].append("Collection statistics may be inconsistent")
                
            except json.JSONDecodeError:
                check_result['status'] = 'fail'
                check_result['issues'].append("Collection index is corrupted (invalid JSON)")
                self.results['issues'].append("Collection index file is corrupted")
            except Exception as e:
                check_result['status'] = 'fail'
                check_result['issues'].append(f"Error reading collection index: {e}")
                self.results['issues'].append("Cannot read collection index")
        
        self.results['checks']['collection_index'] = check_result
        print(f"  Status: {check_result['status'].upper()}")
    
    def _check_metadata_integrity(self) -> None:
        """Check metadata files integrity."""
        print("📄 Checking metadata integrity...")
        
        check_result = {
            'status': 'pass',
            'details': {},
            'issues': []
        }
        
        metadata_files = []
        corrupted_files = []
        total_size = 0
        
        # Find all metadata files
        for root, dirs, files in os.walk(self.music_root):
            for file in files:
                if file == ".band_metadata.json":
                    metadata_files.append(Path(root) / file)
        
        check_result['details']['total_metadata_files'] = len(metadata_files)
        
        # Check each metadata file
        for metadata_file in metadata_files:
            try:
                with open(metadata_file) as f:
                    metadata = json.load(f)
                
                # Basic structure validation
                if not isinstance(metadata, dict):
                    corrupted_files.append(str(metadata_file))
                    continue
                
                # Check required fields
                if 'band_name' not in metadata:
                    corrupted_files.append(str(metadata_file))
                    continue
                
                total_size += metadata_file.stat().st_size
                
            except json.JSONDecodeError:
                corrupted_files.append(str(metadata_file))
            except Exception:
                corrupted_files.append(str(metadata_file))
        
        check_result['details']['corrupted_files'] = len(corrupted_files)
        check_result['details']['total_size_kb'] = total_size / 1024
        
        if corrupted_files:
            check_result['status'] = 'warning' if len(corrupted_files) < len(metadata_files) * 0.1 else 'fail'
            check_result['issues'].append(f"{len(corrupted_files)} corrupted metadata files found")
            
            if len(corrupted_files) <= 5:
                check_result['details']['corrupted_file_list'] = corrupted_files
            
            if check_result['status'] == 'fail':
                self.results['issues'].append("Significant metadata corruption detected")
            else:
                self.results['warnings'].append("Some metadata files are corrupted")
        
        self.results['checks']['metadata_integrity'] = check_result
        print(f"  Status: {check_result['status'].upper()}")
    
    def _check_file_synchronization(self) -> None:
        """Check synchronization between filesystem and metadata."""
        print("🔄 Checking file synchronization...")
        
        check_result = {
            'status': 'pass',
            'details': {},
            'issues': []
        }
        
        # Count actual bands and albums
        actual_bands = {}
        
        for item in self.music_root.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                album_folders = []
                try:
                    for album_item in item.iterdir():
                        if album_item.is_dir():
                            # Count music files in album
                            music_files = [
                                f for f in album_item.iterdir() 
                                if f.is_file() and f.suffix.lower() in self.music_extensions
                            ]
                            if music_files:  # Only count albums with music files
                                album_folders.append({
                                    'name': album_item.name,
                                    'track_count': len(music_files)
                                })
                except PermissionError:
                    continue
                
                actual_bands[item.name] = {
                    'albums_count': len(album_folders),
                    'albums': album_folders
                }
        
        check_result['details']['actual_bands'] = len(actual_bands)
        check_result['details']['actual_albums'] = sum(band['albums_count'] for band in actual_bands.values())
        
        # Compare with collection index
        collection_index_file = self.music_root / ".collection_index.json"
        if collection_index_file.exists():
            try:
                with open(collection_index_file) as f:
                    collection_index = json.load(f)
                
                indexed_bands = collection_index.get('bands', {})
                check_result['details']['indexed_bands'] = len(indexed_bands)
                
                # Find discrepancies
                missing_from_index = set(actual_bands.keys()) - set(indexed_bands.keys())
                missing_from_filesystem = set(indexed_bands.keys()) - set(actual_bands.keys())
                
                if missing_from_index:
                    check_result['status'] = 'warning'
                    check_result['issues'].append(f"{len(missing_from_index)} bands not in index")
                    check_result['details']['missing_from_index'] = len(missing_from_index)
                    self.results['warnings'].append("Some bands not indexed - rescan recommended")
                
                if missing_from_filesystem:
                    check_result['status'] = 'warning'
                    check_result['issues'].append(f"{len(missing_from_filesystem)} indexed bands not found")
                    check_result['details']['missing_from_filesystem'] = len(missing_from_filesystem)
                    self.results['warnings'].append("Some indexed bands missing from filesystem")
                
                # Check album counts for existing bands
                album_count_mismatches = 0
                for band_name in set(actual_bands.keys()) & set(indexed_bands.keys()):
                    actual_count = actual_bands[band_name]['albums_count']
                    indexed_count = indexed_bands[band_name].get('albums_count', 0)
                    
                    if actual_count != indexed_count:
                        album_count_mismatches += 1
                
                if album_count_mismatches > 0:
                    check_result['status'] = 'warning'
                    check_result['issues'].append(f"{album_count_mismatches} bands have album count mismatches")
                    check_result['details']['album_count_mismatches'] = album_count_mismatches
                    self.results['warnings'].append("Album counts may be outdated")
                
            except (json.JSONDecodeError, KeyError):
                check_result['status'] = 'fail'
                check_result['issues'].append("Cannot compare with collection index")
        else:
            check_result['status'] = 'warning'
            check_result['issues'].append("No collection index to compare against")
        
        self.results['checks']['file_synchronization'] = check_result
        print(f"  Status: {check_result['status'].upper()}")
    
    def _check_performance_metrics(self) -> None:
        """Check performance-related metrics."""
        print("🚀 Checking performance metrics...")
        
        check_result = {
            'status': 'pass',
            'details': {},
            'issues': []
        }
        
        # Count total items for performance assessment
        total_bands = 0
        total_albums = 0
        total_tracks = 0
        largest_band = {'name': '', 'albums': 0}
        largest_album = {'name': '', 'tracks': 0}
        
        scan_start = time.time()
        
        for band_folder in self.music_root.iterdir():
            if not band_folder.is_dir() or band_folder.name.startswith('.'):
                continue
                
            total_bands += 1
            band_albums = 0
            
            try:
                for album_folder in band_folder.iterdir():
                    if not album_folder.is_dir():
                        continue
                    
                    total_albums += 1
                    band_albums += 1
                    
                    # Count tracks in album
                    track_count = 0
                    for track_file in album_folder.iterdir():
                        if track_file.is_file() and track_file.suffix.lower() in self.music_extensions:
                            track_count += 1
                    
                    total_tracks += track_count
                    
                    # Track largest album
                    if track_count > largest_album['tracks']:
                        largest_album = {
                            'name': f"{band_folder.name}/{album_folder.name}",
                            'tracks': track_count
                        }
                
                # Track largest band
                if band_albums > largest_band['albums']:
                    largest_band = {
                        'name': band_folder.name,
                        'albums': band_albums
                    }
                    
            except PermissionError:
                continue
        
        scan_duration = time.time() - scan_start
        
        check_result['details']['total_bands'] = total_bands
        check_result['details']['total_albums'] = total_albums
        check_result['details']['total_tracks'] = total_tracks
        check_result['details']['scan_duration'] = scan_duration
        check_result['details']['largest_band'] = largest_band
        check_result['details']['largest_album'] = largest_album
        
        # Performance assessments
        if total_bands > 2000:
            check_result['status'] = 'warning'
            check_result['issues'].append(f"Large collection ({total_bands} bands) may impact performance")
            self.results['warnings'].append("Large collection - consider performance optimizations")
        
        if largest_band['albums'] > 100:
            check_result['issues'].append(f"Large band collection: {largest_band['name']} ({largest_band['albums']} albums)")
            self.results['warnings'].append("Some bands have very large album collections")
        
        if largest_album['tracks'] > 50:
            check_result['issues'].append(f"Large album: {largest_album['name']} ({largest_album['tracks']} tracks)")
        
        if scan_duration > 30:
            check_result['status'] = 'warning'
            check_result['issues'].append(f"Slow filesystem scan ({scan_duration:.1f}s)")
            self.results['warnings'].append("Filesystem performance may be degraded")
        
        # Calculate performance score
        performance_score = 100
        if total_bands > 1000:
            performance_score -= min(30, (total_bands - 1000) / 50)
        if scan_duration > 10:
            performance_score -= min(20, (scan_duration - 10) * 2)
        if largest_band['albums'] > 50:
            performance_score -= min(15, (largest_band['albums'] - 50) / 5)
        
        check_result['details']['performance_score'] = max(0, int(performance_score))
        
        self.results['checks']['performance_metrics'] = check_result
        print(f"  Status: {check_result['status'].upper()}")
    
    def _check_cache_health(self) -> None:
        """Check cache and temporary files health."""
        print("🗄️  Checking cache health...")
        
        check_result = {
            'status': 'pass',
            'details': {},
            'issues': []
        }
        
        # Check for cache directories
        cache_locations = [
            self.music_root / ".cache",
            Path.cwd() / "cache",
            Path.home() / ".cache" / "music_mcp"
        ]
        
        total_cache_size = 0
        cache_files = 0
        old_cache_files = 0
        
        for cache_dir in cache_locations:
            if cache_dir.exists():
                for cache_file in cache_dir.rglob("*"):
                    if cache_file.is_file():
                        cache_files += 1
                        file_size = cache_file.stat().st_size
                        total_cache_size += file_size
                        
                        # Check age
                        file_age = time.time() - cache_file.stat().st_mtime
                        if file_age > 30 * 24 * 3600:  # 30 days
                            old_cache_files += 1
        
        check_result['details']['cache_files'] = cache_files
        check_result['details']['cache_size_mb'] = total_cache_size / (1024 * 1024)
        check_result['details']['old_cache_files'] = old_cache_files
        
        # Check cache size
        if total_cache_size > 100 * 1024 * 1024:  # 100MB
            check_result['status'] = 'warning'
            check_result['issues'].append(f"Large cache size: {total_cache_size / (1024*1024):.1f}MB")
            self.results['warnings'].append("Cache size is large - consider cleanup")
        
        if old_cache_files > 0:
            check_result['issues'].append(f"{old_cache_files} old cache files found")
            self.results['warnings'].append("Old cache files found - cleanup recommended")
        
        self.results['checks']['cache_health'] = check_result
        print(f"  Status: {check_result['status'].upper()}")
    
    def _check_configuration(self) -> None:
        """Check configuration files and settings."""
        print("⚙️  Checking configuration...")
        
        check_result = {
            'status': 'pass',
            'details': {},
            'issues': []
        }
        
        # Check environment variables
        env_vars = {
            'MUSIC_ROOT_PATH': os.getenv('MUSIC_ROOT_PATH'),
            'CACHE_DURATION_DAYS': os.getenv('CACHE_DURATION_DAYS'),
            'LOG_LEVEL': os.getenv('LOG_LEVEL')
        }
        
        check_result['details']['environment_variables'] = env_vars
        
        # Validate music root path
        configured_path = env_vars.get('MUSIC_ROOT_PATH')
        if configured_path:
            if Path(configured_path) != self.music_root:
                check_result['status'] = 'warning'
                check_result['issues'].append("MUSIC_ROOT_PATH doesn't match actual path")
                self.results['warnings'].append("Configuration path mismatch")
        
        # Check configuration files
        config_files = {
            '.env': self.music_root / '.env',
            'claude_desktop_config.json': self.music_root / 'claude_desktop_config.json'
        }
        
        existing_configs = []
        for config_name, config_path in config_files.items():
            if config_path.exists():
                existing_configs.append(config_name)
                
                # Validate JSON configs
                if config_name.endswith('.json'):
                    try:
                        with open(config_path) as f:
                            json.load(f)
                    except json.JSONDecodeError:
                        check_result['status'] = 'warning'
                        check_result['issues'].append(f"Invalid JSON in {config_name}")
                        self.results['warnings'].append(f"Configuration file {config_name} is corrupted")
        
        check_result['details']['existing_configs'] = existing_configs
        
        self.results['checks']['configuration'] = check_result
        print(f"  Status: {check_result['status'].upper()}")
    
    def _calculate_overall_health(self) -> None:
        """Calculate overall health status."""
        
        check_statuses = [check['status'] for check in self.results['checks'].values()]
        
        if 'fail' in check_statuses:
            self.results['overall_health'] = 'critical'
        elif 'warning' in check_statuses:
            self.results['overall_health'] = 'warning'
        else:
            self.results['overall_health'] = 'healthy'
    
    def _generate_recommendations(self) -> None:
        """Generate actionable recommendations based on health check results."""
        
        recommendations = []
        
        # Based on specific check results
        fs_check = self.results['checks'].get('filesystem_access', {})
        if fs_check.get('status') == 'fail':
            recommendations.append("Fix filesystem access issues before using the MCP server")
        
        index_check = self.results['checks'].get('collection_index', {})
        if 'Collection index not found' in str(index_check.get('issues', [])):
            recommendations.append("Run initial scan: Use scan_music_folders tool to create collection index")
        elif index_check.get('details', {}).get('days_since_update', 0) > 30:
            recommendations.append("Update collection index: Run scan_music_folders to refresh data")
        
        metadata_check = self.results['checks'].get('metadata_integrity', {})
        if metadata_check.get('details', {}).get('corrupted_files', 0) > 0:
            recommendations.append("Fix corrupted metadata: Re-save metadata for affected bands")
        
        sync_check = self.results['checks'].get('file_synchronization', {})
        if sync_check.get('details', {}).get('missing_from_index', 0) > 0:
            recommendations.append("Rescan collection: Some bands are not indexed")
        
        perf_check = self.results['checks'].get('performance_metrics', {})
        if perf_check.get('details', {}).get('performance_score', 100) < 70:
            recommendations.append("Consider performance optimizations: Use incremental scanning, increase cache duration")
        
        cache_check = self.results['checks'].get('cache_health', {})
        if cache_check.get('details', {}).get('old_cache_files', 0) > 0:
            recommendations.append("Clean up old cache files to free disk space")
        
        # General recommendations
        if self.results['overall_health'] == 'healthy':
            recommendations.extend([
                "Regular maintenance: Run health checks monthly",
                "Keep backups: Use backup-recovery script for metadata",
                "Monitor performance: Large collections benefit from periodic optimization"
            ])
        
        self.results['recommendations'] = recommendations
    
    def print_health_report(self) -> None:
        """Print formatted health check report."""
        
        results = self.results
        
        print("\n" + "=" * 60)
        print("🏥 MUSIC COLLECTION HEALTH REPORT")
        print("=" * 60)
        
        # Overall status
        health_icons = {
            'healthy': '🟢',
            'warning': '🟡',
            'critical': '🔴'
        }
        
        print(f"\n{health_icons[results['overall_health']]} OVERALL HEALTH: {results['overall_health'].upper()}")
        print(f"📅 Check Date: {results['timestamp']}")
        print(f"📁 Music Root: {results['music_root']}")
        print(f"⏱️  Check Duration: {results['metrics'].get('check_duration', 0):.2f}s")
        
        # Check summary
        print(f"\n📊 CHECK SUMMARY:")
        for check_name, check_result in results['checks'].items():
            status_icon = {'pass': '✅', 'warning': '⚠️', 'fail': '❌'}[check_result['status']]
            print(f"  {status_icon} {check_name.replace('_', ' ').title()}: {check_result['status'].upper()}")
        
        # Issues
        if results['issues']:
            print(f"\n❌ CRITICAL ISSUES ({len(results['issues'])}):")
            for i, issue in enumerate(results['issues'], 1):
                print(f"  {i}. {issue}")
        
        # Warnings
        if results['warnings']:
            print(f"\n⚠️  WARNINGS ({len(results['warnings'])}):")
            for i, warning in enumerate(results['warnings'], 1):
                print(f"  {i}. {warning}")
        
        # Recommendations
        if results['recommendations']:
            print(f"\n💡 RECOMMENDATIONS ({len(results['recommendations'])}):")
            for i, rec in enumerate(results['recommendations'], 1):
                print(f"  {i}. {rec}")
        
        # Key metrics
        print(f"\n📈 KEY METRICS:")
        perf_check = results['checks'].get('performance_metrics', {})
        if perf_check.get('details'):
            details = perf_check['details']
            print(f"  📁 Bands: {details.get('total_bands', 0):,}")
            print(f"  💿 Albums: {details.get('total_albums', 0):,}")
            print(f"  🎵 Tracks: {details.get('total_tracks', 0):,}")
            print(f"  🚀 Performance Score: {details.get('performance_score', 0)}/100")
        
        cache_check = results['checks'].get('cache_health', {})
        if cache_check.get('details'):
            cache_size = cache_check['details'].get('cache_size_mb', 0)
            print(f"  🗄️  Cache Size: {cache_size:.1f} MB")
        
        print("\n" + "=" * 60)
    
    def save_report(self, output_file: Optional[str] = None) -> Path:
        """Save health check report to file."""
        
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.music_root / f"health_check_{timestamp}.json"
        
        output_path = Path(output_file)
        
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        return output_path


def create_health_check_script() -> str:
    """Create a simplified health check script for regular use."""
    
    script_content = '''#!/usr/bin/env python3
"""
Quick Health Check for Music Collection MCP Server
"""

import sys
import json
from pathlib import Path
from datetime import datetime

def quick_health_check(music_path):
    """Run a quick health check."""
    
    music_root = Path(music_path)
    print("🏥 Quick Health Check")
    print("=" * 30)
    
    issues = 0
    
    # Check basics
    if not music_root.exists():
        print("❌ Music collection not found")
        return False
    
    # Check collection index
    index_file = music_root / ".collection_index.json"
    if not index_file.exists():
        print("⚠️  Collection index missing - run scan")
        issues += 1
    else:
        try:
            with open(index_file) as f:
                index = json.load(f)
            
            bands = len(index.get('bands', {}))
            print(f"✅ Collection index: {bands} bands")
            
            # Check if outdated
            last_updated = index.get('last_updated')
            if last_updated:
                last_update = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                days_old = (datetime.now() - last_update.replace(tzinfo=None)).days
                if days_old > 30:
                    print(f"⚠️  Index is {days_old} days old")
                    issues += 1
        except (json.JSONDecodeError, KeyError):
            print("❌ Collection index corrupted")
            issues += 1
    
    # Count actual bands
    actual_bands = len([d for d in music_root.iterdir() if d.is_dir() and not d.name.startswith('.')])
    print(f"📁 Filesystem: {actual_bands} band folders")
    
    # Check metadata files
    metadata_files = list(music_root.rglob(".band_metadata.json"))
    print(f"📄 Metadata files: {len(metadata_files)}")
    
    if issues == 0:
        print("🟢 Collection appears healthy")
        return True
    else:
        print(f"🟡 {issues} issues found - run full health check")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python quick_health_check.py <music_path>")
        sys.exit(1)
    
    success = quick_health_check(sys.argv[1])
    sys.exit(0 if success else 1)
'''
    
    return script_content


def main():
    """Main health check interface."""
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python health-check.py <music_path> [--save-report] [--output <file>]")
        print("\nExamples:")
        print("  python health-check.py /home/user/Music")
        print("  python health-check.py C:\\Users\\User\\Music --save-report")
        sys.exit(1)
    
    music_path = sys.argv[1]
    save_report = '--save-report' in sys.argv
    
    output_file = None
    if '--output' in sys.argv:
        try:
            output_index = sys.argv.index('--output')
            output_file = sys.argv[output_index + 1]
        except (ValueError, IndexError):
            print("Error: --output requires a filename")
            sys.exit(1)
    
    # Expand user path and make absolute
    music_path = os.path.abspath(os.path.expanduser(music_path))
    
    if not os.path.exists(music_path):
        print(f"❌ Music path does not exist: {music_path}")
        sys.exit(1)
    
    # Run health check
    health_checker = MusicCollectionHealthCheck(music_path)
    results = health_checker.run_full_health_check()
    
    # Print report
    health_checker.print_health_report()
    
    # Save report if requested
    if save_report or output_file:
        report_path = health_checker.save_report(output_file)
        print(f"\n📄 Health report saved to: {report_path}")
    
    # Create quick health check script
    quick_script_content = create_health_check_script()
    quick_script_path = Path(music_path) / "quick_health_check.py"
    try:
        with open(quick_script_path, 'w') as f:
            f.write(quick_script_content)
        print(f"📋 Quick health check script created: {quick_script_path}")
    except Exception as e:
        print(f"⚠️  Could not create quick health check script: {e}")
    
    # Exit with appropriate code
    if results['overall_health'] == 'critical':
        sys.exit(2)
    elif results['overall_health'] == 'warning':
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main() 