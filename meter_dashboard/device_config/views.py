from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import json


from .models import RaspberryPi, MeterDevice, SystemConfiguration, ConfigurationDeployment
from .serializers import (
    RaspberryPiSerializer,
    MeterDeviceSerializer,
    SystemConfigurationSerializer,
    ConfigurationDeploymentSerializer,
    MeterDeviceJSONSerializer
)
from .services import ConfigurationDeploymentService

# Django Views for Web Interface


def dashboard(request):
    """Main dashboard view"""
    pis = RaspberryPi.objects.filter(is_active=True)
    total_meters = MeterDevice.objects.filter(is_active=True).count()
    recent_deployments = ConfigurationDeployment.objects.all()[:10]

    context = {
        'pis': pis,
        'total_meters': total_meters,
        'recent_deployments': recent_deployments,
    }
    return render(request, 'device_config/dashboard.html', context)


def pi_detail(request, pi_id):
    """Raspberry Pi detail view"""
    pi = get_object_or_404(RaspberryPi, id=pi_id)
    meters = pi.meters.filter(is_active=True)
    system_config = getattr(pi, 'system_config', None)
    deployments = pi.deployments.all()[:10]

    context = {
        'pi': pi,
        'meters': meters,
        'system_config': system_config,
        'deployments': deployments,
    }
    return render(request, 'device_config/pi_detail.html', context)


def meter_list(request):
    """List all meters"""
    meters = MeterDevice.objects.filter(
        is_active=True).select_related('raspberry_pi')
    context = {'meters': meters}
    return render(request, 'device_config/meter_list.html', context)


@login_required
def deploy_config(request, pi_id):
    """Deploy configuration to a specific Pi"""
    pi = get_object_or_404(RaspberryPi, id=pi_id)

    if request.method == 'POST':
        deployment_type = request.POST.get('deployment_type', 'BOTH')
        service = ConfigurationDeploymentService()

        if deployment_type == 'DEVICE_CONFIG':
            deployment = service.deploy_device_config(pi_id)
        elif deployment_type == 'SYSTEM_CONFIG':
            deployment = service.deploy_system_config(pi_id)
        else:
            deployment = service.deploy_both_configs(pi_id)

        if deployment and deployment.status == 'SUCCESS':
            messages.success(
                request, f'Configuration deployed successfully to {pi.pi_name}')
        else:
            messages.error(
                request, f'Failed to deploy configuration to {pi.pi_name}')

    return redirect('device_config:pi_detail', pi_id=pi_id)


def pi_list(request):
    """List all Raspberry Pis"""
    pis = RaspberryPi.objects.all().order_by('-last_updated')
    return render(request, 'device_config/pi_list.html', {'pis': pis})


def add_pi(request):
    """Redirect to admin for adding a new Raspberry Pi"""
    return redirect('/admin/device_config/raspberrypi/add/')


def edit_pi(request, pk):
    """Redirect to admin for editing an existing Raspberry Pi"""
    return redirect(f'/admin/device_config/raspberrypi/{pk}/change/')

# REST API ViewSets


