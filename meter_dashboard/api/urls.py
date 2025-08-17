from django.urls import path
from .views import meter_api

urlpatterns = [
    path('meter/', meter_api, name='meter_api'),
]
