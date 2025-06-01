"""
URL configuration for BioLife project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from django.contrib import admin
from BioLife import app_views as views
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import handler500
from .views import add_click

handler500 = 'BioLife.app_views.custom_error_view'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('identifications/', views.identifications, name='identifications'),
    path('bioblitz/', views.bioblitz, name='bioblitz'),
    path('bioblitz_results/', views.bioblitz_results, name='bioblitz_results'),
    path('add-click/', add_click, name='add_click'),
]

# Add static file serving during development
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Add media file serving during development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
