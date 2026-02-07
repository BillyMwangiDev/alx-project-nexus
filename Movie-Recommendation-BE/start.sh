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

echo "Waiting for database to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0

until poetry run python manage.py migrate || [ $RETRY_COUNT -eq $MAX_RETRIES ]; do
    echo "Database is not ready yet. Retrying in 5 seconds... ($RETRY_COUNT/$MAX_RETRIES)"
    RETRY_COUNT=$((RETRY_COUNT+1))
    sleep 5
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "Database connection failed after maximum retries. Exiting."
    exit 1
fi

echo "Migrations completed successfully!"

echo "Starting Gunicorn with Poetry..."
# Execute gunicorn using poetry run, which will use the local .venv
exec poetry run gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
