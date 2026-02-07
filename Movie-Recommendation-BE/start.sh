#!/usr/bin/env bash

# Exit on error
set -o errexit

echo "Starting Gunicorn with Poetry..."
# Let Poetry resolve the environment
# Execute gunicorn as a module using the system python
exec python -m gunicorn config.wsgi:application --bind 0.0.0.0:$PORT




