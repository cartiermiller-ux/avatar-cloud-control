"""
TextNow Web 端注册自动化脚本
使用 Playwright 浏览器自动化绕过 PerimeterX 风控
"""

import asyncio
import random
import string
import logging
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)

# 尝试导入 playwright
try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    log.error("playwright 未安装，请运行: pip install playwright && playwright install chromium")

# 注册信息配置
FIRST_NAMES = ["James", "John", "Michael", "David", "Chris", "Alex", "Kevin", "Brian", "Ryan", "Eric"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Wilson", "Taylor"]
PASSWORD = "TextNow@2024!"  # 统一密码，便于管理


def generate_email():
    """生成随机邮箱"""
    prefix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    domains = ["gmail.com", "outlook.com", "yahoo.com", "hotmail.com"]
    return f"{prefix}@{random.choice(domains)}"


def generate_name():
    """生成随机姓名"""
    return random.choice(FIRST_NAMES), random.choice(LAST_NAMES)


async def register_textnow_account(headless=False, proxy=None):
    """
    使用浏览器自动化注册 TextNow 账号

    :param headless: 是否无头模式
    :param proxy: 代理服务器 (格式: http://user:pass@host:port)
    :return: dict {success, email, password, sid, phone, error}
    """
    if not PLAYWRIGHT_AVAILABLE:
        return {"success": False, "error": "playwright 未安装"}

    email = generate_email()
    first_name, last_name = generate_name()

    log.info(f"开始注册: {email} | {first_name} {last_name}")

    browser_args = []
    if proxy:
        browser_args.append(f"--proxy-server={proxy}")

    async with async_playwright() as p:
        try:
            # 启动浏览器
            browser = await p.chromium.launch(
                headless=headless,
                args=browser_args if browser_args else None
            )

            context = await browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                locale="en-US",
                timezone_id="America/New_York"
            )

            page = await context.new_page()

            # 监听网络请求，捕获 connect.sid
            sid_cookie = None

            async def capture_sid(response):
                nonlocal sid_cookie
                if 'textnow.com' in response.url:
                    cookies = await context.cookies()
                    for cookie in cookies:
                        if cookie['name'] == 'connect.sid':
                            sid_cookie = cookie['value']

            page.on('response', capture_sid)

            # 访问注册页面
            log.info("打开注册页面...")
            await page.goto("https://www.textnow.com/signup", wait_until="networkidle", timeout=60000)

            # 等待页面加载
            await page.wait_for_timeout(2000)

            # 检查是否有 PerimeterX 拦截
            if "PerimeterX" in await page.title() or "px-captcha" in page.url:
                log.warning("检测到 PerimeterX 验证，需要人工干预")
                # 等待用户手动完成验证
                await page.screenshot(path="px_challenge.png")
                log.info("已截图保存到 px_challenge.png，请手动完成验证")
                # 等待验证完成（最长等待 60 秒）
                try:
                    await page.wait_for_url("**/signup**", timeout=60000)
                except PlaywrightTimeout:
                    await browser.close()
                    return {"success": False, "error": "PerimeterX 验证超时"}

            # 填写注册表单
            log.info("填写注册表单...")

            # 邮箱
            email_input = await page.query_selector('input[type="email"], input[name="email"], input[placeholder*="email"]')
            if email_input:
                await email_input.fill(email)
            else:
                log.warning("未找到邮箱输入框，尝试其他选择器")
                # 尝试查找所有输入框
                inputs = await page.query_selector_all('input')
                for inp in inputs:
                    inp_type = await inp.get_attribute('type')
                    if inp_type in ['email', 'text', None]:
                        await inp.fill(email)
                        break

            await page.wait_for_timeout(500)

            # 密码
            password_input = await page.query_selector('input[type="password"], input[name="password"]')
            if password_input:
                await password_input.fill(PASSWORD)

            await page.wait_for_timeout(500)

            # 姓名（如果有单独的输入框）
            first_name_input = await page.query_selector('input[name="first_name"], input[placeholder*="First"]')
            if first_name_input:
                await first_name_input.fill(first_name)

            last_name_input = await page.query_selector('input[name="last_name"], input[placeholder*="Last"]')
            if last_name_input:
                await last_name_input.fill(last_name)

            await page.wait_for_timeout(500)

            # 点击注册按钮
            log.info("点击注册按钮...")
            signup_button = await page.query_selector('button[type="submit"], button:has-text("Sign Up"), button:has-text("Create Account")')
            if signup_button:
                await signup_button.click()
            else:
                log.warning("未找到注册按钮")
                await page.screenshot(path="signup_page.png")
                await browser.close()
                return {"success": False, "error": "未找到注册按钮"}

            # 等待注册完成
            log.info("等待注册完成...")
            try:
                # 可能会跳转到主页面或显示选号页面
                await page.wait_for_url(lambda url: "textnow.com" in url and url != "https://www.textnow.com/signup", timeout=30000)
            except PlaywrightTimeout:
                log.warning("注册跳转超时，检查当前页面")
                await page.screenshot(path="signup_result.png")

            # 检查是否有错误消息
            error_msg = await page.query_selector('.error, .alert-error, [class*="error"]')
            if error_msg:
                error_text = await error_msg.text_content()
                log.error(f"注册失败: {error_text}")
                await browser.close()
                return {"success": False, "error": error_text}

            # 获取分配的号码
            phone_number = None
            try:
                # 尝试从页面获取号码
                phone_element = await page.query_selector('[class*="phone"], [data-phone], .user-phone')
                if phone_element:
                    phone_number = await phone_element.text_content()

                # 如果没找到，尝试从 URL 或其他地方获取
                if not phone_number:
                    # 检查是否在选择号码页面
                    if "choose-number" in page.url or "select-number" in page.url:
                        # 点击选择第一个可用号码
                        first_number = await page.query_selector('.number-option:first-child, .phone-number-option:first-child')
                        if first_number:
                            await first_number.click()
                            await page.wait_for_timeout(2000)

            except Exception as e:
                log.warning(f"获取号码失败: {e}")

            # 确保 connect.sid 已捕获
            if not sid_cookie:
                cookies = await context.cookies()
                for cookie in cookies:
                    if cookie['name'] == 'connect.sid':
                        sid_cookie = cookie['value']
                        break

            await browser.close()

            result = {
                "success": True,
                "email": email,
                "password": PASSWORD,
                "first_name": first_name,
                "last_name": last_name,
                "sid": sid_cookie,
                "phone": phone_number
            }

            log.info(f"注册成功: {email} | sid={sid_cookie[:20] if sid_cookie else 'N/A'}...")
            return result

        except PlaywrightTimeout as e:
            log.error(f"超时错误: {e}")
            return {"success": False, "error": f"超时: {str(e)}"}

        except Exception as e:
            log.error(f"注册失败: {e}", exc_info=True)
            return {"success": False, "error": str(e)}


