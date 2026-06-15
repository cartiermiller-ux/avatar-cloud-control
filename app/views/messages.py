"""消息 API"""

import logging

from flask import Blueprint, request, jsonify

from .. import requires_auth
from ..models.db import get_db, get_db_dict

log = logging.getLogger(__name__)
messages_bp = Blueprint("messages", __name__)


@messages_bp.route("/api/messages", methods=["GET"])
@requires_auth
def api_messages():
    try:
        conv_id = request.args.get("conv_id", type=int)
        if not conv_id:
            return jsonify({"code": 1, "msg": "缺少conv_id", "data": []})
        conn = get_db_dict()
        cur = conn.cursor()
        cur.execute("SELECT * FROM tn_messages WHERE conversation_id=? ORDER BY sent_at ASC", (conv_id,))
        rows = cur.fetchall()
        conn.close()
        return jsonify({"code": 0, "msg": "", "data": [dict(r) for r in rows]})
    except Exception as e:
        log.error("api_messages error: %s", e)
        return jsonify({"code": 1, "msg": str(e), "data": []})


@messages_bp.route("/api/messages/send", methods=["POST"])
@requires_auth
def api_message_send():
    try:
        data = request.get_json() or {}
        conv_id = data.get("conv_id")
        content = data.get("content", "").strip()
        if not conv_id or not content:
            return jsonify({"code": 1, "msg": "缺少参数"})
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO tn_messages (conversation_id, direction, content, is_auto_reply, sent_at) VALUES (?, 2, ?, 0, datetime('now'))",
            (conv_id, content),
        )
        cur.execute("UPDATE tn_conversations SET last_message_at=datetime('now') WHERE id=?", (conv_id,))
        conn.commit()
        conn.close()
        return jsonify({"code": 0, "msg": "发送成功"})
    except Exception as e:
        log.error("api_message_send error: %s", e)
        return jsonify({"code": 1, "msg": str(e)})
