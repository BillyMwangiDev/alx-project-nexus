#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "Deploying from root directory..."
cd Movie-Recommendation-BE

echo "Configuring Poetry..."
poetry config virtualenvs.create false

echo "Installing production dependencies..."
# --without dev tells poetry to skip pytest, faker, etc.
poetry install --without dev --no-root

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Running migrations..."
python manage.py migrate

echo "Seeding/Updating Movie Database..."
# Run the fetch command
python manage.py fetch_movies || echo "Warning: Movie seeding failed."

echo "Build complete!"