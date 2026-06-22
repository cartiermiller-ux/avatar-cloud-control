# 导入celery实例，注册全部任务
from celery_worker import celery
from .push_task import send_batch_msg
from .auto_reply import match_auto_reply
from .device_heartbeat import offline_clean_task
from .code_release import auto_release_expire_num

# 统一导出任务供celery自动发现
__all__ = [
    "send_batch_msg",
    "match_auto_reply",
    "offline_clean_task",
    "auto_release_expire_num"
]