
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from meter_data.models import MeterReading
from django.forms.models import model_to_dict


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def meter_api(request):
    if request.method == 'POST':
        try:
            data = request.data
            reading = MeterReading.objects.create(
                location=data.get('location', ''),
                device_id=data.get('device_id', ''),
                meter_name=data.get('meter_name', ''),
                time=data.get('time'),
                model=data.get('model', ''),
                watts_total=data.get('watts_total'),
                watts_r_ph=data.get('watts_r_ph'),
                watts_y_ph=data.get('watts_y_ph'),
                watts_b_ph=data.get('watts_b_ph'),
                pf_ave=data.get('pf_ave'),
                pf_r_ph=data.get('pf_r_ph'),
                pf_y_ph=data.get('pf_y_ph'),
                pf_b_ph=data.get('pf_b_ph'),
                vln_average=data.get('vln_average'),
                v_r_ph=data.get('v_r_ph'),
                v_y_ph=data.get('v_y_ph'),
                v_b_ph=data.get('v_b_ph'),
                a_average=data.get('a_average'),
                a_r_ph=data.get('a_r_ph'),
                a_y_ph=data.get('a_y_ph'),
                a_b_ph=data.get('a_b_ph'),
                frequency=data.get('frequency'),
                wh_received=data.get('wh_received'),
                load_hours_delivered=data.get('load_hours_delivered'),
                no_of_interruption=data.get('no_of_interruption'),
                on_hours=data.get('on_hours'),
                v_r_harmonics=data.get('v_r_harmonics'),
                v_y_harmonics=data.get('v_y_harmonics'),
                v_b_harmonics=data.get('v_b_harmonics'),
                a_r_harmonics=data.get('a_r_harmonics'),
                a_y_harmonics=data.get('a_y_harmonics'),
                a_b_harmonics=data.get('a_b_harmonics'),
            )
            return Response({'status': 'success', 'id': reading.id}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'GET':
        device_id = request.GET.get('device_id')
        readings = MeterReading.objects.all()
        if device_id:
            readings = readings.filter(device_id=device_id)
        readings = readings.order_by('-time')[:100]
        data = [model_to_dict(r) for r in readings]
        return Response({'status': 'success', 'readings': data}, status=status.HTTP_200_OK)
    return Response({'status': 'error', 'message': 'Only POST and GET allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
