import os
import django
import datetime
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'device_config_manager.settings')
django.setup()
from device_manager.models import MeterReading

# ...existing constants and functions from elmeasure_LG5310.py...
# (Copy all constants, regAdress, pack, format_seconds_to_hhmmss, ReadMeterOnHours, ReadMeterData)

# --- Paste all code from elmeasure_LG5310.py up to and including ReadMeterData ---
# For brevity, not repeated here, but in your actual file, copy all definitions above

# Example usage: Collect data and save to DCMS

def save_meter_reading_to_dcms(device_id, location, meter_name, model, client, errorFile=None):
    now = datetime.datetime.now()
    data = ReadMeterData(client, device_id, regAdress, errorFile)
    # Map data to fields (adjust indices as needed)
    MeterReading.objects.create(
        location=location,
        device_id=device_id,
        meter_name=meter_name,
        time=now,
        model=model,
        watts_total=data[0],
        watts_r_ph=data[1],
        watts_y_ph=data[2],
        watts_b_ph=data[3],
        pf_ave=data[4],
        pf_r_ph=data[5],
        pf_y_ph=data[6],
        pf_b_ph=data[7],
        vln_average=data[8],
        v_r_ph=data[9],
        v_y_ph=data[10],
        v_b_ph=data[11],
        a_average=data[12],
        a_r_ph=data[13],
        a_y_ph=data[14],
        a_b_ph=data[15],
        frequency=data[16],
        wh_received=data[17],
        load_hours_delivered=data[18],
        no_of_interruption=data[19],
        on_hours=data[20],
        v_r_harmonics=data[21],
        v_y_harmonics=data[22],
        v_b_harmonics=data[23],
        a_r_harmonics=data[24],
        a_y_harmonics=data[25],
        a_b_harmonics=data[26],
    )
    print(f"Saved reading for device {device_id} at {now}")

# Example main loop (replace with your actual Modbus client setup)
if __name__ == "__main__":
    # from pymodbus.client.sync import ModbusTcpClient
    # client = ModbusTcpClient('192.168.1.100')
    # device_id = 1
    # location = 'YourLocation'
    # meter_name = 'LG5310'
    # model = 'LG5310'
    # save_meter_reading_to_dcms(device_id, location, meter_name, model, client)
    pass
