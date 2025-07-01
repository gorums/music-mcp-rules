# Migration Tools & Band Structure Migration System

## Overview

The Music Collection MCP Server includes a comprehensive migration system for migrating bands from one folder structure to another. This system is designed to be safe, reliable, and provide detailed reporting and analytics.

---

## Core Migration Files

### 1. Main Migration Tool
- **File:** `src/mcp_server/tools/migrate_band_structure_tool.py`
- **Purpose:** Primary tool for migrating band folder structures
- **Key Features:**
  - Support for multiple migration types
  - Dry-run mode for previewing changes
  - Automatic backup creation
  - Progress tracking
  - Album type overrides
  - Selective album exclusion

### 2. Migration Reporting Tool
- **File:** `src/mcp_server/tools/migration_reporting_tool.py`
- **Purpose:** Access migration history, statistics, and analytics
- **Report Types:**
  - `history`: Detailed migration history with timestamps
  - `statistics`: Overall migration statistics and success rates
  - `summary`: Combined overview with recent activity

### 3. Core Migration Engine
- **File:** `src/models/migration.py`
- **Purpose:** Main migration logic and orchestration
- **Key Components:**
  - `BandStructureMigrator`: Main migration class
  - `MigrationValidator`: Comprehensive validation system
  - `MigrationType`: Enum for different migration types
  - `MigrationResult`: Detailed migration results
  - `AlbumMigrationOperation`: Individual operation tracking

### 4. Migration Analytics
- **File:** `src/models/migration_analytics.py`
- **Purpose:** Reporting, analytics, and migration insights
- **Features:**
  - Migration report generation
  - Before/after structure comparison
  - Type distribution analysis
  - Success metrics tracking
  - Performance metrics
  - Markdown report generation

### 5. Error Handling & Recovery
- **File:** `src/models/migration_error_handling.py`
- **Purpose:** Comprehensive error handling and recovery
- **Components:**
  - `DiskSpaceMonitor`: Disk space checking
  - `FileLockDetector`: File lock detection
  - `PermissionManager`: Permission handling
  - `MigrationErrorAnalyzer`: Error analysis
  - `MigrationRecoveryManager`: Recovery orchestration

---

## Supported Migration Types

### 1. `default_to_enhanced`
- **From:** Flat structure with year prefixes
- **To:** Type-based organization (Album/, Live/, Demo/, etc.)
- **Example:**
  ```
  Before: Band/
  ├── 1973 - Album Name/
  ├── 1975 - Live Album (Live)/
  └── 1996 - Greatest Hits (Compilation)/
  
  After: Band/
  ├── Album/
  │   └── 1973 - Album Name/
  ├── Live/
  │   └── 1975 - Live Album/
  └── Compilation/
      └── 1996 - Greatest Hits/
  ```

### 2. `legacy_to_default`
- **From:** Simple album names without years
- **To:** Year-prefixed structure
- **Example:**
  ```
  Before: Band/
  ├── Album Name/
  ├── Live Album/
  └── Greatest Hits/
  
  After: Band/
  ├── 1973 - Album Name/
  ├── 1975 - Live Album (Live)/
  └── 1996 - Greatest Hits (Compilation)/
  ```

### 3. `mixed_to_enhanced`
- **From:** Inconsistent patterns
- **To:** Unified enhanced structure

### 4. `enhanced_to_default`
- **From:** Type-based organization
- **To:** Flat structure with year prefixes

---

## Usage Examples

### Basic Migration (Dry Run)
```json
{
  "method": "tools/call",
  "params": {
    "name": "migrate_band_structure",
    "arguments": {
      "band_name": "Metallica",
      "migration_type": "default_to_enhanced",
      "dry_run": true
    }
  }
}
```

### Migration with Type Overrides
```json
{
  "method": "tools/call",
  "params": {
    "name": "migrate_band_structure",
    "arguments": {
      "band_name": "Pink Floyd",
      "migration_type": "default_to_enhanced",
      "dry_run": false,
      "album_type_overrides": {
        "Live at Pompeii": "live",
        "Echoes - Best Of": "compilation"
      },
      "backup_original": true
    }
  }
}
```

### Migration with Exclusions
```json
{
  "method": "tools/call",
  "params": {
    "name": "migrate_band_structure",
    "arguments": {
      "band_name": "Led Zeppelin",
      "migration_type": "default_to_enhanced",
      "dry_run": false,
      "exclude_albums": ["Bootleg Collection"],
      "backup_original": true
    }
  }
}
```

---

## Migration Reporting

### Get Migration History
```json
{
  "method": "tools/call",
  "params": {
    "name": "migration_reporting",
    "arguments": {
      "report_type": "history",
      "band_name": "Metallica",
      "limit": 10
    }
  }
}
```

### Get Migration Statistics
```json
{
  "method": "tools/call",
  "params": {
    "name": "migration_reporting",
    "arguments": {
      "report_type": "statistics"
    }
  }
}
```

### Get Migration Summary
```json
{
  "method": "tools/call",
  "params": {
    "name": "migration_reporting",
    "arguments": {
      "report_type": "summary"
    }
  }
}
```

---

## Safety Features

### 1. Automatic Backup
- Creates timestamped backup before migration
- Includes original folder structure and metadata
- Enables rollback on failure

### 2. Validation System
- Validates source structure before migration
- Checks permissions and disk space
- Validates migration type appropriateness

### 3. Error Recovery
- Handles file system errors gracefully
- Provides detailed error messages and solutions
- Supports partial migration recovery
- Automatic rollback on critical failures

### 4. Progress Tracking
- Real-time progress reporting
- ETA calculations for large migrations
- Detailed operation logging

---

## Migration Analytics & Reporting

### Comprehensive Reports Include:
- **Structure Comparison:** Before/after analysis
- **Type Distribution:** Album type changes
- **Success Metrics:** Success rates and error breakdown
- **Performance Metrics:** Duration and throughput
- **Organization Improvements:** Compliance improvements
- **Unmigrated Recommendations:** Suggestions for remaining albums

### Markdown Reports
The system generates detailed markdown reports with:
- Migration summary statistics
- Structure comparison tables
- Performance metrics
- Error breakdowns
- Recommendations for future migrations

---

## Testing

### Test Files
- `tests/test_models/test_migration.py`: Core migration logic tests
- `tests/test_mcp_server/test_migration_reporting_tool.py`: Reporting tool tests

### Test Coverage
- Migration validation
- Error handling scenarios
- Dry-run functionality
- Backup and rollback
- Progress tracking
- Analytics generation

---

## Key Features Summary

- **Safe Migration:** Automatic backup and rollback capabilities
- **Multiple Migration Types:** Support for 4 different migration patterns
- **Dry-Run Mode:** Preview changes without making actual modifications
- **Progress Tracking:** Real-time progress with ETA calculations
- **Error Recovery:** Comprehensive error handling and recovery
- **Analytics:** Detailed reporting and success metrics
- **Type Overrides:** Manual album type assignments
- **Selective Migration:** Exclude specific albums from migration
- **Validation:** Comprehensive pre-migration validation
- **Atomic Operations:** Thread-safe migration operations

---

This migration system provides a complete, production-ready solution for safely migrating band folder structures while maintaining data integrity and providing comprehensive reporting and analytics. 