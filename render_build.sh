#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "Starting build process..."

# FIX 1: Robust directory navigation (CodeRabbit Fix)
# This ensures that if the folder is missing, the script stops IMMEDIATELY.
cd Movie-Recommendation-BE || { 
    echo "ERROR: Movie-Recommendation-BE directory not found. Current location: $(pwd)"; 
    exit 1; 
}

echo "Installing Poetry..."
pip install poetry

echo "Configuring Poetry..."
poetry config virtualenvs.create false

echo "Installing dependencies..."
# FIX 2: Supported group exclusion syntax (CodeRabbit Fix)
# Using --without dev instead of the deprecated --no-dev
poetry install --without dev --no-root

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Running migrations..."
python manage.py migrate

echo "Seeding/Updating Movie Database..."
# This will use your live TMDB_API_KEY and Postgres DB on Render
python manage.py fetch_movies || echo "Warning: Movie seeding failed, continuing build."

echo "Build complete!"