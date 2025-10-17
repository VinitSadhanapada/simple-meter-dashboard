# Modular Meter Data & Alerting Architecture (Temporary README)

## Overview
This document outlines a modular, scalable, and database-efficient architecture for meter data ingestion, alerting, and retention, suitable for up to hundreds of meters.

---

## 1. Data Ingestion Layer
- **Script/Service:** `mqtt_to_db_ingest.py` (or similar)
- **Role:** Receives raw meter data (e.g., via MQTT) and inserts it into the `meter_readings` table.
- **Retention:** All raw readings are kept for 1 month, then deleted by a scheduled cleanup job.

---

## 2. Alert/Evaluation Addon (Modular)
- **Script/Service:** `alert_monitor_addon.py` (runs independently)
- **Role:**
  - Periodically (e.g., every minute) fetches recent readings for all meters from the DB.
  - For each meter/parameter:
    - Calculates a 10-minute rolling average (in Python, not stored in DB).
    - Checks if the average is out of bounds (voltage, current, frequency, etc.).
    - If an alert condition persists for >10 minutes, inserts a row into the `alert_events` table (with start, end, duration, and average value).
    - For power cut, voltage surge, polarity flip, etc., only significant events are stored.
  - Keeps rolling state in memory for efficiency; only writes to DB when a significant event occurs.

---

## 3. Alert Events Table
- **Table:** `alert_events`
- **Role:** Stores only significant alert events (not every threshold crossing).
- **Fields:**
  - id, device_id, meter_id, parameter, alert_type, start_time, end_time, duration, avg_value, value_at_start, value_at_end, extra_info (JSON).

---

## 4. Cleanup/Retention
- **Script/Job:** `cleanup_old_data.py` (or Django management command/cron)
- **Role:** Deletes old data from `meter_readings` (older than 1 month) and optionally from `alert_events` (if you want to limit history).

---

## 5. UI/API Layer
- **Role:** Fetches live and historical data from `meter_readings` and `alert_events` for display.
- **Averages:** For live display, can calculate 10-min averages on the fly from recent readings.

---

## 6. (Optional) Daily Summary Table
- **Table:** `daily_summaries`
- **Role:** Stores per-day metrics (on-hours, load hours, solar durations, etc.) for fast reporting.

---

## Key Principles
- **Minimal DB Writes:** Only significant alert events are stored, not every threshold crossing.
- **Modular:** Ingestion, alerting, cleanup, and UI are all separate scripts/services.
- **Efficient:** 10-min rolling averages for 200+ meters is lightweight for a modern server.
- **Retention:** All raw data is auto-cleaned after 1 month; only key events are kept long-term.

---

## Example Data/Alert Handling
| Data/Alert Type         | Where to Store         | Retention/Trigger                |
|------------------------ |-----------------------|----------------------------------|
| kWh, kW, kVA, etc.      | meter_readings        | 1 month, then delete             |
| Power cut/surge         | alert_events          | Only if >10 min                  |
| Voltage/Current/Freq    | alert_events          | Only if >10 min out of bounds    |
| Polarity flip           | alert_events          | On event                         |
| Solar durations         | meter_readings/daily  | 1 month, or daily summary        |
| Averages                | Calculate on the fly  | N/A                              |

---

## Scaling Notes
- With proper indexing, 10-min rolling averages for 200+ meters is trivial for PostgreSQL and Python.
- For larger scale, batch queries and/or use materialized views.

---

## Next Steps
- [ ] Create `alert_events` table (SQL provided when resuming)
- [ ] Implement alert addon logic (10-min average, event detection, DB insert)
- [ ] Implement cleanup script/job
- [ ] Integrate with UI/API as needed

---

*This README is temporary and will be updated as implementation progresses.*
# Modular Meter Data & Alerting Architecture (Temporary README)

## Overview
This document outlines a modular, scalable, and database-efficient architecture for meter data ingestion, alerting, and retention, suitable for up to hundreds of meters.

---

## 1. Data Ingestion Layer
- **Script/Service:** `mqtt_to_db_ingest.py` (or similar)
- **Role:** Receives raw meter data (e.g., via MQTT) and inserts it into the `meter_readings` table.
- **Retention:** All raw readings are kept for 1 month, then deleted by a scheduled cleanup job.

---

## 2. Alert/Evaluation Addon (Modular)
- **Script/Service:** `alert_monitor_addon.py` (runs independently)
- **Role:**
  - Periodically (e.g., every minute) fetches recent readings for all meters from the DB.
  - For each meter/parameter:
    - Calculates a 10-minute rolling average (in Python, not stored in DB).
    - Checks if the average is out of bounds (voltage, current, frequency, etc.).
    - If an alert condition persists for >10 minutes, inserts a row into the `alert_events` table (with start, end, duration, and average value).
    - For power cut, voltage surge, polarity flip, etc., only significant events are stored.
  - Keeps rolling state in memory for efficiency; only writes to DB when a significant event occurs.

---

## 3. Alert Events Table
- **Table:** `alert_events`
- **Role:** Stores only significant alert events (not every threshold crossing).
- **Fields:**
  - id, device_id, meter_id, parameter, alert_type, start_time, end_time, duration, avg_value, value_at_start, value_at_end, extra_info (JSON).

---

## 4. Cleanup/Retention
- **Script/Job:** `cleanup_old_data.py` (or Django management command/cron)
- **Role:** Deletes old data from `meter_readings` (older than 1 month) and optionally from `alert_events` (if you want to limit history).

---

## 5. UI/API Layer
- **Role:** Fetches live and historical data from `meter_readings` and `alert_events` for display.
- **Averages:** For live display, can calculate 10-min averages on the fly from recent readings.

---

## 6. (Optional) Daily Summary Table
- **Table:** `daily_summaries`
- **Role:** Stores per-day metrics (on-hours, load hours, solar durations, etc.) for fast reporting.

---

## Key Principles
- **Minimal DB Writes:** Only significant alert events are stored, not every threshold crossing.
- **Modular:** Ingestion, alerting, cleanup, and UI are all separate scripts/services.
- **Efficient:** 10-min rolling averages for 200+ meters is lightweight for a modern server.
- **Retention:** All raw data is auto-cleaned after 1 month; only key events are kept long-term.

---

## Example Data/Alert Handling
| Data/Alert Type         | Where to Store         | Retention/Trigger                |
|------------------------ |-----------------------|----------------------------------|
| kWh, kW, kVA, etc.      | meter_readings        | 1 month, then delete             |
| Power cut/surge         | alert_events          | Only if >10 min                  |
| Voltage/Current/Freq    | alert_events          | Only if >10 min out of bounds    |
| Polarity flip           | alert_events          | On event                         |
| Solar durations         | meter_readings/daily  | 1 month, or daily summary        |
| Averages                | Calculate on the fly  | N/A                              |

---

## Scaling Notes
- With proper indexing, 10-min rolling averages for 200+ meters is trivial for PostgreSQL and Python.
- For larger scale, batch queries and/or use materialized views.

---

## Next Steps
- [ ] Create `alert_events` table (SQL provided when resuming)
- [ ] Implement alert addon logic (10-min average, event detection, DB insert)
- [ ] Implement cleanup script/job
- [ ] Integrate with UI/API as needed

---

*This README is temporary and will be updated as implementation progresses.*
