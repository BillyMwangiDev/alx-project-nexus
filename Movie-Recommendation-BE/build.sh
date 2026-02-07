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
# Enable virtualenv creation to allow "poetry run" to work correctly
poetry config virtualenvs.create true
poetry config virtualenvs.in-project true

echo "Installing dependencies..."
poetry install --no-root







echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Running migrations..."
python manage.py migrate

echo "Build complete!"
