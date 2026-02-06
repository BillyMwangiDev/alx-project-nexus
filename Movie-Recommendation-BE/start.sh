#!/usr/bin/env bash

# Exit on error
set -o errexit

echo "Starting Celery Worker..."
# Run Celery in the background. Keep concurrency=1 for Free Tier to avoid OOM.
celery -A apps.movies_api worker --loglevel=info --concurrency=1 &

echo "Starting Gunicorn..."
# Gunicorn stays in the foreground to keep the Render service running
exec gunicorn apps.movies_api.wsgi:application --bind 0.0.0.0:$PORT
