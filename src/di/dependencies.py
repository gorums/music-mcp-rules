"""
Dependency injection management for the Music Collection MCP Server.

This module provides a centralized dependency injection system for configuration
and other dependencies, ensuring single instance management and testability.
"""

import logging
from typing import Optional, TypeVar, Type, Dict, Any, Callable
from threading import Lock
from contextlib import contextmanager

from src.config import Config
from src.exceptions import ConfigurationError

# Type variables for generic dependency management
T = TypeVar('T')

# Configure logging
logger = logging.getLogger(__name__)


class DependencyContainer:
    """
    Dependency injection container that manages singleton instances
    and provides easy testing with dependency mocking.
    """
    
    def __init__(self):
        """Initialize the dependency container."""
        self._instances: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable[[], Any]] = {}
        self._lock = Lock()
        self._config_instance: Optional[Config] = None
        
    def register_singleton(self, dependency_type: Type[T], factory: Callable[[], T]) -> None:
        """
        Register a singleton factory for a dependency type.
        
        Args:
            dependency_type: The type of dependency to register
            factory: Factory function that creates the dependency instance
        """
        with self._lock:
            self._factories[dependency_type] = factory
            # Clear any existing instance to force recreation
            if dependency_type in self._instances:
                del self._instances[dependency_type]
    
    def register_instance(self, dependency_type: Type[T], instance: T) -> None:
        """
        Register a specific instance for a dependency type.
        
        Args:
            dependency_type: The type of dependency to register
            instance: The specific instance to use
        """
        with self._lock:
            self._instances[dependency_type] = instance
            # Remove factory if it exists
            if dependency_type in self._factories:
                del self._factories[dependency_type]
    
    def get(self, dependency_type: Type[T]) -> T:
        """
        Get a dependency instance, creating it if necessary.
        
        Args:
            dependency_type: The type of dependency to retrieve
            
        Returns:
            The dependency instance
            
        Raises:
            ConfigurationError: If dependency cannot be created or retrieved
        """
        with self._lock:
            # Return existing instance if available
            if dependency_type in self._instances:
                return self._instances[dependency_type]
            
            # Create instance using factory if available
            if dependency_type in self._factories:
                try:
                    instance = self._factories[dependency_type]()
                    self._instances[dependency_type] = instance
                    logger.debug(f"Created new instance of {dependency_type.__name__}")
                    return instance
                except Exception as e:
                    raise ConfigurationError(
                        f"Failed to create dependency instance for {dependency_type.__name__}: {str(e)}",
                        original_exception=e
                    )
            
            # Special handling for Config type
            if dependency_type == Config:
                return self._get_config_instance()
            
            # If no factory registered, raise error
            raise ConfigurationError(
                f"No factory or instance registered for dependency type: {dependency_type.__name__}"
            )
    
    def _get_config_instance(self) -> Config:
        """
        Get or create the Config singleton instance.
        
        Returns:
            The Config instance
        """
        if self._config_instance is None:
            try:
                self._config_instance = Config()
                logger.debug("Created new Config instance")
            except Exception as e:
                raise ConfigurationError(
                    f"Failed to create Config instance: {str(e)}",
                    original_exception=e
                )
        return self._config_instance
    
    def clear(self) -> None:
        """Clear all instances and factories (useful for testing)."""
        with self._lock:
            self._instances.clear()
            self._factories.clear()
            self._config_instance = None
            logger.debug("Cleared all dependency instances and factories")
    
    def has_instance(self, dependency_type: Type[T]) -> bool:
        """
        Check if an instance exists for the given dependency type.
        
        Args:
            dependency_type: The type to check
            
        Returns:
            True if instance exists, False otherwise
        """
        with self._lock:
            return dependency_type in self._instances or (
                dependency_type == Config and self._config_instance is not None
            )
    
    def get_registered_types(self) -> Dict[str, bool]:
        """
        Get information about registered dependency types.
        
        Returns:
            Dictionary mapping type names to whether they have instances
        """
        with self._lock:
            registered = {}
            
            # Add factory-registered types
            for dep_type in self._factories:
                registered[dep_type.__name__] = dep_type in self._instances
            
            # Add instance-registered types
            for dep_type in self._instances:
                if dep_type.__name__ not in registered:
                    registered[dep_type.__name__] = True
            
            # Add Config if it has an instance
            if self._config_instance is not None:
                registered["Config"] = True
            
            return registered


# Global dependency container instance
_container = DependencyContainer()


def get_dependency(dependency_type: Type[T]) -> T:
    """
    Get a dependency from the global container.
    
    Args:
        dependency_type: The type of dependency to retrieve
        
    Returns:
        The dependency instance
    """
    return _container.get(dependency_type)


def get_config() -> Config:
    """
    Get the configuration instance.
    
    Returns:
        The Config singleton instance
    """
    return get_dependency(Config)


def register_dependency_factory(dependency_type: Type[T], factory: Callable[[], T]) -> None:
    """
    Register a factory for creating dependency instances.
    
    Args:
        dependency_type: The type of dependency to register
        factory: Factory function that creates the dependency instance
    """
    _container.register_singleton(dependency_type, factory)


def register_dependency_instance(dependency_type: Type[T], instance: T) -> None:
    """
    Register a specific instance for a dependency type.
    
    Args:
        dependency_type: The type of dependency to register
        instance: The specific instance to use
    """
    _container.register_instance(dependency_type, instance)


@contextmanager
def override_dependency(dependency_type: Type[T], instance: T):
    """
    Context manager for temporarily overriding a dependency (useful for testing).
    
    Args:
        dependency_type: The type of dependency to override
        instance: The instance to use temporarily
    """
    # Store original state
    original_instance = None
    had_instance = _container.has_instance(dependency_type)
    
    if had_instance:
        original_instance = _container.get(dependency_type)
    
    try:
        # Set override instance
        _container.register_instance(dependency_type, instance)
        yield
    finally:
        # Restore original state
        if had_instance and original_instance is not None:
            _container.register_instance(dependency_type, original_instance)
        elif dependency_type in _container._instances:
            # Clear the override if there was no original instance
            with _container._lock:
                del _container._instances[dependency_type]


def clear_dependencies() -> None:
    """Clear all dependencies (useful for testing)."""
    _container.clear()


def get_dependency_info() -> Dict[str, Any]:
    """
    Get information about registered dependencies.
    
    Returns:
        Dictionary with dependency information
    """
    return {
        "registered_types": _container.get_registered_types(),
        "container_id": id(_container),
        "total_instances": len(_container._instances),
        "total_factories": len(_container._factories)
    }


# Initialize default config factory
def _create_default_config() -> Config:
    """Default factory for creating Config instances."""
    return Config()


# Register default Config factory
register_dependency_factory(Config, _create_default_config) 