from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect
from .models import MeterDevice

# ...existing code...

@staff_member_required
def toggle_meter_active(request, pk):
	meter = get_object_or_404(MeterDevice, pk=pk)
	meter.is_active = not meter.is_active
	meter.save()
	# Redirect back to the MeterDevice admin changelist
	return redirect('admin:device_manager_meterdevice_changelist')
from django.shortcuts import render
def meter_list(request):
	meters = MeterDevice.objects.select_related('raspberry_pi').all()
	return render(request, 'device_manager/meter_list.html', {'meters': meters})

def deploy_config(request, pi_id):
	from .models import RaspberryPi, ConfigurationDeployment
	from .services import ConfigurationDeploymentService
	from django.shortcuts import render, get_object_or_404

	pi = get_object_or_404(RaspberryPi, id=pi_id)
	service = ConfigurationDeploymentService()
	deployment_type = request.POST.get('deployment_type', 'DEVICE_CONFIG')
	if deployment_type == 'DEVICE_CONFIG':
		deployment = service.deploy_device_config(pi_id)
	elif deployment_type == 'SYSTEM_CONFIG':
		deployment = service.deploy_system_config(pi_id)
	elif deployment_type == 'BOTH':
		deployment = service.deploy_both_configs(pi_id)
	else:
		deployment = None
	context = {
		'pi': pi,
		'deployment': deployment,
		'deployment_type': deployment_type,
	}
	return render(request, 'device_manager/deploy_result.html', context)

def export_device_config(request, pi_id):
	return HttpResponse(f'<h2>Export Device Config</h2><p>Export device config for Pi ID: {pi_id}</p>')

def export_system_config(request, pi_id):
	return HttpResponse(f'<h2>Export System Config</h2><p>Export system config for Pi ID: {pi_id}</p>')

def test_pi_connection_ajax(request):
	from django.views.decorators.csrf import csrf_exempt
	from django.http import JsonResponse
	from .models import RaspberryPi
	from .services import ConfigurationDeploymentService
	@csrf_exempt
	def inner(request):
		pi_id = request.POST.get('pi_id')
		try:
			pi = RaspberryPi.objects.get(id=pi_id)
			service = ConfigurationDeploymentService()
			ssh_ok, message = service.test_pi_connection(pi)
			pi.ssh_status = ssh_ok
			pi.save(update_fields=['ssh_status'])
			return JsonResponse({'success': True, 'ssh_status': ssh_ok, 'message': message})
		except RaspberryPi.DoesNotExist:
			return JsonResponse({'success': False, 'error': 'Raspberry Pi not found.'})
		except Exception as e:
			return JsonResponse({'success': False, 'error': str(e)})
	return inner(request)
def pi_detail(request, pi_id):
	from .models import RaspberryPi, MeterDevice, SystemConfiguration, ConfigurationDeployment
	from django.shortcuts import render, get_object_or_404

	pi = get_object_or_404(RaspberryPi, id=pi_id)
	meters = MeterDevice.objects.filter(raspberry_pi=pi)
	try:
		system_config = pi.system_config
	except SystemConfiguration.DoesNotExist:
		system_config = None
	deployments = ConfigurationDeployment.objects.filter(raspberry_pi=pi).order_by('-deployed_at')[:10]
	context = {
		'pi': pi,
		'meters': meters,
		'system_config': system_config,
		'deployments': deployments,
	}
	return render(request, 'device_manager/pi_detail.html', context)
def dashboard(request):
	from .models import RaspberryPi, ConfigurationDeployment
	from meter_data.models import MeterReading
	pis = RaspberryPi.objects.all()
	total_meters = MeterDevice.objects.filter(is_active=True).count()
	recent_deployments = ConfigurationDeployment.objects.all()[:10]
	recent_readings = MeterReading.objects.order_by('-time')[:10]
	context = {
		'pis': pis,
		'total_meters': total_meters,
		'recent_deployments': recent_deployments,
		'recent_readings': recent_readings,
	}
	return render(request, 'device_manager/dashboard.html', context)
