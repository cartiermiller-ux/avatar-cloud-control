\# 阿凡达云控 iMessage/SMS群控接码系统 部署文档

\## 系统介绍

完整实现12大功能：设备管控、账号管理、树形分组、接码密钥、批量推送、自动回复、实时坐席聊天、号码共享、三级RBAC权限、多维数据统计，支持iPhone WebSocket长连接、第三方开放接码API。



\## 环境要求

\### 本地单机测试

Python3.12+/MySQL8.0/Redis5+

\### 生产部署

Docker Compose 一键部署 / Linux Nginx反向代理HTTPS



\## 一、本地手动部署步骤

1\. 安装依赖

pip install -r requirements.txt

2\. 导入数据库

mysql -uroot -p < avatar\_cloud.sql

3\. 启动Redis、MySQL服务

4\. 初始化数据库（可选）

flask init\_db

5\. 启动异步任务

python celery\_worker.py

6\. 启动后端Web+WebSocket服务

python run.py

7\. 访问后台：http://127.0.0.1:5000/admin/login

默认账号：root / 密码：123456



\## 二、Docker一键部署

1\. 安装docker \& docker-compose

2\. 执行启动

docker-compose up -d

3\. 等待mysql初始化完成，访问5000端口



\## 三、Nginx生产上线

1\. 将nginx/avatar\_https.conf放入nginx站点配置

2\. 修改域名、SSL证书路径

3\. nginx -t \&\& systemctl reload nginx



\## 四、iPhone设备对接

1\. 本地调试：运行demo\_client/iphone\_sim\_client.py模拟iPhone

2\. 真机iOS：参考iOS\_Swift\_Demo，连接ws://域名/ws/device

3\. 通信协议统一JSON格式，支持心跳、收发短信、验证码上报



\## 五、第三方接码API调用

api\_demo文件夹提供Python/PHP完整封装，鉴权使用X-Api-Key请求头，包含取号、查验证码、释放号码、批量查询历史接口。



\## 六、功能对应清单

1\. 设备管理 | device\_list.html + app/admin/device.py

2\. 账号管理 | account\_list.html + app/admin/account.py

3\. 树形分组 | group\_manage.html + app/admin/group.py

4\. 接码密钥（截图界面）| key\_list.html + app/admin/key.py

5\. 批量推送 | push\_task.html + app/admin/push.py + Celery任务

6\. 自动回复 | auto\_reply.html + app/admin/auto\_reply.py

7\. 实时坐席聊天 | chat\_workbench.html + WebSocket聊天通道

8\. 号码共享 | share\_resource表 + 后台共享生成接口

9\. 三级权限RBAC | sys\_user表 + login\_required/role\_required装饰器

10\. 多维数据统计 | stat\_overview.html + stat\_daily表 + Excel导出

11\. iPhone设备WebSocket长连接 | /ws/device 服务端+客户端Demo

12\. 开放接码API | /api/receive\_code 全套开放接口

