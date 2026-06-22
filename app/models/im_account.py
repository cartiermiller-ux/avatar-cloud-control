from app.db import db
from datetime import datetime

class ImAccount(db.Model):
    __tablename__ = "im_account"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.Integer, nullable=False, comment="所属设备ID")
    group_id = db.Column(db.Integer, nullable=False, comment="所属分组ID")
    phone_number = db.Column(db.String(30), nullable=False, comment="账号号码")
    account_type = db.Column(db.Enum("imessage", "sms"), nullable=False, comment="账号类型")
    register_status = db.Column(db.String(30), default="待激活", comment="激活状态")
    maturity_level = db.Column(db.Enum("低", "中", "高"), default="低", comment="账号权重")
    reconnect_count = db.Column(db.Integer, default=0, comment="掉线重连次数")
    last_msg_time = db.Column(db.DateTime)
    create_time = db.Column(db.DateTime, default=datetime.now)
    # 关联分组
    group_info = db.relationship("GroupInfo", foreign_keys=[group_id], lazy="joined")