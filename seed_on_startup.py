"""Seed database with 20 production-like source systems on container startup."""

import sqlite3
import os
import random
from datetime import datetime, timedelta

SYSTEMS = [
    ("PROD_SALES",       "Production Sales System",       "/data/sources/sales",       "09:00:00", 30,  5),
    ("PROD_INVENTORY",   "Production Inventory System",   "/data/sources/inventory",   "10:00:00", 60,  3),
    ("PROD_CUSTOMER",    "Production Customer System",    "/data/sources/customer",    "08:30:00", 45, 10),
    ("PROD_FINANCE",     "Production Finance System",     "/data/sources/finance",     "07:00:00", 15, 20),
    ("PROD_HR",          "Production HR System",          "/data/sources/hr",          "11:00:00", 120, 2),
    ("PROD_MARKETING",   "Production Marketing System",   "/data/sources/marketing",   "14:00:00", 90,  5),
    ("PROD_LOGISTICS",   "Production Logistics System",   "/data/sources/logistics",   "06:00:00", 30, 15),
    ("PROD_WAREHOUSE",   "Production Warehouse System",   "/data/sources/warehouse",   "12:00:00", 60,  8),
    ("PROD_SUPPLIER",    "Production Supplier System",    "/data/sources/supplier",    "09:30:00", 45, 12),
    ("PROD_PRODUCT",     "Production Product System",     "/data/sources/product",     "10:30:00", 60,  6),
    ("PROD_ORDER",       "Production Order System",       "/data/sources/order",       "08:00:00", 30, 25),
    ("PROD_SHIPPING",    "Production Shipping System",    "/data/sources/shipping",    "13:00:00", 60, 10),
    ("PROD_RETURNS",     "Production Returns System",     "/data/sources/returns",     "15:00:00", 90,  3),
    ("PROD_QC",          "Production Quality Control",    "/data/sources/qc",          "11:30:00", 45,  7),
    ("PROD_COMPLIANCE",  "Production Compliance System",  "/data/sources/compliance",  "16:00:00", 120, 2),
    ("PROD_ANALYTICS",   "Production Analytics System",   "/data/sources/analytics",   "05:00:00", 30, 15),
    ("PROD_REPORTING",   "Production Reporting System",   "/data/sources/reporting",   "17:00:00", 60,  5),
    ("PROD_INTEGRATION", "Production Integration System", "/data/sources/integration", "12:30:00", 90,  8),
    ("PROD_BACKUP",      "Production Backup System",      "/data/sources/backup",      "23:00:00", 60,  1),
    ("PROD_ARCHIVE",     "Production Archive System",     "/data/sources/archive",     "22:00:00", 120, 1),
]

VIOLATION_MAP = {
    "PROD_INTEGRATION": [("critical", "MISSING_FILE",   "3 files by 09:00", "0 files received"),
                         ("high",     "LATE_ARRIVAL",   "09:00", "13:22")],
    "PROD_COMPLIANCE":  [("critical", "MISSING_FILE",   "1 file by 08:00",  "0 files received"),
                         ("medium",   "LATE_ARRIVAL",   "08:00", "09:35")],
    "PROD_FINANCE":     [("high",     "LATE_ARRIVAL",   "08:00", "11:47"),
                         ("medium",   "FILE_COUNT_LOW", "10 files", "6 files")],
    "PROD_ORDER":       [("high",     "LATE_ARRIVAL",   "09:00", "13:22"),
                         ("low",      "LATE_ARRIVAL",   "10:00", "10:18")],
    "PROD_SHIPPING":    [("high",     "FILE_COUNT_LOW", "10 files", "2 files"),
                         ("medium",   "LATE_ARRIVAL",   "10:00", "11:48")],
    "PROD_RETURNS":     [("high",     "LATE_ARRIVAL",   "08:00", "11:47"),
                         ("low",      "FILE_COUNT_LOW", "10 files", "8 files")],
    "PROD_HR":          [("medium",   "LATE_ARRIVAL",   "08:00", "09:35"),
                         ("low",      "LATE_ARRIVAL",   "10:00", "10:18")],
    "PROD_LOGISTICS":   [("medium",   "FILE_COUNT_LOW", "10 files", "6 files"),
                         ("low",      "LATE_ARRIVAL",   "08:00", "08:22")],
    "PROD_WAREHOUSE":   [("medium",   "LATE_ARRIVAL",   "10:00", "11:48")],
    "PROD_SUPPLIER":    [("medium",   "FILE_COUNT_LOW", "10 files", "6 files"),
                         ("low",      "LATE_ARRIVAL",   "10:00", "10:18")],
    "PROD_QC":          [("medium",   "LATE_ARRIVAL",   "08:00", "09:35")],
    "PROD_MARKETING":   [("low",      "LATE_ARRIVAL",   "08:00", "08:22")],
    "PROD_REPORTING":   [("low",      "FILE_COUNT_LOW", "10 files", "8 files")],
    "PROD_PRODUCT":     [("low",      "LATE_ARRIVAL",   "10:00", "10:18")],
    "PROD_BACKUP":      [("low",      "LATE_ARRIVAL",   "08:00", "08:22")],
}

SEVERITY_DEDUCTIONS = {"critical": 40, "high": 20, "medium": 10, "low": 5}
HEALTHY_SYSTEMS = {"PROD_SALES", "PROD_INVENTORY", "PROD_CUSTOMER", "PROD_ANALYTICS", "PROD_ARCHIVE"}


