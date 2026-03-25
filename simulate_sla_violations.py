"""
Negative Testing Script — SLA Violations & Priority Simulation
==============================================================
Injects realistic SLA violations across systems with HIGH / MEDIUM / LOW
priority levels so the dashboard shows a mix of healthy and degraded systems.

Violation scenarios injected:
  CRITICAL  — file never arrived (missing file)
  HIGH      — arrived 3+ hours late
  MEDIUM    — arrived 1-2 hours late
  LOW       — arrived slightly outside window (<30 min)

Also inserts late file_arrivals records to back the violations with real data.

Run:  python simulate_sla_violations.py
"""

import random
import sqlite3
from datetime import date, datetime, timedelta

DB_PATH = "data/file_monitoring.db"

# ── Violation scenarios ────────────────────────────────────────────────────────
# Each entry: (violation_type, severity, expected_template, actual_template, description)
SCENARIOS = {
    "critical": [
        ("MISSING_FILE",    "critical", "1 file by 08:00",  "0 files received",   "No files arrived all day"),
        ("MISSING_FILE",    "critical", "3 files by 09:00",  "0 files received",  "Complete data feed failure"),
    ],
    "high": [
        ("LATE_ARRIVAL",    "high",     "08:00",  "11:47",  "File arrived 3h 47m late"),
        ("LATE_ARRIVAL",    "high",     "09:00",  "13:22",  "File arrived 4h 22m late"),
        ("FILE_COUNT_LOW",  "high",     "10 files", "2 files", "Only 20% of expected files received"),
    ],
    "medium": [
        ("LATE_ARRIVAL",    "medium",   "08:00",  "09:35",  "File arrived 1h 35m late"),
        ("LATE_ARRIVAL",    "medium",   "10:00",  "11:48",  "File arrived 1h 48m late"),
        ("FILE_COUNT_LOW",  "medium",   "10 files", "6 files", "60% of expected files received"),
    ],
    "low": [
        ("LATE_ARRIVAL",    "low",      "08:00",  "08:22",  "File arrived 22 min late"),
        ("LATE_ARRIVAL",    "low",      "10:00",  "10:18",  "File arrived 18 min late"),
        ("FILE_COUNT_LOW",  "low",      "10 files", "8 files", "80% of expected files received"),
    ],
}

# Which systems get which severity (spread across the 20 systems)
SYSTEM_VIOLATION_MAP = {
    # CRITICAL — 2 systems completely broken
    "PROD_INTEGRATION": ["critical", "high"],
    "PROD_COMPLIANCE":  ["critical", "medium"],

    # HIGH — 4 systems with serious issues
    "PROD_FINANCE":     ["high", "medium"],
    "PROD_ORDER":       ["high", "low"],
    "PROD_SHIPPING":    ["high", "medium"],
    "PROD_RETURNS":     ["high", "low"],

    # MEDIUM — 5 systems with moderate issues
    "PROD_HR":          ["medium", "low"],
    "PROD_LOGISTICS":   ["medium", "low"],
    "PROD_WAREHOUSE":   ["medium"],
    "PROD_SUPPLIER":    ["medium", "low"],
    "PROD_QC":          ["medium"],

    # LOW — 4 systems with minor issues
    "PROD_MARKETING":   ["low"],
    "PROD_REPORTING":   ["low"],
    "PROD_PRODUCT":     ["low"],
    "PROD_BACKUP":      ["low"],

    # Healthy — remaining systems get no violations
    # PROD_SALES, PROD_INVENTORY, PROD_CUSTOMER, PROD_ANALYTICS, PROD_ARCHIVE
}

# Priority label derived from worst severity
PRIORITY_MAP = {
    "critical": "HIGH",
    "high":     "HIGH",
    "medium":   "MEDIUM",
    "low":      "LOW",
}


def get_active_systems(cur):
    cur.execute("SELECT id FROM source_systems WHERE is_active=1")
    return [r[0] for r in cur.fetchall()]


def clear_existing_test_violations(cur):
    """Remove violations we inserted previously (keeps real ones)."""
    cur.execute(
        "DELETE FROM sla_violations WHERE expected_value LIKE '%files%' "
        "OR expected_value LIKE '%:00%' OR actual_value LIKE '%files%' "
        "OR actual_value LIKE '%:00%' OR actual_value LIKE '%received%'"
    )
    print(f"  Cleared {cur.rowcount} previous test violations")


