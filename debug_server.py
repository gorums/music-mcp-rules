#!/usr/bin/env python3
"""
Debug script to check MCP server output.
"""

import asyncio
import sys
from pathlib import Path

async def debug_server():
    """Debug the MCP server output."""
    print("🐛 Starting debug session...")
    
    # Start server process
    process = await asyncio.create_subprocess_exec(
        sys.executable, "main.py",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env={"MUSIC_ROOT_PATH": str(Path(__file__).parent / "test_music_collection")}
    )
    
    print("✅ Server process started")
    
    # Send initialize request
    init_request = '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {"experimental": {}, "sampling": {}}, "clientInfo": {"name": "debug-client", "version": "1.0.0"}}}\n'
    
    print(f"📤 Sending request: {init_request.strip()}")
    
    process.stdin.write(init_request.encode())
    await process.stdin.drain()
    
    # Wait a bit and check what we get back
    try:
        # Read stdout with timeout
        stdout_data = await asyncio.wait_for(process.stdout.read(1024), timeout=5.0)
        print(f"📥 Stdout data: {stdout_data}")
        print(f"📥 Stdout decoded: '{stdout_data.decode()}'")
        
        # Check stderr too
        stderr_data = await asyncio.wait_for(process.stderr.read(1024), timeout=1.0)
        print(f"🚨 Stderr data: {stderr_data}")
        print(f"🚨 Stderr decoded: '{stderr_data.decode()}'")
        
    except asyncio.TimeoutError:
        print("⏰ Timeout waiting for response")
    
    # Check if process is still running
    if process.returncode is None:
        print("✅ Process is still running")
    else:
        print(f"❌ Process exited with code: {process.returncode}")
    
    # Cleanup
    process.terminate()
    await process.wait()
    print("🧹 Process terminated")

if __name__ == "__main__":
    asyncio.run(debug_server()) 