class RaspberryPiViewSet(viewsets.ModelViewSet):
    """ViewSet for Raspberry Pi management"""
    queryset = RaspberryPi.objects.all()
    serializer_class = RaspberryPiSerializer

    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Test SSH connection to Raspberry Pi"""
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
        """Get current status of Raspberry Pi"""
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
        """Deploy device configuration to Raspberry Pi"""
        pi = self.get_object()
        service = ConfigurationDeploymentService()
        deployment = service.deploy_device_config(pk)

        if deployment:
            serializer = ConfigurationDeploymentSerializer(deployment)
            return Response(serializer.data)
        else:
            return Response(
                {'error': 'Failed to deploy device configuration'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def deploy_system_config(self, request, pk=None):
        """Deploy system configuration to Raspberry Pi"""
        pi = self.get_object()
        service = ConfigurationDeploymentService()
        deployment = service.deploy_system_config(pk)

        if deployment:
            serializer = ConfigurationDeploymentSerializer(deployment)
            return Response(serializer.data)
        else:
            return Response(
                {'error': 'Failed to deploy system configuration'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def deploy_all_configs(self, request, pk=None):
        """Deploy both configurations to Raspberry Pi"""
        pi = self.get_object()
        service = ConfigurationDeploymentService()
        deployment = service.deploy_both_configs(pk)

        if deployment:
            serializer = ConfigurationDeploymentSerializer(deployment)
            return Response(serializer.data)
        else:
            return Response(
                {'error': 'Failed to deploy configurations'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def device_config_json(self, request, pk=None):
        """Get device_config.json for this Pi"""
        pi = self.get_object()
        meters = pi.meters.filter(is_active=True)
        device_config = [MeterDeviceJSONSerializer(
            meter).data for meter in meters]

        return Response(device_config)

    @action(detail=True, methods=['get'])
    def system_config_json(self, request, pk=None):
        """Get config.json for this Pi"""
        pi = self.get_object()
        system_config, created = SystemConfiguration.objects.get_or_create(
            raspberry_pi=pi)

        return Response(system_config.to_json())


class MeterDeviceViewSet(viewsets.ModelViewSet):
    """ViewSet for Meter Device management"""
    queryset = MeterDevice.objects.all()
    serializer_class = MeterDeviceSerializer

    def get_queryset(self):
        queryset = MeterDevice.objects.all()
        pi_id = self.request.query_params.get('pi_id', None)
        if pi_id is not None:
            queryset = queryset.filter(raspberry_pi_id=pi_id)
        return queryset

    @action(detail=False, methods=['get'])
    def by_pi(self, request):
        """Get meters grouped by Raspberry Pi"""
        meters_by_pi = {}
        pis = RaspberryPi.objects.filter(
            is_active=True).prefetch_related('meters')

        for pi in pis:
            meters = pi.meters.filter(is_active=True)
            meters_by_pi[pi.pi_ip] = {
                'pi_name': pi.pi_name,
                'pi_ip': pi.pi_ip,
                'meters': MeterDeviceSerializer(meters, many=True).data
            }

        return Response(meters_by_pi)

    @action(detail=False, methods=['get'])
    def available_models(self, request):
        """Get all available meter models (predefined + custom)"""
        available_models = MeterDevice.get_available_meter_models()
        predefined_models = MeterDevice.get_predefined_choices()

        return Response({
            'predefined': predefined_models,
            'custom': [model for model in available_models if model not in predefined_models],
            'all': available_models
        })


class SystemConfigurationViewSet(viewsets.ModelViewSet):
    """ViewSet for System Configuration management"""
    queryset = SystemConfiguration.objects.all()
    serializer_class = SystemConfigurationSerializer

    def get_queryset(self):
        queryset = SystemConfiguration.objects.all()
        pi_id = self.request.query_params.get('pi_id', None)
        if pi_id is not None:
            queryset = queryset.filter(raspberry_pi_id=pi_id)
        return queryset


class ConfigurationDeploymentViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Configuration Deployment tracking"""
    queryset = ConfigurationDeployment.objects.all()
    serializer_class = ConfigurationDeploymentSerializer

    def get_queryset(self):
        queryset = ConfigurationDeployment.objects.all()
        pi_id = self.request.query_params.get('pi_id', None)
        if pi_id is not None:
            queryset = queryset.filter(raspberry_pi_id=pi_id)
        return queryset.order_by('-deployed_at')

# Utility Views


@csrf_exempt
def export_device_config(request, pi_id):
    """Export device_config.json for a specific Pi"""
    try:
        pi = RaspberryPi.objects.get(id=pi_id, is_active=True)
        meters = pi.meters.filter(is_active=True)
        device_config = [MeterDeviceJSONSerializer(
            meter).data for meter in meters]

        response = HttpResponse(
            json.dumps(device_config, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="device_config_{pi.pi_name}.json"'
        return response

    except RaspberryPi.DoesNotExist:
        return JsonResponse({'error': 'Raspberry Pi not found'}, status=404)


@csrf_exempt
def export_system_config(request, pi_id):
    """Export config.json for a specific Pi"""
    try:
        pi = RaspberryPi.objects.get(id=pi_id, is_active=True)
        system_config, created = SystemConfiguration.objects.get_or_create(
            raspberry_pi=pi)
        config_data = system_config.to_json()

        response = HttpResponse(
            json.dumps(config_data, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="config_{pi.pi_name}.json"'
        return response

    except RaspberryPi.DoesNotExist:
        return JsonResponse({'error': 'Raspberry Pi not found'}, status=404)
