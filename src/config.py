import os
from typing import Optional
from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """
    Configuration management for the Music Collection MCP Server.
    Reads only from environment variables (Docker ENV or system env) with sensible defaults.
    
    This class is designed to work with dependency injection - use get_config() 
    from src.server.dependencies instead of instantiating directly.
    """
    MUSIC_ROOT_PATH: str = Field(
        default="/music",
        description="Path to the root music directory."
    )
    CACHE_DURATION_DAYS: int = Field(
        default=30,
        description="Cache expiration in days (default: 30)."
    )
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)."
    )

    # Only read from environment variables, no .env file support
    model_config = {
        'env_file': None,  # Explicitly disable .env file loading
    }
    
    @classmethod
    def create_instance(cls) -> 'Config':
        """
        Create a new Config instance with validation.
        
        Returns:
            Config instance
            
        Raises:
            RuntimeError: If configuration validation fails
        """
        try:
            return cls()
        except ValidationError as e:
            raise RuntimeError(f"Configuration validation error: {e}")
    
    def validate_configuration(self) -> None:
        """
        Validate current configuration settings.
        
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate music root path format
        if not self.MUSIC_ROOT_PATH:
            raise ValueError("MUSIC_ROOT_PATH cannot be empty")
        
        # Validate cache duration
        if self.CACHE_DURATION_DAYS < 1:
            raise ValueError("CACHE_DURATION_DAYS must be at least 1")
        
        # Validate log level
        valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.LOG_LEVEL.upper() not in valid_log_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {', '.join(valid_log_levels)}")
    
    def get_music_root_path(self) -> str:
        """Get the music root path."""
        return self.MUSIC_ROOT_PATH
    
    def get_cache_duration_days(self) -> int:
        """Get the cache duration in days."""
        return self.CACHE_DURATION_DAYS
    
    def get_log_level(self) -> str:
        """Get the log level."""
        return self.LOG_LEVEL
    
    def __str__(self) -> str:
        """String representation of configuration."""
        return (
            f"Config(MUSIC_ROOT_PATH='{self.MUSIC_ROOT_PATH}', "
            f"CACHE_DURATION_DAYS={self.CACHE_DURATION_DAYS}, "
            f"LOG_LEVEL='{self.LOG_LEVEL}')"
        )


# Note: Global config instance removed - use dependency injection instead
# Import get_config from src.server.dependencies for getting config instances 