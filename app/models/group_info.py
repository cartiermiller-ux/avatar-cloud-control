from app.db import db
from datetime import datetime

class GroupInfo(db.Model):
    __tablename__ = "group_info"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    parent_id = db.Column(db.Integer, default=0, comment="父分组ID")
    group_name = db.Column(db.String(100), nullable=False, comment="分组名称")
    desc = db.Column(db.String(500), default="", comment="分组备注")
    create_time = db.Column(db.DateTime, default=datetime.now)