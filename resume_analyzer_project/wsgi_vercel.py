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

# Note: Database credentials should be set in Vercel environment variables
# and not hardcoded here for security reasons

# Import Django's WSGI handler
from django.core.wsgi import get_wsgi_application

# Get the WSGI application
application = get_wsgi_application()

# Vercel expects the variable to be named 'app'
app = application
