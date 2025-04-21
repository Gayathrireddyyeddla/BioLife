from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return render(request, 'home.html')

def identifications(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        return render(request, 'identifications.html', {'username': username})
    return render(request, 'identifications_form.html')

def bioblitz(request):
    return HttpResponse('Hello')
