from app.db import db
from datetime import datetime

class StatDaily(db.Model):
    __tablename__ = "stat_daily"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stat_date = db.Column(db.Date, nullable=False, comment="统计日期")
    group_id = db.Column(db.Integer, nullable=False, comment="分组ID，0=全平台汇总")
    device_online_num = db.Column(db.Integer, default=0, comment="在线设备")
    total_send = db.Column(db.Integer, default=0, comment="当日发送总量")
    total_success = db.Column(db.Integer, default=0, comment="送达成功")
    total_fail = db.Column(db.Integer, default=0, comment="发送失败")
    total_reply = db.Column(db.Integer, default=0, comment="收到回复")
    total_get_code = db.Column(db.Integer, default=0, comment="接码取号次数")
    wifi_calling_online = db.Column(db.Integer, default=0, comment="开启WiFi Calling设备数")
    create_time = db.Column(db.DateTime, default=datetime.now)
    group_info = db.relationship("GroupInfo", foreign_keys=[group_id], lazy="joined")