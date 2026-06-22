from flask import request, jsonify
from app.admin import admin_bp, login_required, render_admin
from app.models.push_task import PushTask
from app.models.group_info import GroupInfo
from app import db

# 推送任务页面
@admin_bp.route("/push/task")
@login_required
def push_task_page():
    return render_admin("push_task.html", page="push_task")

# 获取任务列表
@admin_bp.route("/push/getTaskList")
@login_required
def push_get_task_list():
    page = int(request.args.get("page",1))
    limit = int(request.args.get("limit",20))
    data = PushTask.query.limit(limit).offset((page-1)*limit).all()
    total = PushTask.query.count()
    res = []
    for task in data:
        # 拼接分组名称
        group_names = ",".join([g.group_name for g in GroupInfo.query.filter(GroupInfo.id.in_(task.group_ids.split(","))).all()])
        res.append({
            "id": task.id,
            "task_name": task.task_name,
            "group_names": group_names,
            "total_count": task.total_count,
            "send_count": task.send_count,
            "success_count": task.success_count,
            "fail_count": task.fail_count,
            "reply_count": task.reply_count,
            "progress": task.progress,
            "status": task.status,
            "create_time": task.create_time.strftime("%Y-%m-%d %H:%M:%S")
        })
    return jsonify({"code":200, "count": total, "data": res})

# 新建推送任务弹窗
@admin_bp.route("/push/addTaskPopup")
@login_required
def push_add_task_popup():
    group_list = GroupInfo.query.all()
    return render_admin("push_add_popup.html", group_list=group_list)

# 终止运行中任务
@admin_bp.route("/push/stopTask", methods=["POST"])
@login_required
def push_stop_task():
    task_id = request.form.get("id")
    task = PushTask.query.get(task_id)
    task.status = "已终止"
    db.session.commit()
    # 下发celery停止任务指令
    return jsonify({"code":200, "msg": "任务已终止"})

# 任务详情弹窗
@admin_bp.route("/push/taskDetail")
@login_required
def push_task_detail():
    task_id = request.args.get("id")
    task = PushTask.query.get(task_id)
    return render_admin("push_task_detail.html", task=task)