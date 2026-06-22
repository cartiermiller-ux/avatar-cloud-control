from app.tasks import celery
from app.models.auto_reply_rule import AutoReplyRule
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from app.models.device_info import DeviceInfo
from app import db
from run import send_device_command

@celery.task
def match_auto_reply(session_id: int, incoming_text: str, local_phone: str, group_id: int):
    """收到客户消息，匹配自动回复规则并下发回复指令"""
    # 查询当前分组生效规则
    rule_list = AutoReplyRule.query.filter(
        AutoReplyRule.status == 1,
        (AutoReplyRule.bind_group_ids == "" | AutoReplyRule.bind_group_ids.like(f"%{group_id}%"))
    ).all()
    hit_rule = None
    for rule in rule_list:
        keyword_arr = rule.match_keyword.split(",")
        for kw in keyword_arr:
            if kw.strip() and kw.strip() in incoming_text:
                hit_rule = rule
                break
        if hit_rule:
            break
    if not hit_rule:
        return {"code": 200, "msg": "无匹配自动回复规则"}

    # 查找本机对应设备SN
    dev = DeviceInfo.query.join(ImAccount, ImAccount.device_id == DeviceInfo.id).filter(
        ImAccount.phone_number == local_phone
    ).first()
    if not dev:
        return {"code": 400, "msg": "未找到对应设备"}

    # 下发回复消息到iPhone设备
    session_info = ChatSession.query.get(session_id)
    send_device_command(
        device_sn=dev.device_sn,
        cmd_type="im_send_msg",
        data={
            "target_phone": session_info.target_phone,
            "content": hit_rule.reply_text,
            "img_url": hit_rule.reply_img
        }
    )
    # 写入我方回复记录
    new_msg = ChatMessage(
        session_id=session_id,
        direction="out",
        msg_type="image" if hit_rule.reply_img else "text",
        content=hit_rule.reply_text
    )
    db.session.add(new_msg)
    db.session.commit()
    return {"code": 200, "msg": "自动回复已发送", "rule_name": hit_rule.rule_name}