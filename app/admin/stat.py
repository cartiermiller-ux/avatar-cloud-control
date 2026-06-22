from flask import request, jsonify, make_response
import pandas as pd
from io import BytesIO
from app.admin import admin_bp, login_required, render_admin
from app.models.stat_daily import StatDaily
from app.models.group_info import GroupInfo
from app import db

# 数据统计页面
@admin_bp.route("/stat")
@login_required
def stat_overview_page():
    return render_admin("stat_overview.html", page="stat")

# 获取汇总统计卡片数据
@admin_bp.route("/stat/getData")
@login_required
def stat_get_data():
    stat_date = request.args.get("stat_date")
    group_id = int(request.args.get("group_id", 0))
    query = StatDaily.query.filter_by(stat_date=stat_date)
    if group_id != 0:
        query = query.filter_by(group_id=group_id)
    data = query.first()
    if not data:
        empty_data = {
            "device_online_num":0,"total_send":0,"total_success":0,"total_fail":0,
            "total_reply":0,"total_get_code":0,"wifi_calling_online":0
        }
        return jsonify({"code":200, "data": empty_data})
    res = {
        "device_online_num": data.device_online_num,
        "total_send": data.total_send,
        "total_success": data.total_success,
        "total_fail": data.total_fail,
        "total_reply": data.total_reply,
        "total_get_code": data.total_get_code,
        "wifi_calling_online": data.wifi_calling_online
    }
    return jsonify({"code":200, "data": res})

# 分组明细表格数据
@admin_bp.route("/stat/getGroupDetail")
@login_required
def stat_get_group_detail():
    stat_date = request.args.get("stat_date")
    page = int(request.args.get("page",1))
    limit = int(request.args.get("limit",15))
    query = StatDaily.query.filter_by(stat_date=stat_date).filter(StatDaily.group_id != 0).join(GroupInfo, GroupInfo.id == StatDaily.group_id)
    total = query.count()
    data = query.limit(limit).offset((page-1)*limit).all()
    res = []
    for item in data:
        res.append({
            "group_name": item.group_info.group_name,
            "device_online_num": item.device_online_num,
            "total_send": item.total_send,
            "total_success": item.total_success,
            "total_fail": item.total_fail,
            "total_reply": item.total_reply,
            "total_get_code": item.total_get_code,
            "wifi_calling_online": item.wifi_calling_online
        })
    return jsonify({"code":200, "count": total, "data": res})

# 导出Excel报表
@admin_bp.route("/stat/exportExcel")
@login_required
def stat_export_excel():
    stat_date = request.args.get("stat_date")
    data_list = StatDaily.query.filter_by(stat_date=stat_date).filter(StatDaily.group_id !=0).join(GroupInfo, GroupInfo.id == StatDaily.group_id).all()
    export_data = []
    for row in data_list:
        export_data.append({
            "分组名称": row.group_info.group_name,
            "在线设备": row.device_online_num,
            "发送总量": row.total_send,
            "送达成功": row.total_success,
            "发送失败": row.total_fail,
            "收到回复": row.total_reply,
            "接码取号次数": row.total_get_code,
            "WiFi Calling在线设备": row.wifi_calling_online
        })
    df = pd.DataFrame(export_data)
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    response = make_response(output.read())
    response.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    response.headers["Content-Disposition"] = f'attachment; filename="{stat_date}_数据统计报表.xlsx"'
    return response