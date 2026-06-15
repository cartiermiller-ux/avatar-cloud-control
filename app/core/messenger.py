"""
TextNow Factory - 消息发送核心模块
提供文本/图片/链接发送，适配代理IP、异常重试、防风控。
"""

import os
import time
import random
import logging

try:
    import requests
    from requests.exceptions import RequestException, ProxyError, Timeout
except ImportError:
    requests = None

log = logging.getLogger(__name__)

# ========== 配置 ==========
UPLOAD_FOLDER = "static/uploads"
REQ_TIMEOUT = 15
SEND_INTERVAL_MIN = 2
SEND_INTERVAL_MAX = 5
MAX_RETRY = 2
# TextNow API 基础地址（根据实际环境修改）
TEXTNOW_BASE = "https://www.textnow.com"


def _build_proxies(proxy_info):
    """
    将 get_account_proxy() 返回的 dict 转为 requests proxies 格式。
    proxy_info 格式: {"ip", "port", "user", "pwd", "proxy_url"}
    """
    if not proxy_info:
        return None
    url = proxy_info.get("proxy_url") or proxy_info.get("proxy")
    if url:
        return {"http": url, "https": url}
    return None


def _build_session(account):
    """
    为账号构建 requests.Session，注入 cookie/auth headers。
    account 应包含: sid, token, user_agent, px_auth, client_id, device_fp, os_version
    """
    sess = requests.Session() if requests else None
    if not sess:
        return None

    # 携带 TextNow 鉴权信息
    sess.headers.update({
        "User-Agent": account.get("user_agent") or "TextNow/6.60.1 (iPhone; iOS 16.3.1)",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US",
        "Content-Type": "application/json",
    })

    # cookie 方式：TextNow 使用 sid 作为 session
    if account.get("sid"):
        sess.cookies.set("sid", account["sid"], domain=".textnow.com")

    # 部分接口用 Authorization header
    if account.get("token"):
        sess.headers["Authorization"] = f"Bearer {account['token']}"

    return sess


def _random_sleep(base_min=None, base_max=None):
    """随机休眠，模拟人工操作间隔"""
    lo = base_min or SEND_INTERVAL_MIN
    hi = base_max or SEND_INTERVAL_MAX
    time.sleep(random.uniform(lo, hi))


def send_text_message(account, target_number, content, proxy_info=None):
    """
    发送文本/链接消息到 TextNow。

    :param account: 账号 dict（来自 tn_accounts），需含 sid/token/user_agent
    :param target_number: 目标手机号（含区号，如 +1xxxxxxxxxx）
    :param content: 文本内容或链接
    :param proxy_info: get_account_proxy() 返回的代理 dict，可为 None
    :return: dict {"success": bool, "msg": str, "message_id": str}
    """
    if not requests:
        return {"success": False, "msg": "requests 未安装", "message_id": ""}

    proxies = _build_proxies(proxy_info)
    sess = _build_session(account)
    retry = 0

    while retry <= MAX_RETRY:
        try:
            url = f"{TEXTNOW_BASE}/api/messages"
            payload = {
                "contact_value": target_number,
                "message": content,
                "content_type": "text",
                "read": True
            }

            resp = sess.post(url, json=payload, proxies=proxies, timeout=REQ_TIMEOUT)

            if resp.status_code in (200, 201):
                data = resp.json()
                msg_id = data.get("id", data.get("message_id", ""))
                _random_sleep()
                return {"success": True, "msg": "", "message_id": msg_id}

            # 非 200 可能是限流/鉴权过期
            log.warning("send_text status=%d body=%s", resp.status_code, resp.text[:200])
            retry += 1
            time.sleep(2)

        except (ProxyError, Timeout) as e:
            log.warning("send_text 代理/超时异常(retry=%d): %s", retry, e)
            retry += 1
            time.sleep(3)
        except RequestException as e:
            log.error("send_text 网络异常: %s", e)
            return {"success": False, "msg": str(e), "message_id": ""}
        except Exception as e:
            log.error("send_text 未知异常: %s", e)
            return {"success": False, "msg": str(e), "message_id": ""}

    return {"success": False, "msg": f"重试{MAX_RETRY+1}次失败", "message_id": ""}


def send_image_message(account, target_number, image_path, proxy_info=None):
    """
    发送图片消息（MMS）到 TextNow。

    :param account: 账号 dict
    :param target_number: 目标手机号
    :param image_path: 图片完整路径（绝对路径）
    :param proxy_info: 代理 dict
    :return: dict {"success": bool, "msg": str}
    """
    if not requests:
        return {"success": False, "msg": "requests 未安装"}

    if not image_path or not os.path.isfile(image_path):
        log.error("send_image 文件不存在: %s", image_path)
        return {"success": False, "msg": f"图片不存在: {image_path}"}

    proxies = _build_proxies(proxy_info)
    sess = _build_session(account)
    retry = 0

    while retry <= MAX_RETRY:
        try:
            url = f"{TEXTNOW_BASE}/api/mms.send"

            with open(image_path, "rb") as f:
                files = {"file": (os.path.basename(image_path), f)}
                data = {
                    "contact_value": target_number,
                    "message": "",  # MMS 主体可选
                }

                # 上传文件时不能用 JSON content-type，session 的默认 header 会冲突
                headers = {"Content-Type": None}
                resp = sess.post(url, files=files, data=data, headers=headers,
                                 proxies=proxies, timeout=30)

            if resp.status_code in (200, 201):
                _random_sleep(3, 6)
                return {"success": True, "msg": ""}

            log.warning("send_image status=%d body=%s", resp.status_code, resp.text[:200])
            retry += 1
            time.sleep(2)

        except (ProxyError, Timeout) as e:
            log.warning("send_image 代理/超时异常(retry=%d): %s", retry, e)
            retry += 1
            time.sleep(3)
        except RequestException as e:
            log.error("send_image 网络异常: %s", e)
            return {"success": False, "msg": str(e)}
        except Exception as e:
            log.error("send_image 未知异常: %s", e)
            return {"success": False, "msg": str(e)}

    return {"success": False, "msg": f"重试{MAX_RETRY+1}次失败"}


