# 安全加固修复报告

## 目标
修复代码审查中发现的安全漏洞和协议一致性问题。

## 修复清单

### 1. 密码安全 — bcrypt 替代 SHA-256
- **auth.py**: `_verify_password()` 支持 bcrypt + SHA-256 兼容验证
- **auth.py**: `_hash_password()` 优先 bcrypt，回退 SHA-256
- **auth.py**: 登录成功后自动升级旧 SHA-256 哈希为 bcrypt
- **auth.py**: 添加会话固定攻击防护（登录时 `session.clear()` 再重建）
- **db.py**: `init_default_data()` 新建管理员使用 bcrypt 哈希
- **scripts/upgrade_admin_bcrypt.py**: 现有管理员哈希升级为 bcrypt
- ✅ 测试通过：错误密码被拒绝，正确密码登录成功，哈希已升级为 `$2b$12$`

### 2. SQL 注入修复
- **salesman_assign.py**: `api_assign_logs()` 中 LIMIT/OFFSET 从 f-string 拼接改为参数化查询 `?`

### 3. 凭据暴露修复
- **accounts.py**: CSV 导出移除 password、sid、token、proxy_user、proxy_pwd 字段
- **accounts.py**: proxy_str() 不再包含代理认证信息

### 4. 配置安全
- **settings.py**: SECRET_KEY 默认 `os.urandom(32).hex()`（不再硬编码）
- **settings.py**: FLASK_DEBUG 默认 false（不再默认 true）
- **settings.py**: DB_PASS 默认空字符串

### 5. 协议/代码一致性修复
- **message.py**: 全部 SQL 语法改为 SQLite `?` 占位符（之前用 MySQL `%s`）
- **message.py**: 表名修正 `accounts→tn_accounts`, `conversations→tn_conversations`, `messages→tn_messages`
- **message.py**: 字段名修正 `px_authorization→px_auth`, `device_fp→device_fp`, `contact_phone→contact_number`
- **messenger.py**: 修复 import 路径 `models.db→app.models.db`, `core.proxy→app.core.proxy`
- **register.py**: 移除 `check_account_exists()` 引用（函数不存在）
- **register.py**: `SSL_VERIFY` 改为环境变量配置（不再硬编码 `verify=False`）
- **register.py**: 日志脱敏（邮箱/手机号部分遮蔽）
- **register.py**: PX_AUTH_SECRET 改为环境变量（不再硬编码字节串）

### 6. Schema 修复
- **db.py**: `tn_conversations` 增加 `last_message`, `unread`, `salesman_id`, `updated_at` 列
- **db.py**: `tn_accounts` 增加 `salesman_id` 列
- **db.py**: 新增 `tn_account_assign_log` 表
- **scripts/migrate_db.py**: 对现有数据库执行 ALTER TABLE 迁移

### 7. 路径/端点修复
- **__init__.py**: template_folder/static_folder 改为绝对路径指向项目根目录
- **__init__.py**: 登录重定向修正 `pages.dashboard→pages.index`

## 未推送
本地 commit `02cacab` 已保存。GitHub push 因网络问题失败（与昨日相同），需后续手动 `git push origin master`。

## 仍存风险（未修复）
- 无 CSRF 保护
- 无速率限制（登录暴力破解）
- 明文数据库连接密码（SQLite 无加密）
- 调试信息可能泄露（环境变量可控）