from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
import datetime

NO_RESPONSE_FROM_DEVICE = 0
PARAMETER_NOT_AVAILABLE = "NA"

START_ADD = 100

WATTS_TOTAL_STR = "Watts Total"
WATTS_TOTAL_ADD = 0
WATTS_R_PH_STR = "Watts R Ph"
WATTS_R_PH_ADD = 0
WATTS_Y_PH_STR = "Watts Y Ph"
WATTS_Y_PH_ADD = 0
WATTS_B_PH_STR = "Watts B Ph"
WATTS_B_PH_ADD = 0

PH_AVG_STR = "PF Ave"
PH_AVG_ADD = 0
PH_R_PH_STR = "PF R Ph"
PH_R_PH_ADD = 0
PH_Y_PH_STR = "PF Y Ph"
PH_Y_PH_ADD = 0
PH_B_PH_STR = "PF B Ph"
PH_B_PH_ADD = 0

VLN_AVG_STR = "VLN average"
VLN_AVG_ADD = 0
V_R_PH_STR = "V R Ph"
V_R_PH_ADD = 0
V_Y_PH_STR = "V Y Ph"
V_Y_PH_ADD = 0
V_B_PH_STR = "V B Ph"
V_B_PH_ADD = 0

A_AVG_STR = "A average"
A_AVG_ADD = 148
A_R_PH_STR = "A R Ph"
A_R_PH_ADD = 150
A_Y_PH_STR = "A Y Ph"
A_Y_PH_ADD = 0
A_B_PH_STR = "A B Ph"
A_B_PH_ADD = 0

FREQUENCY_STR = "Frequency"
FREQUENCY_ADD = 0

WH_RCVD_STR = "Wh received"
WH_RCVD_ADD = 0

V_R_HARMO_STR = "V R Harmonics"
V_R_HARMO_ADD = 0
V_Y_HARMO_STR = "V Y Harmonics"
V_Y_HARMO_ADD = 0
V_B_HARMO_STR = "V B Harmonics"
V_B_HARMO_ADD = 0

A_R_HARMO_STR = "A R Harmonics"
A_R_HARMO_ADD = 0
A_Y_HARMO_STR = "A Y Harmonics"
A_Y_HARMO_ADD = 0
A_B_HARMO_STR = "A B Harmonics"
A_B_HARMO_ADD = 0

LOAD_HRS_DL_STR = "Load Hours Delivered"
LOAD_HRS_DL_ADD = 0

NO_OF_INTR_STR = "No of interruption"   # Long Inverse
NO_OF_INTR_ADD = 0

ON_HRS_STR = "On Hours"
ON_HRS_ADD = 0

A_R_UNBALANCE_STR = "A R Unbalance"
A_R_UNBALANCE_ADD = 0
A_Y_UNBALANCE_STR = "A Y Unbalance"
A_Y_UNBALANCE_ADD = 0
A_B_UNBALANCE_STR = "A B Unbalance"
A_B_UNBALANCE_ADD = 0

regAdress = [         WATTS_TOTAL_ADD, WATTS_R_PH_ADD, WATTS_Y_PH_ADD, WATTS_B_PH_ADD,
                        PH_AVG_ADD, PH_R_PH_ADD, PH_Y_PH_ADD, PH_B_PH_ADD,
                        VLN_AVG_ADD, V_R_PH_ADD, V_Y_PH_ADD, V_B_PH_ADD,
                        A_AVG_ADD, A_R_PH_ADD, A_Y_PH_ADD, A_B_PH_ADD,
                        FREQUENCY_ADD,
                        WH_RCVD_ADD,
                        LOAD_HRS_DL_ADD,
                        NO_OF_INTR_ADD,
                        ON_HRS_ADD,
                        V_R_HARMO_ADD, V_Y_HARMO_ADD, V_B_HARMO_ADD,
                        A_R_HARMO_ADD, A_Y_HARMO_ADD, A_B_HARMO_ADD]


##########################################################################
# Function to convert 2 int variable into a long inverse
##########################################################################
def pack(tup):
    return (tup[0]<<16)|tup[1]

##########################################################################
# Function to convert seconds into hh:mm:ss format
##########################################################################
def format_seconds_to_hhmmss(seconds):
    hours = seconds // (60*60)
    seconds %= (60*60)
    minutes = seconds // 60
    seconds %= 60
    return "%02i:%02i:%02i" % (hours, minutes, seconds)

