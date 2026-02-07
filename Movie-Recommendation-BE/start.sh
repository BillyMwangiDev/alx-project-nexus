#!/usr/bin/env bash

# Exit on error
set -o errexit

echo "Starting Gunicorn..."
# Activate the virtualenv where packages are installed
source /opt/render/project/src/.venv/bin/activate
# Gunicorn stays in the foreground to keep the Render service running
exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
