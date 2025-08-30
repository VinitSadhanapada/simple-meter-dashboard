from django.urls import path
from . import views

urlpatterns = [
    path('single_meter/', views.single_meter_view, name='single_meter'),
]
