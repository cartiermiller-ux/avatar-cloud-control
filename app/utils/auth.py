from functools import wraps
from flask import session, redirect, url_for, jsonify

# 登录校验装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            # 接口返回json，页面跳转登录
            if request.path.startswith("/api"):
                return jsonify({"code": 401, "msg": "未登录，请先登录后台"})
            return redirect(url_for("admin.auth_login"))
        return f(*args, **kwargs)
    return decorated_function

# 角色权限校验装饰器
def role_required(allow_roles: list):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_role = session.get("role", "user")
            if user_role not in allow_roles:
                return jsonify({"code": 403, "msg": "当前账号无操作权限"})
            return f(*args, **kwargs)
        return decorated_function
    return decorator