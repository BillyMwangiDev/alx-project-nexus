#!/usr/bin/env bash

# Exit on error
set -o errexit

# Ensure we are in the script's directory (Movie-Recommendation-BE)
cd "$(dirname "$0")"

# Check if .venv exists (created by build.sh)
if [ ! -d ".venv" ]; then
    echo "ERROR: .venv directory not found in $(pwd)"
    echo "Files in current directory:"
    ls -la
    exit 1
fi

echo "Starting Gunicorn via .venv..."
exec .venv/bin/gunicorn config.wsgi:application --bind 0.0.0.0:$PORT


