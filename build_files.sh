#!/bin/bash

# Use Python from Vercel's environment
echo "Installing dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt --no-cache-dir

# Set environment variables for the build process
export VERCEL_BUILD=1
# Note: Database credentials should be set in Vercel environment variables
# and not hardcoded here for security reasons

# Collect static files
echo "Collecting static files..."
python3 manage.py collectstatic_no_db --noinput

# Clean up unnecessary files to reduce size
echo "Cleaning up..."
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type d -name "*.dist-info" -exec rm -rf {} +
find . -type d -name "*.egg-info" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type f -name "*.pyd" -delete

# No need to run migrations during build
# Migrations should be run as part of the runtime
