import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
app = create_app()
with app.test_client() as c:
    # Wrong password should return 200 with error message in page
    r = c.post("/login", data={"username": "admin", "password": "wrongpass"}, follow_redirects=True)
    print(f"Wrong password status: {r.status_code}")
    has_error = "error" in r.data.decode("utf-8").lower()
    print(f"Has error in page: {has_error}")

    # Correct login
    r = c.post("/login", data={"username": "admin", "password": "admin123"}, follow_redirects=True)
    print(f"Correct login status: {r.status_code}")

    # Verify bcrypt upgrade happened
    import sqlite3
    conn = sqlite3.connect("data/textnow_factory.db")
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM tn_agents WHERE username='admin'")
    row = cur.fetchone()
    hash_val = row[0]
    is_bcrypt = hash_val.startswith("$2b$") or hash_val.startswith("$2a$")
    print(f"Admin password hash starts with: {hash_val[:20]}...")
    print(f"Is bcrypt: {is_bcrypt}")
    conn.close()

print("Auth security tests completed")