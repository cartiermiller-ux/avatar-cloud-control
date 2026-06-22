from datetime import date
from sqlalchemy import func
from app.models.device_info import DeviceInfo
from app.models.push_task import PushTask
from app.models.code_record import CodeRecord
from app.models.stat_daily import StatDaily
from app import db

def calc_daily_stat(target_date: date, group_id: int = 0):
    """
    生成单日分组/全平台统计数据
    :param target_date: 统计日期
    :param group_id: 0=全平台汇总，其他数字为指定分组
    :return: 统计字典
    """
    filter_group = []
    if group_id > 0:
        filter_group.append(DeviceInfo.group_id == group_id)

    # 在线设备总数
    online_dev_count = DeviceInfo.query.filter(
        DeviceInfo.online_status == 1,
        DeviceInfo.last_heartbeat >= target_date,
        *filter_group
    ).count()

    # WiFi Calling在线设备
    wifi_online_count = DeviceInfo.query.filter(
        DeviceInfo.online_status == 1,
        DeviceInfo.wifi_calling == 1,
        DeviceInfo.last_heartbeat >= target_date,
        *filter_group
    ).count()

    # 推送任务当日统计
    push_sum = db.session.query(
        func.sum(PushTask.total_count).label("total_send"),
        func.sum(PushTask.success_count).label("total_success"),
        func.sum(PushTask.fail_count).label("total_fail"),
        func.sum(PushTask.reply_count).label("total_reply")
    ).filter(
        func.date(PushTask.create_time) == target_date,
        *filter_group
    ).first()

    # 当日接码总次数
    code_count = CodeRecord.query.filter(
        func.date(CodeRecord.create_time) == target_date,
        *filter_group
    ).count()

    stat_data = {
        "stat_date": target_date,
        "group_id": group_id,
        "device_online_num": online_dev_count or 0,
        "wifi_calling_online": wifi_online_count or 0,
        "total_send": push_sum.total_send or 0,
        "total_success": push_sum.total_success or 0,
        "total_fail": push_sum.total_fail or 0,
        "total_reply": push_sum.total_reply or 0,
        "total_get_code": code_count or 0
    }
    # 写入统计表或更新
    exist = StatDaily.query.filter_by(stat_date=target_date, group_id=group_id).first()
    if exist:
        for k, v in stat_data.items():
            setattr(exist, k, v)
    else:
        new_stat = StatDaily(**stat_data)
        db.session.add(new_stat)
    db.session.commit()
    return stat_data