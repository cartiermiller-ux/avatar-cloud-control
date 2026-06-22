from flask import Blueprint, request, redirect, url_for, session, jsonify, render_template
from functools import wraps

# 创建admin蓝图
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# 全局登录校验装饰器
def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session or "role" not in session:
            # 未登录跳转登录页
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"code": 401, "msg": "请先登录系统"})
            return redirect(url_for("admin.login_page"))
        return func(*args, **kwargs)
    return wrapper

# 角色权限校验装饰器 root > admin > user
def role_required(min_role="user"):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            role_map = {"user": 1, "admin": 2, "root": 3}
            user_role = session.get("role", "user")
            if role_map[user_role] < role_map[min_role]:
                return jsonify({"code": 403, "msg": "权限不足，无法操作"})
            return func(*args, **kwargs)
        return wrapper
    return decorator

# 页面路由统一渲染封装
def render_admin(template_name, **kwargs):
    # 注入全局session变量给模板
    kwargs["session"] = session
    return render_template(template_name, **kwargs)

# 导入各模块接口并注册
from . import auth, device, account, group, key, push, auto_reply, chat, stat, upload