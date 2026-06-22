from app.db import db
from datetime import datetime

class AutoReplyRule(db.Model):
    __tablename__ = "auto_reply_rule"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rule_name = db.Column(db.String(100), nullable=False, comment="规则名称")
    match_keyword = db.Column(db.String(300), nullable=False, comment="触发关键词逗号分隔")
    reply_text = db.Column(db.Text, nullable=False, comment="回复文字")
    reply_img = db.Column(db.String(500), default="", comment="回复图片")
    bind_group_ids = db.Column(db.String(500), default="", comment="生效分组，空为全部分组")
    status = db.Column(db.SmallInteger, default=1, comment="1启用 0关闭")
    create_time = db.Column(db.DateTime, default=datetime.now)