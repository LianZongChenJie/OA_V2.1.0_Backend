# 修改行政区划自增属性
ALTER TABLE oa20_dev.oa_area MODIFY COLUMN id int(11) unsigned NOT NULL;

#售票管理，开票状态添加未开票状态
ALTER TABLE oa20_dev.oa_ticket MODIFY COLUMN open_status tinyint(1) unsigned DEFAULT 1 NULL COMMENT '开票状态：0,未开票，1正常 2已作废';

# 导入部门sql
DELIMITER $$

DROP PROCEDURE IF EXISTS update_ancestors$$

CREATE PROCEDURE update_ancestors()
BEGIN
    DECLARE rows_affected INT DEFAULT 1;
    DECLARE loop_count INT DEFAULT 0;

    -- 初始设置：顶级部门 ancestors = '0'
    UPDATE sys_dept SET ancestors = NULL;
    UPDATE sys_dept SET ancestors = '0' WHERE parent_id = 0 OR parent_id IS NULL;

    -- 循环更新子部门
    WHILE rows_affected > 0 AND loop_count < 20 DO
        UPDATE sys_dept AS child
        JOIN sys_dept AS parent ON child.parent_id = parent.dept_id
        SET child.ancestors = CONCAT(parent.ancestors, ',', parent.dept_id)
        WHERE child.ancestors IS NULL
          AND parent.ancestors IS NOT NULL;

        SET rows_affected = ROW_COUNT();
        SET loop_count = loop_count + 1;
    END WHILE;

    -- 处理孤儿部门（父级不存在或未更新成功）
    UPDATE sys_dept SET ancestors = '0' WHERE ancestors IS NULL;
END$$

DELIMITER ;

-- 执行存储过程
CALL update_ancestors();

-- 删除存储过程（可选）
DROP PROCEDURE IF EXISTS update_ancestors;
# 导入部门结束

# 导入角色
START TRANSACTION;

-- 插入数据，忽略主键冲突
INSERT IGNORE INTO sys_role (
    role_id,
    role_name,
    role_key,
    role_sort,
    data_scope,
    menu_check_strictly,
    dept_check_strictly,
    status,
    del_flag,
    create_by,
    create_time,
    update_by,
    update_time,
    remark
)
SELECT
    oa.id,
    LEFT(oa.title, 30),   -- 截断过长的角色名
    CONCAT('group_', oa.id),   -- 生成唯一 role_key
    0,                     -- role_sort 默认 0
    '1',                   -- data_scope 全部数据权限
    1,                     -- menu_check_strictly
    1,                     -- dept_check_strictly
    CASE
        WHEN oa.status = 1 THEN '0'   -- 启用 → 正常
        WHEN oa.status = 0 THEN '1'   -- 禁用 → 停用
        ELSE '1'                      -- 其他 → 停用
    END,
    CASE
        WHEN oa.status = -1 THEN '2'  -- 删除标记
        ELSE '0'
    END,
    'migration',
    FROM_UNIXTIME(oa.create_time),
    'migration',
    FROM_UNIXTIME(oa.update_time),
    oa.`desc`
FROM oa_admin_group oa;

COMMIT;
# 导入角色结束


