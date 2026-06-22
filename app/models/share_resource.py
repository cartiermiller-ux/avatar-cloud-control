from app.db import db
from datetime import datetime

class ShareResource(db.Model):
    __tablename__ = "share_resource"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    source_group_id = db.Column(db.Integer, nullable=False, comment="源分组")
    target_group_id = db.Column(db.Integer, nullable=False, comment="共享目标分组")
    expire_time = db.Column(db.DateTime)
    status = db.Column(db.SmallInteger, default=1)
    create_time = db.Column(db.DateTime, default=datetime.now)