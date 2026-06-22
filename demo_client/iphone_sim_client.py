import socketio
import json
import time
import random

# 服务端WebSocket地址，本地/线上按需修改
SERVER_WS_URL = "http://127.0.0.1:5000"
# 模拟设备序列号（和后台device_info表SN一致）
DEVICE_SN = "IPHONE-2026-0001"
# 本机绑定号码
LOCAL_PHONE = "+18881234567"

# 创建socketio客户端
sio = socketio.Client()

# 连接成功回调
@sio.event
def connect():
    print(f"✅ 设备{DEVICE_SN}已连接服务端WebSocket")
    # 设备登录上报
    login_data = {
        "msg_type": "device_login",
        "device_sn": DEVICE_SN,
        "wifi_calling": 1
    }
    sio.emit("message", login_data)

# 收到服务端下发指令
@sio.event
def message(data):
    print(f"\n📩 收到服务端下发指令：{json.dumps(data, ensure_ascii=False, indent=2)}")
    cmd_type = data.get("cmd_type")
    cmd_data = data.get("data", {})

    if cmd_type == "im_send_msg":
        # 模拟发送iMessage
        target = cmd_data["target_phone"]
        content = cmd_data["content"]
        img = cmd_data.get("img_url", "")
        print(f"📤 模拟发送消息至 {target}：文本={content} 图片={img}")
    elif cmd_type == "disconnect":
        print("⚠️ 服务端下发远程断开指令，客户端即将下线")
        sio.disconnect()

# 断开连接回调
@sio.event
def disconnect():
    print("❌ 与服务端WebSocket断开，5秒后自动重连")
    time.sleep(5)
    start_client()

# 定时心跳发送线程
def heartbeat_loop():
    while True:
        heartbeat_pack = {
            "msg_type": "device_heartbeat",
            "device_sn": DEVICE_SN,
            "wifi_calling": random.choice([0,1])
        }
        sio.emit("message", heartbeat_pack)
        time.sleep(30)

# 模拟收到外部短信/验证码（测试接码功能）
def mock_receive_code():
    time.sleep(12)
    code_pack = {
        "msg_type": "code_receive",
        "device_sn": DEVICE_SN,
        "receive_phone": LOCAL_PHONE,
        "verify_code": str(random.randint(100000,999999)),
        "sender": "+19997654321"
    }
    sio.emit("message", code_pack)

# 模拟客户发来iMessage消息（测试自动回复/聊天工作台）
def mock_customer_msg():
    time.sleep(20)
    msg_pack = {
        "msg_type": "im_incoming_msg",
        "device_sn": DEVICE_SN,
        "target_phone": "+17776543210",
        "local_phone": LOCAL_PHONE,
        "content": "请问价格是多少？",
        "msg_type": "text"
    }
    sio.emit("message", msg_pack)

def start_client():
    try:
        sio.connect(SERVER_WS_URL)
        # 启动心跳、模拟消息后台线程
        sio.start_background_task(heartbeat_loop)
        sio.start_background_task(mock_receive_code)
        sio.start_background_task(mock_customer_msg)
        sio.wait()
    except Exception as e:
        print(f"连接失败：{str(e)}，5秒重试")
        time.sleep(5)
        start_client()

if __name__ == "__main__":
    print("==== iPhone设备模拟客户端启动 ====")
    print(f"设备SN：{DEVICE_SN}")
    print(f"连接服务端：{SERVER_WS_URL}")
    start_client()