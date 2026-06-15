"""会话管理 API"""

import logging

from flask import Blueprint, request, jsonify

from .. import requires_auth
from ..models.db import get_db, get_db_dict

log = logging.getLogger(__name__)
conversations_bp = Blueprint("conversations", __name__)


@conversations_bp.route("/api/conversations", methods=["GET"])
@requires_auth
def api_conversations():
    try:
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 20, type=int)
        status = request.args.get("status", "")
        search = request.args.get("search", "")
        account_id = request.args.get("account_id", type=int)

        conn = get_db_dict()
        cur = conn.cursor()
        where_clauses = []
        params = []
        if status:
            where_clauses.append("c.status=?")
            params.append(int(status))
        if search:
            where_clauses.append("c.contact_number LIKE ?")
            params.append(f"%{search}%")
        if account_id:
            where_clauses.append("c.account_id=?")
            params.append(account_id)

        where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        cur.execute(f"SELECT COUNT(*) as c FROM tn_conversations c{where_sql}", params)
        total = cur.fetchone()["c"]

        offset = (page - 1) * limit
        cur.execute(
            f"""SELECT c.*, a.username as account_name,
            (SELECT COUNT(*) FROM tn_messages WHERE conversation_id=c.id AND direction=1 AND read_status=0) as unread_count,
            (SELECT content FROM tn_messages WHERE conversation_id=c.id ORDER BY sent_at DESC LIMIT 1) as last_preview
            FROM tn_conversations c
            LEFT JOIN tn_accounts a ON c.account_id=a.id
            {where_sql}
            ORDER BY c.last_message_at DESC LIMIT ? OFFSET ?""",
            params + [limit, offset],
        )
        rows = cur.fetchall()
        conn.close()
        return jsonify({"code": 0, "msg": "", "count": total, "data": [dict(r) for r in rows]})
    except Exception as e:
        log.error("api_conversations error: %s", e)
        return jsonify({"code": 1, "msg": str(e), "count": 0, "data": []})


@conversations_bp.route("/api/conversations/close", methods=["POST"])
@requires_auth
def api_conversation_close():
    try:
        conv_id = request.form.get("conv_id") or (request.json or {}).get("conv_id")
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE tn_conversations SET status=0 WHERE id=?", (conv_id,))
        conn.commit()
        conn.close()
        return jsonify({"code": 0, "msg": "会话已关闭"})
    except Exception as e:
        log.error("api_conversation_close error: %s", e)
        return jsonify({"code": 1, "msg": str(e)})


@conversations_bp.route("/api/conversations/mark_read", methods=["POST"])
@requires_auth
def api_conversation_mark_read():
    try:
        conv_id = request.form.get("conv_id") or (request.json or {}).get("conv_id")
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE tn_messages SET read_status=1 WHERE conversation_id=? AND direction=1", (conv_id,))
        conn.commit()
        conn.close()
        return jsonify({"code": 0, "msg": "已标记已读"})
    except Exception as e:
        log.error("api_conversation_mark_read error: %s", e)
        return jsonify({"code": 1, "msg": str(e)})
