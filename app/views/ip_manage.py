"""IP 池管理 API"""

import csv
import io
import json as json_mod
import logging

from flask import Blueprint, request, jsonify

from .. import requires_auth
from ..models.db import get_db, get_db_dict

log = logging.getLogger(__name__)
ip_bp = Blueprint("ip", __name__)


@ip_bp.route("/api/ip/list", methods=["GET"])
@requires_auth
def api_ip_list():
    try:
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 20, type=int)
        search_ip = request.args.get("ip", "")
        search_status = request.args.get("status", "")

        conn = get_db_dict()
        cur = conn.cursor()
        where = []
        params = []
        if search_ip:
            where.append("ip LIKE ?")
            params.append(f"%{search_ip}%")
        if search_status:
            where.append("status=?")
            params.append(int(search_status))
        where_sql = (" WHERE " + " AND ".join(where)) if where else ""

        cur.execute(f"SELECT COUNT(*) as c FROM tn_ip_pool{where_sql}", params)
        total = cur.fetchone()["c"]

        offset = (page - 1) * limit
        cur.execute(
            f"""SELECT id, ip, port, proxy_user, proxy_pwd, area, ip_type, status,
                    create_time, remark FROM tn_ip_pool{where_sql}
                    ORDER BY id DESC LIMIT ? OFFSET ?""",
            params + [limit, offset],
        )
        rows = cur.fetchall()
        conn.close()

        status_map = {1: "正常", 2: "已分配", 0: "禁用", 3: "失效"}
        data = []
        for r in rows:
            d = dict(r)
            d["status_text"] = status_map.get(d["status"], "未知")
            data.append(d)
        return jsonify({"code": 0, "msg": "", "count": total, "data": data})
    except Exception as e:
        log.error("api_ip_list error: %s", e)
        return jsonify({"code": 1, "msg": str(e), "count": 0, "data": []})


@ip_bp.route("/api/ip/save", methods=["POST"])
@requires_auth
def api_ip_save():
    try:
        data = request.get_json() or dict(request.form)
        ip_id = data.get("id")
        ip = data.get("ip", "").strip()
        port = data.get("port", type=int)
        if not ip or not port:
            return jsonify({"code": 1, "msg": "IP和端口不能为空"})

        conn = get_db()
        cur = conn.cursor()
        if ip_id:
            cur.execute(
                """UPDATE tn_ip_pool SET ip=?, port=?, proxy_user=?, proxy_pwd=?,
                        area=?, remark=? WHERE id=?""",
                (ip, port, data.get("proxy_user", ""), data.get("proxy_pwd", ""), data.get("area", ""), data.get("remark", ""), ip_id),
            )
        else:
            cur.execute(
                """INSERT INTO tn_ip_pool (ip, port, proxy_user, proxy_pwd, area, ip_type, status)
                        VALUES (?, ?, ?, ?, ?, 'residential', 1)""",
                (ip, port, data.get("proxy_user", ""), data.get("proxy_pwd", ""), data.get("area", "")),
            )
        conn.commit()
        conn.close()
        return jsonify({"code": 0, "msg": "保存成功"})
    except Exception as e:
        log.error("api_ip_save error: %s", e)
        return jsonify({"code": 1, "msg": str(e)})


@ip_bp.route("/api/ip/status", methods=["POST"])
@requires_auth
def api_ip_set_status():
    try:
        ip_id = request.form.get("id") or (request.json or {}).get("id")
        new_status = request.form.get("status") or (request.json or {}).get("status")
        if not ip_id or new_status is None:
            return jsonify({"code": 1, "msg": "参数缺失"})
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE tn_ip_pool SET status=? WHERE id=?", (int(new_status), ip_id))
        conn.commit()
        conn.close()
        return jsonify({"code": 0, "msg": "状态已更新"})
    except Exception as e:
        log.error("api_ip_set_status error: %s", e)
        return jsonify({"code": 1, "msg": str(e)})


@ip_bp.route("/api/ip/delete", methods=["POST"])
@requires_auth
def api_ip_delete():
    try:
        ip_id = request.form.get("id") or (request.json or {}).get("id")
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM tn_account_ip WHERE ip_id=?", (ip_id,))
        cur.execute("DELETE FROM tn_ip_pool WHERE id=?", (ip_id,))
        conn.commit()
        conn.close()
        return jsonify({"code": 0, "msg": "删除成功"})
    except Exception as e:
        log.error("api_ip_delete error: %s", e)
        return jsonify({"code": 1, "msg": str(e)})


