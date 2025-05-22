# Music Collection MCP Server

## Configuration Management

The server uses environment variables for configuration. You can set these in a `.env` file in the project root. Example variables:

- `MUSIC_ROOT_PATH`: Path to the root music directory (required)
- `CACHE_DURATION_DAYS`: Cache expiration in days (default: 30)

Example `.env` file:

```
MUSIC_ROOT_PATH=/path/to/your/music/collection
CACHE_DURATION_DAYS=30
```

The configuration is validated at startup. See `src/config.py` for details.
