"""页面路由：渲染 HTML 模板"""

import logging

from flask import Blueprint, render_template

from .. import requires_auth, require_role

log = logging.getLogger(__name__)
pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/health")
def health():
    """健康检查端点 (用于 Docker 健康检查)"""
    return {"status": "ok"}, 200


@pages_bp.route("/")
@requires_auth
def index():
    return render_template("dashboard.html")


@pages_bp.route("/accounts")
@requires_auth
def accounts_page():
    return render_template("accounts.html")


@pages_bp.route("/register")
@requires_auth
def register_page():
    return render_template("register.html")


@pages_bp.route("/matrix")
@requires_auth
def matrix_page():
    return render_template("matrix.html")


@pages_bp.route("/conversations")
@requires_auth
def conversations_page():
    return render_template("conversations.html")


@pages_bp.route("/agents")
@requires_auth
@require_role("admin")
def agents_page():
    return render_template("agents.html")


@pages_bp.route("/salesmen")
@requires_auth
@require_role("admin")
def salesmen_page():
    return render_template("salesmen.html")


@pages_bp.route("/salesman/account")
@requires_auth
def salesman_account_page():
    return render_template("salesman_account.html")


@pages_bp.route("/assign_logs")
@requires_auth
@require_role("admin")
def assign_logs_page():
    return render_template("assign_logs.html")


@pages_bp.route("/ip_manage")
@requires_auth
def ip_manage_page():
    return render_template("ip_manage.html")
