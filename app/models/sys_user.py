from app.db import db
from datetime import datetime

class SysUser(db.Model):
    __tablename__ = "sys_user"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False, comment="登录账号")
    real_name = db.Column(db.String(50), nullable=False, comment="显示名称")
    password = db.Column(db.String(200), nullable=False, comment="bcrypt加密密码")
    role = db.Column(db.Enum("user", "admin", "root"), default="user", comment="角色权限")
    bind_group_ids = db.Column(db.String(500), default="", comment="可操作分组ID逗号分隔")
    status = db.Column(db.SmallInteger, default=1, comment="1启用 0禁用")
    last_login_time = db.Column(db.DateTime)
    create_time = db.Column(db.DateTime, default=datetime.now)