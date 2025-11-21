import os
import psycopg2


DB_CONFIG = {
    "dbname": os.environ.get("DB_NAME", "mfmdb"),
    "user": os.environ.get("DB_USER", "mfmuser"),
    "password": os.environ.get("DB_PASSWORD", "devi"),
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432"),
}


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    with conn.cursor() as cur:
        cur.execute("SELECT id, device_id, meter_name, time, watts_total FROM meter_readings ORDER BY id DESC LIMIT 5;")
        rows = cur.fetchall()
        for r in rows:
            print(r)
    conn.close()


if __name__ == "__main__":
    main()
