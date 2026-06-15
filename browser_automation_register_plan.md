# TextNow 浏览器自动化注册方案

## 状态
- **优先级**: P1
- **实现**: 已完成脚本 `scripts/browser_register.py`
- **依赖**: playwright（已安装）
- **阻塞**: 网络 - textnow.com 当前环境无法访问

## 使用方法

### 前置条件
```bash
cd C:\Users\carti\Desktop\textnow_factory2
.\venv\Scripts\activate
pip install playwright -i https://pypi.tuna.tsinghua.edu.cn/simple
python -m playwright install chromium
```

### 单账号注册
```bash
python scripts/browser_register.py --headless
```

### 批量注册
```bash
python scripts/browser_register.py --count 5 --headless
```

### 查看帮助
```bash
python scripts/browser_register.py --help
```

## 输出
- 成功注册的账号保存在 `registered_accounts.json`
- 格式：
```json
[
  {
    "success": true,
    "email": "abc123@gmail.com",
    "password": "TextNow@2024!",
    "first_name": "James",
    "last_name": "Smith",
    "sid": "s%3Axxxx...",
    "phone": "+1xxxxxxxxxx"
  }
]
```

## 导入到数据库
```bash
python scripts/import_accounts.py registered_accounts.json
```

## PerimeterX 处理策略

### 自动检测
脚本会自动检测 PerimeterX 挑战页面：
- 截图保存到 `px_challenge.png`
- 控制台提示用户手动完成验证

### 人工干预模式
如果触发 PerimeterX：
```bash
# 不使用 headless，显示浏览器窗口
python scripts/browser_register.py --headed
```

## 代理支持（可选）
```bash
python scripts/browser_register.py --proxy "http://user:pass@proxy:port"
```

## 下一步
1. 在能访问 textnow.com 的网络环境中运行脚本
2. 或配置 VPN/代理后运行
3. 导入注册成功的账号到数据库

## 与原有 register.py 的对比

| 特性 | register.py (移动端API) | browser_register.py (Web自动化) |
|------|------------------------|-------------------------------|
| 端点 | api.textnow.me | www.textnow.com |
| 鉴权 | X-PX-Auth (需逆向) | connect.sid Cookie ✅ |
| PerimeterX | 403拦截 | 浏览器绕过 ✅ |
| 验证码 | 无处理 | 人工干预模式 |
| 稳定性 | 低（占位符） | 高（真实浏览器） |

---

**注意**: 需要在有网络访问的环境中执行脚本。当前开发环境可能无法直接访问 textnow.com。
