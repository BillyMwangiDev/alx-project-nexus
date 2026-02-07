#!/usr/bin/env bash

# Ensure we are in the correct directory
if [ -d "Movie-Recommendation-BE" ]; then
    cd Movie-Recommendation-BE
fi

echo "Running migrations..."
poetry run python manage.py migrate

echo "Starting Gunicorn with Poetry..."
# Execute gunicorn using poetry run, which will use the local .venv
exec poetry run gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
