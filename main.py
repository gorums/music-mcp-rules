#!/usr/bin/env python3
"""
Music Collection MCP Server - Main Entry Point

This is the main entry point for the Music Collection MCP Server.
It imports and runs the server from the refactored server package.
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
        # Import and run the MCP server from refactored structure
        from server.core import main as server_main
        server_main()
        
    except KeyboardInterrupt:
        print("\n[STOP] Server stopped by user")
    except Exception as e:
        print(f"[ERROR] Error starting MCP server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 