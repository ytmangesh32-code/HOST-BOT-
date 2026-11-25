FROM python:3.11-slim

# Prevents Python from writing .pyc files & enables unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# Install system deps + Node.js (needed for .js script hosting) + build tools (for pip installs at runtime)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    ca-certificates \
    build-essential \
    gcc \
    g++ \
    make \
    git \
    procps \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs npm \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy bot source
COPY . .

# Create required runtime directories
RUN mkdir -p /app/upload_bots /app/inf

# Expose Flask keep-alive port
EXPOSE 8080

# Healthcheck (optional, verifies Flask is alive)
HEALTHCHECK --interval=60s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Run the bot
CMD ["python", "-u", "HOSTINGbot.py"]