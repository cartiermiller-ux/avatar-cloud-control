-- 创建数据库
CREATE DATABASE IF NOT EXISTS avatar_cloud DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE avatar_cloud;

-- 1. 用户角色权限表 root/admin/user三级权限
DROP TABLE IF EXISTS `sys_user`;
CREATE TABLE `sys_user` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `username` VARCHAR(50) NOT NULL COMMENT '登录账号',
  `password` VARCHAR(128) NOT NULL COMMENT '加密密码',
  `real_name` VARCHAR(50) NOT NULL COMMENT '昵称',
  `role` ENUM('root','admin','user') NOT NULL DEFAULT 'user' COMMENT '角色：root超级管理员/admin分组管理员/user坐席',
  `bind_group_ids` VARCHAR(500) DEFAULT '' COMMENT '绑定分组ID，逗号分隔，root为空代表全权限',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '0禁用 1启用',
  `last_login_time` DATETIME NULL COMMENT '最后登录时间',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY uk_username (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='后台管理员&坐席权限表';

-- 初始化内置账号
INSERT INTO `sys_user` (`username`,`password`,`real_name`,`role`) VALUES
('root','$2b$12$Z8H1wN2XzY9GQkFvM7R6jeOq1uK2v3wX4y5z6','root超级管理员','root'),
('admin','$2b$12$Z8H1wN2XzY9GQkFvM7R6jeOq1uK2v3wX4y5z6','分组管理员','admin'),
('user','$2b$12$Z8H1wN2XzY9GQkFvM7R6jeOq1uK2v3wX4y5z6','普通坐席','user');
-- 明文密码统一为 123456，bcrypt加密存储

-- 2. 分组树形管理表（父子分组）
DROP TABLE IF EXISTS `group_info`;
CREATE TABLE `group_info` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '分组ID',
  `parent_id` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '父分组ID，0为顶级分组',
  `group_name` VARCHAR(100) NOT NULL COMMENT '分组名称',
  `desc` VARCHAR(500) DEFAULT '' COMMENT '分组备注',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY idx_parent (`parent_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='账号/设备树形分组表';

-- 默认基础分组
INSERT INTO `group_info` (`parent_id`,`group_name`,`desc`) VALUES
(0,'总分组','系统顶级根分组'),
(1,'B-美国','美国B线路资源分组'),
(1,'Aa-美国','美国Aa线路资源分组');

-- 3. iPhone设备管理表
DROP TABLE IF EXISTS `device_info`;
CREATE TABLE `device_info` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '设备ID',
  `device_name` VARCHAR(100) NOT NULL COMMENT '设备名称',
  `device_sn` VARCHAR(100) UNIQUE NOT NULL COMMENT 'iPhone设备唯一序列号',
  `phone_number` VARCHAR(30) NOT NULL COMMENT '设备绑定本机号码',
  `group_id` INT UNSIGNED NOT NULL COMMENT '所属分组ID',
  `online_status` TINYINT NOT NULL DEFAULT 0 COMMENT '0离线 1在线',
  `wifi_calling` TINYINT NOT NULL DEFAULT 0 COMMENT '0关闭 1开启WiFi Calling',
  `last_heartbeat` DATETIME NULL COMMENT '最后心跳在线时间',
  `remote_disconnect` TINYINT NOT NULL DEFAULT 0 COMMENT '远程断开标记',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY idx_group (`group_id`),
  KEY idx_online (`online_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='iPhone硬件设备管理表';

-- 4. iMessage/SMS账号表
DROP TABLE IF EXISTS `im_account`;
CREATE TABLE `im_account` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '账号ID',
  `device_id` INT UNSIGNED NOT NULL COMMENT '归属设备ID',
  `group_id` INT UNSIGNED NOT NULL COMMENT '归属分组',
  `account_type` ENUM('imessage','sms') NOT NULL COMMENT '账号类型',
  `phone_number` VARCHAR(30) NOT NULL COMMENT '账号号码',
  `register_status` ENUM('未注册','待激活','正常','封禁') NOT NULL DEFAULT '未注册' COMMENT '注册激活状态',
  `maturity_level` ENUM('低','中','高') NOT NULL DEFAULT '低' COMMENT '账号成熟度',
  `reconnect_count` INT NOT NULL DEFAULT 0 COMMENT '掉线重连次数',
  `last_offline_time` DATETIME NULL COMMENT '上次掉线时间',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY idx_device (`device_id`),
  KEY idx_group (`group_id`),
  KEY idx_status (`register_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='iMessage/SMS账号池表';

-- 5. 接码密钥表（对应截图密钥列表页面）
DROP TABLE IF EXISTS `api_key`;
CREATE TABLE `api_key` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '密钥主键ID',
  `name` VARCHAR(100) NOT NULL COMMENT '密钥名称',
  `key_str` VARCHAR(128) UNIQUE NOT NULL COMMENT '密钥字符串 gck_xxxx',
  `access_scope` VARCHAR(50) NOT NULL COMMENT '访问范围 B-美国/Aa-美国',
  `bind_group_ids` VARCHAR(500) DEFAULT '' COMMENT '绑定可访问分组ID，逗号分隔',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '0停用 1启用中',
  `last_use_time` DATETIME NULL COMMENT '最近调用取码时间',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY idx_status (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='第三方接码API密钥表';

-- 6. 接码号码资源池表
DROP TABLE IF EXISTS `receive_code_num`;
CREATE TABLE `receive_code_num` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '号码ID',
  `phone_number` VARCHAR(30) UNIQUE NOT NULL COMMENT '接码手机号',
  `device_id` INT UNSIGNED NOT NULL COMMENT '归属设备',
  `group_id` INT UNSIGNED NOT NULL COMMENT '归属分组',
  `current_key_id` INT UNSIGNED NULL COMMENT '当前占用密钥ID',
  `lock_minute` INT NOT NULL DEFAULT 5 COMMENT '锁定时长(分钟)',
  `lock_expire_time` DATETIME NULL COMMENT '锁定到期时间',
  `status` ENUM('空闲','占用','离线','封禁') NOT NULL DEFAULT '空闲',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY idx_group (`group_id`),
  KEY idx_status (`status`),
  KEY idx_key (`current_key_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='接码取号号码资源池';

-- 7. 验证码接收记录表
DROP TABLE IF EXISTS `code_record`;
CREATE TABLE `code_record` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '记录ID',
  `phone_number` VARCHAR(30) NOT NULL COMMENT '接收验证码号码',
  `verify_code` VARCHAR(20) DEFAULT '' COMMENT '验证码内容',
  `api_key_id` INT UNSIGNED NOT NULL COMMENT '调用密钥ID',
  `service_name` VARCHAR(100) DEFAULT '' COMMENT '所属业务服务',
  `receive_time` DATETIME NULL COMMENT '验证码接收时间',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY idx_phone (`phone_number`),
  KEY idx_key (`api_key_id`),
  KEY idx_create (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='验证码历史记录表';

-- 8. 批量推送任务表
DROP TABLE IF EXISTS `push_task`;
CREATE TABLE `push_task` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '任务ID',
  `task_name` VARCHAR(100) NOT NULL COMMENT '任务名称',
  `group_ids` VARCHAR(500) NOT NULL COMMENT '下发目标分组',
  `message_content` TEXT NOT NULL COMMENT '推送文本内容',
  `img_urls` TEXT DEFAULT '' COMMENT '附带图片地址，逗号分隔',
  `send_rule` TEXT DEFAULT '' COMMENT '推送规则配置JSON',
  `total_count` INT NOT NULL DEFAULT 0 COMMENT '总发送号码数',
  `send_count` INT NOT NULL DEFAULT 0 COMMENT '已发送数量',
  `success_count` INT NOT NULL DEFAULT 0 COMMENT '送达成功',
  `fail_count` INT NOT NULL DEFAULT 0 COMMENT '发送失败',
  `reply_count` INT NOT NULL DEFAULT 0 COMMENT '收到回复数',
  `progress` TINYINT NOT NULL DEFAULT 0 COMMENT '任务进度百分比',
  `status` ENUM('等待执行','执行中','已完成','已终止') NOT NULL DEFAULT '等待执行',
  `creator_uid` INT UNSIGNED NOT NULL COMMENT '创建人管理员ID',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `finish_time` DATETIME NULL COMMENT '任务完成时间',
  PRIMARY KEY (`id`),
  KEY idx_status (`status`),
  KEY idx_creator (`creator_uid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='iMessage/SMS批量推送任务';

-- 9. 自动回复规则表
DROP TABLE IF EXISTS `auto_reply_rule`;
CREATE TABLE `auto_reply_rule` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '规则ID',
  `rule_name` VARCHAR(100) NOT NULL COMMENT '规则名称',
  `match_keyword` TEXT NOT NULL COMMENT '触发关键词，多词逗号分隔',
  `reply_text` TEXT NOT NULL COMMENT '自动回复文字内容',
  `reply_img` VARCHAR(500) DEFAULT '' COMMENT '回复图片地址',
  `bind_group_ids` VARCHAR(500) DEFAULT '' COMMENT '生效分组',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '0关闭 1启用',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY idx_status (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='消息自动回复规则';

-- 10. 实时聊天会话表（坐席分配）
DROP TABLE IF EXISTS `chat_session`;
CREATE TABLE `chat_session` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '会话ID',
  `target_phone` VARCHAR(30) NOT NULL COMMENT '外部客户号码',
  `local_phone` VARCHAR(30) NOT NULL COMMENT '我方发送账号号码',
  `group_id` INT UNSIGNED NOT NULL COMMENT '归属分组',
  `agent_uid` INT UNSIGNED NULL COMMENT '分配坐席用户ID，NULL=未分配',
  `unread_count` INT NOT NULL DEFAULT 0 COMMENT '未读消息数量',
  `last_msg_time` DATETIME NULL COMMENT '最后消息时间',
  `session_status` ENUM('待分配','处理中','已关闭') NOT NULL DEFAULT '待分配',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY idx_agent (`agent_uid`),
  KEY idx_group (`group_id`),
  KEY idx_status (`session_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='客服实时聊天会话';

-- 11. 聊天消息记录表
DROP TABLE IF EXISTS `chat_message`;
CREATE TABLE `chat_message` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '消息ID',
  `session_id` INT UNSIGNED NOT NULL COMMENT '所属会话ID',
  `msg_type` ENUM('text','image') NOT NULL DEFAULT 'text' COMMENT '消息类型',
  `content` TEXT NOT NULL COMMENT '文字内容/图片链接',
  `direction` ENUM('in','out') NOT NULL COMMENT 'in客户发来 out我方发出',
  `send_status` ENUM('发送中','已送达','发送失败') NOT NULL DEFAULT '发送中',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY idx_session (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='聊天消息历史记录';

-- 12. 号码共享资源表
DROP TABLE IF EXISTS `share_resource`;
CREATE TABLE `share_resource` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '共享ID',
  `share_code` VARCHAR(32) UNIQUE NOT NULL COMMENT '共享短链标识',
  `share_link` VARCHAR(200) NOT NULL COMMENT '完整访问链接',
  `phone_ids` TEXT NOT NULL COMMENT '共享号码ID集合',
  `expire_time` DATETIME NULL COMMENT '共享过期时间，NULL永久有效',
  `creator_uid` INT UNSIGNED NOT NULL COMMENT '创建管理员',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY uk_share_code (`share_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='号码资源共享分发表';

-- 13. 全局数据统计表（多维统计）
DROP TABLE IF EXISTS `stat_daily`;
CREATE TABLE `stat_daily` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '统计ID',
  `stat_date` DATE NOT NULL COMMENT '统计日期',
  `group_id` INT UNSIGNED NOT NULL COMMENT '分组ID，0=全平台汇总',
  `device_online_num` INT NOT NULL DEFAULT 0 COMMENT '当日在线设备数',
  `total_send` INT NOT NULL DEFAULT 0 COMMENT '当日总发送消息',
  `total_success` INT NOT NULL DEFAULT 0 COMMENT '送达成功',
  `total_fail` INT NOT NULL DEFAULT 0 COMMENT '发送失败',
  `total_reply` INT NOT NULL DEFAULT 0 COMMENT '收到回复消息',
  `total_get_code` INT NOT NULL DEFAULT 0 COMMENT '当日接码取号次数',
  `wifi_calling_online` INT NOT NULL DEFAULT 0 COMMENT '开启WiFi Calling设备数量',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_date_group (`stat_date`,`group_id`),
  PRIMARY KEY (`id`),
  KEY idx_date (`stat_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='每日多维数据统计表';

-- 14. 接码取码请求日志（截图「取码请求」标签页）
DROP TABLE IF EXISTS `api_code_request_log`;
CREATE TABLE `api_code_request_log` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '日志ID',
  `api_key_id` INT UNSIGNED NOT NULL COMMENT '调用密钥ID',
  `request_api` VARCHAR(100) NOT NULL COMMENT '接口路径',
  `phone_number` VARCHAR(30) DEFAULT '' COMMENT '操作号码',
  `request_ip` VARCHAR(50) NOT NULL COMMENT '调用方IP',
  `response_code` INT NOT NULL COMMENT '返回状态码 200成功/400失败',
  `response_msg` TEXT DEFAULT '' COMMENT '返回提示信息',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY idx_key (`api_key_id`),
  KEY idx_create (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='接码API调用日志（取码请求页面）';