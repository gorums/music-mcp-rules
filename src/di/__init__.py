"""
Dependency Injection module for the Music Collection MCP Server.

This module provides dependency injection functionality separate from
the server implementation to avoid circular imports.
"""

from .dependencies import (
    get_config,
    get_dependency,
    register_dependency_factory,
    register_dependency_instance,
    override_dependency,
    clear_dependencies
)

__all__ = [
    'get_config',
    'get_dependency',
    'register_dependency_factory',
    'register_dependency_instance',
    'override_dependency',
    'clear_dependencies'
] 