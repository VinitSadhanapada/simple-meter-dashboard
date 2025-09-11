<<<<<<< HEAD

=======
>>>>>>> clubbed_mfm_dcms_16-aug
from django.urls import path
from . import views

app_name = 'meter_readings'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
<<<<<<< HEAD
    path('api/set_failure_mode/', views.api_set_failure_mode, name='api_set_failure_mode'),
    path('latest/', views.latest_readings, name='latest_readings'),
=======
    path('api/meter/', views.api_meter_readings, name='api_meter_readings'),
>>>>>>> clubbed_mfm_dcms_16-aug
]
