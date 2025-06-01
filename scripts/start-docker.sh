#!/bin/bash
# Docker startup script for Music Collection MCP Server

set -e

# Default values
MUSIC_PATH=""
CONTAINER_NAME="music-mcp"
CACHE_DAYS="30"
LOG_LEVEL="ERROR"

# Function to show usage
show_usage() {
    echo "Usage: $0 -m <music_path> [options]"
    echo ""
    echo "Options:"
    echo "  -m, --music-path     Path to music collection (required)"
    echo "  -n, --name          Container name (default: music-mcp)"
    echo "  -c, --cache-days    Cache duration in days (default: 30)"
    echo "  -l, --log-level     Log level (default: ERROR)"
    echo "  -h, --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -m /home/user/Music"
    echo "  $0 -m C:/Users/User/Music -n my-music-server"
    echo "  $0 --music-path /music --cache-days 60 --log-level INFO"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--music-path)
            MUSIC_PATH="$2"
            shift 2
            ;;
        -n|--name)
            CONTAINER_NAME="$2"
            shift 2
            ;;
        -c|--cache-days)
            CACHE_DAYS="$2"
            shift 2
            ;;
        -l|--log-level)
            LOG_LEVEL="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Check required parameters
if [ -z "$MUSIC_PATH" ]; then
    echo "Error: Music path is required"
    show_usage
    exit 1
fi

# Convert Windows paths to WSL format if needed
if [[ "$MUSIC_PATH" =~ ^[A-Za-z]: ]]; then
    echo "Converting Windows path to WSL format..."
    MUSIC_PATH=$(echo "$MUSIC_PATH" | sed 's|^C:|/mnt/c|' | sed 's|\\|/|g')
fi

# Check if music path exists
if [ ! -d "$MUSIC_PATH" ]; then
    echo "Error: Music path does not exist: $MUSIC_PATH"
    exit 1
fi

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "Error: Docker is not running"
    exit 1
fi

# Check if image exists, build if necessary
if ! docker images music-collection-mcp -q | grep -q .; then
    echo "Building Docker image..."
    docker build -t music-collection-mcp .
fi

# Stop existing container if running
if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
    echo "Stopping existing container..."
    docker stop "$CONTAINER_NAME"
fi

# Remove existing container if exists
if docker ps -aq -f name="$CONTAINER_NAME" | grep -q .; then
    echo "Removing existing container..."
    docker rm "$CONTAINER_NAME"
fi

echo "Starting Music Collection MCP Server..."
echo "Music Path: $MUSIC_PATH"
echo "Container Name: $CONTAINER_NAME"
echo "Cache Duration: $CACHE_DAYS days"
echo "Log Level: $LOG_LEVEL"
echo ""

# Start the container
docker run -it --rm \
  --name "$CONTAINER_NAME" \
  -v "$MUSIC_PATH:/music:ro" \
  -e MUSIC_ROOT_PATH=/music \
  -e CACHE_DURATION_DAYS="$CACHE_DAYS" \
  -e LOG_LEVEL="$LOG_LEVEL" \
  music-collection-mcp

echo "Container stopped." 