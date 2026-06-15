"""
TextNow Factory - 集中配置管理
所有配置项统一在此定义，支持环境变量覆盖
"""

import os

# ==================== 代理配置 ====================
PROXY = {
    "http": "socks5h://127.0.0.1:1080",
    "https": "socks5h://127.0.0.1:1080"
} if os.getenv("TN_PROXY") else None

# ==================== 注册配置 ====================
REGISTER_SLEEP_MIN = 10
REGISTER_SLEEP_MAX = 30
REGISTER_PASSWORD = "TextNow@" + ''.join(os.urandom(4).hex())
MAX_REG_RETRY = 3
RETRY_BACKOFF_BASE = 2

# ==================== 日志级别 ====================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ==================== Web 服务配置 ====================
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("WEB_PORT", "8899"))
SECRET_KEY = os.getenv("SECRET_KEY", "textnow-factory-secret-key-2024")
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"

# ==================== 数据库配置 ====================
DB_TYPE = os.getenv("DB_TYPE", "sqlite")  # mysql 或 sqlite
SQLITE_PATH = os.getenv("SQLITE_PATH", "data/textnow_factory.db")

# MySQL 配置
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "123456")
DB_NAME = os.getenv("DB_NAME", "textnow_us")

DB_CONFIG = {
    "host": DB_HOST,
    "port": DB_PORT,
    "user": DB_USER,
    "password": DB_PASS,
    "database": DB_NAME,
    "charset": "utf8mb4",
    "autocommit": True,
    "pool_size": 5,
    "pool_pre_ping": True,
}

# ==================== API 配置 ====================
TEXTNOW_API_URL = "https://api.textnow.me/api/v2/users"
TEXTNOW_APP_VERSION = "26.1.0"

# ==================== 矩阵群发配置 ====================
MATRIX_BATCH_SIZE = int(os.getenv("MATRIX_BATCH_SIZE", "50"))
MATRIX_THREADS = int(os.getenv("MATRIX_THREADS", "4"))
MATRIX_RETRY_MAX = int(os.getenv("MATRIX_RETRY_MAX", "3"))

# ==================== 设备信息池 ====================
DEVICE_POOL = [
    {"model_code": "iPhone14,7", "model_name": "iPhone 14", "os_ver": "16.1", "scale": "3.00"},
    {"model_code": "iPhone12,1", "model_name": "iPhone 11", "os_ver": "16.3.1", "scale": "2.00"},
    {"model_code": "iPhone13,2", "model_name": "iPhone 12", "os_ver": "16.5", "scale": "3.00"},
    {"model_code": "iPhone14,5", "model_name": "iPhone 13", "os_ver": "16.0.2", "scale": "3.00"},
    {"model_code": "iPhone15,2", "model_name": "iPhone 14 Pro", "os_ver": "17.0", "scale": "3.00"},
    {"model_code": "iPhone15,4", "model_name": "iPhone 15", "os_ver": "17.1", "scale": "3.00"},
    {"model_code": "iPhone16,1", "model_name": "iPhone 15 Pro", "os_ver": "17.2", "scale": "3.00"},
]

# ==================== 姓名字典 ====================
FIRST_NAMES = [
    "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph",
    "Thomas", "Charles", "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara",
]
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
]
