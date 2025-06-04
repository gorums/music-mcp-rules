#!/usr/bin/env python3
"""
Main entry point for Music Collection MCP Server.

This script sets up the proper Python path and starts the MCP server.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def main():
    """Main entry point."""
    try:
        # Import and run the MCP server directly
        from music_mcp_server import main as server_main
        server_main()
        
    except KeyboardInterrupt:
        print("\n⏹️  Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting MCP server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 