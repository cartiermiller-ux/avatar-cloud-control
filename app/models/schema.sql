-- TextNow Factory 数据库表结构
-- MySQL 版本（SQLite 需适当调整数据类型）

-- ===================== 账号表 =====================
CREATE TABLE IF NOT EXISTS `tn_accounts` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(255) UNIQUE NOT NULL COMMENT 'TextNow 用户名',
    `password` VARCHAR(255) COMMENT '密码',
    `sid` VARCHAR(255) COMMENT 'Session ID',
    `token` TEXT COMMENT '认证 Token',
    `phone_number` VARCHAR(50) COMMENT 'TextNow 手机号',
    `email` VARCHAR(255) COMMENT '注册邮箱',
    `idfa` VARCHAR(255) COMMENT '设备 IDFA',
    `user_agent` TEXT COMMENT 'User-Agent',
    `px_auth` TEXT COMMENT 'X-PX-Auth',
    `device_fp` VARCHAR(255) COMMENT '设备指纹',
    `os_version` VARCHAR(50) COMMENT 'iOS 版本',
    `client_id` VARCHAR(255) COMMENT 'Client ID',
    `proxy` VARCHAR(255) COMMENT '代理地址',
    `status` TINYINT DEFAULT 1 COMMENT '状态：1=正常，0=禁用，2=异常',
    `health_score` INT DEFAULT 100 COMMENT '健康度评分',
    `last_used_at` DATETIME COMMENT '最后使用时间',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_status` (`status`),
    INDEX `idx_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='TextNow 账号表';

-- ===================== 坐席/操作员表 =====================
CREATE TABLE IF NOT EXISTS `tn_agents` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(255) UNIQUE NOT NULL COMMENT '登录用户名',
    `password_hash` VARCHAR(255) NOT NULL COMMENT '密码 Hash (SHA256)',
    `nickname` VARCHAR(255) COMMENT '昵称',
    `role` VARCHAR(50) DEFAULT 'agent' COMMENT '角色：admin/agent',
    `is_active` TINYINT DEFAULT 1 COMMENT '是否启用：1=是，0=否',
    `last_login_time` DATETIME COMMENT '最后登录时间',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='坐席/操作员表';

-- ===================== 账号分配表 =====================
CREATE TABLE IF NOT EXISTS `tn_account_assignment` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `account_id` INT NOT NULL COMMENT '账号 ID',
    `agent_id` INT NOT NULL COMMENT '坐席 ID',
    `assigned_by` INT COMMENT '分配人 ID',
    `assigned_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY `uk_account_agent` (`account_id`, `agent_id`),
    INDEX `idx_agent` (`agent_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='账号分配表';

-- ===================== 会话表 =====================
CREATE TABLE IF NOT EXISTS `tn_conversations` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `account_id` INT NOT NULL COMMENT '账号 ID',
    `contact_number` VARCHAR(50) NOT NULL COMMENT '联系人号码',
    `status` TINYINT DEFAULT 1 COMMENT '状态：1=打开，0=关闭',
    `last_message_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '最后消息时间',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY `uk_account_contact` (`account_id`, `contact_number`),
    INDEX `idx_account` (`account_id`),
    INDEX `idx_contact` (`contact_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='会话表';

-- ===================== 消息表 =====================
CREATE TABLE IF NOT EXISTS `tn_messages` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `conversation_id` INT NOT NULL COMMENT '会话 ID',
    `direction` TINYINT NOT NULL COMMENT '方向：1=收到，2=发出',
    `content` TEXT COMMENT '消息内容',
    `is_auto_reply` TINYINT DEFAULT 0 COMMENT '是否自动回复：1=是，0=否',
    `read_status` TINYINT DEFAULT 0 COMMENT '已读状态：0=未读，1=已读',
    `msg_type` VARCHAR(50) DEFAULT 'text' COMMENT '消息类型：text/media',
    `sent_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '发送时间',
    `message_id` VARCHAR(255) COMMENT 'TextNow 消息 ID',
    INDEX `idx_conversation` (`conversation_id`),
    INDEX `idx_sent_at` (`sent_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='消息表';

