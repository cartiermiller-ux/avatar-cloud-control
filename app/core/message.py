"""
TextNow Factory - 消息收发核心模块
功能：拉取消息、发送回复、标记已读、会话管理
对齐表结构：accounts / conversations / messages
支持全字段协议鉴权，适配业务员分配体系
"""

import sys
from pathlib import Path

# 确保项目根目录在 Python 路径中

import time
import logging
import requests
from app.models.db import get_db, get_db_dict
from app.config import PROXY

log = logging.getLogger(__name__)


def fetch_messages(account_id, limit=50):
    """
    拉取账号的最新消息，自动同步到数据库
    :param account_id: 账号 ID
    :param limit: 拉取数量
    :return: 新消息数量
    """
    conn = None
    try:
        # 获取账号全字段信息（协议鉴权所需字段全部包含）
        conn = get_db_dict()
        cur = conn.cursor()
        cur.execute(
            """SELECT id, phone, username, sid, token, cookie, user_agent,
                      px_authorization, px_device_fp, proxy, salesman_id
               FROM accounts WHERE id=%s AND status=1""",
            (account_id,)
        )
        account = cur.fetchone()

        if not account:
            log.warning(f"账号不存在或已禁用：ID={account_id}")
            return 0

        # ====================== 真实 TextNow 协议拉取消息 ======================
        headers = {
            "Authorization": f"Bearer {account['token']}",
            "x-px-authorization": account["px_authorization"],
            "User-Agent": account["user_agent"],
            "Cookie": account["cookie"],
            "Accept": "application/json"
        }
        params = {"limit": limit, "direction": "incoming", "read": "false"}
        proxies = {"http": account["proxy"], "https": account["proxy"]} if account["proxy"] else PROXY

        response = requests.get(
            f"https://api.textnow.me/api/v2/users/{account['username']}/messages",
            headers=headers,
            params=params,
            proxies=proxies,
            timeout=30
        )
        response.raise_for_status()
        messages = response.json().get("messages", [])
        # ======================================================================

        # 模拟数据（正式上线删除上面真实调用，保留下面逻辑即可）
        # messages = [
        #     {"contact_value": f"+198765432{i}", "content": f"测试消息{i+1}", "created_at": time.strftime("%Y-%m-%d %H:%M:%S")}
        #     for i in range(3)
        # ]

        new_count = 0
        for msg in messages:
            contact_phone = msg.get("contact_value")
            content = msg.get("content", "")
            msg_time = msg.get("created_at")

            if not contact_phone or not content:
                continue

            # 查找或创建会话（绑定业务员归属）
            cur.execute(
                "SELECT id, unread FROM conversations WHERE account_id=%s AND contact_phone=%s",
                (account_id, contact_phone)
            )
            conv = cur.fetchone()

            if not conv:
                cur.execute(
                    """INSERT INTO conversations 
                       (account_id, contact_phone, last_message, unread, salesman_id) 
                       VALUES (%s, %s, %s, 1, %s)""",
                    (account_id, contact_phone, content, account["salesman_id"])
                )
                conv_id = cur.lastrowid
            else:
                conv_id = conv["id"]
                # 更新会话最后一条消息 + 未读数+1
                cur.execute(
                    """UPDATE conversations 
                       SET last_message=%s, unread = unread + 1, updated_at=NOW()
                       WHERE id=%s""",
                    (content, conv_id)
                )

            # 插入消息记录
            cur.execute(
                """INSERT INTO messages (conversation_id, direction, content, created_at) 
                   VALUES (%s, 1, %s, %s)""",
                (conv_id, content, msg_time)
            )
            new_count += 1

        conn.commit()
        log.info(f"✅ 账号 {account['phone']} 拉取到 {new_count} 条新消息")
        return new_count

    except Exception as e:
        if conn:
            conn.rollback()
        log.error(f"❌ 拉取消息失败（账号ID={account_id}）：{e}", exc_info=True)
        return 0
    finally:
        if conn:
            conn.close()


