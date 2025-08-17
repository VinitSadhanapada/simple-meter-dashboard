import psycopg2
from psycopg2.extras import RealDictCursor


class PostgresHelper:
    def __init__(self, dbname, user, password, host='localhost', port=5432):
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.conn = None

    def connect(self):
        self.conn = psycopg2.connect(
            dbname=self.dbname,
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port
        )

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def execute(self, query, params=None, commit=False):
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            if commit:
                self.conn.commit()

    def fetchall(self, query, params=None):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchall()

    def fetchone(self, query, params=None):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchone()

    def insert_and_get_id(self, query, params=None):
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            self.conn.commit()
            return cur.fetchone()[0]


# Example usage:
if __name__ == "__main__":
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
    db.execute(
        "CREATE TABLE IF NOT EXISTS test_table (id SERIAL PRIMARY KEY, name TEXT)", commit=True)
    db.execute("INSERT INTO test_table (name) VALUES (%s)",
               ("hello",), commit=True)
    rows = db.fetchall("SELECT * FROM test_table")
    print(rows)
    db.close()

# --- Meter Data Example ---
# Suppose your meter data has: timestamp, device_id, param1, param2, ...
# Adjust columns as needed for your real data structure.


def create_meter_table(db):
    db.execute('''
        CREATE TABLE IF NOT EXISTS meter_readings (
            id SERIAL PRIMARY KEY,
            location TEXT,
            device_id TEXT NOT NULL,
            meter_name TEXT,
            time TIMESTAMP NOT NULL,
            model TEXT,
            watts_total REAL,
            watts_r_ph REAL,
            watts_y_ph REAL,
            watts_b_ph REAL,
            pf_ave REAL,
            pf_r_ph REAL,
            pf_y_ph REAL,
            pf_b_ph REAL,
            vln_average REAL,
            v_r_ph REAL,
            v_y_ph REAL,
            v_b_ph REAL,
            a_average REAL,
            a_r_ph REAL,
            a_y_ph REAL,
            a_b_ph REAL,
            frequency REAL,
            wh_received REAL,
            load_hours_delivered REAL,
            no_of_interruption REAL,
            on_hours TEXT,
            v_r_harmonics REAL,
            v_y_harmonics REAL,
            v_b_harmonics REAL,
            a_r_harmonics REAL,
            a_y_harmonics REAL,
            a_b_harmonics REAL
        )
    ''', commit=True)


def insert_meter_reading(db, location, device_id, meter_name, time, model,
                         watts_total, watts_r_ph, watts_y_ph, watts_b_ph,
                         pf_ave, pf_r_ph, pf_y_ph, pf_b_ph,
                         vln_average, v_r_ph, v_y_ph, v_b_ph,
                         a_average, a_r_ph, a_y_ph, a_b_ph,
                         frequency, wh_received, load_hours_delivered, no_of_interruption, on_hours,
                         v_r_harmonics, v_y_harmonics, v_b_harmonics,
                         a_r_harmonics, a_y_harmonics, a_b_harmonics):
    print(
        f"DEBUG: insert_meter_reading time value: {time} (type: {type(time)})")
    db.execute('''
        INSERT INTO meter_readings (
            location, device_id, meter_name, time, model,
            watts_total, watts_r_ph, watts_y_ph, watts_b_ph,
            pf_ave, pf_r_ph, pf_y_ph, pf_b_ph,
            vln_average, v_r_ph, v_y_ph, v_b_ph,
            a_average, a_r_ph, a_y_ph, a_b_ph,
            frequency, wh_received, load_hours_delivered, no_of_interruption, on_hours,
            v_r_harmonics, v_y_harmonics, v_b_harmonics,
            a_r_harmonics, a_y_harmonics, a_b_harmonics
        ) VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s
        )
    ''', (
        location, device_id, meter_name, time, model,
        watts_total, watts_r_ph, watts_y_ph, watts_b_ph,
        pf_ave, pf_r_ph, pf_y_ph, pf_b_ph,
        vln_average, v_r_ph, v_y_ph, v_b_ph,
        a_average, a_r_ph, a_y_ph, a_b_ph,
        frequency, wh_received, load_hours_delivered, no_of_interruption, on_hours,
        v_r_harmonics, v_y_harmonics, v_b_harmonics,
        a_r_harmonics, a_y_harmonics, a_b_harmonics
    ), commit=True)


def get_latest_readings(db, device_id, limit=10):
    return db.fetchall('''
        SELECT * FROM meter_readings
        WHERE device_id = %s
        ORDER BY time DESC
        LIMIT %s
    ''', (device_id, limit))


if __name__ == "__main__":
    # ...existing code...
    # Meter data example usage with all CSV columns:
    from datetime import datetime
    create_meter_table(db)
    insert_meter_reading(
        db,
        "dev1", "Meter 1", datetime.now(), "LG6400",
        100.1, 33.2, 33.3, 33.6,
        0.98, 0.97, 0.99, 0.96,
        415.0, 230.1, 230.2, 230.3,
        5.1, 1.7, 1.8, 1.6,
        50.0, 12345.6, 100.0, 2, 500.0,
        2.1, 2.2, 2.3,
        0.1, 0.2, 0.3
    )
    readings = get_latest_readings(db, "dev1", limit=5)
    print("Latest meter readings:", readings)
    db.close()
