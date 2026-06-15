# ============================================================
# 阿凡达云控 (Avatar Cloud Control) - Dockerfile
# ============================================================
# 多阶段构建：构建阶段 + 运行阶段
# ============================================================

# -------------------- 阶段1: 构建 --------------------
FROM python:3.11-slim AS builder

WORKDIR /app

# 安装编译依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmariadb-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# -------------------- 阶段2: 运行 --------------------
FROM python:3.11-slim

WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmariadb-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制已安装的包
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# 复制应用代码
COPY . .

# 创建数据目录
RUN mkdir -p data app/static/uploads logs

# 设置环境变量默认值
ENV PYTHONUNBUFFERED=1
ENV FLASK_DEBUG=false
ENV DB_TYPE=sqlite
ENV SQLITE_PATH=data/textnow_factory.db
ENV WEB_HOST=0.0.0.0
ENV WEB_PORT=8899

# 暴露端口
EXPOSE 8899

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8899/health || exit 1

# 启动命令
CMD ["gunicorn", "--bind", "0.0.0.0:8899", "--workers", "4", "--threads", "2", "--timeout", "120", "run:app"]