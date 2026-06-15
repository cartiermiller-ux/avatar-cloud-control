"""业务员分配 & 日志 API"""

import logging
from datetime import datetime

from flask import Blueprint, request, jsonify, session

from .. import requires_auth, require_role
from ..models.db import get_db, get_db_dict

log = logging.getLogger(__name__)
salesman_assign_bp = Blueprint("salesman_assign", __name__)


@salesman_assign_bp.route("/api/accounts/assign_salesman", methods=["POST"])
@requires_auth
@require_role("admin")
def api_assign_salesman():
    try:
        data = request.get_json() or {}
        account_ids = data.get("account_ids", [])
        salesman_id = data.get("salesman_id")
        operator_id = session.get("agent_id")

        if not account_ids:
            return jsonify({"code": 1, "msg": "请选择账号"})
        if not salesman_id:
            return jsonify({"code": 1, "msg": "请选择业务员"})

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM tn_salesman WHERE id=?", (salesman_id,))
        sm = cur.fetchone()
        if not sm:
            conn.close()
            return jsonify({"code": 1, "msg": "业务员不存在"})

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        success = 0
        fail = 0
        for aid in account_ids:
            try:
                cur.execute("SELECT salesman_id FROM tn_accounts WHERE id=?", (aid,))
                row = cur.fetchone()
                if not row:
                    fail += 1
                    continue
                old_sid = row[0]
                cur.execute("UPDATE tn_accounts SET salesman_id=?, updated_at=? WHERE id=?", (salesman_id, now, aid))
                cur.execute(
                    """INSERT INTO tn_account_assign_log
                    (account_id, old_salesman_id, new_salesman_id, operate_type, operator_id, operate_time)
                    VALUES (?, ?, ?, 'assign', ?, ?)""",
                    (aid, old_sid, salesman_id, operator_id, now),
                )
                success += 1
            except Exception as ex:
                log.error("assign aid=%s error: %s", aid, ex)
                fail += 1
        conn.commit()
        conn.close()
        return jsonify({"code": 0, "msg": f"分配完成：成功{success}个，失败{fail}个", "data": {"success": success, "fail": fail}})
    except Exception as e:
        log.error("api_assign_salesman error: %s", e)
        return jsonify({"code": 1, "msg": str(e)})


@salesman_assign_bp.route("/api/accounts/recover", methods=["POST"])
@requires_auth
@require_role("admin")
def api_accounts_recover():
    try:
        data = request.get_json() or {}
        account_ids = data.get("account_ids", [])
        operator_id = session.get("agent_id")

        if not account_ids:
            return jsonify({"code": 1, "msg": "请选择账号"})

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_db()
        cur = conn.cursor()
        success = 0
        fail = 0
        for aid in account_ids:
            try:
                cur.execute("SELECT salesman_id FROM tn_accounts WHERE id=?", (aid,))
                row = cur.fetchone()
                if not row or not row[0]:
                    fail += 1
                    continue
                old_sid = row[0]
                cur.execute("UPDATE tn_accounts SET salesman_id=NULL, updated_at=? WHERE id=?", (now, aid))
                cur.execute(
                    """INSERT INTO tn_account_assign_log
                    (account_id, old_salesman_id, new_salesman_id, operate_type, operator_id, operate_time)
                    VALUES (?, ?, NULL, 'recover', ?, ?)""",
                    (aid, old_sid, operator_id, now),
                )
                success += 1
            except Exception as ex:
                log.error("recover aid=%s error: %s", aid, ex)
                fail += 1
        conn.commit()
        conn.close()
        return jsonify({"code": 0, "msg": f"回收完成：成功{success}个，失败{fail}个", "data": {"success": success, "fail": fail}})
    except Exception as e:
        log.error("api_accounts_recover error: %s", e)
        return jsonify({"code": 1, "msg": str(e)})


