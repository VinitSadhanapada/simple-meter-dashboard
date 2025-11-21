import paho.mqtt.client as mqtt
import json
import psycopg2
import subprocess
import os
import time
from datetime import datetime

# Prefer a global meter config at /home/pi/meter_config/config.json; fall back to script-local config.json
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PREFERRED_CONFIG_DIR = os.environ.get('METER_CONFIG_DIR', '/home/pi/meter_config')
PREFERRED_CONFIG_PATH = os.path.join(PREFERRED_CONFIG_DIR, 'config.json')
FALLBACK_CONFIG_PATH = os.path.join(SCRIPT_DIR, 'config.json')

CONFIG_PATH = PREFERRED_CONFIG_PATH if os.path.exists(PREFERRED_CONFIG_PATH) else FALLBACK_CONFIG_PATH
try:
    with open(CONFIG_PATH) as f:
        CONFIG = json.load(f)
    print(f"[DEBUG] Loaded config: {CONFIG_PATH}", flush=True)
    if CONFIG_PATH != PREFERRED_CONFIG_PATH:
        print(f"[WARN] Preferred config not found at {PREFERRED_CONFIG_PATH}; using {CONFIG_PATH}", flush=True)
except FileNotFoundError:
    raise FileNotFoundError(
        f"Config file not found. Expected at {PREFERRED_CONFIG_PATH} or {FALLBACK_CONFIG_PATH}. "
        f"Create /home/pi/meter_config/config.json or set METER_CONFIG_DIR."
    )

DB_CONFIG = {
    'dbname': os.environ.get('DB_NAME', 'mfmdb'),
    'user': os.environ.get('DB_USER', 'mfmuser'),
    'password': os.environ.get('DB_PASSWORD', 'devi'),
    'host': os.environ.get('DB_HOST', CONFIG.get('DB_SERVER_IP', 'localhost') or 'localhost'),
    'port': os.environ.get('DB_PORT', '5432'),
}


def test_db_insert():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        with conn.cursor() as cur:
            cur.execute("CREATE TABLE IF NOT EXISTS test_insert_table (id serial PRIMARY KEY, test_col text);")
            cur.execute("INSERT INTO test_insert_table (test_col) VALUES ('test at startup') RETURNING id;")
            inserted_id = cur.fetchone()[0]
            conn.commit()
            print(f"[DEBUG] Test insert succeeded, id={inserted_id}", flush=True)
        conn.close()
    except Exception as e:
        print(f"[DEBUG] Test insert failed: {e}", flush=True)

# MQTT broker config (offline defaults to localhost, no auth unless provided)
MQTT_BROKER = os.environ.get('MQTT_BROKER', CONFIG.get('MQTT_BROKER_IP', 'localhost') or 'localhost')
MQTT_PORT = int(os.environ.get('MQTT_PORT', '1883'))
MQTT_USER = os.environ.get('MQTT_USER', CONFIG.get('MQTT_USER'))
MQTT_PASS = os.environ.get('MQTT_PASS', CONFIG.get('MQTT_PASS'))
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
    # Inject failure mode if present (for simulation)
    import os, json
    mode_path = os.path.join(os.path.dirname(__file__), 'failure_mode.json')
    failure_mode = 'none'
    if os.path.exists(mode_path):
        try:
            with open(mode_path, 'r') as f:
                failure_mode = json.load(f).get('mode', 'none')
        except Exception:
            pass
    meter_data['failure_mode'] = failure_mode
    # Ensure device_id is an integer and skip if not
    if 'device_id' in meter_data:
        try:
            meter_data['device_id'] = int(meter_data['device_id'])
        except Exception:
            print(f"Skipping insert: device_id is not an integer ({meter_data['device_id']})")
            return  # Skip this insert
    # Execute insert and auto-recover DB connection once on OperationalError
    try:
        with conn.cursor() as cur:
            cur.execute(INSERT_QUERY, meter_data)
            conn.commit()
        return conn
    except psycopg2.OperationalError as e:
        print(f"[WARN] DB connection lost: {e}; attempting reconnect once...", flush=True)
        try:
            conn.close()
        except Exception:
            pass
        conn = psycopg2.connect(**DB_CONFIG)
        with conn.cursor() as cur:
            cur.execute(INSERT_QUERY, meter_data)
            conn.commit()
        return conn
    # Enqueue alert evaluation into Celery/Redis via alerting dispatcher (keeps ingest decoupled)
    try:
        # Allow completely disabling alert dispatch to avoid Redis/Celery in local tests
        if os.environ.get('DISABLE_ALERT_DISPATCH', '0') in ('1', 'true', 'True'):
            print("[DEBUG] Alert dispatch disabled (DISABLE_ALERT_DISPATCH=1)", flush=True)
        else:
            from alerting.dispatcher import enqueue_alert_processing
            devid = meter_data.get('device_id') or meter_data.get('meter_name') or 'unknown'
            ok = enqueue_alert_processing(str(devid), meter_data)
            if not ok:
                print("[WARN] Alert dispatch returned False; /api/alerts may be empty.", flush=True)
    except Exception as e:
        print(f"[WARN] Alert dispatch import failed: {e}", flush=True)

# Removed file-based current_alerts; using Redis/Celery exclusively now.