from django.http import HttpResponse

def home(request):
	return HttpResponse('<h2>Device Manager Home</h2><p>Welcome to the Device Manager app.</p>')


from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import RaspberryPi, MeterDevice, SystemConfiguration, ConfigurationDeployment
from .serializers import (
	RaspberryPiSerializer,
	MeterDeviceSerializer,
	SystemConfigurationSerializer,
	ConfigurationDeploymentSerializer
)
from .services import ConfigurationDeploymentService

class RaspberryPiViewSet(viewsets.ModelViewSet):
	queryset = RaspberryPi.objects.all()
	serializer_class = RaspberryPiSerializer

	from rest_framework.permissions import AllowAny
	@action(
		detail=True,
		methods=['post'],
		permission_classes=[AllowAny],
		authentication_classes=[]
	)
	def test_connection(self, request, pk=None):
		pi = self.get_object()
		service = ConfigurationDeploymentService()
		success, message = service.test_pi_connection(pi)
		return Response({
			'success': success,
			'message': message,
			'pi_ip': pi.pi_ip
		})

	@action(detail=True, methods=['get'])
	def status(self, request, pk=None):
		pi = self.get_object()
		service = ConfigurationDeploymentService()
		success, status_data = service.get_pi_status(pi)
		return Response({
			'success': success,
			'status': status_data,
			'pi_ip': pi.pi_ip
		})

	@action(detail=True, methods=['post'])
	def deploy_device_config(self, request, pk=None):
		pi = self.get_object()
		service = ConfigurationDeploymentService()
		deployment = service.deploy_device_config(pk)
		if deployment:
			serializer = ConfigurationDeploymentSerializer(deployment)
			return Response(serializer.data)
		else:
			return Response({'error': 'Failed to deploy device configuration'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

	@action(detail=True, methods=['post'])
	def deploy_system_config(self, request, pk=None):
		pi = self.get_object()
		service = ConfigurationDeploymentService()
		deployment = service.deploy_system_config(pk)
		if deployment:
			serializer = ConfigurationDeploymentSerializer(deployment)
			return Response(serializer.data)
		else:
			return Response({'error': 'Failed to deploy system configuration'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

	@action(detail=True, methods=['post'])
	def deploy_all_configs(self, request, pk=None):
		pi = self.get_object()
		service = ConfigurationDeploymentService()
		deployment = service.deploy_both_configs(pk)
		if deployment:
			serializer = ConfigurationDeploymentSerializer(deployment)
			return Response(serializer.data)
		else:
			return Response({'error': 'Failed to deploy configurations'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

	@action(detail=True, methods=['get'])
	def device_config_json(self, request, pk=None):
		pi = self.get_object()
		meters = pi.meters.filter(is_active=True)
		# Use a simple serializer for config JSON
		device_config = [
			{
				'meter_name': m.meter_name,
				'meter_address': m.meter_address,
				'meter_model': m.meter_model,
				'location': m.location,
				'pi_ip': pi.pi_ip,
				'pi_name': pi.pi_name
			} for m in meters
		]
		return Response(device_config)

	@action(detail=True, methods=['get'])
	def system_config_json(self, request, pk=None):
		pi = self.get_object()
		try:
			system_config = pi.system_config
			config_data = system_config.to_json()
		except SystemConfiguration.DoesNotExist:
			config_data = {}
		return Response(config_data)

class MeterDeviceViewSet(viewsets.ModelViewSet):
	queryset = MeterDevice.objects.all()
	serializer_class = MeterDeviceSerializer

class SystemConfigurationViewSet(viewsets.ModelViewSet):
	queryset = SystemConfiguration.objects.all()
	serializer_class = SystemConfigurationSerializer

class ConfigurationDeploymentViewSet(viewsets.ModelViewSet):
	queryset = ConfigurationDeployment.objects.all()
	serializer_class = ConfigurationDeploymentSerializer
