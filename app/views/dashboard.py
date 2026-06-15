"""控制台统计 API"""

import logging

from flask import Blueprint, jsonify

from .. import requires_auth
from ..models.db import get_db_dict

log = logging.getLogger(__name__)
dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/api/dashboard/stats", methods=["GET"])
@requires_auth
def api_dashboard_stats():
    try:
        conn = get_db_dict()
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) as c FROM tn_accounts")
        total_accounts = cur.fetchone()["c"]

        cur.execute("SELECT COUNT(*) as c FROM tn_accounts WHERE status=1")
        active_accounts = cur.fetchone()["c"]

        cur.execute("SELECT COUNT(*) as c FROM tn_conversations WHERE status=1")
        open_conversations = cur.fetchone()["c"]

        cur.execute("SELECT COUNT(*) as c FROM tn_messages WHERE direction=2 AND DATE(sent_at)=DATE('now')")
        today_replies = cur.fetchone()["c"]

        cur.execute(
            """SELECT m.id, m.content, m.sent_at, m.direction, a.username
               FROM tn_messages m
               LEFT JOIN tn_conversations c ON m.conversation_id=c.id
               LEFT JOIN tn_accounts a ON c.account_id=a.id
               ORDER BY m.sent_at DESC LIMIT 5"""
        )
        recent_messages = []
        for row in cur.fetchall():
            content = row["content"] or ""
            recent_messages.append(
                {
                    "id": row["id"],
                    "time": row["sent_at"].strftime("%m-%d %H:%M") if row["sent_at"] else "",
                    "account": row["username"] or "未知",
                    "content": content[:30] + "..." if len(content) > 30 else content,
                    "direction": row["direction"],
                }
            )

        conn.close()
        return jsonify(
            {
                "code": 0,
                "msg": "",
                "data": {
                    "active_accounts": active_accounts,
                    "total_accounts": total_accounts,
                    "open_conversations": open_conversations,
                    "today_replies": today_replies,
                    "system_status": "正常",
                    "recent_messages": recent_messages,
                },
            }
        )
    except Exception as e:
        log.error("api_dashboard_stats error: %s", e)
        return jsonify(
            {
                "code": 1,
                "msg": str(e),
                "data": {
                    "active_accounts": 0,
                    "total_accounts": 0,
                    "open_conversations": 0,
                    "today_replies": 0,
                    "system_status": "异常",
                    "recent_messages": [],
                },
            }
        )
