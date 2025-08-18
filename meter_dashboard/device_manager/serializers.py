


from rest_framework import serializers
from .models import RaspberryPi, MeterDevice, SystemConfiguration, ConfigurationDeployment

class RaspberryPiSerializer(serializers.ModelSerializer):
	meter_count = serializers.SerializerMethodField()

	class Meta:
		model = RaspberryPi
		fields = ['id', 'pi_name', 'pi_ip', 'location', 'is_active',
				  'last_updated', 'created_at', 'meter_count']
		read_only_fields = ['last_updated', 'created_at']

	def get_meter_count(self, obj):
		return obj.meters.filter(is_active=True).count()


class MeterDeviceSerializer(serializers.ModelSerializer):
	pi_name = serializers.CharField(
		source='raspberry_pi.pi_name', read_only=True)
	pi_ip = serializers.CharField(source='raspberry_pi.pi_ip', read_only=True)

	class Meta:
		model = MeterDevice
		fields = ['id', 'meter_name', 'meter_address', 'meter_model', 'location',
				  'raspberry_pi', 'pi_name', 'pi_ip', 'is_active', 'last_updated', 'created_at']
		read_only_fields = ['last_updated', 'created_at']


class SystemConfigurationSerializer(serializers.ModelSerializer):
	pi_name = serializers.CharField(
		source='raspberry_pi.pi_name', read_only=True)
	pi_ip = serializers.CharField(source='raspberry_pi.pi_ip', read_only=True)

	class Meta:
		model = SystemConfiguration
		fields = ['id', 'raspberry_pi', 'pi_name', 'pi_ip', 'simulation_mode', 'reading_interval',
				  'inter_device_delay', 'port', 'enable_mqtt', 'enable_rtc', 'last_updated']
		read_only_fields = ['last_updated']


class ConfigurationDeploymentSerializer(serializers.ModelSerializer):
	pi_name = serializers.CharField(
		source='raspberry_pi.pi_name', read_only=True)
	pi_ip = serializers.CharField(source='raspberry_pi.pi_ip', read_only=True)

	class Meta:
		model = ConfigurationDeployment
		fields = ['id', 'raspberry_pi', 'pi_name', 'pi_ip', 'deployment_type', 'status',
				  'error_message', 'deployed_at', 'completed_at']
		read_only_fields = ['deployed_at', 'completed_at', 'status', 'error_message']

class MeterDeviceSerializer(serializers.ModelSerializer):
	class Meta:
		model = MeterDevice
		fields = '__all__'

class SystemConfigurationSerializer(serializers.ModelSerializer):
	class Meta:
		model = SystemConfiguration
		fields = '__all__'

class ConfigurationDeploymentSerializer(serializers.ModelSerializer):
	class Meta:
		model = ConfigurationDeployment
		fields = '__all__'
