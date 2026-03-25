"""
Simulate file transfers for all active source systems.
Creates sample files in each system's watch directory AND records
them directly in the database so the dashboard picks them up immediately.
"""

import os
import random
import sqlite3
import time
from datetime import datetime
from pathlib import Path

DB_PATH = "data/file_monitoring.db"

# File name templates per system type
FILE_TEMPLATES = {
    "SALES":       ["sales_daily_{date}.csv", "sales_report_{date}.xlsx", "revenue_{date}.csv"],
    "INVENTORY":   ["inventory_snapshot_{date}.csv", "stock_levels_{date}.txt", "reorder_{date}.csv"],
    "CUSTOMER":    ["customer_data_{date}.csv", "crm_export_{date}.csv", "contacts_{date}.txt"],
    "FINANCE":     ["gl_entries_{date}.csv", "ap_report_{date}.xlsx", "balance_sheet_{date}.csv"],
    "HR":          ["headcount_{date}.csv", "payroll_{date}.csv", "attendance_{date}.txt"],
    "MARKETING":   ["campaign_{date}.csv", "leads_{date}.csv", "analytics_{date}.xlsx"],
    "LOGISTICS":   ["shipments_{date}.csv", "routes_{date}.txt", "delivery_{date}.csv"],
    "WAREHOUSE":   ["wh_inventory_{date}.csv", "bin_locations_{date}.txt", "picks_{date}.csv"],
    "SUPPLIER":    ["supplier_feed_{date}.csv", "po_status_{date}.csv", "invoices_{date}.txt"],
    "PRODUCT":     ["product_catalog_{date}.csv", "pricing_{date}.csv", "attributes_{date}.txt"],
    "ORDER":       ["orders_{date}.csv", "order_status_{date}.csv", "backorders_{date}.txt"],
    "SHIPPING":    ["shipping_manifest_{date}.csv", "tracking_{date}.txt", "labels_{date}.csv"],
    "RETURNS":     ["returns_{date}.csv", "refunds_{date}.csv", "rma_{date}.txt"],
    "QC":          ["qc_results_{date}.csv", "defects_{date}.txt", "inspection_{date}.csv"],
    "COMPLIANCE":  ["audit_log_{date}.csv", "compliance_report_{date}.txt", "violations_{date}.csv"],
    "ANALYTICS":   ["events_{date}.csv", "metrics_{date}.csv", "kpi_report_{date}.xlsx"],
    "REPORTING":   ["daily_report_{date}.csv", "summary_{date}.txt", "dashboard_{date}.csv"],
    "INTEGRATION": ["api_sync_{date}.csv", "etl_output_{date}.txt", "mapping_{date}.csv"],
    "BACKUP":      ["backup_manifest_{date}.txt", "backup_log_{date}.csv"],
    "ARCHIVE":     ["archive_index_{date}.csv", "archive_log_{date}.txt"],
    "DEFAULT":     ["data_{date}.csv", "export_{date}.txt", "feed_{date}.csv"],
}

def get_templates(system_id: str):
    for key, templates in FILE_TEMPLATES.items():
        if key in system_id.upper():
            return templates
    return FILE_TEMPLATES["DEFAULT"]

def make_csv_content(rows: int = 20) -> str:
    lines = ["id,timestamp,value,status"]
    for i in range(1, rows + 1):
        lines.append(f"{i},{datetime.now().isoformat()},{random.uniform(10, 9999):.2f},OK")
    return "\n".join(lines)

def make_txt_content(system_id: str) -> str:
    return (
        f"System: {system_id}\n"
        f"Generated: {datetime.now().isoformat()}\n"
        f"Records: {random.randint(50, 500)}\n"
        f"Status: SUCCESS\n"
    )

def simulate(num_files_per_system: int = 3, delay_seconds: float = 0.1):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, name, directory_path FROM source_systems WHERE is_active=1")
    systems = cur.fetchall()

    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    total_files = 0
    total_db = 0

    print(f"\n{'='*60}")
    print(f"  Simulating file transfers for {len(systems)} systems")
    print(f"  Files per system: {num_files_per_system}")
    print(f"{'='*60}\n")

    for sys_id, sys_name, dir_path in systems:
        # Skip paths that don't belong to this machine
        if dir_path.startswith("/data/") or dir_path == "C:\\data\\test1":
            print(f"  [SKIP] {sys_id} — path not on this machine")
            continue

        watch_dir = Path(dir_path)
        watch_dir.mkdir(parents=True, exist_ok=True)

        templates = get_templates(sys_id)
        now = datetime.now()

        for i in range(num_files_per_system):
            template = templates[i % len(templates)]
            filename = template.format(date=f"{date_str}_{i+1}")
            filepath = watch_dir / filename
            file_size = random.randint(1024, 512000)  # 1KB – 500KB

            # Write the actual file
            if filename.endswith(".csv") or filename.endswith(".xlsx"):
                filepath.write_text(make_csv_content(), encoding="utf-8")
            else:
                filepath.write_text(make_txt_content(sys_id), encoding="utf-8")
            total_files += 1

            # Record in database directly
            cur.execute(
                """INSERT INTO file_arrivals
                   (source_system_id, filename, file_path, file_size_bytes,
                    arrival_timestamp, processed_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    sys_id,
                    filename,
                    str(filepath),
                    file_size,
                    now.isoformat(),
                    now.isoformat(),
                ),
            )
            total_db += 1

            if delay_seconds:
                time.sleep(delay_seconds)

        print(f"  [OK] {sys_id:20s} -> {num_files_per_system} files written + recorded in DB")

    conn.commit()
    conn.close()

    print(f"\n{'='*60}")
    print(f"  Done. {total_files} files created, {total_db} records inserted into DB.")
    print(f"  Refresh the dashboard to see the new arrivals.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    simulate(num_files_per_system=3, delay_seconds=0.1)
