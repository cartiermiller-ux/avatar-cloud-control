# Avatar Cloud Control

TextNow 账号管理平台 — 注册、分发、群发、会话一体化管理系统。

## 项目结构

```
textnow_factory2/
├── app/                          # 应用主包
│   ├── __init__.py               # Flask 应用工厂 (create_app)
│   ├── config/                   # 配置模块
│   │   ├── __init__.py
│   │   └── settings.py           # 所有配置项 (支持环境变量覆盖)
│   ├── models/                   # 数据模型
│   │   ├── __init__.py
│   │   ├── db.py                 # 数据库连接 (SQLite/MySQL 双支持)
│   │   └── schema.sql            # MySQL 建表语句
│   ├── views/                    # 路由 (Blueprint)
│   │   ├── auth.py               # 登录/登出
│   │   ├── pages.py             # 页面渲染
│   │   ├── dashboard.py         # 控制台统计 API
│   │   ├── accounts.py          # 账号管理 CRUD + 导入导出
│   │   ├── register.py          # 注册任务 API
│   │   ├── matrix.py            # 矩阵群发 API
│   │   ├── agents.py            # 客服代理管理 API
│   │   ├── salesmen.py          # 业务员管理 API
│   │   ├── salesman_assign.py   # 业务员分配/回收/日志 API
│   │   ├── conversations.py     # 会话管理 API
│   │   ├── messages.py          # 消息收发 API
│   │   ├── templates.py         # 消息模板 API
│   │   ├── ip_manage.py         # IP 池管理 API
│   │   └── upload.py            # 文件上传 API
│   ├── core/                     # 核心业务模块
│   │   ├── register.py          # 账号注册编辑
│   │   ├── message.py           # 消息收发编辑
│   │   ├── messenger.py         # 消息发送器 (文本/图片/链接)
│   │   ├── matrix.py            # 矩阵群发引擎
│   │   └── proxy.py             # 代理 IP 工具
│   └── common/                   # 通用工具 (暂留)
├── templates/                    # HTML 模板 (Layui)
├── static/                       # 静态资源
│   └── uploads/                  # 上传文件目录
├── scripts/                      # 运维脚本
│   ├── init_db.py               # 数据库初始化
│   ├── import_accounts.py       # 账号导入工具
│   └── import_20_expired.py     # 过期账号导入
├── data/                         # 数据目录
│   └── textnow_factory.db       # SQLite 数据库
├── venv/                         # Python 虚拟环境
├── run.py                        # 应用入口
├── requirements.txt              # Python 依赖
├── .gitignore
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
cd textnow_factory2
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. 启动服务

```bash
python run.py
```

默认地址: `http://0.0.0.0:8899`

### 3. 默认账号

- 用户名: `admin`
- 密码: `admin123`

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DB_TYPE` | `sqlite` | 数据库类型 (sqlite/mysql) |
| `SQLITE_PATH` | `data/textnow_factory.db` | SQLite 路径 |
| `WEB_HOST` | `0.0.0.0` | 监听地址 |
| `WEB_PORT` | `8899` | 监听端口 |
| `SECRET_KEY` | 内置默认 | Flask 会话密钥 |
| `FLASK_DEBUG` | `true` | 调试模式 |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `TN_PROXY` | 关闭 | 启用 SOCKS5 代理 |

## API 路由一览

| 模块 | 路由 | 说明 |
|------|------|------|
| 认证 | `POST /login` | 登录 |
| 认证 | `GET /logout` | 登出 |
| 控制台 | `GET /api/dashboard/stats` | 统计数据 |
| 账号 | `GET/POST /api/accounts` | 列表/新增 |
| 账号 | `POST /api/accounts/update` | 更新 |
| 账号 | `POST /api/accounts/delete` | 删除 |
| 账号 | `POST /api/accounts/batch_import` | 批量导入 |
| 账号 | `GET /api/accounts/export` | 导出 |
| 注册 | `GET /api/register/tasks` | 注册任务列表 |
| 注册 | `POST /api/register/create` | 创建注册任务 |
| 注册 | `POST /api/register/cancel` | 取消任务 |
| 矩阵 | `GET /api/matrix/tasks` | 群发任务列表 |
| 矩阵 | `POST /api/matrix/create` | 创建群发任务 |
| 矩阵 | `POST /api/matrix/start` | 启动群发 |
| 会话 | `GET /api/conversations` | 会话列表 |
| 消息 | `GET /api/messages` | 消息列表 |
| 消息 | `POST /api/messages/send` | 发送消息 |
| IP管理 | `GET /api/ip/list` | IP 列表 |
| IP管理 | `POST /api/ip/batch_import` | IP 批量导入 |
| 业务员 | `GET /api/salesmen` | 业务员列表 |
| 客服 | `GET /api/agents` | 客服代理列表 |

## 技术栈

- **后端**: Flask + SQLAlchemy (兼容 SQLite / MySQL)
- **前端**: Layui CDN + 原生 JS
- **数据库**: SQLite (开箱即用) / MySQL (生产环境)
