from flask import request, jsonify
from app.admin import admin_bp, login_required, render_admin
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from app import db

# 聊天工作台页面
@admin_bp.route("/agent/list")
@login_required
def chat_workbench_page():
    return render_admin("chat_workbench.html", page="agent")

# 获取会话列表
@admin_bp.route("/chat/getSessionList")
@login_required
def chat_get_session_list():
    uid = session["user_id"]
    # 坐席只能看分配给自己的会话，root/admin查看全部
    if session["role"] == "user":
        session_list = ChatSession.query.filter_by(agent_uid=uid).all()
    else:
        session_list = ChatSession.query.all()
    res = []
    for s in session_list:
        res.append({
            "id": s.id,
            "target_phone": s.target_phone,
            "local_phone": s.local_phone,
            "unread_count": s.unread_count,
            "last_msg_time": s.last_msg_time.strftime("%Y-%m-%d %H:%M:%S") if s.last_msg_time else ""
        })
    return jsonify({"code":200, "data": res})

# 获取单会话聊天历史记录
@admin_bp.route("/chat/getHistory")
@login_required
def chat_get_history():
    session_id = request.args.get("session_id")
    msg_list = ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.create_time).all()
    res = []
    for msg in msg_list:
        res.append({
            "msg_type": msg.msg_type,
            "content": msg.content,
            "direction": msg.direction
        })
    # 清空未读计数
    chat_session = ChatSession.query.get(session_id)
    chat_session.unread_count = 0
    db.session.commit()
    return jsonify({"code":200, "data": res})