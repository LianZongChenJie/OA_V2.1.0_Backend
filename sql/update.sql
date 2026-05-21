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
-- 修复排序规则冲突：oa_admin 合并到 sys_user（无冲突版）
INSERT INTO oa20_dev_test.sys_user (
    dept_id,
    did,
    pid,
    position_id,
    position_name,
    position_rank,
    user_name,
    nick_name,
    user_type,
    is_staff,
    email,
    phonenumber,
    job_number,
    birthday,
    age,
    work_date,
    work_location,
    native_place,
    nation,
    home_address,
    current_address,
    contact,
    contact_mobile,
    resident_type,
    resident_place,
    graduate_school,
    graduate_day,
    political,
    marital_status,
    idcard,
    education,
    speciality,
    social_account,
    medical_account,
    provident_account,
    bank_account,
    bank_info,
    sex,
    avatar,
    file_ids,
    user_desc,
    is_hide,
    entry_time,
    delete_time,
    password,
    status,
    del_flag,
    login_ip,
    login_num,
    is_lock,
    login_date,
    pwd_update_date,
    create_time,
    update_time,
    remark,
    auth_did,
    auth_dids,
    son_dids,
    admin_status
)
SELECT
    0 AS dept_id,
    a.did,
    a.pid,
    a.position_id,
    a.position_name,
    a.position_rank,
    a.username AS user_name,
    a.name AS nick_name,
    CASE a.type
        WHEN 1 THEN '01'
        WHEN 2 THEN '02'
        WHEN 3 THEN '03'
        ELSE '00'
        END AS user_type,
    a.is_staff,
    a.email,
    CAST(a.mobile AS CHAR) AS phonenumber,
    a.job_number,
    a.birthday,
    a.age,
    a.work_date,
    a.work_location,
    a.native_place,
    a.nation,
    a.home_address,
    a.current_address,
    a.contact,
    a.contact_mobile,
    a.resident_type,
    a.resident_place,
    a.graduate_school,
    a.graduate_day,
    a.political,
    a.marital_status,
    a.idcard,
    a.education,
    a.speciality,
    a.social_account,
    a.medical_account,
    a.provident_account,
    a.bank_account,
    a.bank_info,
    CASE a.sex
        WHEN 1 THEN '0'
        WHEN 2 THEN '1'
        ELSE '2'
        END AS sex,
    a.thumb AS avatar,
    a.file_ids,
    a.desc AS user_desc,
    a.is_hide,
    a.entry_time,
    a.delete_time,
    a.pwd AS password,
    CASE a.status
        WHEN -1 THEN '1'
        WHEN 0 THEN '1'
        WHEN 1 THEN '0'
        WHEN 2 THEN '1'
        ELSE '1'
        END AS status,
    IF(a.delete_time > 0, '2', '0') AS del_flag,
    a.last_login_ip AS login_ip,
    a.login_num,
    a.is_lock,
    FROM_UNIXTIME(a.last_login_time) AS login_date,
    NULL AS pwd_update_date,
    FROM_UNIXTIME(a.create_time) AS create_time,
    FROM_UNIXTIME(a.update_time) AS update_time,
    '' AS remark,
    a.auth_did,
    a.auth_dids,
    a.son_dids,
    a.status AS admin_status
FROM oa20_dev_test.oa_admin a
WHERE NOT EXISTS (
    SELECT 1 FROM oa20_dev_test.sys_user u
    WHERE
       -- 强制统一排序规则，解决报错
        (u.job_number = a.job_number COLLATE utf8mb4_unicode_ci AND u.job_number != '')
       OR
        (u.phonenumber = CAST(a.mobile AS CHAR) COLLATE utf8mb4_unicode_ci AND a.mobile != 0)
);

-- 合并岗位数据：oa_position 同步到 sys_post（已修复字符集排序冲突）
INSERT INTO oa20_dev_test.sys_post (
    post_code,
    post_name,
    post_sort,
    work_price,
    status,
    create_time,
    update_time,
    remark
)
SELECT
    -- 岗位编码：用 id 生成唯一编码（无重复）
    CONCAT('POST_', a.id) AS post_code,
    a.title AS post_name,
    -- 排序：默认 0 或自定
    0 AS post_sort,
    a.work_price,
    -- 状态对齐：oa(-1删除/0禁用/1启用) → sys(0正常/1停用)
    CASE a.status
        WHEN 1 THEN '0'  -- 启用 → 正常
        WHEN 0 THEN '1'  -- 禁用 → 停用
        WHEN -1 THEN '1' -- 删除 → 停用
        ELSE '1'
        END AS status,
    FROM_UNIXTIME(a.create_time) AS create_time,
    FROM_UNIXTIME(a.update_time) AS update_time,
    a.remark
FROM oa20_dev_test.oa_position a
-- 关键：岗位名称已存在则不插入，避免重复
WHERE NOT EXISTS (
    SELECT 1 FROM oa20_dev_test.sys_post p
    WHERE p.post_name = a.title COLLATE utf8mb4_unicode_ci
);

-- 根据用户名匹配，将 oa_admin.did 赋值给 sys_user.dept_id
UPDATE oa20_dev_test.sys_user u
    JOIN oa20_dev_test.oa_admin a
ON u.user_name = a.username COLLATE utf8mb4_unicode_ci  -- 按用户名匹配 + 解决字符集冲突
    SET u.dept_id = a.did  -- 把旧表部门id 赋值给新表dept_id


