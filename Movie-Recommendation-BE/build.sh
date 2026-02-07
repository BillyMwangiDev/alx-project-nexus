#!/usr/bin/env bash
set -o errexit

# Export environment variables for build-time Django commands
# These override any missing env vars from render.yaml during build
export DEBUG="True"
export ALLOWED_HOSTS="*"

echo "Installing dependencies..."
# Explicitly use the virtualenv python to install dependencies
# This ensures packages are installed where we expect them
/opt/render/project/src/.venv/bin/python -m pip install --upgrade pip
/opt/render/project/src/.venv/bin/python -m pip install -r requirements.txt

# Verify installation
echo "Checking where gunicorn is installed..."
find /opt/render/project/src/.venv -name gunicorn

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Running migrations..."
python manage.py migrate

echo "Build complete!"
