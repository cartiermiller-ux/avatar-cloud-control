from flask import request, session, jsonify
from app.admin import admin_bp, login_required, render_admin
from app.models.sys_user import SysUser
from app import db
from passlib.hash import bcrypt

# 登录页面
@admin_bp.route("/login", methods=["GET"])
def login_page():
    return render_admin("login.html")

# 登录提交接口
@admin_bp.route("/login", methods=["POST"])
def login_submit():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    user = SysUser.query.filter_by(username=username, status=1).first()
    if not user or not bcrypt.verify(password, user.password):
        return jsonify({"code": 400, "msg": "账号或密码错误"})
    # 写入session
    session["user_id"] = user.id
    session["username"] = user.real_name
    session["role"] = user.role
    session["bind_group_ids"] = user.bind_group_ids
    user.last_login_time = db.func.now()
    db.session.commit()
    return jsonify({"code": 200, "msg": "登录成功"})

# 退出登录
@admin_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/admin/login")