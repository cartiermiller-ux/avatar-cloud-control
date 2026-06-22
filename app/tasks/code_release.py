from app.tasks import celery
from app.models.receive_code_num import ReceiveCodeNum
from datetime import datetime
from app import db

@celery.task
def auto_release_expire_num():
    """定时任务：释放已过锁定时长的接码号码"""
    now = datetime.now()
    expire_num_list = ReceiveCodeNum.query.filter(
        ReceiveCodeNum.status == "占用",
        ReceiveCodeNum.lock_expire_time < now
    ).all()
    release_count = 0
    for num in expire_num_list:
        num.status = "空闲"
        num.current_key_id = None
        num.lock_expire_time = None
        release_count += 1
    db.session.commit()
    return {
        "release_count": release_count,
        "run_time": now.strftime("%Y-%m-%d %H:%M:%S")
    }