def insert_violations(cur, system_id: str, severities: list, today: date):
    inserted = 0
    for sev in severities:
        scenarios = SCENARIOS.get(sev, [])
        # Pick 1-2 scenarios per severity level
        picks = random.sample(scenarios, min(len(scenarios), random.randint(1, 2)))
        for vtype, severity, expected, actual, _ in picks:
            # Spread violations over last 7 days
            vdate = today - timedelta(days=random.randint(0, 6))
            cur.execute(
                """INSERT INTO sla_violations
                   (source_system_id, violation_date, violation_type,
                    expected_value, actual_value, severity, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (system_id, vdate.isoformat(), vtype,
                 expected, actual, severity, datetime.utcnow().isoformat()),
            )
            inserted += 1
    return inserted


def insert_late_arrivals(cur, system_id: str, severities: list, today: date):
    """Insert file_arrivals records with late timestamps to back the violations."""
    inserted = 0
    # Expected arrival is 08:00; late arrivals are offset by severity
    delay_map = {"critical": None, "high": 240, "medium": 100, "low": 25}

    for sev in severities:
        delay_min = delay_map.get(sev)
        if delay_min is None:
            # critical = missing, no file arrival record
            continue
        for d in range(min(3, 7)):
            arr_date = today - timedelta(days=d)
            # Base expected: 08:00 + delay
            arr_time = datetime(
                arr_date.year, arr_date.month, arr_date.day, 8, 0, 0
            ) + timedelta(minutes=delay_min + random.randint(-5, 15))

            fname = f"late_{system_id.lower()}_{arr_date.isoformat()}_d{d}.csv"
            fpath = f"/data/watch/{system_id.lower()}/{fname}"
            fsize = random.randint(2048, 204800)

            cur.execute(
                """INSERT INTO file_arrivals
                   (source_system_id, filename, file_path, file_size_bytes,
                    arrival_timestamp, processed_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (system_id, fname, fpath, fsize,
                 arr_time.isoformat(), datetime.utcnow().isoformat()),
            )
            inserted += 1
    return inserted


def update_sla_scores(cur, system_id: str, severities: list, today: date):
    """
    Insert/update sla_scores so the dashboard shows degraded scores.
    Score formula: start at 100, deduct per violation severity.
    """
    deductions = {"critical": 40, "high": 20, "medium": 10, "low": 5}
    total_deduction = sum(deductions.get(s, 0) for s in severities)
    score = max(0.0, 100.0 - total_deduction)

    for d in range(7):
        score_date = today - timedelta(days=d)
        # Vary score slightly per day
        daily_score = max(0.0, score + random.uniform(-3, 3))
        total_checks = random.randint(8, 12)
        failed = max(1, int(total_checks * (1 - daily_score / 100)))
        passed = total_checks - failed

        # Upsert: delete existing then insert
        cur.execute(
            "DELETE FROM sla_scores WHERE source_system_id=? AND score_date=?",
            (system_id, score_date.isoformat()),
        )
        cur.execute(
            """INSERT INTO sla_scores
               (source_system_id, score_date, score, total_checks, passed_checks,
                calculated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (system_id, score_date.isoformat(), round(daily_score, 2),
             total_checks, passed, datetime.utcnow().isoformat()),
        )


def print_summary(results):
    print(f"\n{'='*65}")
    print(f"  {'SYSTEM':<25} {'PRIORITY':<10} {'VIOLATIONS':>10} {'LATE FILES':>10}")
    print(f"  {'-'*25} {'-'*10} {'-'*10} {'-'*10}")
    for sys_id, priority, viols, lates in sorted(results, key=lambda x: x[1]):
        print(f"  {sys_id:<25} {priority:<10} {viols:>10} {lates:>10}")
    print(f"{'='*65}")


def simulate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    active = get_active_systems(cur)
    today = date.today()

    print(f"\n{'='*65}")
    print(f"  SLA Negative Testing — injecting violations")
    print(f"  Active systems: {len(active)}")
    print(f"  Date: {today}")
    print(f"{'='*65}\n")

    # Check sla_scores table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sla_scores'")
    has_scores_table = cur.fetchone() is not None

    clear_existing_test_violations(cur)

    results = []
    for system_id in active:
        severities = SYSTEM_VIOLATION_MAP.get(system_id)
        if not severities:
            # Healthy system — ensure good score
            if has_scores_table:
                for d in range(7):
                    score_date = today - timedelta(days=d)
                    cur.execute(
                        "DELETE FROM sla_scores WHERE source_system_id=? AND score_date=?",
                        (system_id, score_date.isoformat()),
                    )
                    cur.execute(
                        """INSERT INTO sla_scores
                           (source_system_id, score_date, score, total_checks,
                            passed_checks, calculated_at)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (system_id, score_date.isoformat(),
                         round(random.uniform(95, 100), 2),
                         10, 10, datetime.utcnow().isoformat()),
                    )
            results.append((system_id, "HEALTHY", 0, 0))
            continue

        # Worst severity determines priority label
        worst = severities[0]
        priority = PRIORITY_MAP.get(worst, "LOW")

        viols = insert_violations(cur, system_id, severities, today)
        lates = insert_late_arrivals(cur, system_id, severities, today)
        if has_scores_table:
            update_sla_scores(cur, system_id, severities, today)

        results.append((system_id, priority, viols, lates))
        print(f"  [{priority:<6}] {system_id:<25} {viols} violations, {lates} late arrivals")

    conn.commit()
    conn.close()

    print_summary(results)
    print("\n  Refresh the dashboard to see SLA violations and priority indicators.")
    print("  Tip: Click a system card → SLA Metrics tab to see violation details.\n")


if __name__ == "__main__":
    simulate()