def send_image_text_combo(account, target_number, image_path, text_content, proxy_info=None):
    """
    图片+文字组合发送：先发图片，再发文字链接。

    :return: dict {"img_success": bool, "text_success": bool}
    """
    img_result = send_image_message(account, target_number, image_path, proxy_info)
    if img_result["success"]:
        time.sleep(1)
    text_result = send_text_message(account, target_number, text_content, proxy_info)
    return {"img_success": img_result["success"], "text_success": text_result["success"]}


def get_account_dict_from_db(account_id):
    """
    从数据库获取账号完整信息 dict，供发送函数使用。
    """
    try:
        from models.db import get_db_dict
        conn = get_db_dict()
        cur = conn.cursor()
        cur.execute("SELECT * FROM tn_accounts WHERE id=?", (account_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None
    except Exception as e:
        log.error("get_account_dict error: %s", e)
        return None


# ========== 矩阵群发任务执行器 ==========

def run_matrix_task(task_id):
    """
    后台线程执行矩阵群发任务。
    逐个遍历 broadcast_item，根据任务类型调用对应发送函数。
    """
    try:
        from models.db import get_db, get_db_dict
        from core.proxy import get_account_proxy

        conn_d = get_db_dict()
        cur = conn_d.cursor()

        # 读取任务
        cur.execute("SELECT * FROM tn_broadcast_task WHERE id=?", (task_id,))
        task = cur.fetchone()
        if not task:
            log.error("run_matrix_task: 任务 %s 不存在", task_id)
            return

        # 更新为运行中
        conn = get_db()
        conn.execute("UPDATE tn_broadcast_task SET status=1, started_at=datetime('now') WHERE id=?", (task_id,))
        conn.commit()

        task_name = task.get("task_name") or task.get("name", "")
        task_type = task.get("task_type", "text")
        content = task.get("content", "")
        image_path = task.get("image_path", "")

        # 读取所有待发送 item
        cur.execute("SELECT * FROM tn_broadcast_item WHERE task_id=? AND status=0 ORDER BY id", (task_id,))
        items = cur.fetchall()
        conn_d.close()

        total = len(items)
        success_count = 0
        failed_count = 0

        for idx, item in enumerate(items):
            item_id = item["id"]
            account_id = item["account_id"]
            target = item["target_number"]

            log.info("群发 [%s/%s] item=%s account=%s → %s", idx + 1, total, item_id, account_id, target)

            # 获取账号信息和代理
            account = get_account_dict_from_db(account_id)
            proxy_info = get_account_proxy(account_id)

            if not account:
                _mark_item_failed(conn, item_id, "账号不存在")
                failed_count += 1
                continue

            # 根据任务类型发送
            result = None
            try:
                if task_type in ("text", "link"):
                    result = send_text_message(account, target, content, proxy_info)

                elif task_type == "image":
                    full_path = os.path.join(os.getcwd(), UPLOAD_FOLDER, image_path)
                    result = send_image_message(account, target, full_path, proxy_info)

                elif task_type == "image_text":
                    full_path = os.path.join(os.getcwd(), UPLOAD_FOLDER, image_path)
                    combo = send_image_text_combo(account, target, full_path, content, proxy_info)
                    if combo["img_success"] and combo["text_success"]:
                        result = {"success": True, "msg": ""}
                    else:
                        result = {"success": False, "msg": "图片或文本发送失败"}

                else:
                    result = {"success": False, "msg": f"未知任务类型: {task_type}"}

            except Exception as e:
                result = {"success": False, "msg": str(e)}

            # 更新 item 状态
            if result and result["success"]:
                conn.execute(
                    "UPDATE tn_broadcast_item SET status=1, sent_at=datetime('now'), message_id=? WHERE id=?",
                    (result.get("message_id", ""), item_id)
                )
                success_count += 1
            else:
                err_msg = (result.get("msg", "") if result else "未知错误")[:200]
                _mark_item_failed(conn, item_id, err_msg)
                failed_count += 1

            # 更新任务进度
            conn.execute(
                "UPDATE tn_broadcast_task SET sent_count=?, failed_count=? WHERE id=?",
                (success_count, failed_count, task_id)
            )
            conn.commit()

            # 目标间随机间隔
            _random_sleep(2, 5)

        # 任务完成
        conn.execute(
            "UPDATE tn_broadcast_task SET status=2, finished_at=datetime('now'), sent_count=?, failed_count=? WHERE id=?",
            (success_count, failed_count, task_id)
        )
        conn.commit()
        conn.close()
        log.info("群发任务 %s 完成: 成功=%d 失败=%d", task_id, success_count, failed_count)

    except Exception as e:
        log.error("run_matrix_task(%s) 致命错误: %s", task_id, e, exc_info=True)
        try:
            conn.execute("UPDATE tn_broadcast_task SET status=3 WHERE id=?", (task_id,))
            conn.commit()
            conn.close()
        except:
            pass


def _mark_item_failed(conn, item_id, error_msg):
    """标记发送 item 为失败"""
    try:
        conn.execute(
            "UPDATE tn_broadcast_item SET status=2, error_msg=?, retry_count=retry_count+1 WHERE id=?",
            (error_msg, item_id)
        )
    except Exception as e:
        log.error("_mark_item_failed error: %s", e)
