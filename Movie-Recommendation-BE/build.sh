#!/usr/bin/env bash
set -o errexit

# Export environment variables for build-time Django commands
# These are needed because render.yaml env vars aren't available yet during build
export DEBUG="${DEBUG:-True}"
export ALLOWED_HOSTS="${ALLOWED_HOSTS:-*}"

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Running migrations..."
python manage.py migrate

echo "Build complete!"
