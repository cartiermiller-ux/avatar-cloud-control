# TextNow 逆向 API 接口验证报告

**验证时间**: 2026-06-16 00:11
**验证方式**: 代码审读 + 外部开源项目交叉验证

---

## 总判定：**部分正确，存在多处关键错误，当前代码无法端到端跑通**

---

## 1. API 端点验证

| 代码中的端点 | 判定 | 说明 |
|---|---|---|
| `api.textnow.me/api/v2/users` (POST 注册) | ⚠️ 域名正确，路径存疑 | 移动端 API 域名正确，但注册端点路径未经公开验证。社区项目均走 Web 端 `www.textnow.com` |
| `api.textnow.me/api/v2/users/{username}/messages` | ⚠️ 域名正确，路径可能过时 | 移动端域名正确，但社区项目普遍使用 Web 端 API |
| `www.textnow.com/api/messages` (POST 发送) | ✅ 基本正确 | 与 PyTextNow、pythontextnow 等开源项目一致 |
| `www.textnow.com/api/mms.send` (POST 图片) | ⚠️ 未验证 | 开源项目中无对应实现 |

**核心问题：项目混用了两套 API 体系**

```
移动端 API (api.textnow.me)     Web 端 API (www.textnow.com)
├── 鉴权: X-PX-Auth + X-Idfa     ├── 鉴权: connect.sid Cookie
├── 注册: register.py ✅         ├── 注册: 无（需浏览器）
├── 消息: message.py ❌ 字段不匹配 ├── 消息: PyTextNow ✅
└── 风控: PerimeterX 移动端      └── 风控: PerimeterX Web 端 + _px3 Cookie
```

---

## 2. X-PX-Auth 生成算法验证

**代码实现** (`register.py:107-115`):
```python
secret = b"textnow_px_secret_2024"
raw = f'{dev_info["idfa"]}{dev_info["px_uuid"]}{ts}'.encode("utf-8")
sig = base64.b64encode(hmac.new(secret, raw, hashlib.sha256).digest()).decode("utf-8")
r64 = ''.join(random.choice(string.hexdigits.lower()) for _ in range(64))
pad = ''.join(random.choice(string.ascii_letters + string.digits + "+/=") for _ in range(200))
return f"3:{r64}:{sig}:{pad}"
```

| 项目 | 判定 | 说明 |
|---|---|---|
| 格式 `3:{hex}:{sig}:{pad}` | ⚠️ 格式可能正确 | PerimeterX v3 格式确实如此 |
| HMAC-SHA256 算法 | ⚠️ 算法可能正确 | PX 确实使用 HMAC-SHA256 |
| Secret `textnow_px_secret_2024` | ❌ **错误** | 占位符，需从客户端 JS 提取真实密钥 |
| 随机填充 200 字符 | ⚠️ 可疑 | 真实 PX Auth 填充包含加密行为指纹，非纯随机 |

---

## 3. 鉴权字段/表名不一致（代码内部 bug）

| 模块 | 写入字段 | 读取字段 | 状态 |
|---|---|---|---|
| register.py | `px_auth` | message.py 读取 `px_authorization` | ❌ 不匹配 |
| register.py | `device_fp` | message.py 读取 `px_device_fp` | ❌ 不匹配 |
| register.py | `phone_number` | message.py 读取 `phone` | ❌ 不匹配 |
| register.py 写入 `tn_accounts` | message.py 查询 `accounts` | ❌ 表名不匹配 |

---

## 4. 致命问题汇总

```
┌─────────────────────────────────────────────────────────────┐
│ ❌ 无法跑通的根本原因                                         │
├─────────────────────────────────────────────────────────────┤
│ 1. X-PX-Auth Secret 是占位符                                 │
│    → 注册请求 100% 会被 PerimeterX 拦截返回 403              │
│                                                              │
│ 2. 注册缺少验证码环节                                        │
│    → TextNow 注册有 PerimeterX 人机验证                      │
│    → 即使 secret 正确，也需处理 _px3 Cookie / CAPTCHA        │
│                                                              │
│ 3. 鉴权字段命名不一致（代码内部 bug）                         │
│    → 注册写入: px_auth, device_fp, phone_number              │
│    → 消息读取: px_authorization, px_device_fp, phone         │
│                                                              │
│ 4. 表名不一致（代码内部 bug）                                │
│    → register.py 写入 tn_accounts                            │
│    → message.py 查询 accounts                               │
│                                                              │
│ 5. 两套 API 体系混用                                         │
│    → 注册走移动端 api.textnow.me                             │
│    → 发送走 Web 端 www.textnow.com                           │
│    → 两套鉴权体系不互通                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. 修复路线图

| 优先级 | 修复项 | 工作量 |
|---|---|---|
| 🔴 P0 | 统一 API 体系：全走移动端或全走 Web 端 | 中 |
| 🔴 P0 | 修复字段命名不一致 | 小 |
| 🔴 P0 | 修复表名不一致 | 小 |
| 🔴 P0 | 逆向提取真实 PerimeterX secret | 大 |
| 🟠 P1 | 处理注册流程验证码 | 大 |
| 🟠 P1 | 验证移动端消息 API 请求体格式 | 中 |

**最可行路径**：放弃移动端 API，统一改用 **Web 端 API**（`www.textnow.com`），鉴权改为 `connect.sid` Cookie，与 PyTextNow 对齐。注册功能改为浏览器自动化（Playwright/Selenium）。

---

## 参考开源项目

- **PyTextNow**: https://github.com/LaconicFromHell/PyTextNow
- **pythontextnow**: https://github.com/abahbob/pythontextnow

---

## 结论

项目中的 API 端点域名和基本路径方向正确，但：
1. **X-PX-Auth 的 HMAC Secret 是错误的占位符**
2. **注册缺少验证码处理**
3. **代码内部字段/表名不一致**

当前状态**无法端到端跑通**，需要选择统一 API 体系并修复内部不一致问题。
