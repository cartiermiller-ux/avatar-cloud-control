from app.db import db
from datetime import datetime

class ChatSession(db.Model):
    __tablename__ = "chat_session"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    target_phone = db.Column(db.String(30), nullable=False, comment="客户号码")
    local_phone = db.Column(db.String(30), nullable=False, comment="我方设备号码")
    group_id = db.Column(db.Integer, nullable=False)
    agent_uid = db.Column(db.Integer, comment="分配坐席ID")
    unread_count = db.Column(db.Integer, default=0, comment="未读消息数")
    last_msg_time = db.Column(db.DateTime)
    status = db.Column(db.Enum("待分配", "处理中", "已关闭"), default="待分配")
    create_time = db.Column(db.DateTime, default=datetime.now)
    msg_list = db.relationship("ChatMessage", backref="session", lazy="select")