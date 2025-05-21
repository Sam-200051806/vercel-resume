#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Starting build process..."

# Clean pip cache
echo "Cleaning pip cache..."
pip cache purge

# Upgrade pip with specific trusted host
echo "Upgrading pip..."
pip install --upgrade pip --trusted-host pypi.org --trusted-host files.pythonhosted.org

# Install dependencies with specific options to avoid compression issues
echo "Installing dependencies..."
if [ -f "requirements-render.txt" ] && [ "$RENDER" = "true" ]; then
    echo "Using Render-specific requirements file..."
    pip install -r requirements-render.txt --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org
else
    echo "Using standard requirements file..."
    pip install -r requirements.txt --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org
fi

# Verify installations
echo "Verifying installations..."
pip list

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Apply migrations
echo "Applying migrations..."
python manage.py migrate

echo "Build process completed successfully!"