def send_reply(conv_id, content, account_id=None):
    """
    发送回复消息
    :param conv_id: 会话 ID
    :param content: 回复内容
    :param account_id: 账号 ID（可选，默认从会话中获取）
    :return: (success: bool, error: str)
    """
    conn = None
    try:
        conn = get_db_dict()
        cur = conn.cursor()

        # 获取会话信息
        cur.execute(
            "SELECT account_id, contact_phone FROM conversations WHERE id=%s",
            (conv_id,)
        )
        conv = cur.fetchone()
        if not conv:
            return False, "会话不存在"

        if not account_id:
            account_id = conv["account_id"]

        # 获取账号全字段信息
        cur.execute(
            """SELECT id, phone, username, sid, token, cookie, user_agent,
                      px_authorization, px_device_fp, proxy
               FROM accounts WHERE id=%s AND status=1""",
            (account_id,)
        )
        account = cur.fetchone()
        if not account:
            return False, "账号不存在或已禁用"

        # ====================== 真实 TextNow 协议发送消息 ======================
        headers = {
            "Authorization": f"Bearer {account['token']}",
            "x-px-authorization": account["px_authorization"],
            "User-Agent": account["user_agent"],
            "Cookie": account["cookie"],
            "Content-Type": "application/json"
        }
        payload = {"to": conv["contact_phone"], "content": content, "type": "TEXT"}
        proxies = {"http": account["proxy"], "https": account["proxy"]} if account["proxy"] else PROXY

        response = requests.post(
            f"https://api.textnow.me/api/v2/users/{account['username']}/messages",
            headers=headers,
            json=payload,
            proxies=proxies,
            timeout=30
        )
        response.raise_for_status()
        # ======================================================================

        # 模拟发送（正式上线删除上面真实调用）
        # log.info(f"发送回复到 {conv['contact_phone']}：{content[:20]}...")
        # time.sleep(0.3)

        # 记录发送的消息
        cur.execute(
            """INSERT INTO messages (conversation_id, direction, content) 
               VALUES (%s, 2, %s)""",
            (conv_id, content)
        )

        # 更新会话最后一条消息
        cur.execute(
            "UPDATE conversations SET last_message=%s, updated_at=NOW() WHERE id=%s",
            (content, conv_id)
        )

        conn.commit()
        log.info(f"✅ 会话 {conv_id} 回复发送成功")
        return True, None

    except Exception as e:
        if conn:
            conn.rollback()
        log.error(f"❌ 发送回复失败（会话ID={conv_id}）：{e}")
        return False, str(e)
    finally:
        if conn:
            conn.close()


def mark_read(conv_id):
    """
    标记会话为已读（清零未读数）
    :param conv_id: 会话 ID
    """
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "UPDATE conversations SET unread = 0, updated_at=NOW() WHERE id=%s",
            (conv_id,)
        )
        conn.commit()
        log.info(f"✅ 会话 {conv_id} 已标记为已读")
    except Exception as e:
        if conn:
            conn.rollback()
        log.error(f"❌ 标记已读失败：{e}")
    finally:
        if conn:
            conn.close()


def close_conversation(conv_id):
    """
    关闭会话（软关闭，更新状态）
    注：若需启用此功能，请先给 conversations 表增加 status 字段
    ALTER TABLE conversations ADD COLUMN status TINYINT DEFAULT 1 COMMENT '1开启 0关闭';
    :param conv_id: 会话 ID
    """
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "UPDATE conversations SET status = 0, updated_at=NOW() WHERE id=%s",
            (conv_id,)
        )
        conn.commit()
        log.info(f"✅ 会话 {conv_id} 已关闭")
    except Exception as e:
        if conn:
            conn.rollback()
        log.error(f"❌ 关闭会话失败：{e}")
    finally:
        if conn:
            conn.close()


def get_conversation_messages(conv_id, limit=100):
    """
    获取会话的消息列表（按时间正序）
    :param conv_id: 会话 ID
    :param limit: 数量限制
    :return: 消息列表
    """
    conn = None
    try:
        conn = get_db_dict()
        cur = conn.cursor()
        cur.execute(
            """SELECT id, direction, content, created_at 
               FROM messages 
               WHERE conversation_id=%s 
               ORDER BY created_at ASC 
               LIMIT %s""",
            (conv_id, limit)
        )
        messages = cur.fetchall()
        return messages
    except Exception as e:
        log.error(f"❌ 获取会话消息失败：{e}")
        return []
    finally:
        if conn:
            conn.close()