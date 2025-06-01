#!/usr/bin/env python3
"""
Backup and Recovery System for Music Collection MCP Server

This script provides comprehensive backup and recovery procedures for:
- Metadata files (.band_metadata.json)
- Collection index (.collection_index.json)
- Cache files and configuration
- Server logs and analysis data
"""

import os
import sys
import json
import shutil
import tarfile
import gzip
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import hashlib


class MusicMCPBackup:
    """Comprehensive backup system for Music Collection MCP Server."""
    
    def __init__(self, music_root: str, backup_root: str = None):
        """
        Initialize backup system.
        
        Args:
            music_root: Root path of music collection
            backup_root: Root path for backups (default: music_root/backups)
        """
        self.music_root = Path(music_root)
        self.backup_root = Path(backup_root) if backup_root else self.music_root / "backups"
        self.backup_root.mkdir(exist_ok=True)
        
        # Backup timestamp
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # File patterns to backup
        self.metadata_patterns = [
            ".band_metadata.json",
            ".collection_index.json",
            ".collection_insight.json"
        ]
        
        self.cache_patterns = [
            ".cache",
            "logs",
            "*.log"
        ]
    
    def create_full_backup(self, compress: bool = True, 
                          include_logs: bool = False) -> Path:
        """
        Create a full backup of all metadata and configuration.
        
        Args:
            compress: Whether to compress the backup
            include_logs: Whether to include log files
            
        Returns:
            Path to the created backup file
        """
        print("🔄 Creating full backup...")
        
        backup_name = f"music_mcp_full_backup_{self.timestamp}"
        backup_dir = self.backup_root / backup_name
        backup_dir.mkdir(exist_ok=True)
        
        # Backup metadata files
        metadata_backup = backup_dir / "metadata"
        metadata_backup.mkdir(exist_ok=True)
        self._backup_metadata_files(metadata_backup)
        
        # Backup configuration
        config_backup = backup_dir / "config"
        config_backup.mkdir(exist_ok=True)
        self._backup_configuration(config_backup)
        
        # Backup logs if requested
        if include_logs:
            logs_backup = backup_dir / "logs"
            logs_backup.mkdir(exist_ok=True)
            self._backup_logs(logs_backup)
        
        # Create backup manifest
        manifest = self._create_backup_manifest(backup_dir)
        manifest_file = backup_dir / "backup_manifest.json"
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # Compress if requested
        if compress:
            compressed_backup = self._compress_backup(backup_dir)
            shutil.rmtree(backup_dir)  # Remove uncompressed version
            backup_path = compressed_backup
        else:
            backup_path = backup_dir
        
        print(f"✅ Full backup created: {backup_path}")
        return backup_path
    
    def create_incremental_backup(self, last_backup_date: Optional[datetime] = None,
                                 compress: bool = True) -> Path:
        """
        Create an incremental backup of changed files.
        
        Args:
            last_backup_date: Date of last backup (if None, finds automatically)
            compress: Whether to compress the backup
            
        Returns:
            Path to the created backup file
        """
        print("🔄 Creating incremental backup...")
        
        if last_backup_date is None:
            last_backup_date = self._find_last_backup_date()
        
        backup_name = f"music_mcp_incremental_backup_{self.timestamp}"
        backup_dir = self.backup_root / backup_name
        backup_dir.mkdir(exist_ok=True)
        
        # Find changed files
        changed_files = self._find_changed_files(last_backup_date)
        
        if not changed_files:
            print("ℹ️  No files changed since last backup")
            shutil.rmtree(backup_dir)
            return None
        
        # Backup changed files
        for file_path in changed_files:
            relative_path = file_path.relative_to(self.music_root)
            backup_file_path = backup_dir / relative_path
            backup_file_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, backup_file_path)
        
        # Create backup manifest
        manifest = self._create_backup_manifest(backup_dir, incremental=True)
        manifest['last_backup_date'] = last_backup_date.isoformat()
        manifest['changed_files'] = [str(f.relative_to(self.music_root)) for f in changed_files]
        
        manifest_file = backup_dir / "backup_manifest.json"
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # Compress if requested
        if compress:
            compressed_backup = self._compress_backup(backup_dir)
            shutil.rmtree(backup_dir)
            backup_path = compressed_backup
        else:
            backup_path = backup_dir
        
        print(f"✅ Incremental backup created: {backup_path}")
        print(f"📁 Backed up {len(changed_files)} changed files")
        return backup_path
    
    def _backup_metadata_files(self, backup_dir: Path) -> None:
        """Backup all metadata files."""
        print("📄 Backing up metadata files...")
        
        files_backed_up = 0
        
        # Walk through music collection and find metadata files
        for root, dirs, files in os.walk(self.music_root):
            root_path = Path(root)
            
            for file in files:
                if any(pattern in file for pattern in self.metadata_patterns):
                    source_file = root_path / file
                    relative_path = source_file.relative_to(self.music_root)
                    backup_file = backup_dir / relative_path
                    
                    # Create directory structure
                    backup_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file
                    shutil.copy2(source_file, backup_file)
                    files_backed_up += 1
        
        print(f"  📋 Backed up {files_backed_up} metadata files")
    
    def _backup_configuration(self, backup_dir: Path) -> None:
        """Backup configuration files."""
        print("⚙️  Backing up configuration...")
        
        config_files = [
            ".env",
            ".env.production", 
            ".env.development",
            "claude_desktop_config.json"
        ]
        
        files_backed_up = 0
        
        for config_file in config_files:
            source_file = self.music_root / config_file
            if source_file.exists():
                backup_file = backup_dir / config_file
                shutil.copy2(source_file, backup_file)
                files_backed_up += 1
        
        # Backup any script configurations
        scripts_dir = self.music_root / "scripts"
        if scripts_dir.exists():
            backup_scripts_dir = backup_dir / "scripts"
            shutil.copytree(scripts_dir, backup_scripts_dir, ignore=shutil.ignore_patterns('*.pyc', '__pycache__'))
        
        print(f"  ⚙️  Backed up {files_backed_up} configuration files")
    
    def _backup_logs(self, backup_dir: Path) -> None:
        """Backup log files."""
        print("📋 Backing up logs...")
        
        log_dirs = [
            self.music_root / "logs",
            Path.cwd() / "logs"
        ]
        
        files_backed_up = 0
        
        for log_dir in log_dirs:
            if log_dir.exists():
                for log_file in log_dir.rglob("*.log"):
                    relative_path = log_file.relative_to(log_dir)
                    backup_file = backup_dir / log_dir.name / relative_path
                    backup_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(log_file, backup_file)
                    files_backed_up += 1
        
        print(f"  📋 Backed up {files_backed_up} log files")
    
    def _create_backup_manifest(self, backup_dir: Path, 
                               incremental: bool = False) -> Dict[str, Any]:
        """Create backup manifest with metadata."""
        
        manifest = {
            'backup_type': 'incremental' if incremental else 'full',
            'timestamp': self.timestamp,
            'created_date': datetime.now().isoformat(),
            'music_root': str(self.music_root),
            'backup_dir': str(backup_dir),
            'files': []
        }
        
        # Catalog all files in backup
        for file_path in backup_dir.rglob("*"):
            if file_path.is_file() and file_path.name != "backup_manifest.json":
                file_info = {
                    'path': str(file_path.relative_to(backup_dir)),
                    'size': file_path.stat().st_size,
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    'checksum': self._calculate_checksum(file_path)
                }
                manifest['files'].append(file_info)
        
        manifest['total_files'] = len(manifest['files'])
        manifest['total_size'] = sum(f['size'] for f in manifest['files'])
        
        return manifest
    
    def _compress_backup(self, backup_dir: Path) -> Path:
        """Compress backup directory."""
        print("🗜️  Compressing backup...")
        
        compressed_file = backup_dir.with_suffix('.tar.gz')
        
        with tarfile.open(compressed_file, 'w:gz') as tar:
            tar.add(backup_dir, arcname=backup_dir.name)
        
        return compressed_file
    
    def _find_last_backup_date(self) -> datetime:
        """Find the date of the last backup."""
        
        backup_files = list(self.backup_root.glob("music_mcp_*backup_*"))
        
        if not backup_files:
            # No previous backups, return 30 days ago
            return datetime.now() - timedelta(days=30)
        
        # Extract dates from backup filenames
        latest_date = datetime.min
        
        for backup_file in backup_files:
            try:
                # Extract timestamp from filename
                parts = backup_file.name.split('_')
                if len(parts) >= 4:
                    date_str = parts[-2]  # Date part
                    time_str = parts[-1].split('.')[0]  # Time part
                    backup_date = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                    latest_date = max(latest_date, backup_date)
            except ValueError:
                continue
        
        return latest_date if latest_date != datetime.min else datetime.now() - timedelta(days=30)
    
    def _find_changed_files(self, since_date: datetime) -> List[Path]:
        """Find files changed since given date."""
        
        changed_files = []
        
        for root, dirs, files in os.walk(self.music_root):
            root_path = Path(root)
            
            for file in files:
                if any(pattern in file for pattern in self.metadata_patterns):
                    file_path = root_path / file
                    
                    # Check modification time
                    mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mod_time > since_date:
                        changed_files.append(file_path)
        
        return changed_files
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file."""
        
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups."""
        
        backups = []
        
        for backup_item in self.backup_root.iterdir():
            if backup_item.name.startswith("music_mcp_"):
                backup_info = {
                    'name': backup_item.name,
                    'path': str(backup_item),
                    'is_compressed': backup_item.suffix == '.gz',
                    'size': backup_item.stat().st_size if backup_item.is_file() else self._get_dir_size(backup_item),
                    'created': datetime.fromtimestamp(backup_item.stat().st_mtime).isoformat()
                }
                
                # Try to read manifest if available
                manifest_path = None
                if backup_item.is_dir():
                    manifest_path = backup_item / "backup_manifest.json"
                elif backup_item.suffix == '.gz':
                    # Would need to extract to read manifest
                    pass
                
                if manifest_path and manifest_path.exists():
                    try:
                        with open(manifest_path) as f:
                            manifest = json.load(f)
                        backup_info.update({
                            'backup_type': manifest.get('backup_type', 'unknown'),
                            'total_files': manifest.get('total_files', 0),
                            'total_size': manifest.get('total_size', 0)
                        })
                    except (json.JSONDecodeError, KeyError):
                        pass
                
                backups.append(backup_info)
        
        # Sort by creation date
        backups.sort(key=lambda x: x['created'], reverse=True)
        return backups
    
    def _get_dir_size(self, dir_path: Path) -> int:
        """Calculate total size of directory."""
        total_size = 0
        for item in dir_path.rglob("*"):
            if item.is_file():
                total_size += item.stat().st_size
        return total_size


