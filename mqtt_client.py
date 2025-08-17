import paho.mqtt.client as mqtt
import time
import json
import threading
import datetime


# HiveMQ Cloud details
BROKER = "e24c6c7ae8e44974b37991fbb4bef22f.s1.eu.hivemq.cloud"
PORT = 8883
USERNAME = "hivemq.webclient.1752922048213"
PASSWORD = "NEuAz>7$w25JH@fcW0k&"
TOPIC = "MONKEY"
CLUSTER ="E0"

CONNECTION_CHECK_INTERVAL = 15 # 15 sec
LOG_FILE_NAME = "mqtt_log.txt"

published_msg = 0
global mqtt_thread

# Callback for successful connection
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        now = datetime.datetime.now()
        logFile.write("["+now.strftime("%Y-%m-%d %H:%M:%S")+"]" + " Connected to HiveMQ Cloud!")
    else:
        now = datetime.datetime.now()
        logFile.write("["+now.strftime("%Y-%m-%d %H:%M:%S")+"]" + " Failed to connect, return code {rc}")


# Function to check connection status
def is_mqtt_connected():
    return client.is_connected()

def mqtt_init():
    # Create MQTT client
    global client
    client = mqtt.Client()
    client.tls_set()
    client.username_pw_set(USERNAME, PASSWORD)
    client.on_connect = on_connect

    # Connect to the broker
    try:
        client.connect(BROKER, PORT, 60)
    except:
        now = datetime.datetime.now()
        logFile.write("["+now.strftime("%Y-%m-%d %H:%M:%S")+"]" + " Not able to connect")

    # Start the network loop in the background
    client.loop_start()

# Example: Periodically check connection and publish
# while True:
#     if is_mqtt_connected():
#         publish_message("Hello from Python!")
#     else:
#         print("Reconnecting...")
#         client.reconnect()  # Attempt to reconnect if disconnected
#     time.sleep(5)

##########################################################################
# Function to start the client and continously check it
##########################################################################
def mqtt_thread_func():
    global logFile
    mqtt_init()

    while True:
        time.sleep(CONNECTION_CHECK_INTERVAL)
        if is_mqtt_connected():
            # Print in a file that mqtt is connected
            now = datetime.datetime.now()
            logFile.write("["+now.strftime("%Y-%m-%d %H:%M:%S")+"]" + " MQTT Client connected !!!")
        else:
            try:
                client.reconnect()
            except:
                now = datetime.datetime.now()
                logFile.write("["+now.strftime("%Y-%m-%d %H:%M:%S")+"]" + " Unable to reconnect...")

##########################################################################
# Function to creat a thread to run mqtt function in background
##########################################################################
def start_mqtt_thread():
    global mqtt_thread
    mqtt_thread = threading.Thread(target=mqtt_thread_func, name="MQTT Thread")
    mqtt_thread.start()

##########################################################################
# Main function
##########################################################################
def mqtt_main():
    global logFile
    logFile = open(LOG_FILE_NAME, "a")

    start_mqtt_thread()

def mqtt_close():
    mqtt_thread.join()
    if is_mqtt_connected():
        client.disconnect()

def construct_JSON(Parameters, regValue, deviceName):
    data = {}

    data["Cluster"] = CLUSTER
    data["Device"] = deviceName

    for x in range(len(Parameters)):
        data[Parameters[x]] = regValue[x]

    json_data = json.dumps(data, indent=len(Parameters))
    return json_data

# Function to publish message
def publish_message(Parameters, regValue, deviceName, qos_level=0):
    global published_msg
    message = construct_JSON(Parameters, regValue, deviceName)
    if is_mqtt_connected():
        client.publish(TOPIC, message, qos=qos_level)
        published_msg += 1
        #print(f"Published: {message}")
    else:
        #check is thread is running
        if mqtt_thread.is_alive() is False:
            # Start the thread
            start_mqtt_thread()
    return published_msg