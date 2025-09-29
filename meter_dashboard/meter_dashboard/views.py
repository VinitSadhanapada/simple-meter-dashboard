from django.shortcuts import render
from device_config.models import MeterDevice

# ...existing code...


def main_dashboard(request):
    page_title = "Meter Dashboard"
    # Fetch meters, available_modes, failure_modes as needed
    meters = MeterDevice.objects.all()  # Example, adjust as needed
    available_modes = ["Normal", "Failure"]  # Example, adjust as needed
    failure_modes = {}  # Example, adjust as needed
    context = {
        "page_title": page_title,
        "meters": meters,
        "available_modes": available_modes,
        "failure_modes": failure_modes,
    }
    return render(request, "dashboard.html", context)
# ...existing code...
