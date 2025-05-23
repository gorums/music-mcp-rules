#!/usr/bin/env python3
"""
Main entry point for Music Collection MCP Server.

This script sets up the proper Python path and starts the MCP server.
"""

import sys
import os
import runpy
from pathlib import Path

# Add the src directory to the Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def main():
    """Main entry point."""
    try:
        # Change working directory to src to help with relative imports
        os.chdir(src_path)
        
        # Run the module as a script, which handles relative imports better
        runpy.run_module("music_mcp_server", run_name="__main__")
        
    except KeyboardInterrupt:
        print("\n⏹️  Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting MCP server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 