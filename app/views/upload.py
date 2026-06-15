"""文件上传 API"""

import os
import logging
from datetime import datetime

from flask import Blueprint, request, jsonify

from .. import requires_auth, UPLOAD_FOLDER

log = logging.getLogger(__name__)
upload_bp = Blueprint("upload", __name__)


@upload_bp.route("/api/upload/image", methods=["POST"])
@requires_auth
def upload_image():
    try:
        if "file" not in request.files:
            return jsonify({"code": 1, "msg": "没有上传文件"})

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"code": 1, "msg": "文件名为空"})

        ext = os.path.splitext(file.filename)[1].lower()
        allowed_ext = [".jpg", ".jpeg", ".png", ".gif", ".bmp"]
        if ext not in allowed_ext:
            return jsonify({"code": 1, "msg": "仅支持 jpg/jpeg/png/gif/bmp 格式"})

        new_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.urandom(4).hex()}{ext}"
        save_path = os.path.join(UPLOAD_FOLDER, new_filename)
        file.save(save_path)

        url_path = f"/static/uploads/{new_filename}"
        return jsonify({"code": 0, "msg": "上传成功", "data": {"url": url_path}})
    except Exception as e:
        log.error("upload_image error: %s", e)
        return jsonify({"code": 1, "msg": str(e)})
