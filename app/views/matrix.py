"""矩阵群发 API"""

import logging
import threading

from flask import Blueprint, request, jsonify, session

from .. import requires_auth
from ..models.db import get_db, get_db_dict
from ..core.messenger import run_matrix_task

log = logging.getLogger(__name__)
matrix_bp = Blueprint("matrix", __name__)


@matrix_bp.route("/api/matrix/tasks", methods=["GET"])
@requires_auth
def api_matrix_tasks():
    try:
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 20, type=int)
        conn = get_db_dict()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as c FROM tn_broadcast_task")
        total = cur.fetchone()["c"]
        offset = (page - 1) * limit
        cur.execute(
            """SELECT id, name, content, status, total_count, sent_count, failed_count,
                    created_by, created_at, started_at, finished_at
                    FROM tn_broadcast_task ORDER BY id DESC LIMIT ? OFFSET ?""",
            (limit, offset),
        )
        rows = cur.fetchall()
        conn.close()
        return jsonify({"code": 0, "msg": "", "count": total, "data": [dict(r) for r in rows]})
    except Exception as e:
        log.error("api_matrix_tasks error: %s", e)
        return jsonify({"code": 1, "msg": str(e), "count": 0, "data": []})


@matrix_bp.route("/api/matrix/tasks/<int:tid>", methods=["GET"])
@requires_auth
def api_matrix_task_detail(tid):
    try:
        conn = get_db_dict()
        cur = conn.cursor()
        cur.execute("SELECT * FROM tn_broadcast_task WHERE id=?", (tid,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return jsonify({"code": 1, "msg": "任务不存在"})
        return jsonify({"code": 0, "data": dict(row)})
    except Exception as e:
        log.error("api_matrix_task_detail error: %s", e)
        return jsonify({"code": 1, "msg": str(e)})


@matrix_bp.route("/api/matrix/create", methods=["POST"])
@requires_auth
def api_matrix_create():
    try:
        data = request.get_json() or {}
        name = data.get("name", "").strip()
        task_type = data.get("task_type", "text").strip()
        content = data.get("content", "").strip()
        image_path = data.get("image_path", "").strip()
        account_ids = data.get("account_ids", [])
        target_numbers = data.get("target_numbers", [])

        if not name:
            return jsonify({"code": 1, "msg": "请输入任务名称"})
        if task_type not in ("text", "image", "link", "image_link"):
            return jsonify({"code": 1, "msg": "无效的任务类型"})
        if task_type in ("text", "link") and not content:
            return jsonify({"code": 1, "msg": "请输入群发内容"})
        if not account_ids:
            return jsonify({"code": 1, "msg": "请选择发送账号"})
        if not target_numbers:
            return jsonify({"code": 1, "msg": "请输入目标号码"})
        if task_type in ("image", "image_link") and not image_path:
            return jsonify({"code": 1, "msg": "请上传图片"})

        username = session.get("agent_username", "admin")
        conn = get_db_dict()
        cur = conn.cursor()
        cur.execute("SELECT id FROM tn_agents WHERE username=?", (username,))
        agent = cur.fetchone()
        agent_id = agent["id"] if agent else 1

        total = len(target_numbers)
        cur.execute(
            """INSERT INTO tn_broadcast_task
            (name, task_name, task_type, content, image_path, status, total_count, sent_count, failed_count, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, 0, ?, 0, 0, ?, datetime('now'))""",
            (name, name, task_type, content, image_path, total, agent_id),
        )
        task_id = cur.lastrowid

        for number in target_numbers:
            for acc_id in account_ids:
                cur.execute(
                    "INSERT INTO tn_broadcast_item (task_id, account_id, target_number, status, retry_count) VALUES (?, ?, ?, 0, 0)",
                    (task_id, acc_id, number.strip()),
                )

        conn.commit()
        conn.close()
        return jsonify({"code": 0, "msg": f"任务创建成功（ID: {task_id}）", "data": {"id": task_id}})
    except Exception as e:
        log.error("api_matrix_create error: %s", e)
        return jsonify({"code": 1, "msg": str(e)})


@matrix_bp.route("/api/matrix/start", methods=["POST"])
@requires_auth
def api_matrix_start():
    try:
        tid = request.form.get("id") or request.json.get("id")
        if not tid:
            return jsonify({"code": 1, "msg": "缺少任务ID"})

        conn = get_db_dict()
        cur = conn.cursor()
        cur.execute("SELECT status FROM tn_broadcast_task WHERE id=?", (tid,))
        task = cur.fetchone()
        conn.close()

        if not task:
            return jsonify({"code": 1, "msg": "任务不存在"})
        if task["status"] == 1:
            return jsonify({"code": 1, "msg": "任务正在运行中"})
        if task["status"] == 2:
            return jsonify({"code": 1, "msg": "任务已完成，请创建新任务"})

        t = threading.Thread(target=run_matrix_task, args=(tid,), daemon=True)
        t.start()
        log.info("矩阵群发任务 %s 已启动", tid)
        return jsonify({"code": 0, "msg": "任务已启动"})
    except Exception as e:
        log.error("api_matrix_start error: %s", e)
        return jsonify({"code": 1, "msg": str(e)})


@matrix_bp.route("/api/matrix/pause", methods=["POST"])
@requires_auth
def api_matrix_pause():
    try:
        tid = request.form.get("id") or request.json.get("id")
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE tn_broadcast_task SET status=3 WHERE id=? AND status=1", (tid,))
        conn.commit()
        conn.close()
        return jsonify({"code": 0, "msg": "任务已暂停"})
    except Exception as e:
        log.error("api_matrix_pause error: %s", e)
        return jsonify({"code": 1, "msg": str(e)})
