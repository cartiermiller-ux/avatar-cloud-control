from flask import request, jsonify
from app.admin import admin_bp, login_required, render_admin
from app.models.im_account import ImAccount
from app.models.device_info import DeviceInfo
from app.models.group_info import GroupInfo
from app import db

# 账号列表页面
@admin_bp.route("/account")
@login_required
def account_page():
    return render_admin("account_list.html", page="account")

# 获取账号表格数据
@admin_bp.route("/account/getList")
@login_required
def account_get_list():
    key = request.args.get("key", "")
    page = int(request.args.get("page",1))
    limit = int(request.args.get("limit",20))
    query = ImAccount.query.join(DeviceInfo, DeviceInfo.id == ImAccount.device_id).join(GroupInfo, GroupInfo.id == ImAccount.group_id)
    if key:
        query = query.filter(ImAccount.phone_number.like(f"%{key}%"))
    total = query.count()
    data = query.limit(limit).offset((page-1)*limit).all()
    res = []
    for item in data:
        res.append({
            "id": item.id,
            "phone_number": item.phone_number,
            "account_type": item.account_type,
            "device_name": item.device_info.device_name,
            "group_name": item.group_info.group_name,
            "register_status": item.register_status,
            "maturity_level": item.maturity_level,
            "reconnect_count": item.reconnect_count
        })
    return jsonify({"code":200, "count": total, "data": res})

# 同步所有设备账号
@admin_bp.route("/account/syncAll", methods=["POST"])
@login_required
def account_sync_all():
    # 模拟同步逻辑，生产对接设备websocket拉取账号
    return jsonify({"code":200, "msg": "账号同步任务已下发，请稍后刷新列表"})

# 掉线重连账号
@admin_bp.route("/account/reconnect", methods=["POST"])
@login_required
def account_reconnect():
    acc_id = request.form.get("id")
    acc = ImAccount.query.get(acc_id)
    acc.reconnect_count += 1
    db.session.commit()
    # 下发重连指令给对应设备
    return jsonify({"code":200, "msg": "已下发账号重连指令"})

# 编辑账号弹窗
@admin_bp.route("/account/edit")
@login_required
def account_edit_popup():
    acc_id = request.args.get("id")
    acc = ImAccount.query.get(acc_id)
    device_list = DeviceInfo.query.filter_by(online_status=1).all()
    group_list = GroupInfo.query.all()
    return render_admin("account_edit_popup.html", acc=acc, device_list=device_list, group_list=group_list)