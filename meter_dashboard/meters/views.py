from django.shortcuts import render, redirect
# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import MeterReading
from .serializers import MeterReadingSerializer
from django.utils import timezone
from datetime import timedelta


import matplotlib.pyplot as plt
import io
import base64

from .models import DeviceConfig, ConfigParameter
import json

from .models import Device
from .utils import push_config_to_pi


@api_view(['POST'])
def meter_data(request):
    serializer = MeterReadingSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def live_dashboard(request):
    readings = MeterReading.objects.all()
    location = request.GET.get('location')
    meter = request.GET.get('meter')
    start_time = request.GET.get('start_time')
    end_time = request.GET.get('end_time')

    if location:
        readings = readings.filter(location=location)
    if meter:
        readings = readings.filter(meter_name=meter)
    if start_time:
        readings = readings.filter(time__gte=start_time)
    if end_time:
        readings = readings.filter(time__lte=end_time)

    # If a time range is set, return all points in that range (up to 1000 for safety)
    if start_time or end_time:
        readings = readings.order_by('time')[:1000]
    else:
        readings = readings.order_by('-time')[:50]
    serializer = MeterReadingSerializer(readings, many=True)
    return Response(serializer.data)


def dashboard_charts(request):
    locations = MeterReading.objects.values_list(
        'location', flat=True).distinct()
    selected_location = request.GET.get('location')
    meters = MeterReading.objects.filter(location=selected_location).values_list(
        'meter_name', flat=True).distinct() if selected_location else []
    selected_meter = request.GET.get('meter')

    # Get start/end time from GET params
    start_time = request.GET.get('start_time')
    end_time = request.GET.get('end_time')

    readings = MeterReading.objects.all()
    if selected_location:
        readings = readings.filter(location=selected_location)
    if selected_meter:
        readings = readings.filter(meter_name=selected_meter)
    if start_time:
        readings = readings.filter(time__gte=start_time)
    if end_time:
        readings = readings.filter(time__lte=end_time)
    readings = readings.order_by('time')

    times = [r.time.strftime('%Y-%m-%d %H:%M:%S') for r in readings]
    vln_average = [
        r.vln_average if r.vln_average is not None else 0 for r in readings]

    # Generate PNG chart with matplotlib for VLN Average
    chart_img = None
    if times and vln_average:
        plt.figure(figsize=(10, 4))
        plt.plot(times, vln_average, color='blue', linewidth=2)
        plt.xlabel('Time')
        plt.ylabel('VLN Average (V)')
        plt.title('VLN Average Over Time')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png')
        buf.seek(0)
        chart_img = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        plt.close()

    context = {
        'locations': locations,
        'meters': meters,
        'selected_location': selected_location,
        'selected_meter': selected_meter,
        'start_time': start_time,
        'end_time': end_time,
        'chart_img': chart_img,
        'times': times,
        'vln_average': vln_average,
    }
    return render(request, 'meters/dashboard_charts.html', context)


@api_view(['GET'])
def get_device_config(request, pi_device_id):
    """API endpoint for Pi devices to get their configuration"""
    try:
        device = DeviceConfig.objects.get(
            device_id=pi_device_id, is_active=True)
        device.last_seen = timezone.now()
        device.save()

        # Build configuration dictionary
        config = {
            'pi_device_id': device.device_id,
            'location': device.location,
            'meter_name': device.meter_name,
            'ip_address': device.ip_address,
            'port': device.port,
            'reading_interval': device.reading_interval,
            'server_url': device.server_url,
        }

        # Add custom parameters
        for param in device.parameters.all():
            config[param.key] = param.value

        return Response(config)
    except DeviceConfig.DoesNotExist:
        return Response({'error': 'Pi device not found'}, status=404)


@api_view(['POST'])
def update_device_status(request, pi_device_id):
    """API endpoint for Pi devices to report their status"""
    try:
        device = DeviceConfig.objects.get(device_id=pi_device_id)
        device.last_seen = timezone.now()
        device.save()
        return Response({'status': 'updated'})
    except DeviceConfig.DoesNotExist:
        return Response({'error': 'Pi device not found'}, status=404)


def device_management(request):
    """Web interface for managing device configurations"""
    devices = DeviceConfig.objects.all().order_by('location', 'device_id')

    if request.method == 'POST':
        # Handle form submission for creating/updating devices
        device_id = request.POST.get('device_id')
        location = request.POST.get('location')
        meter_name = request.POST.get('meter_name')
        ip_address = request.POST.get('ip_address')
        port = request.POST.get('port', 502)
        reading_interval = request.POST.get('reading_interval', 60)
        server_url = request.POST.get('server_url')

        device, created = DeviceConfig.objects.update_or_create(
            device_id=device_id,
            defaults={
                'location': location,
                'meter_name': meter_name,
                'ip_address': ip_address,
                'port': port,
                'reading_interval': reading_interval,
                'server_url': server_url,
            }
        )

        return redirect('device_management')

    context = {
        'devices': devices,
    }
    return render(request, 'meters/device_management.html', context)


@api_view(['POST'])
def push_config_view(request, device_id):
    try:
        device = Device.objects.get(id=device_id)
        status = push_config_to_pi(device)
        return Response({"status": "Config pushed", "http_status": status})
    except Device.DoesNotExist:
        return Response({"error": "Device not found"}, status=404)
