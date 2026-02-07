#!/usr/bin/env bash

# Exit on error
set -o errexit

# Ensure we are in the script's directory (Movie-Recommendation-BE)
cd "$(dirname "$0")"

# Check if .venv exists
if [ ! -d ".venv" ]; then
    echo "ERROR: .venv directory not found in $(pwd)"

    exit 1
fi

echo "Starting Gunicorn via .venv python..."
# Execute directly using the virtualenv python
# This avoids 'poetry run' overhead and path resolution issues
exec .venv/bin/python -m gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
