-- Migration script to add meter_fault_log table to unified PostgreSQL database

CREATE TABLE IF NOT EXISTS meter_fault_log (
    time TIMESTAMP NOT NULL,
    meter_name TEXT NOT NULL,
    fault_true INTEGER NOT NULL,
    v_r_ph_fault INTEGER NOT NULL,
    v_y_ph_fault INTEGER NOT NULL,
    v_b_ph_fault INTEGER NOT NULL,
    a_r_ph_fault INTEGER NOT NULL,
    a_y_ph_fault INTEGER NOT NULL,
    a_b_ph_fault INTEGER NOT NULL,
    pf_ave_fault INTEGER NOT NULL,
    frequency_fault INTEGER NOT NULL,
    v_r_harmonics_fault INTEGER NOT NULL,
    v_y_harmonics_fault INTEGER NOT NULL,
    v_b_harmonics_fault INTEGER NOT NULL,
    a_r_harmonics_fault INTEGER NOT NULL,
    a_y_harmonics_fault INTEGER NOT NULL,
    a_b_harmonics_fault INTEGER NOT NULL,
    watts_total_fault INTEGER NOT NULL
);
