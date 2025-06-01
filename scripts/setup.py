#!/usr/bin/env python3
"""
Setup script for easy installation of Music Collection MCP Server.

This script provides automated installation for different deployment scenarios:
- Local Python installation
- Docker container setup
- Development environment setup
- MCP client configuration
"""

import os
import sys
import subprocess
import json
import platform
from pathlib import Path
from typing import Dict, Any, List, Optional


class MusicMCPSetup:
    """Music Collection MCP Server setup manager."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.system_platform = platform.system().lower()
        self.python_version = sys.version_info
        
    def check_requirements(self) -> Dict[str, bool]:
        """Check system requirements for installation."""
        requirements = {
            "python_version": self.python_version >= (3.8,),
            "docker_available": self._check_docker(),
            "git_available": self._check_git(),
            "pip_available": self._check_pip(),
        }
        return requirements
    
    def _check_docker(self) -> bool:
        """Check if Docker is available."""
        try:
            subprocess.run(["docker", "--version"], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _check_git(self) -> bool:
        """Check if Git is available."""
        try:
            subprocess.run(["git", "--version"], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _check_pip(self) -> bool:
        """Check if pip is available."""
        try:
            subprocess.run([sys.executable, "-m", "pip", "--version"], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def install_local(self, music_path: str, dev_mode: bool = False) -> None:
        """Install for local Python environment."""
        print("🚀 Installing Music Collection MCP Server locally...")
        
        # Install dependencies
        print("📦 Installing Python dependencies...")
        cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
        if dev_mode:
            cmd.extend(["-e", "."])
        
        subprocess.run(cmd, cwd=self.project_root, check=True)
        
        # Create configuration
        config_file = self.project_root / ".env"
        with open(config_file, "w") as f:
            f.write(f"MUSIC_ROOT_PATH={music_path}\n")
            f.write("CACHE_DURATION_DAYS=30\n")
            f.write("LOG_LEVEL=INFO\n")
        
        print(f"✅ Local installation complete!")
        print(f"📁 Music path configured: {music_path}")
        print(f"⚙️  Configuration saved to: {config_file}")
        
    def setup_docker(self, music_path: str, container_name: str = "music-mcp") -> None:
        """Setup Docker container."""
        print("🐳 Setting up Docker container...")
        
        # Build Docker image
        print("🔨 Building Docker image...")
        subprocess.run([
            "docker", "build", "-t", "music-collection-mcp", "."
        ], cwd=self.project_root, check=True)
        
        # Create startup script
        startup_script = self.project_root / "scripts" / "start-docker.sh"
        startup_script.parent.mkdir(exist_ok=True)
        
        with open(startup_script, "w") as f:
            f.write(f"""#!/bin/bash
# Docker startup script for Music Collection MCP Server

docker run -it --rm \\
  --name {container_name} \\
  -v "{music_path}:/music:ro" \\
  -e MUSIC_ROOT_PATH=/music \\
  -e CACHE_DURATION_DAYS=30 \\
  -e LOG_LEVEL=INFO \\
  music-collection-mcp
""")
        
        if self.system_platform != "windows":
            os.chmod(startup_script, 0o755)
        
        print(f"✅ Docker setup complete!")
        print(f"📁 Music path: {music_path}")
        print(f"🚀 Start with: {startup_script}")
        
    def configure_claude_desktop(self, music_path: str, use_docker: bool = False) -> None:
        """Generate Claude Desktop configuration."""
        print("🤖 Configuring Claude Desktop integration...")
        
        if use_docker:
            # Docker-based configuration
            config = {
                "mcpServers": {
                    "music-collection": {
                        "command": "docker",
                        "args": [
                            "run", "-i", "--rm",
                            "-v", f"{music_path}:/music:ro",
                            "-e", "MUSIC_ROOT_PATH=/music",
                            "music-collection-mcp"
                        ],
                        "env": {}
                    }
                }
            }
        else:
            # Local Python configuration
            python_path = sys.executable
            main_script = str(self.project_root / "main.py")
            
            config = {
                "mcpServers": {
                    "music-collection": {
                        "command": python_path,
                        "args": [main_script],
                        "env": {
                            "MUSIC_ROOT_PATH": music_path,
                            "CACHE_DURATION_DAYS": "30",
                            "LOG_LEVEL": "ERROR"
                        }
                    }
                }
            }
        
        # Save configuration
        config_file = self.project_root / "claude_desktop_config.json"
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Claude Desktop configuration generated!")
        print(f"📋 Configuration saved to: {config_file}")
        print(f"📖 Copy contents to your Claude Desktop config file")
        
        # Show platform-specific config locations
        self._show_claude_config_locations()
    
    def _show_claude_config_locations(self) -> None:
        """Show Claude Desktop config file locations by platform."""
        locations = {
            "windows": "%APPDATA%\\Claude\\claude_desktop_config.json",
            "darwin": "~/Library/Application Support/Claude/claude_desktop_config.json", 
            "linux": "~/.config/Claude/claude_desktop_config.json"
        }
        
        if self.system_platform in locations:
            print(f"📍 Claude Desktop config location: {locations[self.system_platform]}")
    
    def create_dev_environment(self, music_path: str) -> None:
        """Setup development environment."""
        print("🛠️  Setting up development environment...")
        
        # Install development dependencies
        print("📦 Installing development dependencies...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "-r", "requirements.txt"
        ], cwd=self.project_root, check=True)
        
        # Install test dependencies
        subprocess.run([
            sys.executable, "-m", "pip", "install",
            "pytest>=7.0.0", "pytest-asyncio>=0.21.0", "psutil>=5.9.0"
        ], check=True)
        
        # Create development configuration
        dev_config = self.project_root / ".env.dev"
        with open(dev_config, "w") as f:
            f.write(f"MUSIC_ROOT_PATH={music_path}\n")
            f.write("CACHE_DURATION_DAYS=1\n") 
            f.write("LOG_LEVEL=DEBUG\n")
        
        # Setup pre-commit hooks (if available)
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", "pre-commit"
            ], check=True)
            
            # Create pre-commit config
            precommit_config = self.project_root / ".pre-commit-config.yaml"
            with open(precommit_config, "w") as f:
                f.write("""repos:
