#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "Starting build process..."

# 1. Directory Navigation
# Move into the backend directory where manage.py is located
cd Movie-Recommendation-BE || { 
    echo "ERROR: Movie-Recommendation-BE directory not found."; 
    exit 1; 
}

# 2. Dependency Management
# Pinning Poetry version to ensure reproducible builds
echo "Installing Poetry..."
pip install "poetry>=1.7,<2.0"

echo "Configuring Poetry..."
poetry config virtualenvs.create false

echo "Installing dependencies..."
# Using --without dev to skip testing/linting tools in production
poetry install --without dev --no-root

# 3. Environment Fallback
# Django requires a SECRET_KEY to initialize. This temporary key allows 
# collectstatic and migrate to run even if the real env var isn't injected yet.
export SECRET_KEY=${SECRET_KEY:-"build-time-only-placeholder-value"}

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Running migrations..."
python manage.py migrate --no-input

echo "Build complete!"