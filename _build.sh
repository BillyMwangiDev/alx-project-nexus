#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "Deploying from root directory..."

# Navigate to the backend directory
cd Movie-Recommendation-BE

echo "Installing Poetry..."
pip install poetry

echo "Configuring Poetry..."
# Force virtualenv creation in the project directory
poetry config virtualenvs.create true
poetry config virtualenvs.in-project true

echo "Installing dependencies..."
poetry install --no-root

echo "Collecting static files..."
poetry run python manage.py collectstatic --no-input

echo "Running migrations..."
poetry run python manage.py migrate

echo "Build complete!"
