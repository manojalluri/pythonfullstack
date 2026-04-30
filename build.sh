#!/bin/bash

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run migrations (optional, depends on if user has DB set up)
echo "Running migrations..."
python3 lms_project/manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python3 lms_project/manage.py collectstatic --noinput --clear

echo "Build completed!"
