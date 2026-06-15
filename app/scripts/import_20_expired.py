"""
导入20个已过期测试账号到 SQLite 数据库
"""
import json
import sqlite3
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SQLITE_PATH

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'textnow_factory.db')
INPUT_FILE = r'C:\Users\carti\Desktop\20.txt'

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    imported = 0
    skipped = 0
    errors = []

    for i, line in enumerate(lines):
        try:
            data = json.loads(line)
        except json.JSONDecodeError as e:
            errors.append(f"Line {i+1}: JSON parse error - {e}")
            continue

        phone = data.get('phone', '')
        username = data.get('username', '')
        email = data.get('email', '')

        # 检查是否已存在（按手机号或用户名）
        cur.execute("SELECT id FROM tn_accounts WHERE phone_number=? OR username=?", (phone, username))
        if cur.fetchone():
            print(f"[跳过] 已存在: {phone} ({username})")
            skipped += 1
            continue

        # 提取 os_version 和 device_model 从 user_agent
        ua = data.get('User-Agent', '')
        device_model = data.get('X-PX-DEVICE-MODEL', '')

        try:
            cur.execute("""
                INSERT INTO tn_accounts (
                    username, password, sid, token, phone_number, email,
                    idfa, user_agent, px_auth, device_fp,
                    os_version, client_id, proxy, status, health_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                username,
                '',  # password - 测试账号无密码字段
                '',  # sid
                data.get('X-PX-AUTHORIZATION', ''),  # token/px_auth
                phone,
                email,
                data.get('IDFA', ''),
                ua,
                data.get('X-PX-AUTHORIZATION', ''),  # px_auth
                data.get('X-PX-DEVICE-FP', ''),
                data.get('X-PX-OS-VERSION', '') + ' (' + device_model + ')',
                data.get('clientId', ''),
                '',  # proxy
                2,   # status=2 表示已过期/异常
                0    # health_score=0 过期号健康度为0
            ))
            imported += 1
            print(f"[导入] #{imported} {phone} | {email} | @{username}")
        except Exception as e:
            errors.append(f"Line {i+1} ({phone}): DB error - {e}")

    conn.commit()
    conn.close()

    print(f"\n{'='*50}")
    print(f"完成！导入: {imported}, 跳过: {skipped}, 错误: {len(errors)}")
    if errors:
        print("\n错误详情:")
        for err in errors:
            print(f"  - {err}")

if __name__ == '__main__':
    main()
