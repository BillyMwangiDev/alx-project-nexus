#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -o errexit

# 1. Directory Navigation
# Checks if we are in the root or need to move into the subdirectory
if [ -f "manage.py" ]; then
    echo "Current directory contains manage.py. Proceeding..."
elif [ -d "Movie-Recommendation-BE" ]; then
    cd Movie-Recommendation-BE || exit 1
    echo "Moved into Movie-Recommendation-BE directory."
else
    echo "ERROR: Could not find manage.py or Movie-Recommendation-BE folder."
    exit 1
fi

# 2. Environment Defaults
export DEBUG=${DEBUG:-False}
export ALLOWED_HOSTS=${ALLOWED_HOSTS:-"localhost"}
export SECRET_KEY=${SECRET_KEY:?"SECRET_KEY must be set in Render Environment Variables"}

# 3. Database Connection & Migration Logic
echo "Waiting for database to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0

# Loop until migrations succeed or max retries reached
until poetry run python manage.py migrate --no-input; do
    EXIT_CODE=$?
    RETRY_COUNT=$((RETRY_COUNT+1))
    
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo "Database connection failed after $MAX_RETRIES attempts. Exiting."
        exit 1
    fi
    
    echo "Database not ready (Exit Code: $EXIT_CODE). Retrying in 5s... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 5
done

echo "Migrations completed successfully!"

# 4. Movie Data Seeding
# We trigger the fetch_movies command here so it shows up in your live logs
echo "Seeding/Updating Movie Database..."
poetry run python manage.py fetch_movies || echo "Warning: Movie seeding failed, but starting server anyway."

# 5. Launch Application
echo "Starting Gunicorn with Poetry..."
# Using 'exec' makes Gunicorn the primary process for better signal handling
exec poetry run gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}"