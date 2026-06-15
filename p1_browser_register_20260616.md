# P1 浏览器自动化注册实现

**时间**: 2026-06-16 00:20
**状态**: 脚本已完成，网络阻塞

---

## 实现内容

### 1. 浏览器自动化注册脚本
- **文件**: `scripts/browser_register.py`
- **技术**: Playwright + Chromium
- **特性**:
  - 支持 headless/headed 模式
  - 自动检测 PerimeterX 挑战
  - 人工干预模式（显示浏览器窗口）
  - 批量注册支持
  - 代理支持
  - 注册结果保存为 JSON

### 2. 与移动端 API 对比

| 特性 | 移动端 API (register.py) | Web 自动化 (browser_register.py) |
|------|------------------------|--------------------------------|
| 端点 | `api.textnow.me` | `www.textnow.com` |
| 鉴权 | X-PX-Auth（占位符 ❌） | connect.sid Cookie ✅ |
| PerimeterX | 403 拦截 | 浏览器绕过 ✅ |
| 验证码 | 无处理 | 人工干预模式 |
| 稳定性 | 低 | 高 |

---

## 依赖安装

```bash
pip install playwright -i https://pypi.tuna.tsinghua.edu.cn/simple
python -m playwright install chromium
```

已验证：
- playwright 1.60.0 ✅
- chromium 已安装 ✅

---

## 阻塞因素

**网络**: 当前开发环境无法访问 textnow.com

解决方案：
1. 在有 VPN/代理的环境中运行脚本
2. 使用 `--proxy` 参数配置代理
3. 在境外服务器上运行

---

## 使用示例

```bash
# 单账号注册（无头模式）
python scripts/browser_register.py --headless

# 显示浏览器（调试模式）
python scripts/browser_register.py --headed

# 批量注册
python scripts/browser_register.py --count 5 --headless

# 使用代理
python scripts/browser_register.py --proxy "http://user:pass@proxy:port"
```

---

## 后续步骤

1. ✅ 脚本完成
2. ⏳ 在可访问环境运行
3. ⏳ 导入账号到数据库
4. ⏳ 验证消息收发功能
