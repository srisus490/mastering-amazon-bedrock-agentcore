# Common Query Examples

## Health Checks

**Q: How is PROD_ANALYTICS doing?**
**A:** Query the file_arrivals table for today's data:
```sql
SELECT 
    COUNT(*) as total_files,
    SUM(CASE WHEN status = 'on_time' THEN 1 ELSE 0 END) as on_time,
    SUM(CASE WHEN status = 'late' THEN 1 ELSE 0 END) as late
FROM file_arrivals
WHERE source_system_id = 'PROD_ANALYTICS'
AND DATE(arrival_timestamp) = DATE('now');
```

**Q: Show me all systems**
**A:** Query the source_systems table:
```sql
SELECT id, name, is_active, sla_threshold_minutes
FROM source_systems
WHERE is_active = TRUE
ORDER BY name;
```

## SLA Violations

**Q: Show me violations from last week**
**A:** Query sla_violations with date filter:
```sql
SELECT 
    sv.source_system_id,
    sv.violation_timestamp,
    sv.delay_minutes,
    sv.severity
FROM sla_violations sv
WHERE sv.violation_timestamp >= DATE('now', '-7 days')
ORDER BY sv.violation_timestamp DESC;
```

**Q: Which system has the most violations?**
**A:** Aggregate violations by system:
```sql
SELECT 
    source_system_id,
    COUNT(*) as violation_count
FROM sla_violations
WHERE violation_timestamp >= DATE('now', '-30 days')
GROUP BY source_system_id
ORDER BY violation_count DESC
LIMIT 5;
```

## Trends

**Q: What's the trend for PROD_SALES?**
**A:** Get daily file counts:
```sql
SELECT 
    DATE(arrival_timestamp) as date,
    COUNT(*) as file_count
FROM file_arrivals
WHERE source_system_id = 'PROD_SALES'
AND arrival_timestamp >= DATE('now', '-30 days')
GROUP BY DATE(arrival_timestamp)
ORDER BY date;
```

## Comparisons

**Q: Compare PROD_ANALYTICS and PROD_SALES**
**A:** Get metrics for both systems:
```sql
SELECT 
    source_system_id,
    COUNT(*) as total_files,
    AVG(CASE WHEN status = 'on_time' THEN 100.0 ELSE 0.0 END) as on_time_percentage
FROM file_arrivals
WHERE source_system_id IN ('PROD_ANALYTICS', 'PROD_SALES')
AND arrival_timestamp >= DATE('now', '-7 days')
GROUP BY source_system_id;
```
