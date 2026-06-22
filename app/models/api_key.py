from app.db import db
from datetime import datetime

class ApiKey(db.Model):
    __tablename__ = "api_key"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, comment="密钥备注名称")
    key_str = db.Column(db.String(100), unique=True, nullable=False, comment="gck_开头密钥")
    access_scope = db.Column(db.String(50), nullable=False, comment="访问范围标识")
    bind_group_ids = db.Column(db.String(500), default="", comment="可使用分组ID")
    status = db.Column(db.SmallInteger, default=1, comment="1启用 0停用")
    last_use_time = db.Column(db.DateTime)
    create_time = db.Column(db.DateTime, default=datetime.now)
    # 关联调用日志
    log_list = db.relationship("ApiCodeRequestLog", backref="api_key", lazy="select")