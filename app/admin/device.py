from flask import request, jsonify
from app.admin import admin_bp, login_required, role_required, render_admin
from app.models.device_info import DeviceInfo
from app.models.group_info import GroupInfo
from app import db

# 设备列表页面
@admin_bp.route("/device")
@login_required
def device_page():
    return render_admin("device_list.html", page="device")

# 获取设备表格数据
@admin_bp.route("/device/getList")
@login_required
def device_get_list():
    key = request.args.get("key", "")
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))
    query = DeviceInfo.query.join(GroupInfo, GroupInfo.id == DeviceInfo.group_id)
    if key:
        query = query.filter(
            DeviceInfo.device_name.like(f"%{key}%") | DeviceInfo.phone_number.like(f"%{key}%")
        )
    total = query.count()
    data = query.limit(limit).offset((page-1)*limit).all()
    res_list = []
    for item in data:
        res_list.append({
            "id": item.id,
            "device_name": item.device_name,
            "device_sn": item.device_sn,
            "phone_number": item.phone_number,
            "group_name": item.group_info.group_name,
            "online_status": item.online_status,
            "wifi_calling": item.wifi_calling,
            "last_heartbeat": item.last_heartbeat.strftime("%Y-%m-%d %H:%M:%S") if item.last_heartbeat else ""
        })
    return jsonify({"code":200, "count": total, "data": res_list})

# 刷新设备在线状态
@admin_bp.route("/device/refreshStatus", methods=["POST"])
@login_required
def device_refresh_status():
    dev_id = request.form.get("id")
    dev = DeviceInfo.query.get(dev_id)
    if not dev:
        return jsonify({"code":400, "msg": "设备不存在"})
    dev.last_heartbeat = db.func.now()
    db.session.commit()
    return jsonify({"code":200, "msg": "状态刷新成功"})

# 远程断开设备
@admin_bp.route("/device/disconnect", methods=["POST"])
@login_required
@role_required("admin")
def device_disconnect():
    dev_id = request.form.get("id")
    dev = DeviceInfo.query.get(dev_id)
    dev.remote_disconnect = 1
    dev.online_status = 0
    db.session.commit()
    # 此处可下发websocket断开指令给设备
    return jsonify({"code":200, "msg": "已远程断开设备连接"})

# 新增设备弹窗页面
@admin_bp.route("/device/addPopup")
@login_required
def device_add_popup():
    group_list = GroupInfo.query.all()
    return render_admin("device_add_popup.html", group_list=group_list)

# 编辑设备弹窗
@admin_bp.route("/device/editPopup")
@login_required
def device_edit_popup():
    dev_id = request.args.get("id")
    dev = DeviceInfo.query.get(dev_id)
    group_list = GroupInfo.query.all()
    return render_admin("device_edit_popup.html", dev=dev, group_list=group_list)