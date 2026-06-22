from flask import request, jsonify
from app.api import api_bp
from app.models.api_key import ApiKey
from app.models.receive_code_num import ReceiveCodeNum
from app.models.code_record import CodeRecord
from app.models.api_code_request_log import ApiCodeRequestLog
from app import db
from datetime import datetime, timedelta

# 全局鉴权函数，校验X-Api-Key头
def check_api_key():
    key_str = request.headers.get("X-Api-Key", "")
    if not key_str:
        return False, "缺少请求头 X-Api-Key", None
    key_info = ApiKey.query.filter_by(key_str=key_str, status=1).first()
    if not key_info:
        return False, "密钥无效或已停用", None
    # 更新密钥最后调用时间
    key_info.last_use_time = db.func.now()
    db.session.commit()
    return True, "ok", key_info

# 记录本次API调用日志
def write_request_log(key_id, api_name, phone, res_code, msg):
    log = ApiCodeRequestLog(
        api_key_id=key_id,
        request_api=api_name,
        phone_number=phone,
        request_ip=request.remote_addr,
        response_code=res_code,
        response_msg=msg
    )
    db.session.add(log)
    db.session.commit()

# 1. 随机获取空闲号码
@api_bp.route("/receive_code/get_random_num", methods=["POST"])
def get_random_num():
    ok, msg, key_info = check_api_key()
    if not ok:
        write_request_log(0, "/get_random_num", "", 403, msg)
        return jsonify({"code":403, "msg":msg})
    lock_min = int(request.json.get("lock_min",5))
    bind_ids = key_info.bind_group_ids.split(",") if key_info.bind_group_ids else []
    # 查询对应分组空闲号码
    num = ReceiveCodeNum.query.filter(
        ReceiveCodeNum.status=="空闲",
        ReceiveCodeNum.group_id.in_(bind_ids)
    ).first()
    if not num:
        write_request_log(key_info.id, "/get_random_num", "", 400, "无空闲号码")
        return jsonify({"code":400, "msg":"当前分组无空闲号码"})
    # 锁定号码
    num.current_key_id = key_info.id
    num.lock_minute = lock_min
    num.lock_expire_time = datetime.now() + timedelta(minutes=lock_min)
    num.status = "占用"
    db.session.commit()
    res_data = {
        "phone": num.phone_number,
        "lock_expire": num.lock_expire_time.strftime("%Y-%m-%d %H:%M:%S")
    }
    write_request_log(key_info.id, "/get_random_num", num.phone_number, 200, "取号成功")
    return jsonify({"code":200, "msg":"success", "data":res_data})

# 2. 根据手机号查询验证码
@api_bp.route("/receive_code/get_code_by_phone", methods=["POST"])
def get_code_by_phone():
    ok, msg, key_info = check_api_key()
    if not ok:
        write_request_log(0, "/get_code_by_phone", "", 403, msg)
        return jsonify({"code":403, "msg":msg})
    phone = request.json.get("phone_number","")
    record = CodeRecord.query.filter_by(phone_number=phone).order_by(CodeRecord.create_time.desc()).first()
    data = {"verify_code": record.verify_code if record else ""}
    write_request_log(key_info.id, "/get_code_by_phone", phone, 200, "查询成功")
    return jsonify({"code":200, "msg":"success", "data":data})

# 3. 手动释放号码
@api_bp.route("/receive_code/release_num", methods=["POST"])
def release_num():
    ok, msg, key_info = check_api_key()
    if not ok:
        write_request_log(0, "/release_num", "", 403, msg)
        return jsonify({"code":403, "msg":msg})
    phone = request.json.get("phone_number","")
    num = ReceiveCodeNum.query.filter_by(phone_number=phone, current_key_id=key_info.id).first()
    if num:
        num.status = "空闲"
        num.current_key_id = None
        num.lock_expire_time = None
        db.session.commit()
    write_request_log(key_info.id, "/release_num", phone, 200, "释放完成")
    return jsonify({"code":200, "msg":"号码已释放"})

# 4. 查询号码状态
@api_bp.route("/receive_code/num_status", methods=["POST"])
def num_status():
    ok, msg, key_info = check_api_key()
    if not ok:
        write_request_log(0, "/num_status", "", 403, msg)
        return jsonify({"code":403, "msg":msg})
    phone = request.json.get("phone_number","")
    num = ReceiveCodeNum.query.filter_by(phone_number=phone).first()
    data = {
        "phone": phone,
        "status": num.status if num else "不存在",
        "lock_expire": num.lock_expire_time.strftime("%Y-%m-%d %H:%M:%S") if (num and num.lock_expire_time) else ""
    }
    write_request_log(key_info.id, "/num_status", phone, 200, "查询状态成功")
    return jsonify({"code":200, "msg":"success", "data":data})

# 5. 批量查询历史验证码
@api_bp.route("/receive_code/batch_history_code", methods=["POST"])
def batch_history():
    ok, msg, key_info = check_api_key()
    if not ok:
        write_request_log(0, "/batch_history_code", "", 403, msg)
        return jsonify({"code":403, "msg":msg})
    phone_list = request.json.get("phones", [])
    res = {}
    for p in phone_list:
        records = CodeRecord.query.filter_by(phone_number=p).order_by(CodeRecord.create_time).all()
        res[p] = [{"code":r.verify_code, "time":r.create_time.strftime("%Y-%m-%d %H:%M:%S")} for r in records]
    write_request_log(key_info.id, "/batch_history_code", ",".join(phone_list), 200, "批量查询成功")
    return jsonify({"code":200, "msg":"success", "data":res})