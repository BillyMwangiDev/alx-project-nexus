#!/usr/bin/env bash

# Exit on error
set -o errexit

echo "Starting Gunicorn..."
# The virtualenv is created during build in the parent directory
# Use relative path that works from Movie-Recommendation-BE directory
exec ../.venv/bin/gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
