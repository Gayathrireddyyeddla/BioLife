from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Click

def home(request):
    return render(request, 'home.html')

def identifications(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        return render(request, 'identifications.html', {'username': username})
    return render(request, 'identifications_form.html')

def bioblitz(request):
    return HttpResponse('Hello')

@csrf_exempt
def add_click(request):
    if request.method == 'POST':
        print("!!!!!!!!")
        try:
            print(request.body)  # Log the request body for debugging
            data = json.loads(request.body)
            button_name = data.get('button_name', '')
            Click.objects.create(button_name=button_name)
            return JsonResponse({'status': 'success'}, status=200)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
