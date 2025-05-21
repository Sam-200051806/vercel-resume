"""
WSGI config for resume_analyzer_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
import sys

# Add the project directory to the Python path
path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if path not in sys.path:
    sys.path.append(path)

from django.core.wsgi import get_wsgi_application

# Set the DJANGO_SETTINGS_MODULE environment variable
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_analyzer_project.settings')

# Set RENDER environment variable for Render-specific settings
if 'RENDER' in os.environ:
    os.environ['RENDER'] = 'True'
    print("Running on Render")

# Get the WSGI application
application = get_wsgi_application()

# For Vercel deployment
app = application
