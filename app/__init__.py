"""
TextNow Factory - Flask 应用工厂
"""

import os
import hashlib
import logging
from pathlib import Path
from functools import wraps

from flask import Flask, request, redirect, jsonify, session

from .config import SECRET_KEY, FLASK_DEBUG, LOG_LEVEL, WEB_HOST, WEB_PORT

# ===================== 日志配置 ====================
logging.basicConfig(level=getattr(logging, LOG_LEVEL.upper(), logging.INFO))
log = logging.getLogger(__name__)

# ===================== 应用根路径 ====================
BASE_DIR = Path(__file__).parent.parent  # 指向 textnow_factory2/
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ===================== 登录验证装饰器 ====================
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "agent_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"code": -1, "msg": "未登录或会话已过期"}), 401
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated


def require_role(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if session.get("agent_role") not in allowed_roles:
                if request.path.startswith("/api/"):
                    return jsonify({"code": -1, "msg": "权限不足"}), 403
                return redirect("/")
            return f(*args, **kwargs)
        return decorated
    return decorator


# ===================== 应用工厂 ====================
def create_app():
    """Flask 应用工厂函数"""
    flask_app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent.parent / 'templates'),
        static_folder=str(Path(__file__).parent.parent / 'static'),
    )
    flask_app.secret_key = SECRET_KEY

    # 注册所有蓝图
    from .views.auth import auth_bp
    from .views.pages import pages_bp
    from .views.accounts import accounts_bp
    from .views.register import register_bp
    from .views.matrix import matrix_bp
    from .views.agents import agents_bp
    from .views.salesmen import salesmen_bp
    from .views.conversations import conversations_bp
    from .views.messages import messages_bp
    from .views.templates import templates_bp
    from .views.ip_manage import ip_bp
    from .views.upload import upload_bp
    from .views.dashboard import dashboard_bp
    from .views.salesman_assign import salesman_assign_bp

    flask_app.register_blueprint(auth_bp)
    flask_app.register_blueprint(pages_bp)
    flask_app.register_blueprint(accounts_bp)
    flask_app.register_blueprint(register_bp)
    flask_app.register_blueprint(matrix_bp)
    flask_app.register_blueprint(agents_bp)
    flask_app.register_blueprint(salesmen_bp)
    flask_app.register_blueprint(conversations_bp)
    flask_app.register_blueprint(messages_bp)
    flask_app.register_blueprint(templates_bp)
    flask_app.register_blueprint(ip_bp)
    flask_app.register_blueprint(upload_bp)
    flask_app.register_blueprint(dashboard_bp)
    flask_app.register_blueprint(salesman_assign_bp)

    # 初始化数据库
    from .models.db import init_schema, init_default_data
    init_schema()
    init_default_data()

    log.info("TextNow Factory app created successfully")
    return flask_app
