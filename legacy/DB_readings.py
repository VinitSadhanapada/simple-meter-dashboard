import time
from postgres_helper import PostgresHelper, get_latest_readings
import json
import re
from pathlib import Path
def strip_jsonc_comments(text):
    text = re.sub(r"//.*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return text
config_path = Path(__file__).parent.absolute() / "config.jsonc"
with open(config_path, 'r') as f:
    config = json.loads(strip_jsonc_comments(f.read()))
db = PostgresHelper(
    dbname="mfmdb",
    user="mfmuser",
    password="devi",
    host=config.get("DB_SERVER_IP", "localhost"),
    port=5432
)
db.connect()

# Get all unique device IDs
cur = db.conn.cursor()
cur.execute(
    "SELECT DISTINCT device_id FROM meter_readings ORDER BY device_id;")
device_ids = [row[0] for row in cur.fetchall()]
cur.close()

try:
    while True:
        for device_id in device_ids:
            print(f"\nLatest 1 reading for Device_ID {device_id}:")
            readings = get_latest_readings(db, device_id, limit=1)
            for row in readings:
                print(row)
        print("\n--- Waiting for new data ---\n")
        time.sleep(5)  # Check every 5 seconds
except KeyboardInterrupt:
    print("Stopped monitoring.")
finally:
    db.close()
