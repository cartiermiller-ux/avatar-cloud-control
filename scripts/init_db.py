#!/usr/bin/env python3
"""
TextNow Factory - 数据库初始化脚本
功能：
1. 创建所有数据库表（执行 schema.sql）
2. 插入默认数据（管理员账号、默认模板等）
"""

import sys
from pathlib import Path

# 确保项目根目录在 Python 路径中
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from models.db import init_schema, init_default_data
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger(__name__)


def main():
    """主函数：初始化数据库"""
    try:
        log.info("开始初始化数据库...")
        
        # 1. 创建表结构
        log.info("1. 创建数据库表...")
        init_schema()
        
        # 2. 插入默认数据
        log.info("2. 插入默认数据...")
        init_default_data()
        
        log.info("✅ 数据库初始化完成！")
        log.info("默认管理员账号：admin / admin123")
        
    except Exception as e:
        log.error(f"❌ 初始化失败：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