-   repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
    -   id: black
        language_version: python3
-   repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
    -   id: flake8
        args: [--max-line-length=88]
-   repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
    -   id: mypy
        additional_dependencies: [types-all]
""")
            
            subprocess.run(["pre-commit", "install"], 
                         cwd=self.project_root, check=False)
            print("✅ Pre-commit hooks installed")
            
        except subprocess.CalledProcessError:
            print("⚠️  Pre-commit setup optional, skipping...")
        
        print(f"✅ Development environment setup complete!")
        print(f"📁 Music path: {music_path}")
        print(f"⚙️  Dev config: {dev_config}")
        print(f"🧪 Run tests: docker build -f Dockerfile.test -t music-mcp-tests . && docker run --rm music-mcp-tests")
    
    def validate_installation(self, music_path: str) -> Dict[str, Any]:
        """Validate installation setup."""
        print("🔍 Validating installation...")
        
        results = {
            "music_path_exists": Path(music_path).exists(),
            "music_path_readable": os.access(music_path, os.R_OK),
            "requirements_satisfied": True,
            "docker_image_available": False,
            "configuration_valid": False
        }
        
        # Check if music path has music files
        music_files = []
        if results["music_path_exists"]:
            for ext in [".mp3", ".flac", ".wav", ".m4a", ".ogg"]:
                music_files.extend(list(Path(music_path).rglob(f"*{ext}")))
        
        results["music_files_found"] = len(music_files)
        
        # Check Docker image
        if self._check_docker():
            try:
                subprocess.run([
                    "docker", "images", "music-collection-mcp", "-q"
                ], capture_output=True, check=True)
                results["docker_image_available"] = True
            except subprocess.CalledProcessError:
                pass
        
        # Validate configuration
        try:
            from config import config
            results["configuration_valid"] = True
        except Exception as e:
            results["config_error"] = str(e)
        
        # Print validation results
        print(f"📁 Music path exists: {'✅' if results['music_path_exists'] else '❌'}")
        print(f"📖 Music path readable: {'✅' if results['music_path_readable'] else '❌'}")
        print(f"🎵 Music files found: {results['music_files_found']}")
        print(f"🐳 Docker image available: {'✅' if results['docker_image_available'] else '❌'}")
        print(f"⚙️  Configuration valid: {'✅' if results['configuration_valid'] else '❌'}")
        
        return results


def main():
    """Main setup interface."""
    print("🎵 Music Collection MCP Server Setup")
    print("=" * 50)
    
    setup = MusicMCPSetup()
    
    # Check requirements
    requirements = setup.check_requirements()
    print("\n📋 System Requirements:")
    for req, status in requirements.items():
        print(f"  {req}: {'✅' if status else '❌'}")
    
    if not requirements["python_version"]:
        print("❌ Python 3.8+ required")
        sys.exit(1)
    
    # Get music collection path
    music_path = input("\n📁 Enter your music collection path: ").strip()
    if not music_path:
        print("❌ Music path required")
        sys.exit(1)
    
    music_path = os.path.abspath(os.path.expanduser(music_path))
    
    if not os.path.exists(music_path):
        print(f"❌ Music path does not exist: {music_path}")
        sys.exit(1)
    
    # Choose installation method
    print("\n🚀 Installation Options:")
    print("1. Local Python installation")
    print("2. Docker container setup")
    print("3. Development environment")
    print("4. Claude Desktop configuration only")
    print("5. Validate existing installation")
    
    choice = input("\nChoose installation method (1-5): ").strip()
    
    try:
        if choice == "1":
            setup.install_local(music_path)
            setup.configure_claude_desktop(music_path, use_docker=False)
        elif choice == "2":
            if not requirements["docker_available"]:
                print("❌ Docker not available")
                sys.exit(1)
            setup.setup_docker(music_path)
            setup.configure_claude_desktop(music_path, use_docker=True)
        elif choice == "3":
            setup.create_dev_environment(music_path)
        elif choice == "4":
            use_docker = input("Use Docker? (y/n): ").strip().lower() == "y"
            setup.configure_claude_desktop(music_path, use_docker=use_docker)
        elif choice == "5":
            setup.validate_installation(music_path)
        else:
            print("❌ Invalid choice")
            sys.exit(1)
            
        print("\n🎉 Setup complete!")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 