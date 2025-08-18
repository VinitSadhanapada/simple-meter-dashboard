from django.urls import path
from .views import meter_api

urlpatterns = [
    path('meters/', meter_api, name='meter_api'),
]
