#!/usr/bin/env bash

# Exit on error
set -o errexit

echo "Starting Gunicorn..."
# Use absolute path to gunicorn in the virtualenv
exec /opt/render/project/src/.venv/bin/gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
