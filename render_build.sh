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


# Export build-time environment variables to ensure collectstatic works
export DEBUG="True"
export ALLOWED_HOSTS="*"
export SECRET_KEY="build-time-secret-key"

echo "Collecting static files..."
poetry run python manage.py collectstatic --no-input

echo "Build complete!"
