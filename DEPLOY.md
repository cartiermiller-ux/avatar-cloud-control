# 阿凡达云控 - 部署文档

## 📋 目录

- [快速开始](#-快速开始)
- [环境要求](#-环境要求)
- [Docker 部署](#-docker-部署)
- [传统部署](#-传统部署)
- [配置说明](#-配置说明)
- [反向代理配置](#-反向代理配置)
- [运维指南](#-运维指南)

---

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/cartiermiller-ux/avatar-cloud-control.git
cd avatar-cloud-control

# 2. 一键启动
docker-compose up -d

# 3. 访问应用
open http://localhost:8899
```

### 方式二：传统部署

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动应用
python run.py
```

---

## 📦 环境要求

### Docker 部署

| 项目 | 要求 |
|------|------|
| Docker | 20.10+ |
| Docker Compose | 2.0+ |
| 内存 | 2GB+ |
| 磁盘 | 5GB+ |

### 传统部署

| 项目 | 要求 |
|------|------|
| Python | 3.9+ |
| pip | 21.0+ |
| 操作系统 | Linux / macOS / Windows (WSL2) |
| 数据库 | SQLite (默认) 或 MySQL 5.7+ |

---

## 🐳 Docker 部署

### 1. 构建镜像

```bash
docker-compose build
```

### 2. 配置环境变量（可选）

创建 `.env` 文件：

```bash
# 应用配置
SECRET_KEY=your-super-secret-key-here-change-in-production
FLASK_DEBUG=false
WEB_PORT=8899

# 日志级别 (DEBUG/INFO/WARNING/ERROR)
LOG_LEVEL=INFO

# 代理配置 (如需要通过代理访问 TextNow)
# TN_PROXY=socks5h://proxy:1080

# 数据库配置
DB_TYPE=sqlite
# DB_TYPE=mysql
# DB_HOST=mysql-server
# DB_PORT=3306
# DB_USER=textnow
# DB_PASS=your-password
# DB_NAME=textnow_us
```

### 3. 启动服务

```bash
# 开发环境
docker-compose up -d

# 生产环境 (使用生产配置)
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 查看日志
docker-compose logs -f

# 查看服务状态
docker-compose ps
```

### 4. 验证部署

```bash
# 健康检查
curl http://localhost:8899/health

# 访问应用
open http://localhost:8899
```

### 5. 停止服务

```bash
docker-compose down

# 删除容器和数据卷 (谨慎操作)
docker-compose down -v
```

---

## 🖥️ 传统部署

### 1. 安装系统依赖

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv libmariadb-dev pkg-config
```

**CentOS/RHEL:**
```bash
sudo yum install -y python3 python3-pip python3-devel mariadb-devel
```

**macOS:**
```bash
brew install python@3.11
```

**Windows:**
```powershell
# 使用 WSL2 或直接安装 Python
winget install Python.Python.3.11
```

### 2. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate     # Windows
```

### 3. 安装 Python 依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
# 创建环境变量文件
cat > .env << 'EOF'
FLASK_DEBUG=false
SECRET_KEY=your-secret-key-here
WEB_HOST=0.0.0.0
WEB_PORT=8899
LOG_LEVEL=INFO
DB_TYPE=sqlite
SQLITE_PATH=data/textnow_factory.db
EOF
```

### 5. 初始化数据库

```bash
# 应用启动时会自动创建数据库和默认管理员账号
# 默认管理员: admin / admin123
```

### 6. 使用 Gunicorn 启动（生产环境）

```bash
# 安装 Gunicorn (已在 requirements.txt 中)
pip install gunicorn

# 启动服务
gunicorn --bind 0.0.0.0:8899 --workers 4 --threads 2 --timeout 120 run:app

# 或使用 systemd 管理服务
sudo cp deployment/avatar-cloud-control.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable avatar-cloud-control
sudo systemctl start avatar-cloud-control
```

### 7. 使用 Systemd 管理（Linux）

创建服务文件 `/etc/systemd/system/avatar-cloud-control.service`:

```ini
[Unit]
Description=Avatar Cloud Control
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/avatar-cloud-control
Environment="PATH=/opt/avatar-cloud-control/venv/bin"
ExecStart=/opt/avatar-cloud-control/venv/bin/gunicorn --bind 0.0.0.0:8899 --workers 4 --timeout 120 run:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable avatar-cloud-control
sudo systemctl start avatar-cloud-control
```

---

## ⚙️ 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `SECRET_KEY` | (随机生成) | Flask 密钥，生产环境必须设置 |
| `FLASK_DEBUG` | `false` | 调试模式 (生产环境设为 false) |
| `WEB_HOST` | `0.0.0.0` | 监听地址 |
| `WEB_PORT` | `8899` | 监听端口 |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `DB_TYPE` | `sqlite` | 数据库类型 (sqlite/mysql) |
| `SQLITE_PATH` | `data/textnow_factory.db` | SQLite 数据库路径 |
| `TN_PROXY` | (空) | SOCKS5 代理地址 |
| `MATRIX_THREADS` | `4` | 矩阵群发线程数 |
| `MATRIX_BATCH_SIZE` | `50` | 矩阵批处理大小 |

### 数据库配置 (MySQL)

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `DB_HOST` | `127.0.0.1` | MySQL 主机 |
| `DB_PORT` | `3306` | MySQL 端口 |
| `DB_USER` | `root` | MySQL 用户名 |
| `DB_PASS` | (空) | MySQL 密码 |
| `DB_NAME` | `textnow_us` | 数据库名 |

---

## 🌐 反向代理配置

### Nginx

```nginx
upstream avatar_cloud {
    server 127.0.0.1:8899;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    client_max_body_size 50M;

    location / {
        proxy_pass http://avatar_cloud;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }

    location /static/ {
        alias /opt/avatar-cloud-control/app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

### Caddy

```caddy
your-domain.com {
    reverse_proxy localhost:8899
    encode zstd gzip
}
```

---

## 🔒 安全建议

### 生产环境必做

1. **设置强 SECRET_KEY**
   ```bash
   # 生成随机密钥
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **关闭调试模式**
   ```bash
   export FLASK_DEBUG=false
   ```

3. **使用 HTTPS**
   - 配置 SSL 证书
   - 使用反向代理或云负载均衡器

4. **配置防火墙**
   ```bash
   # 只允许 80/443 端口访问
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw deny 8899/tcp
   ```

5. **定期备份数据库**
   ```bash
   # 备份脚本
   cp data/textnow_factory.db "backup/textnow_factory_$(date +%Y%m%d).db"
   ```

---

## 🔧 运维指南

### 查看日志

```bash
# Docker 环境
docker-compose logs -f app

# 系统日志 (systemd)
journalctl -u avatar-cloud-control -f

# 应用日志
tail -f logs/app.log
```

### 性能调优

**Gunicorn 工作进程数：**
- CPU 密集型: `2-4 workers`
- I/O 密集型: `4-8 workers`

**线程数：**
- 默认: `2-4 threads`
- 高并发: `8-16 threads`

```bash
# 示例：高并发配置
gunicorn --bind 0.0.0.0:8899 --workers 8 --threads 4 --timeout 120 --keep-alive 5 run:app
```

### 数据迁移

```bash
# 导出数据
sqlite3 data/textnow_factory.db ".dump" > backup.sql

# 导入数据
sqlite3 data/textnow_factory.db < backup.sql
```

### 更新应用

```bash
# Docker 环境
git pull origin master
docker-compose build
docker-compose up -d

# 传统部署
git pull origin master
pip install -r requirements.txt
systemctl restart avatar-cloud-control
```

---

## 📞 故障排除

### 常见问题

**1. 数据库连接失败**
```bash
# 检查 SQLite 文件权限
chmod 755 data/
chmod 644 data/textnow_factory.db

# 或创建新数据库
python -c "from app.models.db import init_schema, init_default_data; init_schema(); init_default_data()"
```

**2. 端口被占用**
```bash
# 查看端口占用
netstat -tlnp | grep 8899

# 修改端口
export WEB_PORT=8898
```

**3. 上传文件失败**
```bash
# 检查上传目录权限
chmod 755 app/static/uploads/
```

**4. Docker 健康检查失败**
```bash
# 检查容器日志
docker-compose logs app

# 检查容器内网络
docker exec avatar-cloud-control curl -f http://localhost:8899/health
```

---

## 📄 许可证

本项目仅供学习和研究使用，请遵守 TextNow 服务条款。

---

## 📞 支持

如有问题，请提交 Issue 或联系维护者。