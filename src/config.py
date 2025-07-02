import os
from typing import Optional
from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """
    Configuration management for the Music Collection MCP Server.
    Reads only from environment variables (Docker ENV or system env) with sensible defaults.
    
    This class is designed to work with dependency injection - use get_config() 
    from src.mcp_server.dependencies instead of instantiating directly.
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

    def __str__(self) -> str:
        """String representation of configuration."""
        return (
            f"Config(MUSIC_ROOT_PATH='{self.MUSIC_ROOT_PATH}', "
            f"CACHE_DURATION_DAYS={self.CACHE_DURATION_DAYS}, "
            f"LOG_LEVEL='{self.LOG_LEVEL}')"
        )


# Note: Global config instance removed - use dependency injection instead
# Import get_config from src.mcp_server.dependencies for getting config instances 