import os
from typing import Optional
from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """
    Configuration management for the Music Collection MCP Server.
    Reads only from environment variables (Docker ENV or system env) with sensible defaults.
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


try:
    config = Config()
except ValidationError as e:
    raise RuntimeError(f"Configuration validation error: {e}") 