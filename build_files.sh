#!/bin/bash

# Use Python from Vercel's environment
echo "Installing dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# Collect static files
echo "Collecting static files..."
python3 manage.py collectstatic --noinput

# No need to run migrations during build
# Migrations should be run as part of the runtime
