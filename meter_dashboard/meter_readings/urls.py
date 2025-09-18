from django.urls import path
from . import views

urlpatterns = [
	path('latest/<str:table_name>/', views.latest_readings, name='latest_readings'),
]

