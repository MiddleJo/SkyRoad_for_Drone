from django.urls import path
from . import views

urlpatterns = [
    path('', views.control_drone),
    path('add_drone/', views.path_planning)
]