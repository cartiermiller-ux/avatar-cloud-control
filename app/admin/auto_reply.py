from flask import request, jsonify
from app.admin import admin_bp, login_required, render_admin
from app.models.auto_reply_rule import AutoReplyRule
from app.models.group_info import GroupInfo
from app import db

# 自动回复页面
@admin_bp.route("/reply")
@login_required
def auto_reply_page():
    return render_admin("auto_reply.html", page="auto_reply")

# 获取规则列表
@admin_bp.route("/reply/getList")
@login_required
def reply_get_list():
    page = int(request.args.get("page",1))
    limit = int(request.args.get("limit",20))
    data = AutoReplyRule.query.limit(limit).offset((page-1)*limit).all()
    total = AutoReplyRule.query.count()
    res = []
    for rule in data:
        group_names = ",".join([g.group_name for g in GroupInfo.query.filter(GroupInfo.id.in_(rule.bind_group_ids.split(","))).all()]) if rule.bind_group_ids else "全部分组"
        res.append({
            "id": rule.id,
            "rule_name": rule.rule_name,
            "match_keyword": rule.match_keyword,
            "reply_text": rule.reply_text,
            "reply_img": rule.reply_img,
            "bind_group_names": group_names,
            "status": rule.status
        })
    return jsonify({"code":200, "count": total, "data": res})

# 新增规则弹窗
@admin_bp.route("/reply/addPopup")
@login_required
def reply_add_popup():
    group_list = GroupInfo.query.all()
    return render_admin("reply_add_popup.html", group_list=group_list)

# 开关规则状态
@admin_bp.route("/reply/switch", methods=["POST"])
@login_required
def reply_switch():
    rule_id = request.form.get("id")
    status = int(request.form.get("status"))
    rule = AutoReplyRule.query.get(rule_id)
    rule.status = status
    db.session.commit()
    return jsonify({"code":200, "msg": "状态切换成功"})

# 编辑规则弹窗
@admin_bp.route("/reply/editPopup")
@login_required
def reply_edit_popup():
    rule_id = request.args.get("id")
    rule = AutoReplyRule.query.get(rule_id)
    group_list = GroupInfo.query.all()
    return render_admin("reply_edit_popup.html", rule=rule, group_list=group_list)

# 删除规则
@admin_bp.route("/reply/del", methods=["POST"])
@login_required
def reply_del():
    rule_id = request.form.get("id")
    rule = AutoReplyRule.query.get(rule_id)
    db.session.delete(rule)
    db.session.commit()
    return jsonify({"code":200, "msg": "规则删除成功"})