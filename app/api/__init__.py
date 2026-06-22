from flask import Blueprint

# 创建接码开放API蓝图
api_bp = Blueprint("api", __name__, url_prefix="/api")

# 导入接口路由，注册到蓝图
from . import code_api