class MusicMCPRestore:
    """Recovery system for Music Collection MCP Server."""
    
    def __init__(self, music_root: str, backup_root: str = None):
        """
        Initialize restore system.
        
        Args:
            music_root: Root path of music collection
            backup_root: Root path for backups
        """
        self.music_root = Path(music_root)
        self.backup_root = Path(backup_root) if backup_root else self.music_root / "backups"
    
    def restore_from_backup(self, backup_path: Union[str, Path], 
                           create_backup_before_restore: bool = True,
                           selective_restore: Optional[List[str]] = None) -> bool:
        """
        Restore from a backup.
        
        Args:
            backup_path: Path to backup file or directory
            create_backup_before_restore: Create backup of current state before restoring
            selective_restore: List of file patterns to restore (None = all files)
            
        Returns:
            True if restore was successful
        """
        print(f"🔄 Restoring from backup: {backup_path}")
        
        backup_path = Path(backup_path)
        
        if not backup_path.exists():
            print(f"❌ Backup not found: {backup_path}")
            return False
        
        # Create backup of current state if requested
        if create_backup_before_restore:
            print("📦 Creating backup of current state...")
            backup_system = MusicMCPBackup(str(self.music_root), str(self.backup_root))
            pre_restore_backup = backup_system.create_full_backup(compress=True)
            print(f"✅ Pre-restore backup created: {pre_restore_backup}")
        
        # Extract if compressed
        restore_dir = backup_path
        temp_extract_dir = None
        
        if backup_path.suffix == '.gz':
            print("📦 Extracting compressed backup...")
            temp_extract_dir = backup_path.parent / f"temp_extract_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            temp_extract_dir.mkdir(exist_ok=True)
            
            with tarfile.open(backup_path, 'r:gz') as tar:
                tar.extractall(temp_extract_dir)
            
            # Find the extracted directory
            extracted_dirs = [d for d in temp_extract_dir.iterdir() if d.is_dir()]
            if extracted_dirs:
                restore_dir = extracted_dirs[0]
            else:
                print("❌ Could not find extracted backup directory")
                return False
        
        try:
            # Read backup manifest
            manifest_file = restore_dir / "backup_manifest.json"
            manifest = None
            
            if manifest_file.exists():
                with open(manifest_file) as f:
                    manifest = json.load(f)
                print(f"📋 Restore manifest: {manifest.get('backup_type', 'unknown')} backup from {manifest.get('created_date', 'unknown')}")
            
            # Restore files
            success = self._restore_files(restore_dir, selective_restore, manifest)
            
            if success:
                print("✅ Restore completed successfully")
            else:
                print("❌ Restore completed with errors")
            
            return success
            
        finally:
            # Clean up temporary extraction directory
            if temp_extract_dir and temp_extract_dir.exists():
                shutil.rmtree(temp_extract_dir)
    
    def _restore_files(self, restore_dir: Path, 
                      selective_restore: Optional[List[str]], 
                      manifest: Optional[Dict[str, Any]]) -> bool:
        """Restore files from backup directory."""
        
        success = True
        files_restored = 0
        
        # Determine what to restore
        restore_paths = []
        
        if manifest and 'files' in manifest:
            # Use manifest to guide restoration
            for file_info in manifest['files']:
                file_path = restore_dir / file_info['path']
                if file_path.exists():
                    restore_paths.append((file_path, file_info))
        else:
            # Find all files to restore
            for file_path in restore_dir.rglob("*"):
                if file_path.is_file() and file_path.name != "backup_manifest.json":
                    restore_paths.append((file_path, None))
        
        # Apply selective restore filter
        if selective_restore:
            filtered_paths = []
            for file_path, file_info in restore_paths:
                relative_path = str(file_path.relative_to(restore_dir))
                if any(pattern in relative_path for pattern in selective_restore):
                    filtered_paths.append((file_path, file_info))
            restore_paths = filtered_paths
        
        # Restore files
        for file_path, file_info in restore_paths:
            try:
                # Determine target path
                relative_path = file_path.relative_to(restore_dir)
                target_path = self.music_root / relative_path
                
                # Create target directory
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                shutil.copy2(file_path, target_path)
                
                # Verify checksum if available
                if file_info and 'checksum' in file_info:
                    backup_system = MusicMCPBackup(str(self.music_root))
                    current_checksum = backup_system._calculate_checksum(target_path)
                    if current_checksum != file_info['checksum']:
                        print(f"⚠️  Checksum mismatch for {relative_path}")
                        success = False
                
                files_restored += 1
                
            except Exception as e:
                print(f"❌ Error restoring {file_path}: {e}")
                success = False
        
        print(f"📁 Restored {files_restored} files")
        return success
    
    def validate_backup(self, backup_path: Union[str, Path]) -> Dict[str, Any]:
        """Validate a backup file integrity."""
        
        backup_path = Path(backup_path)
        
        validation_result = {
            'valid': False,
            'errors': [],
            'warnings': [],
            'file_count': 0,
            'total_size': 0
        }
        
        if not backup_path.exists():
            validation_result['errors'].append(f"Backup file not found: {backup_path}")
            return validation_result
        
        # Extract if needed for validation
        temp_dir = None
        validate_dir = backup_path
        
        if backup_path.suffix == '.gz':
            temp_dir = backup_path.parent / f"temp_validate_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            temp_dir.mkdir(exist_ok=True)
            
            try:
                with tarfile.open(backup_path, 'r:gz') as tar:
                    tar.extractall(temp_dir)
                
                extracted_dirs = [d for d in temp_dir.iterdir() if d.is_dir()]
                if extracted_dirs:
                    validate_dir = extracted_dirs[0]
                else:
                    validation_result['errors'].append("Could not extract backup archive")
                    return validation_result
                    
            except Exception as e:
                validation_result['errors'].append(f"Error extracting backup: {e}")
                return validation_result
        
        try:
            # Check for manifest
            manifest_file = validate_dir / "backup_manifest.json"
            manifest = None
            
            if manifest_file.exists():
                try:
                    with open(manifest_file) as f:
                        manifest = json.load(f)
                except json.JSONDecodeError as e:
                    validation_result['errors'].append(f"Invalid manifest JSON: {e}")
            else:
                validation_result['warnings'].append("No backup manifest found")
            
            # Validate files
            backup_system = MusicMCPBackup(str(self.music_root))
            
            if manifest and 'files' in manifest:
                # Validate against manifest
                for file_info in manifest['files']:
                    file_path = validate_dir / file_info['path']
                    
                    if not file_path.exists():
                        validation_result['errors'].append(f"Missing file: {file_info['path']}")
                        continue
                    
                    # Check size
                    actual_size = file_path.stat().st_size
                    if actual_size != file_info['size']:
                        validation_result['errors'].append(
                            f"Size mismatch for {file_info['path']}: expected {file_info['size']}, got {actual_size}"
                        )
                    
                    # Check checksum
                    if 'checksum' in file_info:
                        actual_checksum = backup_system._calculate_checksum(file_path)
                        if actual_checksum != file_info['checksum']:
                            validation_result['errors'].append(
                                f"Checksum mismatch for {file_info['path']}"
                            )
                
                validation_result['file_count'] = len(manifest['files'])
                validation_result['total_size'] = manifest.get('total_size', 0)
            else:
                # Count files manually
                files = list(validate_dir.rglob("*"))
                validation_result['file_count'] = len([f for f in files if f.is_file()])
                validation_result['total_size'] = sum(f.stat().st_size for f in files if f.is_file())
            
            validation_result['valid'] = len(validation_result['errors']) == 0
            
        finally:
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir)
        
        return validation_result


