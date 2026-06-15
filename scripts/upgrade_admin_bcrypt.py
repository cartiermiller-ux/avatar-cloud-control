import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
import sqlite3

conn = sqlite3.connect("data/textnow_factory.db")
cur = conn.cursor()
cur.execute("SELECT id, password_hash FROM tn_agents WHERE username='admin'")
row = cur.fetchone()
if row:
    old_hash = row[1]
    is_bcrypt = old_hash.startswith(("$2b$", "$2a$"))
    if not is_bcrypt:
        try:
            import bcrypt
            new_hash = bcrypt.hashpw(b"admin123", bcrypt.gensalt(12)).decode("utf-8")
            cur.execute("UPDATE tn_agents SET password_hash=? WHERE id=?", (new_hash, row[0]))
            conn.commit()
            print(f"Upgraded admin password to bcrypt: {new_hash[:20]}...")
        except ImportError:
            print("bcrypt not installed, keeping SHA-256")
    else:
        print(f"Admin already using bcrypt: {old_hash[:20]}...")
else:
    print("No admin user found")
conn.close()
