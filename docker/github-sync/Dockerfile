FROM ubuntu:22.04

# Install required packages
RUN apt-get update && apt-get install -y \
    git \
    curl \
    jq \
    cron \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip3 install --no-cache-dir \
    PyGithub \
    python-dotenv \
    requests \
    aiohttp

# Create app directory
WORKDIR /app

# Copy scripts
COPY scripts/setup.sh /app/setup.sh
COPY docker/github-sync/sync.py /app/sync.py
COPY docker/github-sync/entrypoint.sh /app/entrypoint.sh

# Make scripts executable
RUN chmod +x /app/setup.sh /app/entrypoint.sh

# Create directories
RUN mkdir -p /var/jenkins_home/workspace \
    /var/jenkins_home/backups \
    /var/jenkins_home/logs

# Set environment variables
ENV JENKINS_HOME=/var/jenkins_home \
    SYNC_INTERVAL=300 \
    GITHUB_USERNAME="" \
    GITHUB_TOKEN="" \
    WORKSPACE_DIR=/var/jenkins_home/workspace \
    BACKUP_DIR=/var/jenkins_home/backups \
    LOG_DIR=/var/jenkins_home/logs

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]