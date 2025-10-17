from django.urls import path
from . import views


urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('api/meter/', views.api_meter_readings, name='api_meter_readings'),
    path('latest/', views.latest_readings, name='latest_readings'),
]
