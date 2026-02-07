#!/usr/bin/env bash

# Exit on error
set -o errexit

echo "Starting Gunicorn..."
# Use python -m to run gunicorn from the virtualenv
# Gunicorn stays in the foreground to keep the Render service running
exec python -m gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