async def batch_register(count=1, headless=False, proxy_list=None):
    """批量注册账号"""
    results = []

    for i in range(count):
        log.info(f"\n{'='*50}")
        log.info(f"正在注册第 {i+1}/{count} 个账号")
        log.info(f"{'='*50}")

        proxy = proxy_list[i] if proxy_list and i < len(proxy_list) else None

        result = await register_textnow_account(headless=headless, proxy=proxy)
        results.append(result)

        if result['success']:
            log.info(f"✓ 成功: {result['email']} → {result.get('phone', 'N/A')}")
        else:
            log.error(f"✗ 失败: {result.get('error', '未知错误')}")

        # 注册间隔（避免触发风控）
        if i < count - 1:
            wait_time = random.randint(30, 60)
            log.info(f"等待 {wait_time} 秒后继续...")
            await asyncio.sleep(wait_time)

    return results


def save_results(results, output_file="registered_accounts.json"):
    """保存注册结果到文件"""
    import json
    from pathlib import Path

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    log.info(f"结果已保存到: {output_path.absolute()}")


# 同步接口（供外部调用）
def register_account(headless=False, proxy=None):
    """同步注册接口"""
    if not PLAYWRIGHT_AVAILABLE:
        return {"success": False, "error": "playwright 未安装"}
    return asyncio.run(register_textnow_account(headless=headless, proxy=proxy))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="TextNow 自动注册工具")
    parser.add_argument("--count", type=int, default=1, help="注册数量")
    parser.add_argument("--headless", action="store_true", help="无头模式")
    parser.add_argument("--output", default="registered_accounts.json", help="输出文件")

    args = parser.parse_args()

    if not PLAYWRIGHT_AVAILABLE:
        print("错误: playwright 未安装")
        print("请运行: pip install playwright && playwright install chromium")
        exit(1)

    results = asyncio.run(batch_register(count=args.count, headless=args.headless))

    # 统计
    success_count = sum(1 for r in results if r['success'])
    print(f"\n{'='*50}")
    print(f"注册完成: 成功 {success_count}/{len(results)}")
    print(f"{'='*50}")

    save_results(results, args.output)
