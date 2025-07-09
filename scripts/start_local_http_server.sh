#!/bin/sh
# Start a local HTTP server for browser testing of _index.html
# Usage: ./scripts/start_local_http_server.sh

PORT=8000
ROOT_DIR="$(dirname "$0")/.."
cd "$ROOT_DIR"

# Print info
echo "Starting local HTTP server on port $PORT..."
echo "Open http://localhost:$PORT/_index.html in your browser."

# Use Python 3 http.server
python -m http.server $PORT 