"""注册任务 API"""

import logging
from threading import Thread

from flask import Blueprint, request, jsonify, session

from .. import requires_auth
from ..models.db import get_db, get_db_dict

log = logging.getLogger(__name__)
register_bp = Blueprint("register", __name__)


@register_bp.route("/api/register/tasks", methods=["GET"])
@requires_auth
def api_register_tasks():
    try:
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 20, type=int)
        conn = get_db_dict()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as c FROM tn_register_task")
        total = cur.fetchone()["c"]
        offset = (page - 1) * limit
        cur.execute("SELECT * FROM tn_register_task ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset))
        rows = cur.fetchall()
        conn.close()
        return jsonify({"code": 0, "msg": "", "count": total, "data": [dict(r) for r in rows]})
    except Exception as e:
        log.error("api_register_tasks error: %s", e)
        return jsonify({"code": 1, "msg": str(e), "count": 0, "data": []})


@register_bp.route("/api/register/create", methods=["POST"])
@requires_auth
def api_register_create():
    try:
        name = request.form.get("name", "").strip() or request.json.get("name", "")
        count = request.form.get("count") or request.json.get("count", "0")
        use_proxy = request.form.get("use_proxy") or request.json.get("use_proxy", "0")

        if not name:
            return jsonify({"code": 1, "msg": "请输入任务名称"})
        try:
            count = int(count)
        except ValueError:
            return jsonify({"code": 1, "msg": "注册数量必须是数字"})
        if count <= 0:
            return jsonify({"code": 1, "msg": "注册数量必须大于0"})
        if count > 100:
            return jsonify({"code": 1, "msg": "单次注册数量不能超过100个"})

        proxy_flag = 1 if use_proxy and str(use_proxy) not in ("0", "false", "off", "否", "") else 0

        if proxy_flag:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM tn_ip_pool WHERE status = 1 AND area LIKE '%US%'")
            available_ips = cur.fetchone()[0]
            conn.close()
            if available_ips < count:
                return jsonify({"code": 1, "msg": f"可用美国IP不足！需要{count}个，当前只有{available_ips}个。"})

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO tn_register_task (task_name, total_num, use_proxy, status, success_count, failed_count, created_at)
            VALUES (?, ?, ?, 1, 0, 0, datetime('now'))""",
            (name, count, proxy_flag),
        )
        task_id = cur.lastrowid
        conn.commit()
        conn.close()

        def _run_register_task(tid, cnt, use_proxy_flag):
            try:
                from ..core.register import batch_register_with_db
                batch_register_with_db(tid, cnt, use_proxy_flag)
            except Exception as e:
                log.error("Register task %d error: %s", tid, e)
                try:
                    c = get_db()
                    cc = c.cursor()
                    cc.execute("UPDATE tn_register_task SET status=3, updated_at=datetime('now') WHERE id=?", (tid,))
                    c.commit()
                    c.close()
                except Exception as ee:
                    log.error("Failed to update task status: %s", ee)

        Thread(target=_run_register_task, args=(task_id, count, bool(proxy_flag)), daemon=True).start()
        return jsonify({"code": 0, "msg": f"任务已创建并启动（ID: {task_id}），正在后台执行注册..."})
    except Exception as e:
        log.error("api_register_create error: %s", e)
        return jsonify({"code": 1, "msg": str(e)})


@register_bp.route("/api/register/cancel", methods=["POST"])
@requires_auth
def api_register_cancel():
    try:
        tid = request.form.get("id") or request.json.get("id")
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE tn_register_task SET status=3 WHERE id=? AND status IN (0,1)", (tid,))
        conn.commit()
        conn.close()
        return jsonify({"code": 0, "msg": "已取消"})
    except Exception as e:
        log.error("api_register_cancel error: %s", e)
        return jsonify({"code": 1, "msg": str(e)})
