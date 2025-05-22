import os
from typing import Optional
from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from a .env file if present
load_dotenv()


class Config(BaseSettings):
    """
    Configuration management for the Music Collection MCP Server.
    Reads from environment variables with sensible defaults and validates them.
    """
    MUSIC_ROOT_PATH: str = Field(
        default="/path/to/your/music/collection",
        description="Path to the root music directory."
    )
    CACHE_DURATION_DAYS: int = Field(
        default=30,
        description="Cache expiration in days (default: 30)."
    )

    model_config = {
        'env_file': '.env',
        'env_file_encoding': 'utf-8'
    }


try:
    config = Config()
except ValidationError as e:
    raise RuntimeError(f"Configuration validation error: {e}") 