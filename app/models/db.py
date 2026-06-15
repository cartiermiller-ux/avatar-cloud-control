"""
TextNow Factory - 数据库连接与基础操作
支持 MySQL 和 SQLite 双模式，SQLite schema 与 MySQL 完全一致
"""

import logging
from app.config import DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME, DB_TYPE, SQLITE_PATH

log = logging.getLogger(__name__)

# ===================== MySQL 连接池 ====================
_pool = None

def init_pool():
    """初始化数据库连接池"""
    global _pool
    if DB_TYPE == "sqlite":
        log.info("Using SQLite database: %s", SQLITE_PATH)
        return None
    
    try:
        import pymysql
        from dbutils.pooled_db import PooledDB
        
        _pool = PooledDB(
            creator=pymysql,
            maxconnections=20,
            mincached=5,
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            charset='utf8mb4',
            autocommit=True
        )
        log.info("MySQL pool initialized: %s:%s/%s", DB_HOST, DB_PORT, DB_NAME)
        return _pool
    except Exception as e:
        log.error("MySQL pool init failed: %s", e)
        return None


def get_db():
    """获取数据库连接（普通游标）"""
    if DB_TYPE == "sqlite":
        import sqlite3
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    
    if _pool is None:
        init_pool()
    return _pool.connection()


def get_db_dict():
    """获取数据库连接（字典游标）"""
    if DB_TYPE == "sqlite":
        import sqlite3
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    
    if _pool is None:
        init_pool()
    import pymysql
    conn = _pool.connection()
    conn.cursorclass = pymysql.cursors.DictCursor
    return conn


# ===================== 初始化数据库表结构 ====================
def init_schema():
    """初始化数据库表结构"""
    if DB_TYPE == "sqlite":
        init_schema_sqlite()
    else:
        init_schema_mysql()


def init_schema_mysql():
    """初始化 MySQL 表结构"""
    conn = get_db()
    cur = conn.cursor()
    
    try:
        with open("app/models/schema.sql", "r", encoding="utf-8") as f:
            sql = f.read()
        
        statements = sql.split(";")
        for stmt in statements:
            if stmt.strip():
                cur.execute(stmt)
        
        conn.commit()
        log.info("MySQL schema initialized")
    except Exception as e:
        log.error("MySQL schema init failed: %s", e)
        raise
    finally:
        conn.close()


