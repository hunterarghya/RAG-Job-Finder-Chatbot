# Use a stable Linux Python image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set workdir inside the container
WORKDIR /app

# Copy requirement list first (for caching)
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your entire project
COPY . .

# Default command (can be overridden)
CMD ["python", "main.py"]
