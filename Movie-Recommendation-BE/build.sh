#!/usr/bin/env bash
# Exit on error
set -o errexit

# Ensure we are in the script's directory (Movie-Recommendation-BE)
cd "$(dirname "$0")"

export DEBUG="True"
export ALLOWED_HOSTS="*"

echo "Creating virtual environment..."
# Explicitly create the virtualenv to guarantee its location
python -m venv .venv

echo "Activating virtual environment..."
source .venv/bin/activate
pip install --upgrade pip

echo "Installing Poetry into virtual environment..."
pip install poetry

echo "Configuring Poetry..."
# Tell Poetry to use the currently active virtualenv
poetry config virtualenvs.create false --local

echo "Installing dependencies with Poetry..."
poetry install --no-root




echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Running migrations..."
python manage.py migrate

echo "Build complete!"
