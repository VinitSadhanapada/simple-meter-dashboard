import paho.mqtt.client as mqtt
import json
import psycopg2
import subprocess

CONFIG_PATH = 'config.json'
with open(CONFIG_PATH) as f:
    CONFIG = json.load(f)

DB_CONFIG = {
    'dbname': 'mfmdb',
    'user': 'mfmuser',
    'password': 'devi',
    'host': CONFIG.get('DB_SERVER_IP', 'localhost'),
    'port': '5432',
}

# MQTT broker config
MQTT_BROKER = CONFIG.get('MQTT_BROKER_IP', 'localhost')  # Use your broker's IP
MQTT_PORT = 1883
MQTT_USER = 'myuser'  # Use your Mosquitto username
MQTT_PASS = 'Mahadev@123'  # Use your Mosquitto password
MQTT_TOPIC = 'meter/readings'

# Adjust this to match your meter_readings table fields
INSERT_QUERY = '''
INSERT INTO meter_readings (
    pi_name, pi_ip, location, device_id, meter_name, time, model,
    watts_total, watts_r_ph, watts_y_ph, watts_b_ph,
    pf_ave, pf_r_ph, pf_y_ph, pf_b_ph,
    vln_average, v_r_ph, v_y_ph, v_b_ph,
    a_average, a_r_ph, a_y_ph, a_b_ph,
    frequency, wh_received, load_hours_delivered, no_of_interruption, on_hours,
    v_r_harmonics, v_y_harmonics, v_b_harmonics,
    a_r_harmonics, a_y_harmonics, a_b_harmonics
) VALUES (
    %(pi_name)s, %(pi_ip)s, %(location)s, %(device_id)s, %(meter_name)s, %(time)s, %(model)s,
    %(watts_total)s, %(watts_r_ph)s, %(watts_y_ph)s, %(watts_b_ph)s,
    %(pf_ave)s, %(pf_r_ph)s, %(pf_y_ph)s, %(pf_b_ph)s,
    %(vln_average)s, %(v_r_ph)s, %(v_y_ph)s, %(v_b_ph)s,
    %(a_average)s, %(a_r_ph)s, %(a_y_ph)s, %(a_b_ph)s,
    %(frequency)s, %(wh_received)s, %(load_hours_delivered)s, %(no_of_interruption)s, %(on_hours)s,
    %(v_r_harmonics)s, %(v_y_harmonics)s, %(v_b_harmonics)s,
    %(a_r_harmonics)s, %(a_y_harmonics)s, %(a_b_harmonics)s
)
'''


def insert_meter_reading(conn, meter_data):
    # Ensure device_id is an integer and skip if not
    if 'device_id' in meter_data:
        try:
            meter_data['device_id'] = int(meter_data['device_id'])
        except Exception:
            print(
                f"Skipping insert: device_id is not an integer ({meter_data['device_id']})")
            return  # Skip this insert
    with conn.cursor() as cur:
        cur.execute(INSERT_QUERY, meter_data)
        conn.commit()


def on_message(client, userdata, msg):
    print("Received raw MQTT message:", msg.payload.decode())
    try:
        meter_data = json.loads(msg.payload.decode())
        insert_meter_reading(userdata['conn'], meter_data)
        print("Inserted reading:", meter_data)
    except Exception as e:
        print("Error inserting reading:", e)


def main():
    # Run Mosquitto setup script
    subprocess.run(['sudo', 'python3', 'mosquitto_setup.py'])
    conn = psycopg2.connect(**DB_CONFIG)
    client = mqtt.Client(userdata={'conn': conn})
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe(MQTT_TOPIC)
    client.on_message = on_message
    print("Listening for meter readings...")
    client.loop_forever()


if __name__ == "__main__":
    main()
