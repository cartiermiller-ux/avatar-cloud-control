import uuid
from flask import request, jsonify
from app.admin import admin_bp, login_required, render_admin
from app.models.api_key import ApiKey
from app.models.api_code_request_log import ApiCodeRequestLog
from app.models.group_info import GroupInfo
from app import db

# 接码管理(一) 密钥页面
@admin_bp.route("/key/list1")
@login_required
def key_list_page1():
    return render_admin("key_list.html", page="key1")

# 接码管理(二) 复用同一页面模板，仅区分分组过滤逻辑
@admin_bp.route("/key/list2")
@login_required
def key_list_page2():
    return render_admin("key_list.html", page="key2")

# 获取密钥列表表格数据
@admin_bp.route("/key/getList")
@login_required
def key_get_list():
    name = request.args.get("name", "")
    page = int(request.args.get("page",1))
    limit = int(request.args.get("limit",20))
    query = ApiKey.query
    if name:
        query = query.filter(ApiKey.name.like(f"%{name}%"))
    total = query.count()
    data = query.limit(limit).offset((page-1)*limit).all()
    res = []
    for item in data:
        res.append({
            "id": item.id,
            "name": item.name,
            "key_str": item.key_str,
            "access_scope": item.access_scope,
            "status": item.status,
            "last_use_time": item.last_use_time.strftime("%Y-%m-%d %H:%M:%S") if item.last_use_time else "",
            "create_time": item.create_time.strftime("%Y-%m-%d %H:%M:%S")
        })
    return jsonify({"code":200, "count": total, "data": res})

# 获取取码请求日志（第二个Tab页面）
@admin_bp.route("/key/getRequestLog")
@login_required
def key_get_request_log():
    page = int(request.args.get("page",1))
    limit = int(request.args.get("limit",20))
    query = ApiCodeRequestLog.query.join(ApiKey, ApiKey.id == ApiCodeRequestLog.api_key_id)
    total = query.count()
    data = query.limit(limit).offset((page-1)*limit).all()
    res = []
    for log in data:
        res.append({
            "id": log.id,
            "key_name": log.api_key.name,
            "request_api": log.request_api,
            "phone_number": log.phone_number,
            "request_ip": log.request_ip,
            "response_code": log.response_code,
            "create_time": log.create_time.strftime("%Y-%m-%d %H:%M:%S")
        })
    return jsonify({"code":200, "count": total, "data": res})

# 创建密钥弹窗
@admin_bp.route("/key/createPopup")
@login_required
def key_create_popup():
    group_list = GroupInfo.query.all()
    return render_admin("key_create_popup.html", group_list=group_list)

# 生成新密钥并保存
@admin_bp.route("/key/create", methods=["POST"])
@login_required
def key_create_submit():
    name = request.form.get("name")
    access_scope = request.form.get("access_scope")
    bind_group_ids = request.form.get("bind_group_ids")
    # 生成唯一密钥 gck_xxxx
    new_key_str = f"gck_{str(uuid.uuid4()).replace('-','')[:32]}"
    new_key = ApiKey(
        name=name,
        key_str=new_key_str,
        access_scope=access_scope,
        bind_group_ids=bind_group_ids,
        status=1
    )
    db.session.add(new_key)
    db.session.commit()
    return jsonify({"code":200, "msg": "密钥创建成功", "key": new_key_str})

# 编辑密钥弹窗
@admin_bp.route("/key/editPopup")
@login_required
def key_edit_popup():
    k_id = request.args.get("id")
    key_info = ApiKey.query.get(k_id)
    group_list = GroupInfo.query.all()
    return render_admin("key_edit_popup.html", key=key_info, group_list=group_list)

# 更新密钥启用/停用状态
@admin_bp.route("/key/updateStatus", methods=["POST"])
@login_required
def key_update_status():
    k_id = request.form.get("id")
    status = int(request.form.get("status"))
    key_info = ApiKey.query.get(k_id)
    key_info.status = status
    db.session.commit()
    return jsonify({"code":200, "msg": "状态修改成功"})

# 删除密钥
@admin_bp.route("/key/del", methods=["POST"])
@login_required
def key_del():
    k_id = request.form.get("id")
    key_info = ApiKey.query.get(k_id)
    db.session.delete(key_info)
    db.session.commit()
    return jsonify({"code":200, "msg": "密钥删除成功"})