from django.shortcuts import render
import logging
from django.http import HttpResponse
from .services import process_username

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def home(request):
    return render(request, 'home.html')

def identifications(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        logger.debug(f"POST request received with username: {username}")
        result = process_username(username)
        return render(request, 'identifications.html', {
            'username': username,
            'total_ids': result['total_ids'],
            'unique_users': result['unique_users'],
            'volunteer_hours': result['volunteer_hours'],
            'estimated_coverage_acres': result['estimated_coverage_acres'],
            'id_plot_path': result['id_plot_url'],
            'user_plot_path': result['user_plot_url'],
        })
    logger.debug("GET request received, rendering identifications_form.html")
    return render(request, 'identifications_form.html')

def bioblitz(request):
    return render(request, 'bioblitz.html')