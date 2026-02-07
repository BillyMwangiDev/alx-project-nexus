#!/usr/bin/env bash

# Exit on error
set -o errexit

echo "Starting Gunicorn with Poetry..."
# Let Poetry resolve the environment
exec poetry run gunicorn config.wsgi:application --bind 0.0.0.0:$PORT