def on_message(client, userdata, msg):
    print("Received raw MQTT message:", msg.payload.decode())
    try:
        raw = json.loads(msg.payload.decode())
        # Normalize payload: prefer original uppercase keys per message over duplicated snake_case keys
        def pick(d, snake, uppers):
            for k in uppers:
                if k in d:
                    return d[k]
            return d.get(snake)

        meter_data = {
            # identity/meta
            'pi_name': raw.get('pi_name'),
            'pi_ip': raw.get('pi_ip'),
            'location': raw.get('location'),
            'device_id': pick(raw, 'device_id', ['Device_ID']),
            'meter_name': pick(raw, 'meter_name', ['Meter_Name']),
            'time': pick(raw, 'time', ['Time']),
            'model': pick(raw, 'model', ['Model']),
            # power, pf
            'watts_total': pick(raw, 'watts_total', ['Watts Total']),
            'watts_r_ph': pick(raw, 'watts_r_ph', ['Watts R Ph']),
            'watts_y_ph': pick(raw, 'watts_y_ph', ['Watts Y Ph']),
            'watts_b_ph': pick(raw, 'watts_b_ph', ['Watts B Ph']),
            'pf_ave': pick(raw, 'pf_ave', ['PF Ave']),
            'pf_r_ph': pick(raw, 'pf_r_ph', ['PF R Ph']),
            'pf_y_ph': pick(raw, 'pf_y_ph', ['PF Y Ph']),
            'pf_b_ph': pick(raw, 'pf_b_ph', ['PF B Ph']),
            # voltage
            'vln_average': pick(raw, 'vln_average', ['VLN average']),
            'v_r_ph': pick(raw, 'v_r_ph', ['V R Ph']),
            'v_y_ph': pick(raw, 'v_y_ph', ['V Y Ph']),
            'v_b_ph': pick(raw, 'v_b_ph', ['V B Ph']),
            # current
            'a_average': pick(raw, 'a_average', ['A average']),
            'a_r_ph': pick(raw, 'a_r_ph', ['A R Ph']),
            'a_y_ph': pick(raw, 'a_y_ph', ['A Y Ph']),
            'a_b_ph': pick(raw, 'a_b_ph', ['A B Ph']),
            # misc
            'frequency': pick(raw, 'frequency', ['Frequency']),
            'wh_received': pick(raw, 'wh_received', ['Wh received']),
            'load_hours_delivered': pick(raw, 'load_hours_delivered', ['Load Hours Delivered']),
            'no_of_interruption': pick(raw, 'no_of_interruption', ['No of interruption']),
            'on_hours': pick(raw, 'on_hours', ['On Hours']),
            # harmonics
            'v_r_harmonics': pick(raw, 'v_r_harmonics', ['V R Harmonics']),
            'v_y_harmonics': pick(raw, 'v_y_harmonics', ['V Y Harmonics']),
            'v_b_harmonics': pick(raw, 'v_b_harmonics', ['V B Harmonics']),
            'a_r_harmonics': pick(raw, 'a_r_harmonics', ['A R Harmonics']),
            'a_y_harmonics': pick(raw, 'a_y_harmonics', ['A Y Harmonics']),
            'a_b_harmonics': pick(raw, 'a_b_harmonics', ['A B Harmonics']),
        }

        # Short debug line to verify correct routing
        try:
            print(f"[INGEST] inserting meter={meter_data.get('meter_name')} device_id={meter_data.get('device_id')} time={meter_data.get('time')}", flush=True)
        except Exception:
            pass

        # Insert and update userdata conn if it was recreated
        new_conn = insert_meter_reading(userdata['conn'], meter_data)
        if new_conn is not userdata['conn']:
            userdata['conn'] = new_conn
        print("Inserted reading:", meter_data)
    except Exception as e:
        print("Error inserting reading:", e)


def on_connect(client, userdata, flags, rc):
    try:
        print(f"[DEBUG] MQTT on_connect rc={rc}", flush=True)
        if rc == 0:
            client.subscribe(MQTT_TOPIC)
            print(f"[DEBUG] Subscribed to {MQTT_TOPIC}", flush=True)
        elif rc == 4:
            print("[ERROR] MQTT connection refused: bad username or password", flush=True)
        elif rc == 5:
            print("[ERROR] MQTT connection refused: not authorized", flush=True)
    except Exception as e:
        print(f"[WARN] on_connect handler error: {e}", flush=True)


def on_disconnect(client, userdata, rc):
    # rc == 0 means clean disconnect; non-zero means unexpected
    print(f"[DEBUG] MQTT on_disconnect rc={rc}", flush=True)
    # Using connect_async + loop_start with reconnect_delay_set handles auto-reconnect


def main():
    print("[DEBUG] DB_CONFIG:", DB_CONFIG, flush=True)
    test_db_insert()
    # Optional: Run Mosquitto setup script (enables auth); opt-in via MQTT_SETUP=1
    if os.environ.get('MQTT_SETUP', '0') == '1':
        subprocess.run(['sudo', 'python3', 'mosquitto_setup.py'])
    conn = psycopg2.connect(**DB_CONFIG)
    client = mqtt.Client(userdata={'conn': conn})
    # Only set username/password if both are provided
    if MQTT_USER and MQTT_PASS:
        client.username_pw_set(MQTT_USER, MQTT_PASS)
    else:
        print("[DEBUG] Using anonymous MQTT connection", flush=True)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    # Backoff for automatic reconnects
    try:
        client.reconnect_delay_set(min_delay=1, max_delay=30)
    except Exception:
        pass
    try:
        # Use async connect so that if broker/network isn't ready at boot, client auto-retries
        client.connect_async(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        print(f"[ERROR] MQTT connect setup failed: {e}", flush=True)
    print("Listening for meter readings...", flush=True)
    client.loop_start()
    try:
        # Keep main thread alive while background network thread runs
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            client.loop_stop()
        except Exception:
            pass
        try:
            client.disconnect()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
