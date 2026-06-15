"""
TextNow iOS 账号注册脚本 (最终优化版)
优化点：
1. 完整的配置/数据库模块化
2. 健壮的数据库连接池 + 上下文管理器
3. 命令行参数支持
4. 更真实的设备/邮箱生成
5. 完善的异常处理和连接容错
6. 代理容错 (支持无代理)
7. 账号唯一性校验
8. 更精细的日志和重试策略
9. 避免连接泄漏
"""

import sys
from pathlib import Path

# 确保项目根目录在 Python 路径中

import requests
import uuid
import random
import string
import time
import json
import logging
import hmac
import hashlib
import base64
import argparse
from typing import Dict, Optional

# 本地模块
from app.config import (
    PROXY, REGISTER_SLEEP_MIN, REGISTER_SLEEP_MAX,
    REGISTER_PASSWORD, LOG_LEVEL, MAX_REG_RETRY,
    RETRY_BACKOFF_BASE, TEXTNOW_API_URL, TEXTNOW_APP_VERSION,
    DEVICE_POOL, FIRST_NAMES, LAST_NAMES
)
from app.models.db import init_accounts_schema, get_db, check_account_exists

# ===================== 日志配置 =====================
def setup_logging():
    """初始化日志配置"""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 格式器
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s")
    
    # 文件处理器
    file_handler = logging.FileHandler("tn_run.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

log = setup_logging()

# ===================== 工具函数 =====================
def generate_idfa() -> str:
    """生成符合标准的IDFA (UUID4 大写)"""
    return str(uuid.uuid4()).upper()

def generate_client_id() -> str:
    """生成TextNow客户端ID (符合逆向规则)"""
    hex_part = ''.join(random.choice(string.hexdigits.lower()) for _ in range(32))
    num_part = ''.join(random.choice(string.digits) for _ in range(10))
    return f"{hex_part}x{num_part}"

def generate_random_email() -> str:
    """生成更真实的随机邮箱"""
    # 确保邮箱唯一性
    while True:
        first = random.choice(FIRST_NAMES).lower()
        last = random.choice(LAST_NAMES).lower()
        num = random.randint(1000, 99999)
        suffix = random.choice(["outlook.com", "gmail.com", "yahoo.com", "icloud.com"])
        email = f"{first}{last}{num}@{suffix}"
        if not check_account_exists(email):
            return email

def generate_device_info() -> Dict[str, str]:
    """生成真实的iOS设备信息"""
    dev = random.choice(DEVICE_POOL)
    return {
        "idfa": generate_idfa(),
        "device_fp": generate_idfa(),
        "px_uuid": str(uuid.uuid4()).upper(),
        "px_vid": str(uuid.uuid4()).upper(),
        "device_model": dev["model_name"],
        "device_model_code": dev["model_code"],
        "os_version": dev["os_ver"],
        "scale": dev["scale"],
        "user_agent": f'TextNow/{TEXTNOW_APP_VERSION} ({dev["model_code"]}; iOS {dev["os_ver"]}; Scale/{dev["scale"]})'
    }

def generate_px_auth(dev_info: Dict[str, str], ts: str) -> str:
    """生成X-PX-Auth头 (逆向自TextNow iOS客户端)"""
    # 注意：此处secret仅为示例，需根据实际逆向结果替换
    secret = b"textnow_px_secret_2024"
    raw = f'{dev_info["idfa"]}{dev_info["px_uuid"]}{ts}'.encode("utf-8")
    sig = base64.b64encode(hmac.new(secret, raw, hashlib.sha256).digest()).decode("utf-8")
    r64 = ''.join(random.choice(string.hexdigits.lower()) for _ in range(64))
    pad = ''.join(random.choice(string.ascii_letters + string.digits + "+/=") for _ in range(200))
    return f"3:{r64}:{sig}:{pad}"

def build_headers(dev_info: Dict[str, str], client_id: str, px_auth: str) -> Dict[str, str]:
    """构造标准的TextNow API请求头"""
    return {
        "Host": "api.textnow.me",
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": dev_info["user_agent"],
        "X-Idfa": dev_info["idfa"],
        "X-Client-ID": client_id,
        "X-PX-Auth": px_auth,
        "X-Device-FP": dev_info["device_fp"],
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    }

# ===================== 核心注册逻辑 =====================
def register_one_account(proxy_info: Optional[Dict[str, str]] = None) -> Optional[Dict[str, str]]:
    """
    注册单个TextNow账号
    :param proxy_info: 代理信息字典 {ip, port, proxy_user, proxy_pwd}
    返回：账号信息字典 | None
    """
    session = requests.Session()
    # 配置超时和重试
    session.mount("https://", requests.adapters.HTTPAdapter(max_retries=2))
    
    # 构建代理配置
    proxies = {}
    if proxy_info:
        proxy_url = f"http://{proxy_info.get('proxy_user','')}:{proxy_info.get('proxy_pwd','')}@{proxy_info['ip']}:{proxy_info['port']}"
        proxies = {"http": proxy_url, "https": proxy_url}
        log.info(f"使用代理: {proxy_info['ip']}:{proxy_info['port']} ({proxy_info.get('area','Unknown')})")
    elif PROXY:
        proxies = PROXY
    
    for attempt in range(1, MAX_REG_RETRY + 1):
        try:
            # 生成设备/账号信息
            dev_info = generate_device_info()
            ts = str(int(time.time() * 1000))
            email = generate_random_email()
            client_id = generate_client_id()
            px_auth = generate_px_auth(dev_info, ts)
            
            # 构造请求
            headers = build_headers(dev_info, client_id, px_auth)
            payload = {
                "email": email,
                "password": REGISTER_PASSWORD,
                "first_name": random.choice(FIRST_NAMES),
                "last_name": random.choice(LAST_NAMES),
                "device": {
                    "model": dev_info["device_model"],
                    "os_version": dev_info["os_version"],
                    "idfa": dev_info["idfa"]
                },
                "locale": "en_US",
                "timezone": "America/New_York"
            }
            
            # 发送请求
            log.debug(f"注册请求 - 尝试{attempt} | 邮箱: {email} | 设备: {dev_info['device_model']}")
            response = session.post(
                TEXTNOW_API_URL,
                headers=headers,
                json=payload,
                proxies=proxies,
                timeout=30,
                verify=False  # 忽略SSL验证 (根据实际情况调整)
            )
            
            # 处理响应
            if response.status_code == 200:
                try:
                    resp_json = response.json()
                except json.JSONDecodeError:
                    log.warning(f"❌ 响应JSON解析失败: {response.text[:200]}")
                    continue
                
                account_info = {
                    "cookie": response.headers.get("Set-Cookie", ""),
                    "idfa": dev_info["idfa"],
                    "user_agent": dev_info["user_agent"],
                    "px_auth": px_auth,
                    "device_fp": dev_info["device_fp"],
                    "os_version": dev_info["os_version"],
                    "client_id": client_id,
                    "email": email,
                    "phone": resp_json.get("phone_number", ""),
                    "username": resp_json.get("username", "")
                }
                log.info(f"✅ 注册成功 | 邮箱: {email} | 手机号: {account_info['phone']} | 用户名: @{account_info['username']}")
                return account_info
            
            # 非200状态码处理
            error_msg = f"状态码: {response.status_code} | 响应: {response.text[:200]}"
            log.warning(f"❌ 注册失败 (尝试 {attempt}/{MAX_REG_RETRY}) | {error_msg}")
            
        except requests.exceptions.ProxyError:
            log.error(f"❌ 代理连接失败 (尝试 {attempt}/{MAX_REG_RETRY})")
        except requests.exceptions.Timeout:
            log.error(f"❌ 请求超时 (尝试 {attempt}/{MAX_REG_RETRY})")
        except requests.exceptions.SSLError:
            log.error(f"❌ SSL验证失败 (尝试 {attempt}/{MAX_REG_RETRY})")
        except Exception as e:
            log.error(f"❌ 注册异常 (尝试 {attempt}/{MAX_REG_RETRY}) | 类型: {type(e).__name__} | 详情: {e}")
        
        # 指数退避重试
        if attempt < MAX_REG_RETRY:
            backoff = RETRY_BACKOFF_BASE ** (attempt - 1) + random.uniform(0, 1)
            log.info(f"↳ {backoff:.1f}秒后重试...")
            time.sleep(backoff)
    
    log.error(f"❌ 账号注册失败 (已达最大重试次数 {MAX_REG_RETRY})")
    return None

def save_account(account_info: Dict[str, str], ip_id: Optional[int] = None) -> bool:
    """
    保存账号到数据库
    :param account_info: 账号信息字典
    :param ip_id: 绑定的IP池ID
    返回：保存成功/失败
    """
    if not account_info:
        return False
    
    # SQLite 兼容语法
    insert_sql = """
    INSERT INTO tn_accounts (
        username, password, sid, token, phone_number, email,
        idfa, user_agent, px_auth, device_fp, os_version, client_id, proxy, status, health_score
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(username) DO UPDATE SET
        password = excluded.password,
        px_auth = excluded.px_auth,
        updated_at = CURRENT_TIMESTAMP;
    """
    
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # 插入账号
        cur.execute(insert_sql, (
            account_info.get("username", ""),
            REGISTER_PASSWORD,
            "",  # sid
            account_info.get("cookie", ""),  # token存cookie
            account_info.get("phone", ""),
            account_info.get("email", ""),
            account_info.get("idfa", ""),
            account_info.get("user_agent", ""),
            account_info.get("px_auth", ""),
            account_info.get("device_fp", ""),
            account_info.get("os_version", ""),
            account_info.get("client_id", ""),
            "",  # proxy字段留空，用tn_account_ip表关联
            1,   # status active
            100  # health_score
        ))
        account_id = cur.lastrowid
        
        # 如果指定了IP，建立绑定关系
        if ip_id and account_id:
            cur.execute("""
                INSERT INTO tn_account_ip (account_id, ip_id, bind_time)
                VALUES (?, ?, datetime('now'))
                ON CONFLICT(account_id) DO UPDATE SET
                    ip_id = excluded.ip_id,
                    bind_time = excluded.bind_time
            """, (account_id, ip_id))
            # 更新IP状态为已分配(2)
            cur.execute("UPDATE tn_ip_pool SET status = 2 WHERE id = ?", (ip_id,))
        
        conn.commit()
        conn.close()
        log.info(f"✅ 账号已保存到数据库 | 邮箱: {account_info['email']} | ID: {account_id}")
        return True
    except Exception as e:
        log.error(f"❌ 保存账号失败 | 邮箱: {account_info.get('email','')} | 错误: {e}")
        return False

def batch_register(num_accounts: int, proxy_list: Optional[list] = None, progress_callback=None) -> Dict[str, int]:
    """
    批量注册账号（Web后台调用版本）
    :param num_accounts: 要注册的账号数量
    :param proxy_list: 代理IP列表，每个元素是 {id, ip, port, proxy_user, proxy_pwd, area} 字典
    :param progress_callback: 进度回调函数，接收 (current, total, success, failed) 参数
    返回：{success: int, failed: int}
    """
    # 初始化数据库
    init_accounts_schema()
    
    log.info(f"\n========== 开始批量注册 {num_accounts} 个账号 ==========")
    success_count = 0
    failed_count = 0
    
    for idx in range(num_accounts):
        log.info(f"\n--- 正在注册第 {idx+1}/{num_accounts} 个账号 ---")
        
        # 获取当前IP（如果有）
        proxy_info = None
        ip_id = None
        if proxy_list and idx < len(proxy_list):
            proxy_info = proxy_list[idx]
            ip_id = proxy_info.get('id')
        
        # 注册单个账号
        account = register_one_account(proxy_info)
        if account and save_account(account, ip_id):
            success_count += 1
        else:
            failed_count += 1
            # 标记IP为失效(3)
            if ip_id:
                try:
                    conn = get_db()
                    cur = conn.cursor()
                    cur.execute("UPDATE tn_ip_pool SET status = 3 WHERE id = ?", (ip_id,))
                    conn.commit()
                    conn.close()
                except Exception as e:
                    log.error(f"标记IP失效失败: {e}")
        
        # 进度回调
        if progress_callback:
            try:
                progress_callback(idx + 1, num_accounts, success_count, failed_count)
            except Exception as e:
                log.error(f"进度回调错误: {e}")
        
        # 注册间隔 (最后一个账号不延时)
        if idx < num_accounts - 1:
            delay = random.randint(REGISTER_SLEEP_MIN, REGISTER_SLEEP_MAX)
            log.info(f"↳ 等待 {delay}秒后注册下一个账号...")
            time.sleep(delay)
    
    # 注册完成统计
    log.info(f"\n========== 注册完成 ==========")
    log.info(f"✅ 成功: {success_count} | ❌ 失败: {failed_count} | 📊 成功率: {success_count/num_accounts*100:.1f}%")
    
    return {"success": success_count, "failed": failed_count}


def batch_register_with_db(task_id: int, num_accounts: int, use_proxy: bool = True) -> None:
    """
    批量注册账号（完整版，自动从IP池分配，更新任务状态到数据库）
    :param task_id: 注册任务ID
    :param num_accounts: 要注册的账号数量
    :param use_proxy: 是否使用代理IP
    """
    from app.models.db import get_db
    
    log.info(f"\n========== 任务#{task_id} 开始批量注册 {num_accounts} 个账号 ==========")
    
    # 获取代理IP列表
    proxy_list = []
    if use_proxy:
        conn = get_db()
        cur = conn.cursor()
        # 获取可用的美国IP（status=1 正常）
        cur.execute("""
            SELECT id, ip, port, proxy_user, proxy_pwd, area 
            FROM tn_ip_pool 
            WHERE status = 1 AND area LIKE '%US%'
            LIMIT ?
        """, (num_accounts,))
        rows = cur.fetchall()
        conn.close()
        
        proxy_list = [
            {"id": r[0], "ip": r[1], "port": r[2], "proxy_user": r[3], "proxy_pwd": r[4], "area": r[5]}
            for r in rows
        ]
        
        if len(proxy_list) < num_accounts:
            log.warning(f"可用IP不足: 需要{num_accounts}个，实际只有{len(proxy_list)}个")
            # 更新任务状态为失败
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                UPDATE tn_register_task 
                SET status = 3, failed_count = ?, updated_at = datetime('now')
                WHERE id = ?
            """, (num_accounts, task_id))
            conn.commit()
            conn.close()
            return
    
    # 定义进度回调
    def update_progress(current, total, success, failed):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            UPDATE tn_register_task 
            SET success_count = ?, failed_count = ?, updated_at = datetime('now')
            WHERE id = ?
        """, (success, failed, task_id))
        conn.commit()
        conn.close()
    
    # 执行批量注册
    result = batch_register(num_accounts, proxy_list, update_progress)
    
    # 更新任务最终状态
    conn = get_db()
    cur = conn.cursor()
    status = 2 if result["success"] > 0 else 3  # 2=完成, 3=失败
    cur.execute("""
        UPDATE tn_register_task 
        SET status = ?, success_count = ?, failed_count = ?, updated_at = datetime('now')
        WHERE id = ?
    """, (status, result["success"], result["failed"], task_id))
    conn.commit()
    conn.close()
    
    log.info(f"任务#{task_id} 完成 | 成功: {result['success']} | 失败: {result['failed']}")

# ===================== 命令行入口 =====================
def main():
    parser = argparse.ArgumentParser(description="TextNow iOS 账号注册脚本")
    parser.add_argument("-n", "--number", type=int, default=1, help="要注册的账号数量 (默认: 1)")
    parser.add_argument("-v", "--verbose", action="store_true", help="启用DEBUG日志")
    args = parser.parse_args()
    
    # 动态调整日志级别
    if args.verbose:
        log.setLevel(logging.DEBUG)
        log.debug("✅ 已启用DEBUG日志模式")
    
    # 执行批量注册
    batch_register(args.number)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("\n⚠️ 用户手动中断脚本执行")
    except Exception as e:
        log.critical(f"💥 脚本执行异常终止: {e}")
    finally:
        input("\n运行完毕，按回车键退出...")