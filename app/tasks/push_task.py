from app.tasks import celery
from app.models.push_task import PushTask
from app.models.im_account import ImAccount
from app.models.device_info import DeviceInfo
from app import db
from run import send_device_command
import time

@celery.task(bind=True)
def send_batch_msg(self, task_id: int):
    """批量推送iMessage/SMS消息后台任务"""
    task = PushTask.query.get(task_id)
    if not task or task.status in ["已完成", "已终止"]:
        return {"code": 400, "msg": "任务不存在或已结束"}

    # 获取目标分组全部在线账号
    group_id_list = task.group_ids.split(",")
    account_list = ImAccount.query.join(DeviceInfo, DeviceInfo.id == ImAccount.device_id).filter(
        ImAccount.group_id.in_(group_id_list),
        DeviceInfo.online_status == 1
    ).all()
    task.total_count = len(account_list)
    db.session.commit()

    send_success = 0
    send_fail = 0
    index = 0
    for acc in account_list:
        # 中断检测
        current_task = PushTask.query.get(task_id)
        if current_task.status == "已终止":
            break

        try:
            # 下发发送消息指令到对应iPhone设备
            send_device_command(
                device_sn=acc.device_info.device_sn,
                cmd_type="im_send_msg",
                data={
                    "target_phone": acc.phone_number,
                    "content": task.msg_content,
                    "img_url": task.img_url
                }
            )
            send_success += 1
        except Exception as e:
            send_fail += 1
        index += 1
        task.send_count = index
        task.success_count = send_success
        task.fail_count = send_fail
        task.progress = int((index / task.total_count) * 100) if task.total_count > 0 else 0
        db.session.commit()
        # 间隔防并发过载
        time.sleep(0.8)

    # 任务结束标记
    task.status = "已完成"
    task.finish_time = db.func.now()
    db.session.commit()
    return {
        "task_id": task_id,
        "total": task.total_count,
        "success": send_success,
        "fail": send_fail
    }