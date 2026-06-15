# TextNow API 统一化修复报告

**修复时间**: 2026-06-16 00:13 - 00:20
**优先级**: P0（按验证报告逐项修复）

---

## 已完成的修复

### P0-1：字段/表名不一致 ✅
- `matrix.py`: `accounts` → `tn_accounts`，`phone` → `phone_number`
- `matrix.py`: 注释中 `px_authorization` → `px_auth`，`px_device_fp` → `device_fp`
- `message.py`: `content` → `content[:200]`（防止 last_message 字段溢出）

### P0-2：MySQL 占位符 → SQLite 占位符 ✅
- `matrix.py`: 全部 `%s` → `?`（20+ 处）
- `import_accounts.py`: 全部 `%s` → `?`（2 处）

### P0-3：API 体系统一化 ✅
**变更前**：混用两套 API（注册走移动端 `api.textnow.me`，发消息走 Web 端 `www.textnow.com`）

**变更后**：
| 模块 | 旧端点 | 新端点 | 旧鉴权 | 新鉴权 |
|------|--------|--------|--------|--------|
| message.py (拉取) | `api.textnow.me/api/v2/users/{user}/messages` | `www.textnow.com/api/messages` | Bearer + x-px-authorization | connect.sid Cookie |
| message.py (发送) | `api.textnow.me/api/v2/users/{user}/messages` | `www.textnow.com/api/messages` | Bearer + x-px-authorization | connect.sid Cookie |
| messenger.py (发送) | `www.textnow.com/api/messages` | `www.textnow.com/api/messages` | connect.sid | connect.sid（已对齐） |
| messenger.py (图片) | `www.textnow.com/api/mms.send` | 不变 | connect.sid | 不变 |

**统一后的鉴权方式**：
- **Cookie**: `connect.sid={sid}`（domain: `.textnow.com`）
- **User-Agent**: 浏览器 UA（不再是移动端 UA）
- **Headers**: Origin + Referer（Web API 标配）

**不影响**：
- `register.py`：仍使用移动端 API（`api.textnow.me`），因为 Web 端注册需浏览器自动化（P1 任务）

---

## 仍需修复（P1/P2）

| 优先级 | 问题 | 状态 |
|--------|------|------|
| 🟠 P1 | 注册改为浏览器自动化（绕过 PerimeterX） | 未开始 |
| 🟠 P1 | 注册 PerimeterX secret 逆向提取 | 未开始（依赖抓包） |
| 🟡 P2 | matrix.py 接入真实发送协议（当前为模拟逻辑） | 未开始 |

---

## 验证状态

- ✅ 应用启动正常（61 路由）
- ✅ 本地 commit `889e6d0` 已保存
- ⏳ GitHub push 待网络恢复后推送（3 个未推送 commit）
