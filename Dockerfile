# Build stage
FROM python:3.8-slim as builder

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy project files
COPY pyproject.toml poetry.lock ./
COPY README.md ./
COPY langchain_jenkins ./langchain_jenkins

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Runtime stage
FROM python:3.8-slim

WORKDIR /app

# Copy from builder
COPY --from=builder /usr/local/lib/python3.8/site-packages /usr/local/lib/python3.8/site-packages
COPY --from=builder /app/langchain_jenkins ./langchain_jenkins

# Create non-root user
RUN useradd -m -u 1000 jenkins \
    && chown -R jenkins:jenkins /app

USER jenkins

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose ports
EXPOSE 8000

# Run application
CMD ["python", "-m", "langchain_jenkins.web.app"]