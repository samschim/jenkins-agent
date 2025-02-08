#!/bin/bash

set -e

# Start Prometheus
/bin/prometheus \
    --config.file=/etc/prometheus/prometheus.yml \
    --storage.tsdb.path=/prometheus \
    --web.console.libraries=/usr/share/prometheus/console_libraries \
    --web.console.templates=/usr/share/prometheus/consoles \
    --web.enable-lifecycle \
    --web.enable-admin-api &

# Start Grafana
/usr/share/grafana/bin/grafana-server \
    --config=/etc/grafana/grafana.ini \
    --homepath=/usr/share/grafana \
    --packaging=docker \
    cfg:default.paths.logs=/var/log/grafana \
    cfg:default.paths.data=/var/lib/grafana \
    cfg:default.paths.plugins=/var/lib/grafana/plugins \
    cfg:default.paths.provisioning=/etc/grafana/provisioning &

# Start metrics exporter
exec python3 /app/exporter.py