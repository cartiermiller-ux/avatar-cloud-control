"""业务员管理 API"""

import logging

from flask import Blueprint, request, jsonify

from .. import requires_auth, require_role
from ..models.db import get_db, get_db_dict

log = logging.getLogger(__name__)
salesmen_bp = Blueprint("salesmen", __name__)


@salesmen_bp.route("/api/salesmen", methods=["GET"])
@requires_auth
@require_role("admin")
def api_salesmen():
    try:
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 20, type=int)
        search = request.args.get("search", "")
        conn = get_db_dict()
        cur = conn.cursor()
        if search:
            like = f"%{search}%"
            cur.execute("SELECT COUNT(*) as c FROM tn_salesman WHERE name LIKE ? OR employee_id LIKE ?", (like, like))
        else:
            cur.execute("SELECT COUNT(*) as c FROM tn_salesman")
        total = cur.fetchone()["c"]
        offset = (page - 1) * limit
        if search:
            like = f"%{search}%"
            cur.execute(
                "SELECT * FROM tn_salesman WHERE name LIKE ? OR employee_id LIKE ? ORDER BY id DESC LIMIT ? OFFSET ?",
                (like, like, limit, offset),
            )
        else:
            cur.execute("SELECT * FROM tn_salesman ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset))
        rows = cur.fetchall()
        conn.close()
        return jsonify({"code": 0, "msg": "", "count": total, "data": [dict(r) for r in rows]})
    except Exception as e:
        log.error("api_salesmen error: %s", e)
        return jsonify({"code": 1, "msg": str(e), "count": 0, "data": []})


@salesmen_bp.route("/api/salesmen/<int:sid>", methods=["GET"])
@requires_auth
@require_role("admin")
def api_salesman_detail(sid):
    try:
        conn = get_db_dict()
        cur = conn.cursor()
        cur.execute("SELECT * FROM tn_salesman WHERE id=?", (sid,))
        row = cur.fetchone()
        conn.close()
        if row:
            d = dict(row)
            d["account_ids"] = []
            return jsonify({"code": 0, "msg": "", "data": d})
        return jsonify({"code": 1, "msg": "业务员不存在"})
    except Exception as e:
        log.error("api_salesman_detail error: %s", e)
        return jsonify({"code": 1, "msg": str(e)})


@salesmen_bp.route("/api/salesmen/<int:sid>/performance", methods=["GET"])
@requires_auth
@require_role("admin")
def api_salesman_performance(sid):
    try:
        conn = get_db_dict()
        cur = conn.cursor()
        cur.execute("SELECT * FROM tn_salesman WHERE id=?", (sid,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return jsonify({"code": 1, "msg": "业务员不存在"})
        d = dict(row)
        return jsonify(
            {
                "code": 0,
                "msg": "",
                "data": {
                    "name": d["name"],
                    "employee_id": d["employee_id"],
                    "account_count": d.get("account_count", 0),
                    "monthly_replies": 0,
                    "monthly_broadcasts": 0,
                    "conversion_rate": 0,
                },
            }
        )
    except Exception as e:
        log.error("api_salesman_performance error: %s", e)
        return jsonify({"code": 1, "msg": str(e)})


@salesmen_bp.route("/api/salesmen/add", methods=["POST"])
@requires_auth
@require_role("admin")
def api_salesman_add():
    try:
        data = request.get_json() or {}
        name = data.get("name", "").strip()
        employee_id = data.get("employee_id", "").strip()
        if not name or not employee_id:
            return jsonify({"code": 1, "msg": "姓名和工号不能为空"})
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO tn_salesman (name, employee_id, phone, email, is_active) VALUES (?, ?, ?, ?, ?)",
            (name, employee_id, data.get("phone", ""), data.get("email", ""), 1 if data.get("is_active", True) else 0),
        )
        conn.commit()
        conn.close()
        return jsonify({"code": 0, "msg": "添加成功"})
    except Exception as e:
        log.error("api_salesman_add error: %s", e)
        return jsonify({"code": 1, "msg": str(e)})


@salesmen_bp.route("/api/salesmen/update", methods=["POST"])
@requires_auth
@require_role("admin")
def api_salesman_update():
    try:
        data = request.get_json() or {}
        sid = data.get("id")
        if not sid:
            return jsonify({"code": 1, "msg": "缺少ID"})
        conn = get_db()
        cur = conn.cursor()
        fields = []
        values = []
        for k in ["name", "employee_id", "phone", "email"]:
            if data.get(k) is not None:
                fields.append(f"{k}=?")
                values.append(data[k])
        if data.get("is_active") is not None:
            fields.append("is_active=?")
            values.append(1 if data["is_active"] else 0)
        if fields:
            values.append(sid)
            cur.execute(f"UPDATE tn_salesman SET {','.join(fields)} WHERE id=?", values)
            conn.commit()
        conn.close()
        return jsonify({"code": 0, "msg": "保存成功"})
    except Exception as e:
        log.error("api_salesman_update error: %s", e)
        return jsonify({"code": 1, "msg": str(e)})


@salesmen_bp.route("/api/salesmen/delete", methods=["POST"])
@requires_auth
@require_role("admin")
def api_salesman_delete():
    try:
        sid = request.form.get("id") or (request.json or {}).get("id")
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM tn_salesman WHERE id=?", (sid,))
        conn.commit()
        conn.close()
        return jsonify({"code": 0, "msg": "删除成功"})
    except Exception as e:
        log.error("api_salesman_delete error: %s", e)
        return jsonify({"code": 1, "msg": str(e)})
