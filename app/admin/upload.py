import os
import time
from flask import request, jsonify
from PIL import Image
from app.admin import admin_bp, login_required

# 上传图片接口
@admin_bp.route("/upload/img", methods=["POST"])
@login_required
def upload_img():
    upload_file = request.files["file"]
    if not upload_file:
        return jsonify({"code":400, "msg": "未选择文件"})
    # 存储目录
    save_dir = "static/upload/img"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    # 生成文件名
    suffix = upload_file.filename.split(".")[-1]
    filename = f"{int(time.time())}.{suffix}"
    save_path = os.path.join(save_dir, filename)
    upload_file.save(save_path)
    # 返回访问url
    url = f"/static/upload/img/{filename}"
    return jsonify({"code":200, "url": url, "msg": "上传成功"})