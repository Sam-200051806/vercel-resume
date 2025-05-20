#!/bin/bash

# Use Python from Vercel's environment
echo "Installing dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install Django==4.2.10 --no-cache-dir
python3 -m pip install -r requirements.txt --no-cache-dir

# Set environment variables for the build process
export VERCEL_BUILD=1
# Note: Database credentials should be set in Vercel environment variables
# and not hardcoded here for security reasons

# Create staticfiles directory if it doesn't exist
echo "Creating staticfiles directory..."
mkdir -p staticfiles

# Collect static files
echo "Collecting static files..."
python3 manage.py collectstatic_no_db --noinput

# Make sure staticfiles directory exists and has content
echo "Verifying staticfiles directory..."
ls -la staticfiles
if [ ! -d "staticfiles" ]; then
    echo "Creating empty staticfiles directory..."
    mkdir -p staticfiles
    touch staticfiles/.keep
fi

# Clean up unnecessary files to reduce size
echo "Cleaning up..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
find . -type f -name "*.pyd" -delete 2>/dev/null || true

# No need to run migrations during build
# Migrations should be run as part of the runtime
