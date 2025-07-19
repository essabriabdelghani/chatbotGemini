from django.contrib import admin
from django.urls import path, include  # Ajoute 'include' ici

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('myapp.urls')),  # Inclut les URLs de myapp
]