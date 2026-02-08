#!/usr/bin/env bash

# Exit on error and catch errors in piped commands
set -o errexit
set -o pipefail

# 1. Directory Verification (Fixed with Else Branch)
# This ensures we stop immediately if we aren't in the right place
if [ -f "manage.py" ]; then
    echo "Starting from project root..."
elif [ -d "Movie-Recommendation-BE" ]; then
    cd Movie-Recommendation-BE || exit 1
    echo "Moved into Movie-Recommendation-BE directory."
else
    echo "ERROR: Could not find manage.py or Movie-Recommendation-BE directory." >&2
    exit 1
fi

# 2. Production Environment Checks
export DEBUG=${DEBUG:-False}
export ALLOWED_HOSTS=${ALLOWED_HOSTS:-"localhost"}
export SECRET_KEY=${SECRET_KEY:?"SECRET_KEY must be set in Render Environment Variables"}

# 3. Database Connection Wait & Final Migrations
echo "Waiting for database to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0

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
echo "Seeding/Updating Movie Database..."
poetry run python manage.py fetch_movies || echo "Warning: Movie seeding failed, starting app anyway."

# 5. Start Gunicorn
echo "Starting Gunicorn..."
exec poetry run gunicorn config.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${GUNICORN_WORKERS:-3}" \
    --timeout 120