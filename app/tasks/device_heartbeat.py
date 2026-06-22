from app.tasks import celery
from app.models.device_info import DeviceInfo
from datetime import datetime, timedelta
from app import db

@celery.task
def offline_clean_task():
    """定时任务：超过90秒无心跳自动标记设备离线"""
    expire_time = datetime.now() - timedelta(seconds=90)
    offline_dev_list = DeviceInfo.query.filter(
        DeviceInfo.last_heartbeat < expire_time,
        DeviceInfo.online_status == 1
    ).all()
    offline_count = 0
    for dev in offline_dev_list:
        dev.online_status = 0
        offline_count += 1
    db.session.commit()
    return {
        "clean_offline_count": offline_count,
        "clean_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }