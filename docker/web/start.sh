#!/bin/bash
set -e

# Start nginx
nginx -g "daemon off;" &

# Start FastAPI application
python -m langchain_jenkins.web.app