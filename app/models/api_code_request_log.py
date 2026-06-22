from app.db import db
from datetime import datetime

class ApiCodeRequestLog(db.Model):
    __tablename__ = "api_code_request_log"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    api_key_id = db.Column(db.Integer, nullable=False, comment="所属密钥ID")
    request_api = db.Column(db.String(100), nullable=False, comment="请求接口路径")
    phone_number = db.Column(db.String(30), default="", comment="操作号码")
    request_ip = db.Column(db.String(50), nullable=False, comment="客户端IP")
    response_code = db.Column(db.Integer, nullable=False, comment="返回code")
    response_msg = db.Column(db.String(500), default="")
    create_time = db.Column(db.DateTime, default=datetime.now)