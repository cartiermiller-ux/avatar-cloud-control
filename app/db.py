from flask_sqlalchemy import SQLAlchemy

# 全局唯一数据库实例，全项目共用
db = SQLAlchemy()

def init_db(app):
    """绑定app实例，在run.py中调用初始化"""
    db.init_app(app)