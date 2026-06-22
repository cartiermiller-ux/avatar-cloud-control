import requests
import json

class AvatarCloudCodeClient:
    def __init__(self, api_base: str, api_key: str):
        self.api_base = api_base.rstrip("/")
        self.headers = {
            "X-Api-Key": api_key,
            "Content-Type": "application/json"
        }

    # 1. 随机取在线空闲号码
    def get_random_phone(self, lock_minute: int = 5):
        """
        :param lock_minute: 号码锁定时长，单位分钟
        :return: dict 包含phone、lock_expire锁定到期时间
        """
        url = f"{self.api_base}/get_random_num"
        payload = {"lock_min": lock_minute}
        resp = requests.post(url, headers=self.headers, json=payload, timeout=15)
        return resp.json()

    # 2. 查询号码验证码
    def get_verify_code(self, phone: str):
        url = f"{self.api_base}/get_code_by_phone"
        payload = {"phone_number": phone}
        resp = requests.post(url, headers=self.headers, json=payload, timeout=15)
        return resp.json()

    # 3. 手动释放号码
    def release_phone(self, phone: str):
        url = f"{self.api_base}/release_num"
        payload = {"phone_number": phone}
        resp = requests.post(url, headers=self.headers, json=payload, timeout=15)
        return resp.json()

    # 4. 查询号码状态
    def get_phone_status(self, phone: str):
        url = f"{self.api_base}/num_status"
        payload = {"phone_number": phone}
        resp = requests.post(url, headers=self.headers, json=payload, timeout=15)
        return resp.json()

    # 5. 批量查询历史验证码
    def batch_query_history(self, phone_list: list):
        url = f"{self.api_base}/batch_history_code"
        payload = {"phones": phone_list}
        resp = requests.post(url, headers=self.headers, json=payload, timeout=15)
        return resp.json()


if __name__ == "__main__":
    # ========== 配置参数（修改为你自己的地址和密钥） ==========
    API_BASE_URL = "http://127.0.0.1:5000/api/receive_code"
    API_KEY = "gck_4ed779c2874a465145635d238d6f"

    # 初始化客户端
    client = AvatarCloudCodeClient(API_BASE_URL, API_KEY)

    # 示例1：随机取号，锁定10分钟
    res = client.get_random_phone(lock_minute=10)
    print("【随机取号结果】", json.dumps(res, indent=2, ensure_ascii=False))
    if res["code"] == 200:
        target_phone = res["data"]["phone"]

        # 示例2：查询该号码验证码（循环轮询等待短信）
        import time
        for _ in range(30):
            code_res = client.get_verify_code(target_phone)
            if code_res["code"] == 200 and code_res["data"].get("verify_code"):
                print(f"【获取到验证码】号码:{target_phone} 验证码:{code_res['data']['verify_code']}")
                break
            print("等待验证码...")
            time.sleep(2)

        # 示例3：手动释放号码（业务完成后调用）
        release_res = client.release_phone(target_phone)
        print("【释放号码结果】", json.dumps(release_res, indent=2, ensure_ascii=False))

        # 示例4：查询号码状态
        status_res = client.get_phone_status(target_phone)
        print("【号码状态】", json.dumps(status_res, indent=2, ensure_ascii=False))

        # 示例5：批量查询多个号码历史记录
        batch_res = client.batch_query_history([target_phone])
        print("【批量历史记录】", json.dumps(batch_res, indent=2, ensure_ascii=False))