def main():
    """Main backup/restore interface."""
    
    if len(sys.argv) < 3:
        print("Usage:")
        print("  Backup:   python backup-recovery.py backup <music_path> [backup_path]")
        print("  Restore:  python backup-recovery.py restore <music_path> <backup_file>")
        print("  List:     python backup-recovery.py list <music_path> [backup_path]")
        print("  Validate: python backup-recovery.py validate <backup_file>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "backup":
        music_path = sys.argv[2]
        backup_path = sys.argv[3] if len(sys.argv) > 3 else None
        
        backup_system = MusicMCPBackup(music_path, backup_path)
        
        print("🎵 Music Collection MCP Server Backup")
        print("=" * 50)
        
        backup_type = input("Backup type (full/incremental) [full]: ").strip().lower()
        if not backup_type:
            backup_type = "full"
        
        compress = input("Compress backup? (y/n) [y]: ").strip().lower()
        compress = compress != 'n'
        
        if backup_type == "full":
            include_logs = input("Include logs? (y/n) [n]: ").strip().lower() == 'y'
            result = backup_system.create_full_backup(compress=compress, include_logs=include_logs)
        else:
            result = backup_system.create_incremental_backup(compress=compress)
        
        if result:
            print(f"\n🎉 Backup completed: {result}")
        
    elif command == "restore":
        if len(sys.argv) < 4:
            print("Usage: python backup-recovery.py restore <music_path> <backup_file>")
            sys.exit(1)
        
        music_path = sys.argv[2]
        backup_file = sys.argv[3]
        
        restore_system = MusicMCPRestore(music_path)
        
        print("🎵 Music Collection MCP Server Restore")
        print("=" * 50)
        
        create_backup = input("Create backup before restore? (y/n) [y]: ").strip().lower() != 'n'
        
        success = restore_system.restore_from_backup(
            backup_file, 
            create_backup_before_restore=create_backup
        )
        
        if success:
            print("\n🎉 Restore completed successfully")
        else:
            print("\n❌ Restore completed with errors")
            sys.exit(1)
    
    elif command == "list":
        music_path = sys.argv[2]
        backup_path = sys.argv[3] if len(sys.argv) > 3 else None
        
        backup_system = MusicMCPBackup(music_path, backup_path)
        backups = backup_system.list_backups()
        
        print("🎵 Available Backups")
        print("=" * 50)
        
        if not backups:
            print("No backups found")
        else:
            for backup in backups:
                size_mb = backup['size'] / (1024 * 1024)
                print(f"\n📦 {backup['name']}")
                print(f"   Created: {backup['created']}")
                print(f"   Size: {size_mb:.1f} MB")
                print(f"   Type: {backup.get('backup_type', 'unknown')}")
                if 'total_files' in backup:
                    print(f"   Files: {backup['total_files']}")
    
    elif command == "validate":
        if len(sys.argv) < 3:
            print("Usage: python backup-recovery.py validate <backup_file>")
            sys.exit(1)
        
        backup_file = sys.argv[2]
        
        # Use dummy music path for validation
        restore_system = MusicMCPRestore("/tmp")
        result = restore_system.validate_backup(backup_file)
        
        print("🎵 Backup Validation")
        print("=" * 50)
        
        if result['valid']:
            print("✅ Backup is valid")
        else:
            print("❌ Backup validation failed")
        
        print(f"📁 Files: {result['file_count']}")
        print(f"💾 Size: {result['total_size'] / (1024 * 1024):.1f} MB")
        
        if result['errors']:
            print("\n❌ Errors:")
            for error in result['errors']:
                print(f"  - {error}")
        
        if result['warnings']:
            print("\n⚠️  Warnings:")
            for warning in result['warnings']:
                print(f"  - {warning}")
        
        sys.exit(0 if result['valid'] else 1)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main() 