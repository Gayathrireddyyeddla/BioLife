from django.shortcuts import render, redirect
import logging
from django.http import HttpResponse
from .services import process_username
from .biobiltz_service import process_projectslug

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
    if request.method == 'POST':
        projectslug = request.POST.get('projectslug')
        logger.debug(f"POST request received with projectslug: {projectslug}")
        result = process_projectslug(projectslug)
        return render(request, 'bioblitz_results.html', {
            'projectslug': projectslug,
            'total_observations_place': result['total_observations_place'],
            'Place_Total_Observers': result['Place_Total_Observers'],
            'Place_Total_Species': result['Place_Total_Species'],
            'User_Increase_Percent': result['User_Increase_Percent'],
            'Observation_Increase_Percent': result['Observation_Increase_Percent'],
            'Species_Increase_Percent': result['Species_Increase_Percent'],
            'New_Users': result['New_Users'],
            'New_Users_Percentage': result['New_Users_Percentage'],
            'graph_paths': result['graph_paths'],
        })
    logger.debug("GET request received, rendering bioblitz.html")
    return render(request, 'bioblitz.html')

def bioblitz_results(request):
    result = request.session.get('bioblitz_result', {})
    logger.debug(f"Bioblitz Results: {result}")
    return render(request, 'bioblitz_results.html', {'result': result})