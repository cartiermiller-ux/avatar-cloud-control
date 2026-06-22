# 全局统一导出核心组件，方便项目各处导入
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from .db import db
from .utils.redis_pool import redis_client, redis_url

# 导入所有蓝图
from .admin import admin_bp
from .api import api_bp

__all__ = [
    "db",
    "redis_client",
    "redis_url",
    "admin_bp",
    "api_bp"
]