def seed_database():
    db = os.environ.get("DATABASE_PATH", "/tmp/file_monitoring.db")
    conn = sqlite3.connect(db)
    conn.execute("PRAGMA journal_mode=WAL")

    conn.executescript("""
    CREATE TABLE IF NOT EXISTS source_systems (
        id VARCHAR(50) PRIMARY KEY, name VARCHAR(255) NOT NULL,
        directory_path VARCHAR(500) NOT NULL, is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS sla_definitions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, source_system_id VARCHAR(50),
        expected_arrival_time TIME, expected_arrival_window_minutes INTEGER,
        minimum_files_per_day INTEGER, weight DECIMAL(3,2) DEFAULT 1.0,
        effective_from DATE NOT NULL, effective_to DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS sla_violations (
        id INTEGER PRIMARY KEY AUTOINCREMENT, source_system_id VARCHAR(50),
        violation_date DATE NOT NULL, violation_type VARCHAR(50) NOT NULL,
        expected_value VARCHAR(100), actual_value VARCHAR(100),
        severity VARCHAR(20) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS file_arrivals (
        id INTEGER PRIMARY KEY AUTOINCREMENT, source_system_id VARCHAR(50),
        filename VARCHAR(500) NOT NULL, file_path VARCHAR(1000) NOT NULL,
        arrival_timestamp TIMESTAMP NOT NULL, file_size_bytes BIGINT NOT NULL,
        checksum VARCHAR(64), processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS sla_scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT, source_system_id VARCHAR(50),
        score_date DATE NOT NULL, score DECIMAL(5,2) NOT NULL,
        total_checks INTEGER NOT NULL, passed_checks INTEGER NOT NULL,
        calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS dashboard_cache (
        cache_key VARCHAR(255) PRIMARY KEY, cache_value TEXT NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS configuration_audit (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id VARCHAR(100),
        action VARCHAR(50) NOT NULL, entity_type VARCHAR(50) NOT NULL,
        entity_id VARCHAR(100), old_value TEXT, new_value TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
    """)

    cur = conn.execute("SELECT COUNT(*) FROM source_systems")
    if cur.fetchone()[0] >= 20:
        print("Database already seeded with 20 systems, skipping")
        conn.close()
        return

    conn.execute("DELETE FROM sla_scores")
    conn.execute("DELETE FROM sla_violations")
    conn.execute("DELETE FROM file_arrivals")
    conn.execute("DELETE FROM sla_definitions")
    conn.execute("DELETE FROM source_systems")
    conn.commit()

    conn.executemany(
        "INSERT INTO source_systems (id,name,directory_path,is_active) VALUES (?,?,?,1)",
        [(s[0], s[1], s[2]) for s in SYSTEMS])
    conn.executemany(
        "INSERT INTO sla_definitions "
        "(source_system_id,expected_arrival_time,expected_arrival_window_minutes,"
        "minimum_files_per_day,weight,effective_from) VALUES (?,?,?,?,1.0,'2024-01-01')",
        [(s[0], s[3], s[4], s[5]) for s in SYSTEMS])
    conn.commit()
    print(f"Inserted {len(SYSTEMS)} source systems")

    now = datetime.utcnow()
    rows = []
    for s in SYSTEMS:
        sid, mn = s[0], s[5]
        mx = mn + random.randint(3, 8)
        arr_hour = int(s[3].split(":")[0])
        for d in range(60, -1, -1):
            day = now - timedelta(days=d)
            for i in range(random.randint(mn, mx)):
                offset = random.randint(-30, 30)
                ts = day.replace(hour=arr_hour, minute=0, second=0, microsecond=0) + \
                     timedelta(minutes=offset + i * 3)
                rows.append((sid,
                              f"{sid.lower()}_{d}_{i}.csv",
                              f"/data/{sid.lower()}/{sid.lower()}_{d}_{i}.csv",
                              ts.strftime("%Y-%m-%d %H:%M:%S"),
                              random.randint(2048, 10485760)))
    conn.executemany(
        "INSERT INTO file_arrivals "
        "(source_system_id,filename,file_path,arrival_timestamp,file_size_bytes) "
        "VALUES (?,?,?,?,?)", rows)
    conn.commit()
    print(f"Inserted {len(rows)} file arrivals")

    viols = []
    for sid, scenarios in VIOLATION_MAP.items():
        for d in range(45, 0, -random.randint(2, 5)):
            vdate = (now - timedelta(days=d)).strftime("%Y-%m-%d")
            sev, vtype, exp, act = random.choice(scenarios)
            viols.append((sid, vdate, vtype, exp, act, sev))
    conn.executemany(
        "INSERT INTO sla_violations "
        "(source_system_id,violation_date,violation_type,expected_value,actual_value,severity) "
        "VALUES (?,?,?,?,?,?)", viols)

    for s in SYSTEMS:
        sid = s[0]
        sevs = [v[0] for v in VIOLATION_MAP.get(sid, [])]
        base_score = 100.0 - sum(SEVERITY_DEDUCTIONS.get(sv, 0) for sv in sevs)
        if sid in HEALTHY_SYSTEMS:
            base_score = random.uniform(96, 100)
        for d in range(30):
            sd = (now - timedelta(days=d)).strftime("%Y-%m-%d")
            score = max(0.0, base_score + random.uniform(-3, 3))
            total = random.randint(8, 12)
            failed = max(0, int(total * (1 - score / 100)))
            conn.execute(
                "INSERT INTO sla_scores "
                "(source_system_id,score_date,score,total_checks,passed_checks,calculated_at) "
                "VALUES (?,?,?,?,?,?)",
                (sid, sd, round(score, 2), total, total - failed, now.isoformat()))

    conn.commit()
    conn.close()
    print(f"Inserted {len(viols)} violations and SLA scores. Seed complete!")


if __name__ == "__main__":
    seed_database()
