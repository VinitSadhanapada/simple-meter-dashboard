
import psycopg2
import sys

# Database connection settings (update as needed)
DB_NAME = "mfmdb"
DB_USER = "mfmuser"
DB_PASSWORD = "devi"
DB_HOST = "localhost"
DB_PORT = "5432"

# List of fault columns and their logic
FAULT_COLUMNS = [
    ("v_r_ph_fault", "v_r_ph IS NULL OR v_r_ph < 210 OR v_r_ph > 245"),
    ("v_y_ph_fault", "v_y_ph IS NULL OR v_y_ph < 210 OR v_y_ph > 245"),
    ("v_b_ph_fault", "v_b_ph IS NULL OR v_b_ph < 210 OR v_b_ph > 245"),
    ("a_r_ph_fault", "a_r_ph IS NULL OR a_r_ph < 0 OR a_r_ph > 63"),
    ("a_y_ph_fault", "a_y_ph IS NULL OR a_y_ph < 0 OR a_y_ph > 63"),
    ("a_b_ph_fault", "a_b_ph IS NULL OR a_b_ph < 0 OR a_b_ph > 63"),
    ("pf_ave_fault", "pf_ave IS NULL OR pf_ave < 0.95 OR pf_ave > 1.0"),
    ("frequency_fault", "frequency IS NULL OR frequency < 49.5 OR frequency > 50.5"),
    ("v_r_harmonics_fault", "v_r_harmonics IS NULL OR v_r_harmonics > 5"),
    ("v_y_harmonics_fault", "v_y_harmonics IS NULL OR v_y_harmonics > 5"),
    ("v_b_harmonics_fault", "v_b_harmonics IS NULL OR v_b_harmonics > 5"),
    ("a_r_harmonics_fault", "a_r_harmonics IS NULL OR a_r_harmonics > 8"),
    ("a_y_harmonics_fault", "a_y_harmonics IS NULL OR a_y_harmonics > 8"),
    ("a_b_harmonics_fault", "a_b_harmonics IS NULL OR a_b_harmonics > 8"),
    ("watts_total_fault", "watts_total IS NULL OR watts_total < 0 OR watts_total > 10000")
]

def create_fault_log_table(cur):
    # Compose column definitions for all faults
    fault_cols_sql = ',\n    '.join([f"{col} INTEGER NOT NULL" for col, _ in FAULT_COLUMNS])
    sql = f'''
    CREATE TABLE IF NOT EXISTS meter_fault_log (
        time TIMESTAMP NOT NULL,
        meter_name TEXT NOT NULL,
        fault_true INTEGER NOT NULL,
        {fault_cols_sql}
    );
    '''
    try:
        cur.execute(sql)
        print("Created table: meter_fault_log")
    except Exception as e:
        print(f"Error creating meter_fault_log: {e}")

def populate_fault_log_table(cur):
    # Build the select logic for each fault
    fault_cases = [f"CASE WHEN {logic} THEN 1 ELSE 0 END AS {col}" for col, logic in FAULT_COLUMNS]
    fault_sum = ' + '.join([f"(CASE WHEN {logic} THEN 1 ELSE 0 END)" for col, logic in FAULT_COLUMNS])
    fault_cols = ', '.join([col for col, _ in FAULT_COLUMNS])
    sql = f'''
    INSERT INTO meter_fault_log (time, meter_name, fault_true, {fault_cols})
    SELECT
        time,
        meter_name,
        CASE WHEN ({fault_sum}) > 0 THEN 1 ELSE 0 END AS fault_true,
        {', '.join(fault_cases)}
    FROM meterreadings;
    '''
    try:
        cur.execute(f"TRUNCATE meter_fault_log;")
        cur.execute(sql)
        print("Populated meter_fault_log table.")
    except Exception as e:
        print(f"Error populating meter_fault_log: {e}")

def drop_fault_log_table(cur):
    try:
        cur.execute("DROP TABLE IF EXISTS meter_fault_log;")
        print("Dropped table: meter_fault_log")
    except Exception as e:
        print(f"Error dropping meter_fault_log: {e}")

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ["create", "populate", "drop"]:
        print("Usage: python add_error_log_table.py [create|populate|drop]")
        sys.exit(1)

    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
    )
    cur = conn.cursor()

    if sys.argv[1] == "create":
        create_fault_log_table(cur)
    elif sys.argv[1] == "populate":
        populate_fault_log_table(cur)
    elif sys.argv[1] == "drop":
        drop_fault_log_table(cur)

    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
