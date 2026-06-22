from app.db import db
from datetime import datetime

class ChatMessage(db.Model):
    __tablename__ = "chat_message"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    session_id = db.Column(db.Integer, nullable=False, comment="所属会话ID")
    direction = db.Column(db.Enum("in", "out"), nullable=False, comment="in客户发来 out我方发出")
    msg_type = db.Column(db.Enum("text", "image"), default="text")
    content = db.Column(db.Text, nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.now)