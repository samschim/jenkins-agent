FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY requirements.txt .
COPY langchain_jenkins/webhooks ./webhooks
COPY langchain_jenkins/config ./config
COPY langchain_jenkins/utils ./utils

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user
RUN useradd -m -u 1000 jenkins
USER jenkins

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD ps aux | grep "[p]ython -m webhooks.notifier" || exit 1

# Command to run
CMD ["python", "-m", "webhooks.notifier"]