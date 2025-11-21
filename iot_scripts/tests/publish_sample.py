import json
import os
import time

import paho.mqtt.client as mqtt


BROKER = os.environ.get("MQTT_BROKER", "localhost")
PORT = int(os.environ.get("MQTT_PORT", "1883"))
TOPIC = os.environ.get("MQTT_TOPIC", "meter/readings")
MQTT_USER = os.environ.get("MQTT_USER")
MQTT_PASS = os.environ.get("MQTT_PASS")


def main():
    client = mqtt.Client()
    # Use auth if provided (for brokers with allow_anonymous false)
    if MQTT_USER or MQTT_PASS:
        client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.connect(BROKER, PORT, 60)

    payload = {
        # identity/meta
        "pi_name": "pi-test",
        "pi_ip": "192.168.1.50",
        "location": "Lab",
        "Device_ID": 101,  # supports either 'device_id' or 'Device_ID'
        "Meter_Name": "Test-Meter",
        "Time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "Model": "EL-TEST",
        # power & pf
        "Watts Total": 123.45,
        "Watts R Ph": 40.0,
        "Watts Y Ph": 41.0,
        "Watts B Ph": 42.0,
        "PF Ave": 0.98,
        "PF R Ph": 0.97,
        "PF Y Ph": 0.99,
        "PF B Ph": 0.98,
        # voltage
        "VLN average": 230.0,
        "V R Ph": 229.0,
        "V Y Ph": 231.0,
        "V B Ph": 230.5,
        # current
        "A average": 5.0,
        "A R Ph": 4.9,
        "A Y Ph": 5.1,
        "A B Ph": 5.0,
        # misc
        "Frequency": 50.0,
        "Wh received": 1000.0,
        "Load Hours Delivered": 12.0,
        "No of interruption": 0,
        "On Hours": "12:00",
        # harmonics
        "V R Harmonics": 1.1,
        "V Y Harmonics": 1.2,
        "V B Harmonics": 1.3,
        "A R Harmonics": 0.9,
        "A Y Harmonics": 1.0,
        "A B Harmonics": 1.1,
    }

    # Publish retained so new subscribers receive it immediately
    client.publish(TOPIC, json.dumps(payload), qos=1, retain=True)
    print(f"Published test payload to {TOPIC} on {BROKER}:{PORT}")
    client.disconnect()


if __name__ == "__main__":
    main()
