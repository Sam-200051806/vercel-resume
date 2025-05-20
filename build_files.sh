#!/bin/bash

# Use Python from Vercel's environment
echo "Installing dependencies..."
python3 -m pip install --upgrade pip

# Install Django first, separately
echo "Installing Django..."
python3 -m pip install Django==4.2.10 --no-cache-dir

# Then install other dependencies
echo "Installing other dependencies..."
python3 -m pip install -r requirements.txt --no-cache-dir

# Set environment variables for the build process
export VERCEL_BUILD=1
# Note: Database credentials should be set in Vercel environment variables
# and not hardcoded here for security reasons

# Create staticfiles directory if it doesn't exist
echo "Creating staticfiles directory..."
mkdir -p staticfiles

# Create a dummy file in staticfiles to ensure it's not empty
echo "Creating dummy file in staticfiles..."
echo "This file ensures the staticfiles directory is not empty." > staticfiles/.keep

# Skip collectstatic during build as it requires database access
echo "Skipping collectstatic during build..."

# Make sure staticfiles directory exists and has content
echo "Verifying staticfiles directory..."
ls -la staticfiles

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
