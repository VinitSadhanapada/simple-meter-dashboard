
from django.urls import path
from . import views

app_name = 'meter_readings'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/set_failure_mode/', views.api_set_failure_mode, name='api_set_failure_mode'),
    path('latest/', views.latest_readings, name='latest_readings'),
]
