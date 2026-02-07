#!/usr/bin/env bash
# Exit on error
set -o errexit

# Ensure we are in the script's directory (Movie-Recommendation-BE)
cd "$(dirname "$0")"

export DEBUG="True"
export ALLOWED_HOSTS="*"

echo "Installing Poetry..."
pip install poetry

echo "Configuring Poetry..."
poetry config virtualenvs.in-project true

echo "Installing dependencies with Poetry..."
poetry install --no-root



echo "Collecting static files..."
poetry run python manage.py collectstatic --no-input

echo "Running migrations..."
poetry run python manage.py migrate

echo "Build complete!"
