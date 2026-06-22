from app.db import db
from datetime import datetime

class PushTask(db.Model):
    __tablename__ = "push_task"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_name = db.Column(db.String(100), nullable=False, comment="任务名称")
    group_ids = db.Column(db.String(500), nullable=False, comment="下发分组ID逗号分隔")
    msg_content = db.Column(db.Text, nullable=False, comment="推送文本内容")
    img_url = db.Column(db.String(500), default="", comment="推送图片地址")
    total_count = db.Column(db.Integer, default=0, comment="总目标号码数")
    send_count = db.Column(db.Integer, default=0, comment="已发送")
    success_count = db.Column(db.Integer, default=0, comment="送达成功")
    fail_count = db.Column(db.Integer, default=0, comment="发送失败")
    reply_count = db.Column(db.Integer, default=0, comment="收到回复")
    progress = db.Column(db.Integer, default=0, comment="进度百分比")
    status = db.Column(db.Enum("等待执行", "执行中", "已完成", "已终止"), default="等待执行")
    creator_id = db.Column(db.Integer, nullable=False, comment="创建管理员ID")
    create_time = db.Column(db.DateTime, default=datetime.now)
    finish_time = db.Column(db.DateTime)