import os
import redis
from dotenv import load_dotenv

load_dotenv(".env")
REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# Redis连接地址（供Celery broker使用）
redis_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# 全局redis客户端
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True,
    socket_timeout=5
)