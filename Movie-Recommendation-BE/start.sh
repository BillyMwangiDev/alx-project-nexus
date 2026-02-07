#!/usr/bin/env bash

# Exit on error
set -o errexit

echo "Starting Gunicorn with Poetry..."
# Let Poetry resolve the environment
# Execute gunicorn directly from the virtual environment
exec ./.venv/bin/gunicorn config.wsgi:application --bind 0.0.0.0:$PORT




