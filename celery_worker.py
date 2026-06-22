import sys
sys.path.insert(0, ".")
from celery import Celery, Task
import os
import dotenv

# 全局加载.env
dotenv.load_dotenv(".env")
os.environ.setdefault("FLASK_APP", "run.py")

# 先加载Flask应用实例
from run import app
from app.utils.redis_pool import redis_url

# 自定义Task：所有任务自动携带Flask上下文
class FlaskContextTask(Task):
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return self.run(*args, **kwargs)

# 实例化celery
celery = Celery("avatar_tasks", broker=redis_url, backend=redis_url, task_cls=FlaskContextTask)
celery.conf.update(app.config)
celery.autodiscover_tasks(["app.tasks"])

if __name__ == "__main__":
    # Windows必须eventlet池，Linux可去掉-P eventlet
    celery.worker_main(["worker", "--loglevel=info", "-c", "4", "-P", "eventlet"])