-- ===================== 回复模板表 =====================
CREATE TABLE IF NOT EXISTS `tn_templates` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(255) NOT NULL COMMENT '模板名称',
    `shortcut` VARCHAR(50) COMMENT '快捷指令',
    `content` TEXT COMMENT '模板内容',
    `category` VARCHAR(100) COMMENT '分类',
    `is_active` TINYINT DEFAULT 1 COMMENT '是否启用：1=是，0=否',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_shortcut` (`shortcut`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='回复模板表';

-- ===================== 自动回复规则表 =====================
CREATE TABLE IF NOT EXISTS `tn_auto_rules` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(255) COMMENT '规则名称',
    `keywords` TEXT COMMENT '关键词（逗号分隔）',
    `template_id` INT COMMENT '关联模板 ID',
    `priority` INT DEFAULT 0 COMMENT '优先级',
    `is_active` TINYINT DEFAULT 1 COMMENT '是否启用：1=是，0=否',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_priority` (`priority`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='自动回复规则表';

-- ===================== 注册任务表 =====================
CREATE TABLE IF NOT EXISTS `tn_register_task` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `task_name` VARCHAR(255) NOT NULL DEFAULT '',
    `total_num` INTEGER DEFAULT 0 COMMENT '注册数量',
    `use_proxy` TINYINT DEFAULT 0 COMMENT '是否使用代理：0=否，1=是',
    `status` TINYINT DEFAULT 1 COMMENT '状态：0=待开始，1=注册中，2=完成，3=失败/取消',
    `success_count` INTEGER DEFAULT 0,
    `failed_count` INTEGER DEFAULT 0,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ===================== 群发任务表 =====================
CREATE TABLE IF NOT EXISTS `tn_broadcast_task` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(255) COMMENT '任务名称',
    `content` TEXT COMMENT '群发内容',
    `status` TINYINT DEFAULT 0 COMMENT '状态：0=待发送，1=发送中，2=完成，3=暂停',
    `total_count` INT DEFAULT 0 COMMENT '总数量',
    `sent_count` INT DEFAULT 0 COMMENT '已发送',
    `failed_count` INT DEFAULT 0 COMMENT '失败数',
    `created_by` INT COMMENT '创建人 ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `started_at` DATETIME COMMENT '开始时间',
    `finished_at` DATETIME COMMENT '完成时间',
    INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='群发任务表';

-- ===================== 群发明细表 =====================
CREATE TABLE IF NOT EXISTS `tn_broadcast_item` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `task_id` INT NOT NULL COMMENT '任务 ID',
    `account_id` INT COMMENT '发送账号 ID',
    `target_number` VARCHAR(50) COMMENT '目标号码',
    `status` TINYINT DEFAULT 0 COMMENT '状态：0=待发送，1=成功，2=失败，3=重试中',
    `retry_count` INT DEFAULT 0 COMMENT '重试次数',
    `error_msg` TEXT COMMENT '错误信息',
    `sent_at` DATETIME COMMENT '发送时间',
    INDEX `idx_task` (`task_id`),
    INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='群发明细表';

-- ===================== 系统设置表 =====================
CREATE TABLE IF NOT EXISTS `tn_settings` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `key` VARCHAR(255) UNIQUE NOT NULL COMMENT '配置键',
    `value` TEXT COMMENT '配置值',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_key` (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统设置表';

-- ===================== 初始化默认数据 =====================
-- 默认管理员账号：admin / admin123
INSERT IGNORE INTO `tn_agents` (`username`, `password_hash`, `nickname`, `role`, `is_active`) 
VALUES ('admin', SHA2('admin123', 256), '管理员', 'admin', 1);

-- 默认回复模板
INSERT IGNORE INTO `tn_templates` (`name`, `shortcut`, `content`, `category`, `is_active`)
VALUES 
('问候', 'hello', '您好！有什么我可以帮助您的吗？', '常用', 1),
('感谢', 'thanks', '感谢您的咨询，祝您生活愉快！', '常用', 1);

-- 默认系统设置
INSERT IGNORE INTO `tn_settings` (`key`, `value`)
VALUES 
('site_name', 'TextNow Factory'),
('max_accounts_per_agent', '10'),
('auto_reply_enabled', '1');
