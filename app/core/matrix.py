"""
TextNow Factory - 矩阵群发核心模块
批量发送消息到多个联系人
支持：分批、多线程、失败重试、进度跟踪、状态实时更新
对齐表结构：matrix_tasks / matrix_send_records / accounts
"""

import sys
from pathlib import Path

# 确保项目根目录在 Python 路径中

import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.models.db import get_db, get_db_dict
from app.config import MATRIX_BATCH_SIZE, MATRIX_THREADS, MATRIX_RETRY_MAX

log = logging.getLogger(__name__)


def run_task(task_id):
    """
    执行矩阵群发任务（后台异步调用入口）
    :param task_id: 任务 ID
    """
    conn = get_db()
    cur = conn.cursor()

    try:
        # 1. 查询任务基础信息
        cur.execute("SELECT * FROM matrix_tasks WHERE id = %s", (task_id,))
        task = cur.fetchone()
        if not task:
            log.error(f"任务 {task_id} 不存在")
            return

        # 2. 更新任务状态为执行中
        cur.execute("UPDATE matrix_tasks SET status = 1 WHERE id = %s", (task_id,))
        conn.commit()

        # 3. 查询发送账号
        cur.execute("SELECT * FROM accounts WHERE salesman_id = %s AND status = 1", (task["salesman_id"],))
        accounts = cur.fetchall()
        if not accounts:
            cur.execute("UPDATE matrix_tasks SET status = 4, fail_count = 1 WHERE id = %s", (task_id,))
            conn.commit()
            log.warning(f"任务 {task_id} 无可用账号")
            return

        # 4. 解析目标号码列表
        target_numbers = task["target_list"].split("\n")
        target_numbers = [n.strip() for n in target_numbers if n.strip()]
        if not target_numbers:
            cur.execute("UPDATE matrix_tasks SET status = 4 WHERE id = %s", (task_id,))
            conn.commit()
            return

        # 5. 多账号轮询发送
        success = 0
        fail = 0
        targets = [{"number": n, "content": task["content"]} for n in target_numbers]

        # 分批处理
        for i in range(0, len(targets), MATRIX_BATCH_SIZE):
            batch = targets[i:i + MATRIX_BATCH_SIZE]
            account = accounts[i % len(accounts)]  # 轮询分配账号

            with ThreadPoolExecutor(max_workers=MATRIX_THREADS) as executor:
                futures = {
                    executor.submit(send_one, task_id, account, t): t
                    for t in batch
                }
                for future in as_completed(futures):
                    is_ok, _ = future.result()
                    if is_ok:
                        success += 1
                    else:
                        fail += 1

            # 实时更新进度
            cur.execute(
                "UPDATE matrix_tasks SET send_count = %s, success_count = %s, fail_count = %s WHERE id = %s",
                (success + fail, success, fail, task_id)
            )
            conn.commit()

            # 批次间隔
            time.sleep(2)

        # 6. 任务完成
        cur.execute("UPDATE matrix_tasks SET status = 2 WHERE id = %s", (task_id,))
        conn.commit()
        log.info(f"任务 {task_id} 执行完成：成功 {success}，失败 {fail}")

    except Exception as e:
        conn.rollback()
        cur.execute("UPDATE matrix_tasks SET status = 4 WHERE id = %s", (task_id,))
        conn.commit()
        log.error(f"任务 {task_id} 执行异常：{str(e)}", exc_info=True)
    finally:
        conn.close()


def send_one(task_id, account, target):
    """
    发送单条消息
    :param task_id: 任务 ID
    :param account: 全字段账号信息 dict
    :param target: 目标 {"number": "1234567890", "content": "消息内容"}
    :return: (success: bool, error: str)
    """
    number = target["number"]
    content = target["content"]
    retry_count = 0
    last_error = ""

    while retry_count <= MATRIX_RETRY_MAX:
        try:
            # ====================== TODO: 接入 TextNow 真实协议发送 ======================
            # 需调用 core 层的协议方法，使用 account 中的全字段鉴权：
            # px_authorization / cookie / user_agent / px_device_fp 等
            # 示例：response = textnow_api.send_message(account, number, content)
            # ==========================================================================

            # 模拟发送逻辑（上线前替换为真实协议调用）
            log.info(f"[{account['phone']}] → {number}：{content[:20]}...")
            time.sleep(0.3)

            # 记录发送成功
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO matrix_send_records 
                   (task_id, account_id, target_phone, content, status) 
                   VALUES (%s, %s, %s, %s, 1)""",
                (task_id, account["id"], number, content)
            )
            conn.commit()
            conn.close()

            return True, None

        except Exception as e:
            last_error = str(e)
            retry_count += 1
            time.sleep(2 * retry_count)  # 指数退避重试

    # 重试全部失败，记录结果
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO matrix_send_records 
           (task_id, account_id, target_phone, content, status, error_msg) 
           VALUES (%s, %s, %s, %s, 0, %s)""",
        (task_id, account["id"], number, content, last_error)
    )
    conn.commit()
    conn.close()

    return False, last_error


def create_task(salesman_id, task_name, content, target_numbers):
    """
    创建矩阵群发任务
    :param salesman_id: 业务员 ID
    :param task_name: 任务名称
    :param content: 群发内容
    :param target_numbers: 目标号码列表（换行分隔字符串）
    :return: task_id
    """
    conn = get_db()
    cur = conn.cursor()

    try:
        # 计算目标总数
        numbers = [n.strip() for n in target_numbers.split("\n") if n.strip()]
        total = len(numbers)

        # 创建任务主记录
        cur.execute(
            """INSERT INTO matrix_tasks 
               (salesman_id, task_name, target_list, content, send_count, success_count, fail_count, status) 
               VALUES (%s, %s, %s, %s, 0, 0, 0, 0)""",
            (salesman_id, task_name, target_numbers, content)
        )
        task_id = cur.lastrowid

        conn.commit()
        log.info(f"✅ 矩阵任务已创建：ID={task_id}, 名称={task_name}, 目标数={total}")
        return task_id

    except Exception as e:
        conn.rollback()
        log.error(f"❌ 创建矩阵任务失败：{e}")
        raise
    finally:
        conn.close()


def get_task_detail(task_id):
    """
    获取任务详情与进度
    :param task_id: 任务 ID
    :return: dict
    """
    conn = get_db_dict()
    cur = conn.cursor()
    cur.execute("SELECT * FROM matrix_tasks WHERE id = %s", (task_id,))
    task = cur.fetchone()
    conn.close()
    return task


def get_task_records(task_id, page=1, limit=20):
    """
    分页获取任务发送明细
    :param task_id: 任务 ID
    :param page: 页码
    :param limit: 每页条数
    :return: (total, records)
    """
    conn = get_db_dict()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) as total FROM matrix_send_records WHERE task_id = %s", (task_id,))
    total = cur.fetchone()["total"]

    offset = (page - 1) * limit
    cur.execute(
        """SELECT r.*, a.phone as account_phone 
           FROM matrix_send_records r 
           LEFT JOIN accounts a ON r.account_id = a.id
           WHERE r.task_id = %s
           ORDER BY r.id DESC
           LIMIT %s OFFSET %s""",
        (task_id, limit, offset)
    )
    records = cur.fetchall()
    conn.close()

    return total, records