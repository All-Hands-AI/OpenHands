#!/bin/bash
set -e

# Clean the prometheus multiprocess directory before starting
if [ -n "$PROMETHEUS_MULTIPROC_DIR" ]; then
    echo "Cleaning Prometheus multiprocess directory: $PROMETHEUS_MULTIPROC_DIR"
    rm -rf "$PROMETHEUS_MULTIPROC_DIR"/*
    mkdir -p "$PROMETHEUS_MULTIPROC_DIR"
fi

# Start the application with all provided arguments
exec "$@"
