#!/usr/bin/env bash

# Exit on error
set -o errexit

echo "Starting Gunicorn..."
# Execute using default python (system-level install)
# This works because we set virtualenvs.create false in build.sh
exec python -m gunicorn config.wsgi:application --bind 0.0.0.0:$PORT



