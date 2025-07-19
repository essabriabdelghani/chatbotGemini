from django.urls import path
from . import views
from .views import launch_chatbot
urlpatterns = [
    path('inscription/', views.inscription, name='inscription'),
    path('connexion/', views.connexion, name='connexion'),
    path('chatbot/', launch_chatbot, name='launch_chatbot'),
]