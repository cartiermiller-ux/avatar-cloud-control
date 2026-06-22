from app.db import db
from datetime import datetime

class ReceiveCodeNum(db.Model):
    __tablename__ = "receive_code_num"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group_id = db.Column(db.Integer, nullable=False)
    phone_number = db.Column(db.String(30), unique=True, nullable=False)
    status = db.Column(db.Enum("空闲", "占用", "离线"), default="空闲")
    current_key_id = db.Column(db.Integer, comment="当前占用密钥ID")
    lock_minute = db.Column(db.Integer, default=5)
    lock_expire_time = db.Column(db.DateTime)
    create_time = db.Column(db.DateTime, default=datetime.now)