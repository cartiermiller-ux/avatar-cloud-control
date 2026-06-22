import sys
sys.path.insert(0, ".")
from flask import Flask, request
from flask_socketio import SocketIO
import dotenv
import os

# 加载环境变量
dotenv.load_dotenv(".env")

# 创建Flask应用实例
app = Flask(__name__)

# 正确加载配置模块（字符串传入，无命名冲突）
app.config.from_object("app.config")

# 初始化数据库
from app.db import db
db.init_app(app)

# Windows本地调试 async_mode 改用 threading，避免报错
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading", manage_session=False)

# 注册蓝图
from app.admin import admin_bp
from app.api import api_bp
app.register_blueprint(admin_bp)
app.register_blueprint(api_bp)

# WebSocket 消息入口
from app.websocket.device_ws import handle_device_ws_msg, send_device_command
@socketio.on("message")
def ws_entrance(json_data):
    return handle_device_ws_msg(json_data, request.sid)

# 数据库初始化命令行
@app.cli.command("init_db")
def init_db():
    with app.app_context():
        db.create_all()
        print("✅ 数据表创建完成，请导入avatar_cloud.sql初始化管理员账号")

# 对外导出
__all__ = ["app", "db", "socketio", "send_device_command"]

if __name__ == "__main__":
    PORT = int(os.getenv("SERVER_PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=PORT, debug=False, use_reloader=False)
    print(f"服务启动：http://127.0.0.1:{PORT}/admin/login")