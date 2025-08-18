from django.shortcuts import render
from django.http import JsonResponse

def dashboard(request):
    """Simple dashboard view"""
    return render(request, 'meter_readings/dashboard.html', {
        'page_title': 'Meter Readings Dashboard'
    })

def api_meter_readings(request):
    """Simple API endpoint for meter readings"""
    return JsonResponse({
        'status': 'success',
        'message': 'Meter readings API endpoint'
    })
