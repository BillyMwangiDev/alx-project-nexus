#!/usr/bin/env bash

# Ensure we are in the correct directory
if [ -d "Movie-Recommendation-BE" ]; then
    cd Movie-Recommendation-BE
fi


# Export runtime environment variables as a fallback to ensure Django starts
# These will be overridden by Render Dashboard variables if they exist
export DEBUG=${DEBUG:-True}
export ALLOWED_HOSTS=${ALLOWED_HOSTS:-"*"}
export SECRET_KEY=${SECRET_KEY:-"runtime-secret-key-for-startup"}

echo "Running migrations..."
poetry run python manage.py migrate

echo "Starting Gunicorn with Poetry..."
# Execute gunicorn using poetry run, which will use the local .venv
exec poetry run gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
