"""
WSGI config for Vercel deployment.
This is a simplified version that doesn't require database access.
"""

import os
import sys

# Add the project directory to the Python path
path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if path not in sys.path:
    sys.path.append(path)

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_analyzer_project.settings')
os.environ['VERCEL_REGION'] = 'vercel'  # Mark as running on Vercel

# Set database environment variables if not already set
if 'DB_NAME' not in os.environ:
    os.environ['DB_NAME'] = 'postgres'
if 'DB_USER' not in os.environ:
    os.environ['DB_USER'] = 'postgres'
if 'DB_PASSWORD' not in os.environ:
    os.environ['DB_PASSWORD'] = 'Sambhav@1806'
if 'DB_HOST' not in os.environ:
    os.environ['DB_HOST'] = 'db.wpsxiwyvmiwtyymaertc.supabase.co'
if 'DB_PORT' not in os.environ:
    os.environ['DB_PORT'] = '5432'

# Import Django's WSGI handler
from django.core.wsgi import get_wsgi_application

# Get the WSGI application
application = get_wsgi_application()

# Vercel expects the variable to be named 'app'
app = application
