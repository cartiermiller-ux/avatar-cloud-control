"""
TextNow Factory - 应用入口
用法: python run.py
"""

import os
import sys
from pathlib import Path

# 确保项目根目录在路径中
BASE_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(BASE_DIR))

from app.config import WEB_HOST, WEB_PORT, FLASK_DEBUG
from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", WEB_PORT))
    host = os.environ.get("HOST", WEB_HOST)
    app.run(host=host, port=port, debug=FLASK_DEBUG)
