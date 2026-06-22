from datetime import datetime
from app.models.device_info import DeviceInfo
from app.models.code_record import CodeRecord
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from app import db

# 全局设备在线连接映射 key:设备SN, value:socketio会话ID
device_socket_map = {}

def handle_device_ws_msg(json_data, sid):
    """
    处理iPhone设备WebSocket上报消息
    :param json_data: 设备发来的json数据包
    :param sid: 当前socket连接会话ID
    """
    msg_type = json_data.get("msg_type")
    dev_sn = json_data.get("device_sn")
    if not dev_sn:
        return {"code": 400, "msg": "缺失设备SN标识"}

    # 查找数据库设备记录
    dev = DeviceInfo.query.filter_by(device_sn=dev_sn).first()
    if not dev:
        return {"code": 404, "msg": "该设备未在后台注册，断开连接"}

    # 心跳/登录注册连接
    if msg_type == "device_login":
        device_socket_map[dev_sn] = sid
        dev.online_status = 1
        dev.wifi_calling = json_data.get("wifi_calling", 0)
        dev.last_heartbeat = datetime.now()
        db.session.commit()
        print(f"【设备上线】SN:{dev_sn} 会话ID:{sid}")
        return {"code": 200, "msg": "登录成功，保持心跳连接"}

    elif msg_type == "device_heartbeat":
        # 更新心跳时间
        dev.last_heartbeat = datetime.now()
        dev.wifi_calling = json_data.get("wifi_calling", 0)
        db.session.commit()
        return {"code": 200, "msg": "心跳接收正常"}

    elif msg_type == "code_receive":
        # 设备上报收到验证码
        phone = json_data["receive_phone"]
        code = json_data["verify_code"]
        sender = json_data.get("sender", "未知发送方")
        new_code = CodeRecord(
            phone_number=phone,
            verify_code=code,
            api_key_id=None,
            service_name=f"外部发送号码:{sender}"
        )
        db.session.add(new_code)
        db.session.commit()
        print(f"【接码记录】号码:{phone} 验证码:{code}")
        return {"code": 200, "msg": "验证码已入库"}

    elif msg_type == "im_incoming_msg":
        # 客户发来iMessage/SMS消息，创建会话+消息记录
        target_phone = json_data["target_phone"]
        local_phone = json_data["local_phone"]
        content = json_data["content"]
        group_id = dev.group_id

        # 查询或创建会话
        session = ChatSession.query.filter_by(
            target_phone=target_phone,
            local_phone=local_phone
        ).first()
        if not session:
            session = ChatSession(
                target_phone=target_phone,
                local_phone=local_phone,
                group_id=group_id,
                unread_count=1,
                status="待分配"
            )
            db.session.add(session)
            db.session.flush()
        else:
            session.unread_count += 1
            session.last_msg_time = datetime.now()

        # 写入消息记录
        new_msg = ChatMessage(
            session_id=session.id,
            direction="in",
            msg_type=json_data.get("msg_type", "text"),
            content=content
        )
        db.session.add(new_msg)
        db.session.commit()

        # 触发自动回复异步任务
        from app.tasks import match_auto_reply
        match_auto_reply.delay(session.id, content, local_phone, group_id)
        return {"code": 200, "msg": "客户消息已接收，自动回复匹配中"}

    else:
        return {"code": 400, "msg": f"未知消息类型:{msg_type}"}


def send_device_command(device_sn: str, cmd_type: str, data: dict):
    """
    下发指令到指定在线iPhone设备
    :param device_sn: 目标设备序列号
    :param cmd_type: 指令类型 im_send_msg / disconnect
    :param data: 指令附带参数
    """
    from run import socketio
    if device_sn not in device_socket_map:
        raise Exception(f"设备{device_sn}当前离线，无法下发指令")
    target_sid = device_socket_map[device_sn]
    send_json = {
        "cmd_type": cmd_type,
        "data": data
    }
    socketio.emit("message", send_json, to=target_sid)
    return True