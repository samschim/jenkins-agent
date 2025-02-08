FROM prom/prometheus:v2.45.0 as prometheus
FROM grafana/grafana:10.1.0 as grafana
FROM python:3.8-slim

# Install required packages
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Prometheus and Grafana binaries
COPY --from=prometheus /bin/prometheus /bin/prometheus
COPY --from=prometheus /etc/prometheus/prometheus.yml /etc/prometheus/prometheus.yml
COPY --from=grafana /usr/share/grafana /usr/share/grafana

# Install Python packages
RUN pip install --no-cache-dir \
    prometheus_client \
    psutil \
    aiohttp \
    fastapi \
    uvicorn

# Create app directory
WORKDIR /app

# Copy configuration and scripts
COPY docker/monitoring/config/prometheus.yml /etc/prometheus/prometheus.yml
COPY docker/monitoring/config/grafana/dashboards /etc/grafana/dashboards
COPY docker/monitoring/config/grafana/datasources /etc/grafana/datasources
COPY docker/monitoring/exporter.py /app/exporter.py
COPY docker/monitoring/entrypoint.sh /app/entrypoint.sh

# Make scripts executable
RUN chmod +x /app/entrypoint.sh

# Expose ports
EXPOSE 3000 9090 9100

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]