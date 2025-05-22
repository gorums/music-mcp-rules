# Use official Python image
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Set environment variables (can be overridden)
ENV MUSIC_ROOT_PATH=/music
ENV CACHE_DURATION_DAYS=30
ENV LOG_LEVEL=INFO

# Expose no ports (stdio server)

# Default command
CMD ["python", "src/music_mcp_server.py"] 