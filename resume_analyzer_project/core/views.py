from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def health_check(request):
    """
    A simple view that doesn't require database access.
    Used to test if the application is running correctly.
    """
    return HttpResponse("Application is running correctly!", content_type="text/plain")

def index(request):
    """
    A simple view that renders the index page.
    """
    return render(request, 'index.html')
