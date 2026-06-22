from app.db import db
from datetime import datetime

class DeviceInfo(db.Model):
    __tablename__ = "device_info"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_sn = db.Column(db.String(100), unique=True, nullable=False, comment="设备唯一序列号")
    device_name = db.Column(db.String(100), nullable=False, comment="设备名称")
    phone_number = db.Column(db.String(30), nullable=False, comment="本机号码")
    group_id = db.Column(db.Integer, nullable=False, comment="所属分组ID")
    online_status = db.Column(db.SmallInteger, default=0, comment="1在线 0离线")
    wifi_calling = db.Column(db.SmallInteger, default=0, comment="1开启 0关闭")
    remote_disconnect = db.Column(db.SmallInteger, default=0, comment="远程断开标记")
    last_heartbeat = db.Column(db.DateTime)
    create_time = db.Column(db.DateTime, default=datetime.now)
    # 关联分组
    group_info = db.relationship("GroupInfo", foreign_keys=[group_id], lazy="joined")
    # 关联账号
    im_account_list = db.relationship("ImAccount", backref="device_info", lazy="select")