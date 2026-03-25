# File Monitoring Database Schema

## Tables

### source_systems
Stores information about monitored source systems.

**Columns:**
- `id` (TEXT, PRIMARY KEY): Unique system identifier (e.g., "PROD_ANALYTICS")
- `name` (TEXT): Human-readable system name
- `description` (TEXT): System purpose and details
- `is_active` (BOOLEAN): Whether system is currently monitored
- `sla_threshold_minutes` (INTEGER): Expected file arrival time in minutes
- `created_at` (TIMESTAMP): Record creation time

**Example:**
```sql
SELECT * FROM source_systems WHERE id = 'PROD_ANALYTICS';
```

### file_arrivals
Tracks all file arrivals from source systems.

**Columns:**
- `id` (INTEGER, PRIMARY KEY): Auto-increment ID
- `source_system_id` (TEXT, FOREIGN KEY): References source_systems.id
- `file_name` (TEXT): Name of arrived file
- `file_path` (TEXT): Full path to file
- `file_size_bytes` (INTEGER): File size in bytes
- `arrival_timestamp` (TIMESTAMP): When file arrived
- `expected_timestamp` (TIMESTAMP): When file was expected
- `status` (TEXT): 'on_time', 'late', or 'missing'
- `created_at` (TIMESTAMP): Record creation time

**Relationships:**
- Many file_arrivals belong to one source_system

**Common Queries:**
```sql
-- Get today's file arrivals for a system
SELECT * FROM file_arrivals 
WHERE source_system_id = 'PROD_ANALYTICS' 
AND DATE(arrival_timestamp) = DATE('now');

-- Count files by status
SELECT status, COUNT(*) as count 
FROM file_arrivals 
WHERE source_system_id = 'PROD_ANALYTICS'
GROUP BY status;
```

### sla_violations
Records SLA violations when files arrive late.

**Columns:**
- `id` (INTEGER, PRIMARY KEY): Auto-increment ID
- `source_system_id` (TEXT, FOREIGN KEY): References source_systems.id
- `file_arrival_id` (INTEGER, FOREIGN KEY): References file_arrivals.id
- `violation_timestamp` (TIMESTAMP): When violation occurred
- `delay_minutes` (INTEGER): How many minutes late
- `severity` (TEXT): 'low', 'medium', or 'high'
- `resolved` (BOOLEAN): Whether issue is resolved
- `created_at` (TIMESTAMP): Record creation time

**Severity Levels:**
- Low: 0-30 minutes late
- Medium: 31-60 minutes late
- High: 60+ minutes late

**Common Queries:**
```sql
-- Get unresolved violations
SELECT * FROM sla_violations 
WHERE source_system_id = 'PROD_ANALYTICS' 
AND resolved = FALSE;

-- Count violations by severity
SELECT severity, COUNT(*) as count 
FROM sla_violations 
WHERE source_system_id = 'PROD_ANALYTICS'
GROUP BY severity;
```
