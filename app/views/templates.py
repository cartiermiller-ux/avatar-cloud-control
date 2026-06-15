"""模板 API"""

import logging

from flask import Blueprint, jsonify

from .. import requires_auth
from ..models.db import get_db_dict

log = logging.getLogger(__name__)
templates_bp = Blueprint("templates", __name__)


@templates_bp.route("/api/templates", methods=["GET"])
@requires_auth
def api_templates():
    try:
        conn = get_db_dict()
        cur = conn.cursor()
        cur.execute("SELECT * FROM tn_templates WHERE is_active=1")
        rows = cur.fetchall()
        conn.close()
        return jsonify({"code": 0, "msg": "", "data": [dict(r) for r in rows]})
    except Exception as e:
        log.error("api_templates error: %s", e)
        return jsonify({"code": 1, "msg": str(e), "data": []})
