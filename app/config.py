import os
import dotenv

# 加载根目录.env环境变量
dotenv.load_dotenv(".env")

# 基础安全密钥
SECRET_KEY = os.getenv("SECRET_KEY", "avatar_cloud_default_secret_2026")

# 数据库配置
DB_ENGINE = os.getenv("DB_ENGINE", "mysql")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "root123456")
DB_NAME = os.getenv("DB_NAME", "avatar_cloud")

# Redis配置
REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# Web服务端口
SERVER_PORT = int(os.getenv("SERVER_PORT", 5000))
TRUSTED_PROXIES = eval(os.getenv("TRUSTED_PROXIES", '["127.0.0.1"]'))

# 文件上传配置
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "app/static/upload/img")
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 10485760))

# 接码默认锁定时长
DEFAULT_LOCK_MIN = int(os.getenv("DEFAULT_LOCK_MIN", 5))

# 拼接数据库连接字符串
if DB_ENGINE == "mysql":
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
else:
    SQLALCHEMY_DATABASE_URI = "sqlite:///avatar_local.db"

# SQLAlchemy全局开关
SQLALCHEMY_TRACK_MODIFICATIONS = False