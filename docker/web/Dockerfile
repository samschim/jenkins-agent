# Build stage for React frontend
FROM node:16-alpine as frontend-builder

WORKDIR /app/frontend

# Copy frontend files
COPY langchain_jenkins/web/frontend/package*.json ./
RUN npm ci

COPY langchain_jenkins/web/frontend/ ./
RUN npm run build

# Build stage for Python backend
FROM python:3.8-slim as backend-builder

ARG POETRY_VERSION=1.4.2

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=$POETRY_VERSION \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="$POETRY_HOME/bin:$PATH"

WORKDIR /app

# Copy project files
COPY pyproject.toml poetry.lock ./
COPY README.md ./
COPY langchain_jenkins ./langchain_jenkins

# Install dependencies
RUN poetry install --no-dev --no-root

# Runtime stage
FROM python:3.8-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        nginx \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 jenkins \
    && mkdir -p /app /app/logs /app/data \
    && chown -R jenkins:jenkins /app

# Configure nginx
COPY docker/web/nginx.conf /etc/nginx/nginx.conf
RUN mkdir -p /var/log/nginx \
    && chown -R jenkins:jenkins /var/log/nginx \
    && chown -R jenkins:jenkins /var/lib/nginx

WORKDIR /app

# Copy built frontend
COPY --from=frontend-builder /app/frontend/build /app/static
# Copy Python packages
COPY --from=backend-builder /usr/local/lib/python3.8/site-packages /usr/local/lib/python3.8/site-packages
COPY --from=backend-builder /app/langchain_jenkins ./langchain_jenkins

# Switch to non-root user
USER jenkins

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose ports
EXPOSE 8000 80

# Start script
COPY docker/web/start.sh /app/start.sh
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]