"""认证路由：登录、登出"""

import hashlib
import logging

from flask import Blueprint, render_template, request, redirect, session

from ..models.db import get_db_dict

log = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_db_dict()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, password_hash, role, nickname, is_active FROM tn_agents WHERE username=?",
            (username,),
        )
        agent = cur.fetchone()
        conn.close()

        if not agent:
            return render_template("login.html", error="账号不存在")
        if not agent["is_active"]:
            return render_template("login.html", error="账号已被禁用")

        pwd_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        if pwd_hash != agent["password_hash"]:
            return render_template("login.html", error="密码错误")

        session["agent_id"] = agent["id"]
        session["agent_username"] = agent["username"]
        session["agent_role"] = agent["role"]
        session["agent_nickname"] = agent["nickname"]
        return redirect("/")

    return render_template("login.html", error=None)


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
