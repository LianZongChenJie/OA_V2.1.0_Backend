-- ============================================
-- 招标文件智能生成模块 - 数据库建表SQL
-- ============================================

-- 1. 招标文件信息表
CREATE TABLE IF NOT EXISTS `oa_tender_document` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT 'ID',
    `tender_uuid` VARCHAR(64) NOT NULL COMMENT '招标文件UUID',
    `file_name` VARCHAR(256) NOT NULL DEFAULT '' COMMENT '原始文件名',
    `tender_name` VARCHAR(256) NOT NULL DEFAULT '' COMMENT '招标项目名称',
    `tender_code` VARCHAR(128) NOT NULL DEFAULT '' COMMENT '招标编号',
    `company_name` VARCHAR(256) NOT NULL DEFAULT '' COMMENT '招标单位',
    `total_pages` INT NOT NULL DEFAULT 0 COMMENT '总页数',
    `status` SMALLINT NOT NULL DEFAULT 0 COMMENT '状态:0已解析,1匹配中,2已完成',
    `requirements_json` TEXT COMMENT '人员配置要求JSON',
    `score_standard_json` TEXT COMMENT '评标标准JSON',
    `file_path` VARCHAR(500) NOT NULL DEFAULT '' COMMENT '原始文件路径',
    `generated_file_path` VARCHAR(500) NOT NULL DEFAULT '' COMMENT '生成的投标文件路径',
    `admin_id` INT NOT NULL DEFAULT 0 COMMENT '创建人',
    `create_time` BIGINT NOT NULL DEFAULT 0 COMMENT '创建时间',
    `update_time` BIGINT NOT NULL DEFAULT 0 COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_tender_uuid` (`tender_uuid`),
    KEY `idx_tender_name` (`tender_name`),
    KEY `idx_tender_code` (`tender_code`),
    KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='招标文件信息表';

-- 2. 招标要求明细表
CREATE TABLE IF NOT EXISTS `oa_tender_requirement` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT 'ID',
    `tender_id` INT NOT NULL DEFAULT 0 COMMENT '关联招标文件ID',
    `requirement_type` VARCHAR(64) NOT NULL DEFAULT '' COMMENT '要求类型:学历/工作/技能/证书/业绩',
    `requirement_key` VARCHAR(128) NOT NULL DEFAULT '' COMMENT '要求键:education/work_years/skills/certificates',
    `operator` VARCHAR(32) NOT NULL DEFAULT '' COMMENT '运算符:eq/gte/lte/contains/in',
    `requirement_value` VARCHAR(500) NOT NULL DEFAULT '' COMMENT '要求值',
    `score_weight` DECIMAL(5,2) NOT NULL DEFAULT 0.00 COMMENT '评分权重(0-100)',
    `description` TEXT COMMENT '要求描述',
    `create_time` BIGINT NOT NULL DEFAULT 0 COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_tender_id` (`tender_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='招标要求明细表';

-- 3. 投标人员映射表
CREATE TABLE IF NOT EXISTS `oa_bid_personnel_mapping` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT 'ID',
    `tender_id` INT NOT NULL DEFAULT 0 COMMENT '关联招标文件ID',
    `resume_id` INT NOT NULL DEFAULT 0 COMMENT '简历ID',
    `match_score` DECIMAL(5,2) NOT NULL DEFAULT 0.00 COMMENT '匹配得分',
    `match_reason` TEXT COMMENT '匹配原因',
    `sort_order` INT NOT NULL DEFAULT 0 COMMENT '排序序号',
    `is_selected` SMALLINT NOT NULL DEFAULT 0 COMMENT '是否选中:1选中,0推荐中',
    `create_time` BIGINT NOT NULL DEFAULT 0 COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_tender_id` (`tender_id`),
    KEY `idx_resume_id` (`resume_id`),
    KEY `idx_is_selected` (`is_selected`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='投标人员映射表';

-- ============================================
-- 菜单插入SQL
-- ============================================
-- 招标文件管理菜单（parent_id=4 为AI管理目录）
INSERT INTO `sys_menu` (`menu_id`, `menu_name`, `parent_id`, `order_num`, `path`, `component`, `query`, `route_name`, `is_frame`, `is_cache`, `menu_type`, `visible`, `status`, `perms`, `icon`, `create_by`, `create_time`, `update_by`, `update_time`, `remark`)
VALUES (2516, '招标文件管理', 4, 5, 'tender', 'ai/tender/index', NULL, NULL, 1, 0, 'C', '0', '0', 'tender:list', 'education', 1, NOW(), NULL, NULL, '招标文件智能生成管理');

-- 招标文件管理按钮权限
INSERT INTO `sys_menu` (`menu_id`, `menu_name`, `parent_id`, `order_num`, `path`, `component`, `query`, `route_name`, `is_frame`, `is_cache`, `menu_type`, `visible`, `status`, `perms`, `icon`, `create_by`, `create_time`, `update_by`, `update_time`, `remark`)
VALUES (2517, '招标文件上传', 2516, 1, '', NULL, NULL, NULL, 1, 0, 'F', '0', '0', 'tender:add', '#', 1, NOW(), NULL, NULL, '');

INSERT INTO `sys_menu` (`menu_id`, `menu_name`, `parent_id`, `order_num`, `path`, `component`, `query`, `route_name`, `is_frame`, `is_cache`, `menu_type`, `visible`, `status`, `perms`, `icon`, `create_by`, `create_time`, `update_by`, `update_time`, `remark`)
VALUES (2518, '人员匹配', 2516, 2, '', NULL, NULL, NULL, 1, 0, 'F', '0', '0', 'tender:match', '#', 1, NOW(), NULL, NULL, '');

INSERT INTO `sys_menu` (`menu_id`, `menu_name`, `parent_id`, `order_num`, `path`, `component`, `query`, `route_name`, `is_frame`, `is_cache`, `menu_type`, `visible`, `status`, `perms`, `icon`, `create_by`, `create_time`, `update_by`, `update_time`, `remark`)
VALUES (2519, '选择人员', 2516, 3, '', NULL, NULL, NULL, 1, 0, 'F', '0', '0', 'tender:select', '#', 1, NOW(), NULL, NULL, '');

INSERT INTO `sys_menu` (`menu_id`, `menu_name`, `parent_id`, `order_num`, `path`, `component`, `query`, `route_name`, `is_frame`, `is_cache`, `menu_type`, `visible`, `status`, `perms`, `icon`, `create_by`, `create_time`, `update_by`, `update_time`, `remark`)
VALUES (2520, '生成投标文件', 2516, 4, '', NULL, NULL, NULL, 1, 0, 'F', '0', '0', 'tender:generate', '#', 1, NOW(), NULL, NULL, '');

INSERT INTO `sys_menu` (`menu_id`, `menu_name`, `parent_id`, `order_num`, `path`, `component`, `query`, `route_name`, `is_frame`, `is_cache`, `menu_type`, `visible`, `status`, `perms`, `icon`, `create_by`, `create_time`, `update_by`, `update_time`, `remark`)
VALUES (2521, '删除招标文件', 2516, 5, '', NULL, NULL, NULL, 1, 0, 'F', '0', '0', 'tender:delete', '#', 1, NOW(), NULL, NULL, '');

-- 关联超级管理员角色（role_id=1）
INSERT INTO `sys_role_menu` (`role_id`, `menu_id`) VALUES (1, 2516);
INSERT INTO `sys_role_menu` (`role_id`, `menu_id`) VALUES (1, 2517);
INSERT INTO `sys_role_menu` (`role_id`, `menu_id`) VALUES (1, 2518);
INSERT INTO `sys_role_menu` (`role_id`, `menu_id`) VALUES (1, 2519);
INSERT INTO `sys_role_menu` (`role_id`, `menu_id`) VALUES (1, 2520);
INSERT INTO `sys_role_menu` (`role_id`, `menu_id`) VALUES (1, 2521);
