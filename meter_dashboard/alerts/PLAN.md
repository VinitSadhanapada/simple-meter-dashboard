# Alerts App Implementation Plan

## 1. Goals
Provide a lightweight, maintainable alert evaluation pipeline for ~15 energy meters without requiring Celery/Redis initially, while keeping an easy migration path to an asynchronous architecture later.

## 2. Scope (Phase 1)
- Track *current* active alerts for threshold breaches over a 10‑minute rolling window.
- Evaluate simple numeric thresholds (e.g. voltage within [210, 250]).
- Store active alerts in `ActiveAlert` table (no historical event log yet).
- Management command (`check_meter_alerts`) runs periodically via cron/systemd.
- API/Dashboard can read active alerts directly from DB.

Out-of-scope for Phase 1:
- Redis TTL state
- Celery tasks or beat scheduling
- Notification dispatch (email/SMS/WebSocket)
- Complex correlation rules (rate-of-change, multi-device dependencies)

## 3. Data Model (Initial)
`ActiveAlert` fields:
- `meter_id` (int; later ForeignKey to `Meter`)
- `code` (string; rule identifier, e.g. `voltage_out_of_range`)
- `value` (float; representative aggregated metric like average voltage)
- `first_seen` (timestamp) — set at creation
- `last_updated` (auto)
Unique key: (`meter_id`, `code`) ensures single row per active rule per meter.

Future model additions:
- `AlertEvent` for historical activation/clear logs
- `AlertRuleConfig` for per-meter dynamic thresholds

## 4. Evaluation Logic
For each meter:
1. Query readings in `[now - 10m, now]`.
2. Compute aggregates: avg/min/max voltage (extendable set).
3. Determine if any aggregate violates configured threshold.
4. If violation: upsert `ActiveAlert` with current aggregate value.
5. Else: delete existing `ActiveAlert` rows for that rule.

Edge cases:
- No readings in window: optionally clear existing alert or leave unchanged (decision: Phase 1 — leave unchanged, so transient ingestion gaps don’t auto-clear).
- Erroneous readings/outliers: (Phase 2 — add smoothing or trimmed mean).
- Duplicate readings: rely on DB constraints upstream.

## 5. Configuration Strategy
Phase 1: static dictionary in command module.
Phase 2: table-driven thresholds; allow editing via admin or config file.
Phase 3: complex rule DSL or JSON definitions.

## 6. Scheduling & Operations
Initial run path: system cron every 1–2 minutes.
Example cron line (run inside project venv):
```
*/2 * * * * /path/to/venv/bin/python /path/to/manage.py check_meter_alerts >> /var/log/meter_alerts.log 2>&1
```
Later migration: Celery beat — convert logic to a shared task `evaluate_alerts_all_meters.delay()`.

## 7. Migration Path to Celery/Redis (Optional Future)
- Introduce Redis service in `docker-compose.yml`.
- Add Celery worker & beat services.
- Split evaluation into per-meter tasks for parallelism.
- Store transient state in Redis keys (`alert:{meter}:{code}`) with TTL; DB rows only for activation/clear events.
- Add notification tasks triggered on activation events.

## 8. API & UI Integration (Future)
Add endpoint: `GET /api/alerts/active` returning JSON list of active alerts.
Response shape (proposal):
```
[
  {"meter_id": 12, "code": "voltage_out_of_range", "value": 255.3, "first_seen": "2025-11-20T09:10:31Z"}
]
```
Dashboard: highlight affected meters, include duration (`now - first_seen`).

## 9. Testing Strategy
- Unit: function for threshold evaluation given synthetic readings list.
- Integration: create mock readings in test DB, run command, assert `ActiveAlert` rows.
- Edge tests: boundary at exactly low/high threshold, empty window, clearing logic.

## 10. Performance Considerations
For 15 meters, naive per‑meter queries acceptable. Optimize later by single aggregate query:
```
SELECT meter_id, AVG(voltage) AS avg_v, MIN(voltage) AS min_v, MAX(voltage) AS max_v
FROM meter_readings
WHERE timestamp >= now() - interval '10 minutes'
GROUP BY meter_id;
```
Then apply thresholds in Python with one pass.

## 11. Incremental Task List
Phase 1 Tasks:
1. (DONE) Create `alerts` app skeleton.
2. Add `ActiveAlert` model; migrate after enabling app in `INSTALLED_APPS`.
3. Implement real ORM aggregates in command.
4. Wire `Meter` ForeignKey (replace `meter_id` int).
5. Add simple API endpoint for active alerts.
6. Add cron instructions to deployment docs.
7. Basic tests.

Phase 2 Tasks:
- Dynamic per-meter thresholds.
- Historical `AlertEvent` log.
- Simple web UI panel.

Phase 3 Tasks:
- Celery/Redis migration.
- Notification dispatch.
- Advanced rule DSL & grouping.

## 12. Acceptance Criteria (Phase 1)
- Running command inserts an alert row when any meter’s average voltage leaves [210, 250].
- Clearing occurs when average returns within bounds.
- Command exits successfully with summary message.
- API endpoint returns current active alerts in < 150 ms locally.
- Tests cover activation and clearing.

## 13. Open Questions
- Exact reading model field names? (Need to inspect `meter_readings` app.)
- Voltage source field name? (Assumed `voltage`.)
- Desired behavior on missing data window? Keep vs clear? (Currently: keep.)
- Threshold per meter or global? (Phase 1: global.)

## 14. Next Immediate Steps
Await confirmation before:
- Adding app to `INSTALLED_APPS` & running migrations.
- Implementing real query logic & tests.

---
This plan is staged to minimize risk while enabling future scalability. Review and confirm adjustments before moving to implementation steps.
