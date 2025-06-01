# Music Collection MCP Server - Deployment Scripts

This directory contains comprehensive deployment and maintenance scripts for the Music Collection MCP Server.

## 📁 Script Directory Structure

```
scripts/
├── setup.py                    # Main setup script for all installation methods
├── start-docker.sh            # Docker startup script with options
├── validate-music-structure.py # Music collection structure validator
├── backup-recovery.py         # Backup and recovery system
├── health-check.py            # Collection health monitoring
├── monitoring/
│   └── logging-config.py      # Logging and monitoring configuration
└── claude-desktop-configs/    # Claude Desktop configuration examples
    ├── README.md
    ├── local-python-config.json
    ├── docker-config.json
    ├── development-config.json
    ├── multi-collection-config.json
    └── network-storage-config.json
```

## 🚀 Quick Start

### 1. Automated Setup
Run the main setup script for guided installation:

```bash
python scripts/setup.py
```

This will:
- Check system requirements
- Guide you through installation options
- Configure your music collection path
- Generate Claude Desktop configuration
- Validate your setup

### 2. Docker Quick Start
Use the Docker startup script:

```bash
# Make executable (Linux/macOS)
chmod +x scripts/start-docker.sh

# Start with your music collection
./scripts/start-docker.sh -m /path/to/your/music
```

### 3. Docker Compose
For persistent deployment:

```bash
# Update docker-compose.yml with your music path
# Then start the service
docker-compose up music-mcp
```

## 📋 Script Descriptions

### 🔧 setup.py
**Comprehensive setup and installation script**

```bash
python scripts/setup.py
```

**Features:**
- System requirements check
- Multiple installation methods (local Python, Docker, development)
- Automatic dependency installation
- Claude Desktop configuration generation
- Installation validation

**Installation Methods:**
1. **Local Python**: Install dependencies locally and run with Python
2. **Docker Container**: Build and run in Docker with automatic startup scripts
3. **Development Environment**: Setup with testing tools and debug configuration
4. **Configuration Only**: Generate Claude Desktop configs without installation

### 🐳 start-docker.sh
**Docker container startup script with options**

```bash
./scripts/start-docker.sh -m /path/to/music [options]
```

**Options:**
- `-m, --music-path`: Path to music collection (required)
- `-n, --name`: Container name (default: music-mcp)
- `-c, --cache-days`: Cache duration in days (default: 30)
- `-l, --log-level`: Log level (default: ERROR)
- `-h, --help`: Show help message

**Features:**
- Automatic Docker image building
- Windows path conversion for WSL
- Container management (stop/remove existing)
- Validation checks
- Cross-platform compatibility

### 🔍 validate-music-structure.py
**Music collection structure validator**

```bash
python scripts/validate-music-structure.py /path/to/music
```

**What it checks:**
- Folder structure compliance (Band/Album/Track)
- File naming conventions
- Performance-impacting issues
- Special characters and encoding
- Collection size optimization
- Duplicate detection

**Output:**
- Detailed validation report
- Performance recommendations
- Structure optimization suggestions
- JSON report file

### 💾 backup-recovery.py
**Comprehensive backup and recovery system**

```bash
# Create backup
python scripts/backup-recovery.py backup /path/to/music

# Restore from backup
python scripts/backup-recovery.py restore /path/to/music /path/to/backup.tar.gz

# List available backups
python scripts/backup-recovery.py list /path/to/music

# Validate backup integrity
python scripts/backup-recovery.py validate /path/to/backup.tar.gz
```

**Features:**
- Full and incremental backups
- Metadata file backup (.band_metadata.json, .collection_index.json)
- Configuration backup
- Compression support
- Integrity validation with checksums
- Selective restore capabilities

### 🏥 health-check.py
**Collection health monitoring system**

```bash
python scripts/health-check.py /path/to/music [--save-report] [--output report.json]
```

**Health Checks:**
- Filesystem access and permissions
- Collection index integrity
- Metadata file corruption
- File synchronization issues
- Performance metrics
- Cache health
- Configuration validation

