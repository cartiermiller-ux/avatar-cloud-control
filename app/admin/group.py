from flask import request, jsonify
from app.admin import admin_bp, login_required, render_admin
from app.models.group_info import GroupInfo
from app import db

# 分组管理页面
@admin_bp.route("/group")
@login_required
def group_page():
    return render_admin("group_manage.html", page="group")

# 获取树形分组数据
@admin_bp.route("/group/getTree")
@login_required
def group_get_tree():
    all_group = GroupInfo.query.all()
    tree_data = []
    def build_tree(parent_id=0):
        child_list = []
        for g in all_group:
            if g.parent_id == parent_id:
                node = {
                    "id": g.id,
                    "group_name": g.group_name,
                    "children": build_tree(g.id)
                }
                child_list.append(node)
        return child_list
    tree_data = build_tree(0)
    return jsonify({"code":200, "data": tree_data})

# 新增分组
@admin_bp.route("/group/add", methods=["POST"])
@login_required
def group_add():
    parent_id = int(request.form.get("parent_id", 0))
    group_name = request.form.get("group_name")
    new_group = GroupInfo(parent_id=parent_id, group_name=group_name, desc="")
    db.session.add(new_group)
    db.session.commit()
    return jsonify({"code":200, "msg": "分组新增成功"})

# 编辑分组名称
@admin_bp.route("/group/edit", methods=["POST"])
@login_required
def group_edit():
    g_id = request.form.get("id")
    g = GroupInfo.query.get(g_id)
    g.group_name = request.form.get("group_name")
    db.session.commit()
    return jsonify({"code":200, "msg": "修改成功"})

# 删除分组
@admin_bp.route("/group/del", methods=["POST"])
@login_required
def group_del():
    g_id = request.form.get("id")
    g = GroupInfo.query.get(g_id)
    db.session.delete(g)
    db.session.commit()
    return jsonify({"code":200, "msg": "分组删除成功"})

# 分组下拉简单列表（统计页面使用）
@admin_bp.route("/group/getSimpleList")
@login_required
def group_simple_list():
    data = GroupInfo.query.all()
    res = [{"id": g.id, "group_name": g.group_name} for g in data]
    return jsonify({"code":200, "data": res})