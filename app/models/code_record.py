from app.db import db
from datetime import datetime

class CodeRecord(db.Model):
    __tablename__ = "code_record"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    phone_number = db.Column(db.String(30), nullable=False, comment="接收号码")
    verify_code = db.Column(db.String(20), nullable=False, comment="验证码")
    api_key_id = db.Column(db.Integer, comment="获取该码的密钥ID")
    service_name = db.Column(db.String(200), default="", comment="来源备注")
    create_time = db.Column(db.DateTime, default=datetime.now)