@salesman_assign_bp.route("/api/salesman/accounts", methods=["GET"])
@requires_auth
def api_salesman_account_list():
    try:
        role = session.get("agent_role")
        salesman_id = session.get("agent_id")

        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 20, type=int)
        search = request.args.get("search", "")
        offset = (page - 1) * limit

        conn = get_db_dict()
        cur = conn.cursor()

        if role == "admin":
            base_sql = """SELECT a.*, p.ip as bind_ip, s.name as salesman_name
                FROM tn_accounts a
                LEFT JOIN tn_account_ip ai ON a.id = ai.account_id
                LEFT JOIN tn_ip_pool p ON ai.ip_id = p.id
                LEFT JOIN tn_salesman s ON a.salesman_id = s.id"""
        else:
            base_sql = f"""SELECT a.*, p.ip as bind_ip, s.name as salesman_name
                FROM tn_accounts a
                LEFT JOIN tn_account_ip ai ON a.id = ai.account_id
                LEFT JOIN tn_ip_pool p ON ai.ip_id = p.id
                LEFT JOIN tn_salesman s ON a.salesman_id = s.id
                WHERE a.salesman_id = {salesman_id}"""

        if search:
            like = f"%{search}%"
            if "WHERE" in base_sql:
                base_sql += f" AND (a.username LIKE '{like}' OR a.phone_number LIKE '{like}')"
            else:
                base_sql += f" WHERE a.username LIKE '{like}' OR a.phone_number LIKE '{like}'"

        cur.execute(f"SELECT COUNT(*) as c FROM ({base_sql}) as t")
        total = cur.fetchone()["c"]
        cur.execute(base_sql + f" ORDER BY a.id DESC LIMIT {limit} OFFSET {offset}")
        rows = cur.fetchall()
        conn.close()
        return jsonify({"code": 0, "msg": "", "count": total, "data": [dict(r) for r in rows]})
    except Exception as e:
        log.error("api_salesman_account_list error: %s", e)
        return jsonify({"code": 1, "msg": str(e), "count": 0, "data": []})


@salesman_assign_bp.route("/api/assign_logs", methods=["GET"])
@requires_auth
@require_role("admin")
def api_assign_logs():
    try:
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 20, type=int)
        offset = (page - 1) * limit

        conn = get_db_dict()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as c FROM tn_account_assign_log")
        total = cur.fetchone()["c"]

        cur.execute(
            f"""SELECT l.*,
            a.username as account_username,
            os.name as old_salesman_name,
            ns.name as new_salesman_name,
            op.username as operator_name
            FROM tn_account_assign_log l
            LEFT JOIN tn_accounts a ON l.account_id = a.id
            LEFT JOIN tn_salesman os ON l.old_salesman_id = os.id
            LEFT JOIN tn_salesman ns ON l.new_salesman_id = ns.id
            LEFT JOIN tn_agents op ON l.operator_id = op.id
            ORDER BY l.id DESC LIMIT {limit} OFFSET {offset}"""
        )
        rows = cur.fetchall()
        conn.close()
        return jsonify({"code": 0, "msg": "", "count": total, "data": [dict(r) for r in rows]})
    except Exception as e:
        log.error("api_assign_logs error: %s", e)
        return jsonify({"code": 1, "msg": str(e), "count": 0, "data": []})


@salesman_assign_bp.route("/api/accounts/unassign_salesman", methods=["POST"])
@requires_auth
def api_unassign_salesman():
    try:
        data = request.get_json() or {}
        account_ids = data.get("account_ids", [])

        if not account_ids:
            return jsonify({"code": 1, "msg": "请选择账号"})

        conn = get_db()
        cur = conn.cursor()
        success = 0
        for aid in account_ids:
            cur.execute("UPDATE tn_accounts SET salesman_id=NULL WHERE id=?", (aid,))
            success += 1
        conn.commit()
        conn.close()
        return jsonify({"code": 0, "msg": f"已解除{success}个账号的业务员绑定"})
    except Exception as e:
        log.error("api_unassign_salesman error: %s", e)
        return jsonify({"code": 1, "msg": str(e)})


@salesman_assign_bp.route("/api/salesman/list_all", methods=["GET"])
@requires_auth
def api_salesman_list_all():
    try:
        conn = get_db_dict()
        cur = conn.cursor()
        cur.execute("SELECT id, name, employee_id FROM tn_salesman WHERE is_active=1 ORDER BY id")
        rows = cur.fetchall()
        conn.close()
        return jsonify({"code": 0, "data": [dict(r) for r in rows]})
    except Exception as e:
        log.error("api_salesman_list_all error: %s", e)
        return jsonify({"code": 1, "msg": str(e)})
