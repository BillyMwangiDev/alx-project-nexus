#!/usr/bin/env bash

# Exit on error
set -o errexit

# Ensure we are in the script's directory (Movie-Recommendation-BE)
cd "$(dirname "$0")"

# poetry run handles the virtualenv path automatically
exec poetry run gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
