"""代理(客服)管理 API"""

import hashlib
import logging

from flask import Blueprint, request, jsonify

from .. import requires_auth, require_role
from ..models.db import get_db, get_db_dict

log = logging.getLogger(__name__)
agents_bp = Blueprint("agents", __name__)


@agents_bp.route("/api/agents", methods=["GET"])
@requires_auth
@require_role("admin")
def api_agents():
    try:
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 20, type=int)
        conn = get_db_dict()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as c FROM tn_agents")
        total = cur.fetchone()["c"]
        offset = (page - 1) * limit
        cur.execute(
            "SELECT id, username, nickname, role, is_active, last_login_time, created_at FROM tn_agents ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        rows = cur.fetchall()
        conn.close()
        return jsonify({"code": 0, "msg": "", "count": total, "data": [dict(r) for r in rows]})
    except Exception as e:
        log.error("api_agents error: %s", e)
        return jsonify({"code": 1, "msg": str(e), "count": 0, "data": []})


@agents_bp.route("/api/agents/<int:aid>", methods=["GET"])
@requires_auth
@require_role("admin")
def api_agent_detail(aid):
    try:
        conn = get_db_dict()
        cur = conn.cursor()
        cur.execute("SELECT id, username, nickname, role, is_active, last_login_time, created_at FROM tn_agents WHERE id=?", (aid,))
        row = cur.fetchone()
        conn.close()
        if row:
            return jsonify({"code": 0, "msg": "", "data": dict(row)})
        return jsonify({"code": 1, "msg": "代理不存在"})
    except Exception as e:
        log.error("api_agent_detail error: %s", e)
        return jsonify({"code": 1, "msg": str(e)})


@agents_bp.route("/api/agents/add", methods=["POST"])
@requires_auth
@require_role("admin")
def api_agent_add():
    try:
        data = request.get_json() or {}
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        if not username or not password:
            return jsonify({"code": 1, "msg": "用户名和密码不能为空"})

        pwd_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO tn_agents (username, password_hash, nickname, role, is_active) VALUES (?, ?, ?, ?, ?)",
            (username, pwd_hash, data.get("nickname", ""), data.get("role", "agent"), 1 if data.get("is_active", True) else 0),
        )
        conn.commit()
        conn.close()
        return jsonify({"code": 0, "msg": "添加成功"})
    except Exception as e:
        log.error("api_agent_add error: %s", e)
        return jsonify({"code": 1, "msg": str(e)})


@agents_bp.route("/api/agents/update", methods=["POST"])
@requires_auth
@require_role("admin")
def api_agent_update():
    try:
        data = request.get_json() or {}
        aid = data.get("id")
        if not aid:
            return jsonify({"code": 1, "msg": "缺少ID"})

        conn = get_db()
        cur = conn.cursor()
        fields = []
        values = []
        if data.get("nickname") is not None:
            fields.append("nickname=?")
            values.append(data["nickname"])
        if data.get("role") is not None:
            fields.append("role=?")
            values.append(data["role"])
        if data.get("is_active") is not None:
            fields.append("is_active=?")
            values.append(1 if data["is_active"] else 0)
        if data.get("password"):
            fields.append("password_hash=?")
            values.append(hashlib.sha256(data["password"].encode("utf-8")).hexdigest())

        if fields:
            values.append(aid)
            cur.execute(f"UPDATE tn_agents SET {','.join(fields)} WHERE id=?", values)
            conn.commit()
        conn.close()
        return jsonify({"code": 0, "msg": "保存成功"})
    except Exception as e:
        log.error("api_agent_update error: %s", e)
        return jsonify({"code": 1, "msg": str(e)})


@agents_bp.route("/api/agents/delete", methods=["POST"])
@requires_auth
@require_role("admin")
def api_agent_delete():
    try:
        aid = request.form.get("id") or (request.json or {}).get("id")
        if str(aid) == "1":
            return jsonify({"code": 1, "msg": "不能删除管理员账号"})
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM tn_agents WHERE id=?", (aid,))
        conn.commit()
        conn.close()
        return jsonify({"code": 0, "msg": "删除成功"})
    except Exception as e:
        log.error("api_agent_delete error: %s", e)
        return jsonify({"code": 1, "msg": str(e)})
