#!/bin/bash

# Exit on error
set -e

# Default values
COVERAGE=false
INTEGRATION=false
UNIT=true

# Parse arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -i|--integration)
            INTEGRATION=true
            shift
            ;;
        -u|--unit)
            UNIT=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Start test infrastructure
echo "Starting test infrastructure..."
docker-compose -f docker-compose.test.yml up -d

# Wait for services
echo "Waiting for services..."
sleep 10

# Run tests
if [ "$COVERAGE" = true ]; then
    echo "Running tests with coverage..."
    if [ "$INTEGRATION" = true ]; then
        pytest tests/ --cov=langchain_jenkins -v
    else
        pytest tests/unit/ --cov=langchain_jenkins -v
    fi
else
    echo "Running tests..."
    if [ "$INTEGRATION" = true ]; then
        if [ "$UNIT" = true ]; then
            pytest tests/ -v
        else
            pytest tests/integration/ -v
        fi
    else
        pytest tests/unit/ -v
    fi
fi

# Stop test infrastructure
echo "Stopping test infrastructure..."
docker-compose -f docker-compose.test.yml down

# Check test results
if [ $? -eq 0 ]; then
    echo "Tests passed successfully!"
    exit 0
else
    echo "Tests failed!"
    exit 1
fi