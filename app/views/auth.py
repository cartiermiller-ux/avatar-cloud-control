"""认证路由：登录、登出"""

import hashlib
import logging

from flask import Blueprint, render_template, request, redirect, url_for, session

from ..models.db import get_db_dict

log = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__)


def _verify_password(password: str, stored_hash: str) -> bool:
    """验证密码（兼容 SHA-256 和 bcrypt）"""
    # 先尝试 bcrypt
    try:
        import bcrypt
        if stored_hash.startswith("$2b$") or stored_hash.startswith("$2a$"):
            return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
    except ImportError:
        pass
    # 兼容旧 SHA-256 无盐哈希
    return hashlib.sha256(password.encode("utf-8")).hexdigest() == stored_hash


def _hash_password(password: str) -> str:
    """哈希密码（优先 bcrypt，回退 SHA-256）"""
    try:
        import bcrypt
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(12)).decode("utf-8")
    except ImportError:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()


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

        if not _verify_password(password, agent["password_hash"]):
            return render_template("login.html", error="密码错误")

        # 会话固定攻击防护：登录成功后重新生成 session
        old_data = {k: v for k, v in session.items() if k.startswith("agent_")}
        session.clear()
        session.update(old_data)
        session["agent_id"] = agent["id"]
        session["agent_username"] = agent["username"]
        session["agent_role"] = agent["role"]
        session["agent_nickname"] = agent["nickname"]

        # 如果是旧 SHA-256 哈希，自动升级为 bcrypt
        if not agent["password_hash"].startswith(("$2b$", "$2a$")):
            try:
                conn = get_db_dict()
                cur = conn.cursor()
                cur.execute(
                    "UPDATE tn_agents SET password_hash=? WHERE id=?",
                    (_hash_password(password), agent["id"]),
                )
                conn.commit()
                conn.close()
            except Exception:
                pass  # 升级失败不影响登录

        return redirect(url_for("pages.index"))

    return render_template("login.html", error=None)


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
