"""
TextNow Factory - 住宅IP代理工具模块
提供从 db 读取账号绑定 IP、构造 requests 代理字典的功能
"""

import logging
log = logging.getLogger(__name__)

try:
    import requests
except ImportError:
    requests = None


def get_account_proxy(account_id):
    """
    从数据库读取指定账号绑定的住宅IP。
    
    返回 dict 或 None:
        {"ip": str, "port": int, "user": str, "pwd": str, "proxy_url": str}
    
    用法：
        proxy_info = get_account_proxy(account_id)
        if proxy_info:
            proxies = {
                "http": proxy_info["proxy_url"],
                "https": proxy_info["proxy_url"]
            }
        else:
            proxies = None
        
        resp = requests.get("https://example.com", proxies=proxies, timeout=15)
    """
    try:
        from app.models.db import get_db_dict
        conn = get_db_dict()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT p.ip, p.port, p.proxy_user, p.proxy_pwd, p.area
            FROM tn_ip_pool p
            INNER JOIN tn_account_ip ai ON p.id = ai.ip_id
            WHERE ai.account_id = ?
        """, (account_id,))
        row = cur.fetchone()
        conn.close()
        
        if not row:
            return None
        
        ip = row["ip"]
        port = row["port"]
        user = row["proxy_user"] or ""
        pwd = row["proxy_pwd"] or ""
        area = row["area"] or ""
        
        if user and pwd:
            proxy_url = f"http://{user}:{pwd}@{ip}:{port}"
        else:
            proxy_url = f"http://{ip}:{port}"
        
        return {
            "ip": ip,
            "port": port,
            "user": user,
            "pwd": pwd,
            "area": area,
            "proxy_url": proxy_url
        }
    except Exception as e:
        log.error("get_account_proxy(%s) error: %s", account_id, e)
        return None


def auto_assign_proxy(account_id):
    """
    自动为账号分配一条空闲的住宅IP。
    返回分配的代理信息 dict，无可用IP返回 None。
    """
    try:
        from app.models.db import get_db
        conn = get_db()
        cur = conn.cursor()
        
        # 取第一条正常、未分配的IP
        cur.execute("SELECT id, ip, port, proxy_user, proxy_pwd FROM tn_ip_pool WHERE status=1 LIMIT 1")
        row = cur.fetchone()
        if not row:
            conn.close()
            return None
        
        ip_id = row[0]
        ip = row[1]
        port = row[2]
        proxy_user = row[3] or ""
        proxy_pwd = row[4] or ""
        
        # 绑定关联（先清除旧绑定）
        cur.execute("DELETE FROM tn_account_ip WHERE account_id=?", (account_id,))
        cur.execute("INSERT INTO tn_account_ip (account_id, ip_id) VALUES (?, ?)", (account_id, ip_id))
        cur.execute("UPDATE tn_ip_pool SET status=2 WHERE id=?", (ip_id,))
        conn.commit()
        conn.close()
        
        if proxy_user and proxy_pwd:
            proxy_url = f"http://{proxy_user}:{proxy_pwd}@{ip}:{port}"
        else:
            proxy_url = f"http://{ip}:{port}"
        
        return {"ip": ip, "port": port, "user": proxy_user, "pwd": proxy_pwd, "proxy_url": proxy_url}
    except Exception as e:
        log.error("auto_assign_proxy(%s) error: %s", account_id, e)
        return None


def check_ip_alive(ip_addr, port, proxy_user="", proxy_pwd="", timeout=10):
    """
    检测一条IP是否可用。
    
    返回:
        True: 可用
        False: 不可用
    """
    if requests is None:
        log.warning("requests not installed, skipping IP check")
        return None
    
    try:
        if proxy_user and proxy_pwd:
            proxy_url = f"http://{proxy_user}:{proxy_pwd}@{ip_addr}:{port}"
        else:
            proxy_url = f"http://{ip_addr}:{port}"
        
        proxies = {"http": proxy_url, "https": proxy_url}
        resp = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=timeout)
        return resp.status_code == 200
    except Exception:
        return False


def request_with_proxy(account_id, method, url, **kwargs):
    """
    使用账号绑定的代理IP发送HTTP请求。
    
    参数同 requests.request，自动注入 proxies。
    
    返回:
        requests.Response 或 None（无代理或请求失败时）
    """
    if requests is None:
        log.warning("requests not installed, cannot proxy request")
        return None
    
    proxy_info = get_account_proxy(account_id)
    if proxy_info:
        proxies = {
            "http": proxy_info["proxy_url"],
            "https": proxy_info["proxy_url"]
        }
        kwargs["proxies"] = proxies
        kwargs.setdefault("timeout", 15)
    
    try:
        return requests.request(method, url, **kwargs)
    except Exception as e:
        log.error("request_with_proxy(account=%s, %s %s) error: %s", account_id, method, url, e)
        return None
