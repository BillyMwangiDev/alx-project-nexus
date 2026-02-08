#!/usr/bin/env bash

# Exit on error and catch errors in piped commands
set -o errexit
set -o pipefail

# 1. Directory Verification
# Ensures we are in the folder containing manage.py
if [ -f "manage.py" ]; then
    echo "Starting from project root..."
elif [ -d "Movie-Recommendation-BE" ]; then
    cd Movie-Recommendation-BE || exit 1
    echo "Moved into Movie-Recommendation-BE directory."
fi

# 2. Production Environment Checks
# Ensure critical variables exist before starting
export DEBUG=${DEBUG:-False}
export ALLOWED_HOSTS=${ALLOWED_HOSTS:-"localhost"}
export SECRET_KEY=${SECRET_KEY:?"SECRET_KEY must be set in Render Environment Variables"}

# 3. Database Connection Wait & Final Migrations
echo "Waiting for database to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0

# Loop until migrations succeed (database is reachable)
until poetry run python manage.py migrate --no-input; do
    RETRY_COUNT=$((RETRY_COUNT+1))
    
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo "Database connection failed after maximum retries. Exiting."
        exit 1
    fi
    
    echo "Database not ready. Retrying in 5 seconds... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 5
done

echo "Migrations completed successfully!"

# 4. Data Seeding
# Fetches initial movie data from TMDB. 
# We run this here so you can see the progress in your live logs.
echo "Seeding/Updating Movie Database..."
poetry run python manage.py fetch_movies || echo "Warning: Movie seeding failed, starting app anyway."

# 5. Start Gunicorn
# Uses 'exec' to handle process signals correctly.
# Defaulting to 3 workers for better concurrency on Render.
echo "Starting Gunicorn..."
exec poetry run gunicorn config.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${GUNICORN_WORKERS:-3}" \
    --timeout 120