##########################################################################
# Function to read meter data from holding registers
##########################################################################
def ReadMeterData(client, deviceID, Parameters, errorFile):
    returnVal = [0] * len(Parameters)
    Address = A_AVG_ADD
    
    try:
        response1 = client.read_holding_registers(Address, 4, unit=deviceID)
    except:
        #print("Received ModbusException from library while reading address " + str(Address) + " For device: " + str(deviceID))
        now = datetime.datetime.now()
        if errorFile:

            errorFile.write("["+now.strftime("%Y-%m-%d %H:%M:%S")+"]" + " Received ModbusException from library while reading address " + str(Address) + " For device: " + str(deviceID)+"\n")
        returnVal = [-1] * len(Parameters)
        return returnVal
    
    if response1.isError():
        # print(f"Received exception from device ({response1})")
        now = datetime.datetime.now()
        if errorFile:

            errorFile.write("["+now.strftime("%Y-%m-%d %H:%M:%S")+"]" + " Received exception from device ({response1})"+"\n")
        # THIS IS NOT A PYTHON EXCEPTION, but a valid modbus message
        # Try reading the same value one more time.
        try:
            response1 = client.read_holding_registers(Address, 4, unit=deviceID)
        except:
            # print("Received ModbusException from library while reading address " + str(Address) + " For device: " + str(deviceID))
            now = datetime.datetime.now()
            if errorFile:

                errorFile.write("["+now.strftime("%Y-%m-%d %H:%M:%S")+"]" + " Received ModbusException from library while reading address " + str(Address) + " For device: " + str(deviceID)+"\n")
            returnVal = [-1] * len(Parameters)
            return returnVal

        if response1.isError():
            # print(f"Received exception from device 2nd time ({response1})")
            now = datetime.datetime.now()
            if errorFile:

                errorFile.write("["+now.strftime("%Y-%m-%d %H:%M:%S")+"]" + " Received exception from device 2nd time ({response1})"+"\n")
            # THIS IS NOT A PYTHON EXCEPTION, but a valid modbus message
            returnVal = [NO_RESPONSE_FROM_DEVICE] * len(Parameters)
            return returnVal
    
    fullList = response1.registers

    for x in range(len(regAdress)):
        #tempReg = fullList[regAdress[x]-START_ADD:]
        if(regAdress[x]==A_AVG_ADD):
            decoder = BinaryPayloadDecoder.fromRegisters(fullList, Endian.Big, wordorder=Endian.Little)
            returnVal[x+1] = round(decoder.decode_32bit_float(), 2)
        elif(regAdress[x]==A_R_PH_ADD):
            tempReg = fullList[2:]
            decoder = BinaryPayloadDecoder.fromRegisters(tempReg, Endian.Big, wordorder=Endian.Little)
            returnVal[x+1] = round(decoder.decode_32bit_float(), 2)
        else:
            returnVal[x+1] = "NA"
    
    return returnVal

def save_reading_to_dcms(location, device_id, meter_name, model, readings, timestamp=None):
    try:
        import os
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'device_config_manager.settings')
        django.setup()
        from device_manager.models import MeterReading
        MeterReading.objects.create(
            location=location,
            device_id=device_id,
            meter_name=meter_name,
            time=timestamp or datetime.datetime.now(),
            model=model,
            watts_total=readings[0],
            watts_r_ph=readings[1],
            watts_y_ph=readings[2],
            watts_b_ph=readings[3],
            pf_ave=readings[4],
            pf_r_ph=readings[5],
            pf_y_ph=readings[6],
            pf_b_ph=readings[7],
            vln_average=readings[8],
            v_r_ph=readings[9],
            v_y_ph=readings[10],
            v_b_ph=readings[11],
            a_average=readings[12],
            a_r_ph=readings[13],
            a_y_ph=readings[14],
            a_b_ph=readings[15],
            frequency=readings[16],
            wh_received=readings[17],
            load_hours_delivered=readings[18],
            no_of_interruption=readings[19],
            on_hours=readings[20],
            v_r_harmonics=readings[21],
            v_y_harmonics=readings[22],
            v_b_harmonics=readings[23],
            a_r_harmonics=readings[24],
            a_y_harmonics=readings[25],
            a_b_harmonics=readings[26],
        )
        print(f"[DCMS] Saved reading for device {device_id} at {timestamp or datetime.datetime.now()}")
    except Exception as e:
        print(f"[DCMS] Failed to save reading: {e}")