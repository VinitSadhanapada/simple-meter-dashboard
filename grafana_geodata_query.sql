SELECT
    'Meter ' || split_part(meter_name, '.', 2) AS meter_label,
    MAX(location) AS location,
    CASE
        WHEN
            GREATEST(
                MAX(COALESCE(v_r_ph_fault, 0)), MAX(COALESCE(v_y_ph_fault, 0)), MAX(COALESCE(v_b_ph_fault, 0)),
                MAX(COALESCE(a_r_ph_fault, 0)), MAX(COALESCE(a_y_ph_fault, 0)), MAX(COALESCE(a_b_ph_fault, 0)),
                MAX(COALESCE(pf_ave_fault, 0)), MAX(COALESCE(frequency_fault, 0)),
                MAX(COALESCE(v_r_harmonics_fault, 0)), MAX(COALESCE(v_y_harmonics_fault, 0)), MAX(COALESCE(v_b_harmonics_fault, 0)),
                MAX(COALESCE(a_r_harmonics_fault, 0)), MAX(COALESCE(a_y_harmonics_fault, 0)), MAX(COALESCE(a_b_harmonics_fault, 0)),
                MAX(COALESCE(watts_total_fault, 0))
            ) = 1 THEN 1
        ELSE 0
    END AS status,
    TRIM(BOTH ', ' FROM
        CONCAT(
            CASE WHEN GREATEST(MAX(COALESCE(v_r_ph_fault, 0)), MAX(COALESCE(v_y_ph_fault, 0)), MAX(COALESCE(v_b_ph_fault, 0))) = 1 THEN 'Voltage Fault, ' ELSE '' END,
            CASE WHEN GREATEST(MAX(COALESCE(a_r_ph_fault, 0)), MAX(COALESCE(a_y_ph_fault, 0)), MAX(COALESCE(a_b_ph_fault, 0))) = 1 THEN 'Current Fault, ' ELSE '' END,
            CASE WHEN MAX(COALESCE(pf_ave_fault, 0)) = 1 THEN 'Power Factor Fault, ' ELSE '' END,
            CASE WHEN MAX(COALESCE(frequency_fault, 0)) = 1 THEN 'Frequency Fault, ' ELSE '' END,
            CASE WHEN GREATEST(
                MAX(COALESCE(v_r_harmonics_fault, 0)), MAX(COALESCE(v_y_harmonics_fault, 0)), MAX(COALESCE(v_b_harmonics_fault, 0)),
                MAX(COALESCE(a_r_harmonics_fault, 0)), MAX(COALESCE(a_y_harmonics_fault, 0)), MAX(COALESCE(a_b_harmonics_fault, 0))
            ) = 1 THEN 'Harmonics Fault, ' ELSE '' END,
            CASE WHEN MAX(COALESCE(watts_total_fault, 0)) = 1 THEN 'Power Fault, ' ELSE '' END
        )
    ) AS faults,
    10.975588 + 0.01 * SIN(2 * PI() * (ROW_NUMBER() OVER (ORDER BY meter_name)-1) / (SELECT COUNT(DISTINCT meter_name) FROM meterreadings WHERE $__timeFilter(time))) AS latitude,
    76.737517 + 0.01 * COS(2 * PI() * (ROW_NUMBER() OVER (ORDER BY meter_name)-1) / (SELECT COUNT(DISTINCT meter_name) FROM meterreadings WHERE $__timeFilter(time))) AS longitude
FROM meterreadings
WHERE $__timeFilter(time)
GROUP BY meter_name
