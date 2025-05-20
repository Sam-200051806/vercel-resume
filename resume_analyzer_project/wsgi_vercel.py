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

# Set DEBUG to False in production
os.environ['DEBUG'] = 'False'

# Note: Database credentials should be set in Vercel environment variables
# and not hardcoded here for security reasons

# Import Django's WSGI handler
from django.core.wsgi import get_wsgi_application

# Get the WSGI application
application = get_wsgi_application()

# Vercel expects the variable to be named 'app'
app = application

# Simple error handling for debugging
def handler(environ, start_response):
    try:
        return app(environ, start_response)
    except Exception as e:
        status = '500 Internal Server Error'
        response_headers = [('Content-type', 'text/plain')]
        start_response(status, response_headers)
        return [f"Error: {str(e)}".encode()]

# Use the handler for debugging, but use the regular app in production
if os.environ.get('DEBUG') == 'True':
    app = handler
