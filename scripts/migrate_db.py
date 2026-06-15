import sqlite3
conn = sqlite3.connect("data/textnow_factory.db")
cur = conn.cursor()

# Add tn_account_assign_log table
cur.execute("""CREATE TABLE IF NOT EXISTS tn_account_assign_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    old_salesman_id INTEGER,
    new_salesman_id INTEGER,
    operate_type TEXT DEFAULT '',
    operator_id INTEGER,
    operate_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")

# Add missing columns to tn_conversations
migrations = [
    "ALTER TABLE tn_conversations ADD COLUMN last_message TEXT DEFAULT ''",
    "ALTER TABLE tn_conversations ADD COLUMN unread INTEGER DEFAULT 0",
    "ALTER TABLE tn_conversations ADD COLUMN salesman_id INTEGER",
    "ALTER TABLE tn_conversations ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    "ALTER TABLE tn_accounts ADD COLUMN salesman_id INTEGER",
]
for sql in migrations:
    try:
        cur.execute(sql)
    except Exception as e:
        print(f"Skip: {e}")

conn.commit()

# Verify
tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print(f"Tables: {len(tables)}")
for t in tables:
    print(t[0])

cols = cur.execute("PRAGMA table_info(tn_conversations)").fetchall()
print("tn_conversations columns:")
for c in cols:
    print(f"  {c[1]} ({c[2]})")

cols = cur.execute("PRAGMA table_info(tn_accounts)").fetchall()
print("tn_accounts columns:")
for c in cols:
    print(f"  {c[1]} ({c[2]})")

conn.close()
print("Migration done")