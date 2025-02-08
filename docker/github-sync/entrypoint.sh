#!/bin/bash

set -e

# Start cron service
service cron start

# Run initial setup
/app/setup.sh setup

# Start sync process
exec python3 /app/sync.py