#!/bin/bash

# Use Python from Vercel's environment
echo "Installing dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pip install psycopg2-binary

# Set environment variables for the build process
export VERCEL_BUILD=1
# Note: Database credentials should be set in Vercel environment variables
# and not hardcoded here for security reasons

# Collect static files
echo "Collecting static files..."
python3 manage.py collectstatic_no_db --noinput

# No need to run migrations during build
# Migrations should be run as part of the runtime
