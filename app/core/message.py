"""
TextNow Factory - 消息收发核心模块
功能：拉取消息、发送回复、标记已读、会话管理
对齐表结构：tn_accounts / tn_conversations / tn_messages
支持全字段协议鉴权，适配业务员分配体系
兼容 SQLite(?占位符) 和 MySQL(%s占位符) 双模式
"""

import time
import logging
import requests
from app.models.db import get_db, get_db_dict, DB_TYPE
from app.config import PROXY

log = logging.getLogger(__name__)

# SQLite 用 ?，MySQL 用 %s
PH = "?" if DB_TYPE == "sqlite" else "%s"


def fetch_messages(account_id, limit=50):
    """
    拉取账号的最新消息，自动同步到数据库
    :param account_id: 账号 ID
    :param limit: 拉取数量
    :return: 新消息数量
    """
    conn = None
    try:
        conn = get_db_dict()
        cur = conn.cursor()
        # 修正字段名：对齐 tn_accounts 实际列名
        cur.execute(
            f"""SELECT id, phone_number, username, sid, token, user_agent,
                      px_auth, device_fp, proxy, salesman_id
               FROM tn_accounts WHERE id={PH} AND status=1""",
            (account_id,)
        )
        account = cur.fetchone()

        if not account:
            log.warning("账号不存在或已禁用：ID=%s", account_id)
            return 0

        # ====================== 真实 TextNow 协议拉取消息 ======================
        headers = {
            "Authorization": f"Bearer {account['token']}",
            "x-px-authorization": account["px_auth"],
            "User-Agent": account["user_agent"],
            "Cookie": f"sid={account['sid']}" if account.get("sid") else "",
            "Accept": "application/json"
        }
        params = {"limit": limit, "direction": "incoming", "read": "false"}
        proxies = {"http": account["proxy"], "https": account["proxy"]} if account.get("proxy") else PROXY

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

        new_count = 0
        for msg in messages:
            contact_phone = msg.get("contact_value")
            content = msg.get("content", "")
            msg_time = msg.get("created_at")

            if not contact_phone or not content:
                continue

            # 查找或创建会话（绑定业务员归属）—— 修正表名 tn_conversations
            cur.execute(
                f"SELECT id, unread FROM tn_conversations WHERE account_id={PH} AND contact_number={PH}",
                (account_id, contact_phone)
            )
            conv = cur.fetchone()

            if not conv:
                cur.execute(
                    f"""INSERT INTO tn_conversations
                       (account_id, contact_number, last_message, unread, salesman_id)
                       VALUES ({PH}, {PH}, {PH}, 1, {PH})""",
                    (account_id, contact_phone, content[:200], account.get("salesman_id"))
                )
                conv_id = cur.lastrowid
            else:
                conv_id = conv["id"]
                cur.execute(
                    f"""UPDATE tn_conversations
                       SET last_message={PH}, unread = unread + 1, updated_at=CURRENT_TIMESTAMP
                       WHERE id={PH}""",
                    (content, conv_id)
                )

            # 插入消息记录—— 修正表名 tn_messages
            cur.execute(
                f"""INSERT INTO tn_messages (conversation_id, direction, content, sent_at)
                   VALUES ({PH}, 1, {PH}, {PH})""",
                (conv_id, content, msg_time)
            )
            new_count += 1

        conn.commit()
        log.info("账号 %s 拉取到 %d 条新消息", account.get("phone_number", ""), new_count)
        return new_count

    except Exception as e:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        log.error("拉取消息失败（账号ID=%s）：%s", account_id, e, exc_info=True)
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

        cur.execute(
            f"SELECT account_id, contact_number FROM tn_conversations WHERE id={PH}",
            (conv_id,)
        )
        conv = cur.fetchone()
        if not conv:
            return False, "会话不存在"

        if not account_id:
            account_id = conv["account_id"]

        # 修正字段名对齐 tn_accounts
        cur.execute(
            f"""SELECT id, phone_number, username, sid, token, user_agent,
                      px_auth, device_fp, proxy
               FROM tn_accounts WHERE id={PH} AND status=1""",
            (account_id,)
        )
        account = cur.fetchone()
        if not account:
            return False, "账号不存在或已禁用"

        # ====================== 真实 TextNow 协议发送消息 ======================
        headers = {
            "Authorization": f"Bearer {account['token']}",
            "x-px-authorization": account["px_auth"],
            "User-Agent": account["user_agent"],
            "Cookie": f"sid={account['sid']}" if account.get("sid") else "",
            "Content-Type": "application/json"
        }
        payload = {"to": conv["contact_number"], "content": content, "type": "TEXT"}
        proxies = {"http": account["proxy"], "https": account["proxy"]} if account.get("proxy") else PROXY

        response = requests.post(
            f"https://api.textnow.me/api/v2/users/{account['username']}/messages",
            headers=headers,
            json=payload,
            proxies=proxies,
            timeout=30
        )
        response.raise_for_status()
        # ======================================================================

        # 记录发送的消息
        cur.execute(
            f"""INSERT INTO tn_messages (conversation_id, direction, content)
               VALUES ({PH}, 2, {PH})""",
            (conv_id, content)
        )

        # 更新会话最后一条消息
        cur.execute(
            f"UPDATE tn_conversations SET last_message={PH}, updated_at=CURRENT_TIMESTAMP WHERE id={PH}",
            (content, conv_id)
        )

        conn.commit()
        log.info("会话 %s 回复发送成功", conv_id)
        return True, None

    except Exception as e:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        log.error("发送回复失败（会话ID=%s）：%s", conv_id, e)
        return False, str(e)
    finally:
        if conn:
            conn.close()


def mark_read(conv_id):
    """标记会话为已读（清零未读数）"""
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            f"UPDATE tn_conversations SET unread = 0, updated_at=CURRENT_TIMESTAMP WHERE id={PH}",
            (conv_id,)
        )
        conn.commit()
        log.info("会话 %s 已标记为已读", conv_id)
    except Exception as e:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        log.error("标记已读失败：%s", e)
    finally:
        if conn:
            conn.close()


def close_conversation(conv_id):
    """关闭会话（软关闭，更新状态）"""
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            f"UPDATE tn_conversations SET status = 0, updated_at=CURRENT_TIMESTAMP WHERE id={PH}",
            (conv_id,)
        )
        conn.commit()
        log.info("会话 %s 已关闭", conv_id)
    except Exception as e:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        log.error("关闭会话失败：%s", e)
    finally:
        if conn:
            conn.close()


def get_conversation_messages(conv_id, limit=100):
    """获取会话的消息列表（按时间正序）"""
    conn = None
    try:
        conn = get_db_dict()
        cur = conn.cursor()
        cur.execute(
            f"""SELECT id, direction, content, sent_at
               FROM tn_messages
               WHERE conversation_id={PH}
               ORDER BY sent_at ASC
               LIMIT {PH}""",
            (conv_id, limit)
        )
        messages = cur.fetchall()
        return messages
    except Exception as e:
        log.error("获取会话消息失败：%s", e)
        return []
    finally:
        if conn:
            conn.close()
