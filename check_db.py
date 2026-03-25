import sqlite3

conn = sqlite3.connect('data/file_monitoring.db')
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print("Tables:", tables)

for (table,) in tables:
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    count = cur.fetchone()[0]
    print(f"  {table}: {count} rows")
    if count > 0 and table == 'source_systems':
        cur.execute(f"SELECT * FROM {table} LIMIT 5")
        print("  Sample:", cur.fetchall())

conn.close()