**Output:**
- Comprehensive health report
- Critical issues and warnings
- Actionable recommendations
- Performance scoring
- JSON report export

### 📊 monitoring/logging-config.py
**Advanced logging and monitoring configuration**

```python
from scripts.monitoring.logging_config import setup_monitoring

# Setup monitoring for different environments
monitoring = setup_monitoring(environment="production", log_dir="/app/logs")
logger = monitoring['main_logger']
performance_logger = monitoring['performance_logger']
```

**Features:**
- Environment-specific configurations (development, testing, production)
- Performance monitoring with JSON logs
- MCP request/response logging
- Error tracking and analysis
- Log rotation and cleanup
- Analysis script generation

## 🔧 Claude Desktop Configuration

### Configuration Examples
The `claude-desktop-configs/` directory contains ready-to-use configuration examples:

1. **local-python-config.json**: For local Python installations
2. **docker-config.json**: For Docker container deployments
3. **development-config.json**: For development with debug logging
4. **multi-collection-config.json**: For multiple music collections
5. **network-storage-config.json**: For network storage setups

### Configuration Locations
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### Setup Process
1. Choose appropriate configuration from examples
2. Update paths to match your music collection
3. Copy to your Claude Desktop config file
4. Restart Claude Desktop

## 🐳 Docker Deployment

### Using docker-compose.yml
The project includes a Docker Compose configuration for easy deployment:

```bash
# Production deployment
docker-compose up music-mcp

# Development deployment
docker-compose --profile dev up music-mcp-dev
```

**Features:**
- Production and development configurations
- Volume management for logs and backups
- Health checks
- Restart policies
- Network isolation

### Manual Docker Commands
```bash
# Build image
docker build -t music-collection-mcp .

# Run container
docker run -it --rm \
  --name music-mcp \
  -v "/path/to/music:/music:ro" \
  -e MUSIC_ROOT_PATH=/music \
  music-collection-mcp
```

## 🔧 Maintenance Scripts

### Quick Health Check
Generated automatically by health-check.py:

```bash
python quick_health_check.py /path/to/music
```

### Log Analysis
Generated by logging configuration:

```bash
python analyze_logs.py /path/to/logs
```

## 📝 Best Practices

### Security
- Use read-only volume mounts for music collections (`-v path:/music:ro`)
- Avoid exposing sensitive directories
- Use ERROR log level in production
- Regularly update Docker images

### Performance
- Run validation before large deployments
- Use incremental backups for large collections
- Monitor cache size and cleanup regularly
- Consider splitting very large collections

### Maintenance
- Run health checks monthly
- Create backups before major changes
- Monitor logs for performance issues
- Update collection index when filesystem changes

## 🆘 Troubleshooting

### Common Issues

**Docker not starting:**
```bash
# Check Docker status
docker info

# Check image exists
docker images music-collection-mcp
```

**Permission errors:**
```bash
# Check music path permissions
ls -la /path/to/music

# Fix permissions if needed
chmod -R 755 /path/to/music
```

**Path issues on Windows:**
- Use forward slashes or escaped backslashes in paths
- Consider using WSL paths (`/mnt/c/...`) for Docker

**Configuration not working:**
- Validate JSON syntax in Claude Desktop config
- Check path formatting and existence
- Verify environment variables

### Getting Help
1. Run health check for diagnostics
2. Check logs for error messages
3. Validate music structure
4. Review configuration examples
5. Test with minimal setup first

## 🔄 Development Workflow

### Setting up Development Environment
```bash
# Use setup script for development
python scripts/setup.py
# Choose option 3: Development environment

# Or manually:
pip install -r requirements.txt
pip install pytest pytest-asyncio psutil pre-commit

# Run tests
docker build -f Dockerfile.test -t music-mcp-tests .
docker run --rm music-mcp-tests
```

### Contributing
- Follow code style guidelines in docs/CODE_STYLE.md
- Add tests for new features
- Update documentation
- Run validation scripts before submitting

This comprehensive deployment system ensures reliable, maintainable installations of the Music Collection MCP Server across different environments and use cases. 