def init_schema_sqlite():
    """初始化 SQLite 表结构（完整版，12张表）"""
    import sqlite3, hashlib, os
    
    required_tables = ['tn_accounts','tn_agents','tn_account_assignment','tn_conversations','tn_messages',
                       'tn_templates','tn_auto_rules','tn_broadcast_task','tn_broadcast_item','tn_settings',
                       'tn_register_task','tn_salesman','tn_ip_pool','tn_account_ip']
    
    # Check if all 12 tables exist
    if os.path.exists(SQLITE_PATH):
        conn = sqlite3.connect(SQLITE_PATH)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        existing = [r[0] for r in cur.fetchall()]
        missing = [t for t in required_tables if t not in existing]
        if not missing:
            conn.close()
            log.info("SQLite already initialized (%d tables, all present)", len(existing))
            return
        log.info("SQLite missing tables: %s - creating them", ','.join(missing))
    else:
        os.makedirs(os.path.dirname(SQLITE_PATH) or '.', exist_ok=True)
        conn = sqlite3.connect(SQLITE_PATH)
        cur = conn.cursor()

    try:
        cur.execute("""CREATE TABLE IF NOT EXISTS tn_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
            password TEXT, sid TEXT, token TEXT, phone_number TEXT, email TEXT,
            idfa TEXT, user_agent TEXT, px_auth TEXT, device_fp TEXT,
            os_version TEXT, client_id TEXT, proxy TEXT, status INTEGER DEFAULT 1,
            health_score INTEGER DEFAULT 100, last_used_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        
        cur.execute("""CREATE TABLE IF NOT EXISTS tn_agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL, nickname TEXT, role TEXT DEFAULT 'agent',
            is_active INTEGER DEFAULT 1, last_login_time TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        
        cur.execute("""CREATE TABLE IF NOT EXISTS tn_account_assignment (
            id INTEGER PRIMARY KEY AUTOINCREMENT, account_id INTEGER NOT NULL,
            agent_id INTEGER NOT NULL, assigned_by INTEGER,
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(account_id, agent_id))""")
        
        cur.execute("""CREATE TABLE IF NOT EXISTS tn_conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT, account_id INTEGER NOT NULL,
            contact_number TEXT NOT NULL, status INTEGER DEFAULT 1,
            last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(account_id, contact_number))""")
        
        cur.execute("""CREATE TABLE IF NOT EXISTS tn_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT, conversation_id INTEGER NOT NULL,
            direction INTEGER NOT NULL, content TEXT, is_auto_reply INTEGER DEFAULT 0,
            read_status INTEGER DEFAULT 0, msg_type TEXT DEFAULT 'text',
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, message_id TEXT)""")
        
        cur.execute("""CREATE TABLE IF NOT EXISTS tn_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            shortcut TEXT, content TEXT, category TEXT,
            is_active INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        
        cur.execute("""CREATE TABLE IF NOT EXISTS tn_auto_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, keywords TEXT,
            template_id INTEGER, priority INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        
        cur.execute("""CREATE TABLE IF NOT EXISTS tn_broadcast_task (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, content TEXT,
            status INTEGER DEFAULT 0, total_count INTEGER DEFAULT 0,
            sent_count INTEGER DEFAULT 0, failed_count INTEGER DEFAULT 0,
            created_by INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP, finished_at TIMESTAMP)""")
        
        cur.execute("""CREATE TABLE IF NOT EXISTS tn_broadcast_item (
            id INTEGER PRIMARY KEY AUTOINCREMENT, task_id INTEGER NOT NULL,
            account_id INTEGER, target_number TEXT, status INTEGER DEFAULT 0,
            retry_count INTEGER DEFAULT 0, error_msg TEXT, sent_at TIMESTAMP)""")
        
        cur.execute("""CREATE TABLE IF NOT EXISTS tn_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT UNIQUE NOT NULL,
            value TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        
        cur.execute("""CREATE TABLE IF NOT EXISTS tn_ip_pool (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ip TEXT NOT NULL,
            port INTEGER NOT NULL, proxy_user TEXT DEFAULT '',
            proxy_pwd TEXT DEFAULT '', area TEXT DEFAULT '',
            ip_type TEXT DEFAULT 'residential', status INTEGER DEFAULT 1,
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, remark TEXT DEFAULT '')""")

        cur.execute("""CREATE TABLE IF NOT EXISTS tn_account_ip (
            id INTEGER PRIMARY KEY AUTOINCREMENT, account_id INTEGER NOT NULL,
            ip_id INTEGER NOT NULL, bind_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(account_id))""")
        
        cur.execute("""CREATE TABLE IF NOT EXISTS tn_register_task (
            id INTEGER PRIMARY KEY AUTOINCREMENT, task_name TEXT NOT NULL,
            total_num INTEGER DEFAULT 0, use_proxy INTEGER DEFAULT 0,
            status INTEGER DEFAULT 0, success_count INTEGER DEFAULT 0,
            failed_count INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")

        cur.execute("""CREATE TABLE IF NOT EXISTS tn_salesman (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            employee_id TEXT UNIQUE NOT NULL, phone TEXT, email TEXT,
            is_active INTEGER DEFAULT 1, account_count INTEGER DEFAULT 0,
            monthly_performance REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")

        # Default data
        admin_hash = hashlib.sha256('admin123'.encode()).hexdigest()
        cur.execute("INSERT OR IGNORE INTO tn_agents (username,password_hash,nickname,role,is_active) VALUES (?,?,?,?,?)",
                   ('admin', admin_hash, 'Admin', 'admin', 1))
        cur.execute("INSERT OR IGNORE INTO tn_templates (name,shortcut,content,category,is_active) VALUES (?,?,?,?,?)",
                   ('Hello', 'hello', 'Hi! How can I help you?', 'General', 1))
        cur.execute("INSERT OR IGNORE INTO tn_templates (name,shortcut,content,category,is_active) VALUES (?,?,?,?,?)",
                   ('Thanks', 'thanks', 'Thank you for your inquiry!', 'General', 1))
        cur.execute("INSERT OR IGNORE INTO tn_settings (key,value) VALUES (?,?)", ('site_name', 'TextNow Factory'))
        cur.execute("INSERT OR IGNORE INTO tn_settings (key,value) VALUES (?,?)", ('max_accounts_per_agent', '10'))
        cur.execute("INSERT OR IGNORE INTO tn_settings (key,value) VALUES (?,?)", ('auto_reply_enabled', '1'))
        
        conn.commit()
        log.info("SQLite schema initialized (14 tables, added tn_ip_pool + tn_account_ip)")
    except Exception as e:
        log.error("SQLite schema init failed: %s", e)
        raise
    finally:
        conn.close()


def init_default_data():
    """初始化默认数据（默认管理员账号）"""
    conn = get_db_dict()
    cur = conn.cursor()
    
    try:
        import hashlib
        
        cur.execute("SELECT id FROM tn_agents WHERE username='admin'")
        if not cur.fetchone():
            pwd_hash = hashlib.sha256("admin123".encode('utf-8')).hexdigest()
            
            if DB_TYPE == "sqlite":
                cur.execute(
                    """INSERT INTO tn_agents (username, password_hash, nickname, role, is_active) 
                       VALUES (?, ?, ?, ?, ?)""",
                    ('admin', pwd_hash, 'Admin', 'admin', 1)
                )
            else:
                cur.execute(
                    """INSERT INTO tn_agents (username, password_hash, nickname, role, is_active) 
                       VALUES (?, ?, ?, ?, ?)""",
                    ('admin', pwd_hash, 'Admin', 'admin', 1)
                )
            
            conn.commit()
            log.info("Default admin created: admin/admin123")
    except Exception as e:
        log.error("Default data init failed: %s", e)
        raise
    finally:
        conn.close()


# ===================== 模块初始化 ====================
init_pool()
init_schema()