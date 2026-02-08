#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "Starting build process..."


cd Movie-Recommendation-BE || echo "Already in Movie-Recommendation-BE or directory not found"

echo "Installing Poetry..."
pip install poetry

echo "Configuring Poetry..."

poetry config virtualenvs.create false

echo "Installing dependencies..."
poetry install --no-dev --no-root

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Running migrations..."
python manage.py migrate

echo "Seeding/Updating Movie Database..."

python manage.py fetch_movies || echo "Warning: Movie seeding failed, continuing build."

echo "Build complete!"