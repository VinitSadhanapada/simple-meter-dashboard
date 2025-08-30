from django.shortcuts import render
from django.db import connections
from django.http import JsonResponse
import pandas as pd

# Example: Fetch data for a single meter from PostgreSQL

def single_meter_view(request):
    meter_id = request.GET.get('meter_id', 1)  # Default to 1 for demo
    with connections['default'].cursor() as cursor:
        cursor.execute('''
            SELECT timestamp, reading_value
            FROM meterreadings
            WHERE meter_id = %s
            ORDER BY timestamp DESC
            LIMIT 1000
        ''', [meter_id])
        rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=['timestamp', 'reading_value'])
    data = df.to_dict(orient='records')
    return render(request, 'visual/single_meter.html', {'data': data, 'meter_id': meter_id})