@ip_bp.route("/api/ip/batch_import", methods=["POST"])
@requires_auth
def api_ip_batch_import():
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"code": 1, "msg": "未选择上传文件"})

        text = file.read().decode("utf-8-sig")
        rows_data = []
        if file.filename.endswith(".csv"):
            reader = csv.DictReader(io.StringIO(text))
            for row in reader:
                rows_data.append(row)
        elif file.filename.endswith(".jsonl"):
            for line in text.strip().splitlines():
                line = line.strip()
                if line:
                    rows_data.append(json_mod.loads(line))
        else:
            return jsonify({"code": 1, "msg": "仅支持 csv / jsonl 格式"})

        if not rows_data:
            return jsonify({"code": 1, "msg": "文件内容为空"})

        conn = get_db()
        cur = conn.cursor()
        succ = 0
        fail = 0
        for row in rows_data:
            try:
                ip = str(row.get("ip") or "").strip()
                port = int(row.get("port") or 0)
                if not ip or not port:
                    fail += 1
                    continue
                cur.execute(
                    """INSERT INTO tn_ip_pool (ip, port, proxy_user, proxy_pwd, area, ip_type, status, remark)
                            VALUES (?, ?, ?, ?, ?, 'residential', 1, ?)""",
                    (ip, port, str(row.get("proxy_user", "")), str(row.get("proxy_pwd", "")), str(row.get("area", "")), str(row.get("remark", ""))),
                )
                succ += 1
            except Exception:
                fail += 1
        conn.commit()
        conn.close()
        return jsonify({"code": 0, "msg": f"导入完成：成功 {succ} 条，失败 {fail} 条"})
    except Exception as e:
        log.error("api_ip_batch_import error: %s", e)
        return jsonify({"code": 1, "msg": str(e)})


@ip_bp.route("/api/ip/available", methods=["GET"])
@requires_auth
def api_ip_available():
    try:
        conn = get_db_dict()
        cur = conn.cursor()
        cur.execute("SELECT id, ip, port, area FROM tn_ip_pool WHERE status=1 ORDER BY id ASC")
        rows = cur.fetchall()
        conn.close()
        return jsonify({"code": 0, "msg": "", "data": [dict(r) for r in rows]})
    except Exception as e:
        log.error("api_ip_available error: %s", e)
        return jsonify({"code": 1, "msg": str(e), "data": []})


@ip_bp.route("/api/ip/assign", methods=["POST"])
@requires_auth
def api_ip_assign():
    try:
        data = request.get_json() or {}
        account_id = data.get("account_id")
        ip_id = data.get("ip_id")
        if not account_id or not ip_id:
            return jsonify({"code": 1, "msg": "参数缺失"})

        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM tn_account_ip WHERE account_id=?", (account_id,))
        cur.execute(
            """UPDATE tn_ip_pool SET status=1 WHERE id IN
                    (SELECT ip_id FROM tn_account_ip WHERE account_id=?)""",
            (account_id,),
        )
        cur.execute("INSERT OR REPLACE INTO tn_account_ip (account_id, ip_id) VALUES (?, ?)", (account_id, ip_id))
        cur.execute("UPDATE tn_ip_pool SET status=2 WHERE id=?", (ip_id,))
        conn.commit()
        conn.close()
        return jsonify({"code": 0, "msg": "IP分配成功"})
    except Exception as e:
        log.error("api_ip_assign error: %s", e)
        return jsonify({"code": 1, "msg": str(e)})


@ip_bp.route("/api/ip/unassign", methods=["POST"])
@requires_auth
def api_ip_unassign():
    try:
        account_id = request.form.get("account_id") or (request.json or {}).get("account_id")
        if not account_id:
            return jsonify({"code": 1, "msg": "缺少account_id"})
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """UPDATE tn_ip_pool SET status=1 WHERE id IN
                    (SELECT ip_id FROM tn_account_ip WHERE account_id=?)""",
            (account_id,),
        )
        cur.execute("DELETE FROM tn_account_ip WHERE account_id=?", (account_id,))
        conn.commit()
        conn.close()
        return jsonify({"code": 0, "msg": "已解除绑定"})
    except Exception as e:
        log.error("api_ip_unassign error: %s", e)
        return jsonify({"code": 1, "msg": str(e)})
