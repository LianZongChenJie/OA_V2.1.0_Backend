from typing import Annotated

from fastapi import Body, Path, Query, Request, Response
from pydantic_validation_decorator import ValidateFields
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import DataResponseModel, PageResponseModel, ResponseBaseModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_dashboard.entity.vo.schedule_vo import OaScheduleBaseModel, OaSchedulePageQueryModel
from module_dashboard.service.schedule_service import ScheduleService
from module_project.entity.vo.project_task_vo import (
    AddProjectTaskModel,
    DeleteProjectTaskModel,
    EditProjectTaskModel,
    ProjectTaskModel,
    ProjectTaskPageQueryModel,
)
from module_project.service.project_task_service import ProjectTaskService
from utils.log_util import logger
from utils.response_util import ResponseUtil

project_task_controller = APIRouterPro(
    prefix='/project/task', order_num=20, tags=['项目管理 - 任务管理'], dependencies=[PreAuthDependency()]
)


@project_task_controller.get(
    '/list',
    summary='获取项目任务分页列表接口',
    description='用于获取项目任务分页列表',
    dependencies=[UserInterfaceAuthDependency('project:task:list')],
)
async def get_project_task_list(
        request: Request,
        project_task_page_query: Annotated[ProjectTaskPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    获取项目任务列表
    
    :param request: Request 对象
    :param project_task_page_query: 查询参数
    :param query_db: 数据库会话
    :param current_user: 当前用户
    :return: 任务列表
    """
    from sqlalchemy import text
    from datetime import datetime
    from utils.common_util import CamelCaseUtil
    
    # 分页参数
    page_num = project_task_page_query.page_num if project_task_page_query.page_num else 1
    page_size = project_task_page_query.page_size if project_task_page_query.page_size else 10
    offset = (page_num - 1) * page_size
    
    # 当前用户信息
    user_id = current_user.user.user_id
    is_admin = current_user.user.admin
    auth_dids = current_user.user.auth_dids or ''
    son_dids = current_user.user.son_dids or ''
    
    # 构建 WHERE 条件
    conditions = ["t.delete_time = 0"]
    params = {}
    
    # 状态筛选
    if project_task_page_query.status_filter is not None:
        conditions.append("t.status = :status")
        params['status'] = project_task_page_query.status_filter
    
    # 优先级筛选
    if project_task_page_query.priority_filter is not None:
        conditions.append("t.priority = :priority")
        params['priority'] = project_task_page_query.priority_filter
    
    # 工作类型筛选
    if project_task_page_query.work_id_filter is not None:
        conditions.append("t.work_id = :work_id")
        params['work_id'] = project_task_page_query.work_id_filter
    
    # 项目筛选
    if project_task_page_query.project_id_filter is not None:
        conditions.append("t.project_id = :project_id")
        params['project_id'] = project_task_page_query.project_id_filter
    
    # 关键词搜索
    if project_task_page_query.keywords:
        conditions.append("(t.title LIKE :keywords OR t.content LIKE :keywords)")
        params['keywords'] = f"%{project_task_page_query.keywords}%"
    
    # 负责人筛选
    director_uid_list = project_task_page_query.get_director_uid_list()
    if director_uid_list:
        conditions.append("t.director_uid IN :director_uids")
        params['director_uids'] = tuple(director_uid_list)
    
    # 根据 tab 参数设置查询条件
    current_time = int(datetime.now().timestamp())
    seven_days_later = current_time + 7 * 86400
    
    if project_task_page_query.tab == 1:
        # 进行中
        conditions.append("t.status < 3")
    elif project_task_page_query.tab == 2:
        # 即将逾期
        conditions.append("t.status < 3")
        conditions.append("t.end_time BETWEEN :current_time AND :seven_days_later")
        params['current_time'] = current_time
        params['seven_days_later'] = seven_days_later
    elif project_task_page_query.tab == 3:
        # 已逾期
        conditions.append("t.status < 3")
        conditions.append("t.end_time < :current_time")
        params['current_time'] = current_time
    
    # 数据权限过滤（非管理员）
    if not is_admin:
        permission_conditions = [
            "t.admin_id = :user_id",
            "t.director_uid = :user_id",
        ]
        params['user_id'] = user_id
        
        # 部门权限
        if auth_dids or son_dids:
            dept_ids = set()
            if auth_dids:
                dept_ids.update([int(d.strip()) for d in auth_dids.split(',') if d.strip()])
            if son_dids:
                dept_ids.update([int(d.strip()) for d in son_dids.split(',') if d.strip()])
            
            if dept_ids:
                permission_conditions.append("t.did IN :dept_ids")
                params['dept_ids'] = tuple(dept_ids)
        
        # 协助人员
        permission_conditions.append("t.assist_admin_ids LIKE :assist_ids")
        params['assist_ids'] = f"%{user_id}%"
        
        if permission_conditions:
            conditions.append("(" + " OR ".join(permission_conditions) + ")")
    
    where_clause = " AND ".join(conditions)
    
    # 构建完整 SQL 查询
    sql = text(f"""
        SELECT 
            t.id,
            t.title,
            t.pid,
            t.before_task AS beforeTask,
            t.project_id AS projectId,
            t.work_id AS workId,
            t.step_id AS stepId,
            t.plan_hours AS planHours,
            t.end_time AS endTime,
            t.over_time AS overTime,
            t.admin_id AS adminId,
            t.director_uid AS directorUid,
            t.did,
            t.assist_admin_ids AS assistAdminIds,
            t.priority,
            t.status,
            t.done_ratio AS doneRatio,
            t.content,
            t.create_time AS createTime,
            t.update_time AS updateTime,
            t.delete_time AS deleteTime,
            p.name AS projectName,
            u1.nick_name AS adminName,
            u1.user_name AS userName,
            u2.nick_name AS directorName,
            u2.user_name AS directorUserName,
            d.dept_name AS deptName,
            CASE t.priority
                WHEN 1 THEN '低'
                WHEN 2 THEN '中'
                WHEN 3 THEN '高'
                WHEN 4 THEN '紧急'
                ELSE '未知'
            END AS priorityName,
            CASE t.status
                WHEN 1 THEN '待办的'
                WHEN 2 THEN '进行中'
                WHEN 3 THEN '已完成'
                WHEN 4 THEN '已拒绝'
                WHEN 5 THEN '已关闭'
                ELSE '未知'
            END AS statusName,
            wc.title AS workName,
            FROM_UNIXTIME(t.end_time, '%Y-%m-%d') AS endTimeStr,
            FROM_UNIXTIME(t.create_time, '%Y-%m-%d %H:%i:%s') AS createTimeStr,
            FROM_UNIXTIME(t.update_time, '%Y-%m-%d %H:%i:%s') AS updateTimeStr,
            FROM_UNIXTIME(t.over_time, '%Y-%m-%d %H:%i:%s') AS overTimeStr
        FROM oa_project_task t
        LEFT JOIN oa_project p ON t.project_id = p.id
        LEFT JOIN sys_user u1 ON t.admin_id = u1.user_id
        LEFT JOIN sys_user u2 ON t.director_uid = u2.user_id
        LEFT JOIN sys_dept d ON t.did = d.dept_id
        LEFT JOIN oa_work_cate wc ON t.work_id = wc.id
        WHERE {where_clause}
        ORDER BY t.status ASC, t.create_time DESC
        LIMIT :limit OFFSET :offset
    """)
    
    # 执行查询获取总数
    count_sql = text(f"""
        SELECT COUNT(*) as total
        FROM oa_project_task t
        LEFT JOIN oa_project p ON t.project_id = p.id
        LEFT JOIN sys_user u1 ON t.admin_id = u1.user_id
        LEFT JOIN sys_user u2 ON t.director_uid = u2.user_id
        LEFT JOIN sys_dept d ON t.did = d.dept_id
        LEFT JOIN oa_work_cate wc ON t.work_id = wc.id
        WHERE {where_clause}
    """)
    
    # 添加分页参数到 params
    params['limit'] = page_size
    params['offset'] = offset
    
    # 执行总数查询
    count_result = await query_db.execute(count_sql, params)
    total = count_result.scalar()
    
    # 执行分页查询
    result = await query_db.execute(sql, params)
    rows = result.mappings().all()
    
    # 转换为字典列表并处理数据类型
    task_list = []
    for row in rows:
        task_dict = dict(row)
        
        # 处理数值类型
        for key in ['id', 'pid', 'beforeTask', 'projectId', 'workId', 'stepId', 
                    'endTime', 'overTime', 'adminId', 'directorUid', 'did', 
                    'priority', 'status', 'doneRatio', 'createTime', 'updateTime', 'deleteTime']:
            if key in task_dict and task_dict[key] is not None:
                task_dict[key] = int(task_dict[key])
        
        # 处理浮点数
        if 'planHours' in task_dict and task_dict['planHours'] is not None:
            task_dict['planHours'] = float(task_dict['planHours'])
        
        # 处理字符串默认值
        if 'assistAdminIds' not in task_dict or task_dict['assistAdminIds'] is None:
            task_dict['assistAdminIds'] = ""
        
        task_list.append(task_dict)
    
    # 计算是否有下一页
    has_next = page_num * page_size < total
    
    logger.info(f'获取任务列表成功，共 {total} 条记录')
    
    return ResponseUtil.success(rows=task_list, dict_content={'total': total, 'pageNum': page_num, 'pageSize': page_size, 'hasNext': has_next})


@project_task_controller.get(
    '/hour',
    summary='获取任务工时列表接口',
    description='用于获取任务工时记录列表（支持按任务ID、时间范围、关键词等筛选）',
    dependencies=[UserInterfaceAuthDependency('project:task:hour:list')],
)
async def get_project_task_hour_list(
        request: Request,
        schedule_page_query: Annotated[OaSchedulePageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    获取任务工时列表

    对应 PHP 接口：project/task/hour?page=1&limit=20&range_time=&username=&uid=&keywords=

    :param request: Request 对象
    :param schedule_page_query: 查询参数（包含 tid, range_time, keywords, uid 等）
    :param query_db: 数据库会话
    :param current_user: 当前用户
    :return: 工时列表
    """
    from sqlalchemy import text
    from datetime import datetime
    from utils.common_util import CamelCaseUtil

    # 分页参数
    page_num = schedule_page_query.page_num if schedule_page_query.page_num else 1
    page_size = schedule_page_query.page_size if schedule_page_query.page_size else 20
    offset = (page_num - 1) * page_size

    # 构建 WHERE 条件
    conditions = ["s.delete_time = 0"]
    params = {}

    # 任务ID筛选
    if schedule_page_query.tid:
        conditions.append("s.tid = :tid")
        params['tid'] = schedule_page_query.tid

    # 用户ID筛选
    if schedule_page_query.uid:
        conditions.append("s.admin_id = :uid")
        params['uid'] = schedule_page_query.uid

    # 关键词搜索（标题或备注）
    if schedule_page_query.keywords:
        conditions.append("(s.title LIKE :keywords OR s.remark LIKE :keywords)")
        params['keywords'] = f"%{schedule_page_query.keywords}%"

    # 时间范围筛选
    if schedule_page_query.range_time:
        try:
            range_parts = schedule_page_query.range_time.split('至')
            if len(range_parts) == 2:
                start_timestamp = int(datetime.strptime(range_parts[0].strip(), "%Y-%m-%d").timestamp())
                end_timestamp = int(datetime.strptime(range_parts[1].strip(), "%Y-%m-%d").timestamp()) + 86399
                conditions.append("s.start_time BETWEEN :start_time AND :end_time")
                params['start_time'] = start_timestamp
                params['end_time'] = end_timestamp
        except Exception as e:
            logger.warning(f'解析时间范围失败：{str(e)}')

    where_clause = " AND ".join(conditions)

    # 构建完整 SQL 查询（直接在 SQL 中添加 LIMIT 和 OFFSET）
    sql = text(f"""
        SELECT 
            s.id,
            s.title,
            s.cid,
            s.cmid,
            s.ptid,
            s.tid,
            s.admin_id,
            s.did,
            s.start_time,
            s.end_time,
            s.labor_time,
            s.labor_type,
            s.remark,
            s.file_ids,
            s.delete_time,
            s.create_time,
            s.update_time,
            u.nick_name AS admin_name,
            u.user_name,
            d.dept_name,
            wc.title AS work_title,
            p.name AS project_name,
            t.title AS task_title,
            CASE s.labor_type
                WHEN 1 THEN '案头'
                WHEN 2 THEN '外勤'
                ELSE '未知'
            END AS labor_type_name,
            FROM_UNIXTIME(s.start_time, '%Y-%m-%d %H:%i:%s') AS start_time_str,
            FROM_UNIXTIME(s.end_time, '%Y-%m-%d %H:%i:%s') AS end_time_str,
            FROM_UNIXTIME(s.create_time, '%Y-%m-%d %H:%i:%s') AS create_time_str,
            FROM_UNIXTIME(s.update_time, '%Y-%m-%d %H:%i:%s') AS update_time_str
        FROM oa_schedule s
        LEFT JOIN sys_user u ON s.admin_id = u.user_id
        LEFT JOIN sys_dept d ON u.dept_id = d.dept_id
        LEFT JOIN oa_work_cate wc ON s.cid = wc.id
        LEFT JOIN oa_project_task t ON s.tid = t.id
        LEFT JOIN oa_project p ON t.project_id = p.id
        WHERE {where_clause}
        ORDER BY s.create_time DESC
        LIMIT :limit OFFSET :offset
    """)

    # 执行查询获取总数
    count_sql = text(f"""
        SELECT COUNT(*) as total
        FROM oa_schedule s
        LEFT JOIN sys_user u ON s.admin_id = u.user_id
        LEFT JOIN sys_dept d ON u.dept_id = d.dept_id
        LEFT JOIN oa_work_cate wc ON s.cid = wc.id
        LEFT JOIN oa_project_task t ON s.tid = t.id
        LEFT JOIN oa_project p ON t.project_id = p.id
        WHERE {where_clause}
    """)

    # 添加分页参数到 params
    params['limit'] = page_size
    params['offset'] = offset

    # 执行总数查询
    count_result = await query_db.execute(count_sql, params)
    total = count_result.scalar()

    # 执行分页查询
    result = await query_db.execute(sql, params)
    rows = result.mappings().all()

    # 转换为字典列表并处理数据类型
    hour_list = []
    for row in rows:
        hour_dict = dict(row)

        # 处理数值类型
        for key in ['id', 'cid', 'cmid', 'ptid', 'tid', 'admin_id', 'did',
                    'start_time', 'end_time', 'delete_time', 'create_time', 'update_time', 'labor_type']:
            if key in hour_dict and hour_dict[key] is not None:
                hour_dict[key] = int(hour_dict[key])

        # 处理浮点数
        if 'labor_time' in hour_dict and hour_dict['labor_time'] is not None:
            hour_dict['labor_time'] = float(hour_dict['labor_time'])

        # 处理字符串默认值
        if 'file_ids' not in hour_dict or hour_dict['file_ids'] is None:
            hour_dict['file_ids'] = ""
        if 'remark' not in hour_dict or hour_dict['remark'] is None:
            hour_dict['remark'] = ""

        hour_list.append(hour_dict)

    # 转换为驼峰命名
    hour_list = CamelCaseUtil.transform_result(hour_list)

    # 计算是否有下一页
    has_next = page_num * page_size < total

    response_data = {
        'rows': hour_list,
        'total': total,
        'pageNum': page_num,
        'pageSize': page_size,
        'hasNext': has_next
    }

    logger.info(f'获取任务工时列表成功，共 {total} 条记录')

    return ResponseUtil.success(rows=hour_list, dict_content={'total': total, 'pageNum': page_num, 'pageSize': page_size, 'hasNext': has_next})


@project_task_controller.post(
    '',
    summary='新增项目任务接口',
    description='用于新增项目任务',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('project:task:add')],
)
@ValidateFields(validate_model='add_project_task')
@Log(title='项目任务管理', business_type=BusinessType.INSERT)
async def add_project_task(
        request: Request,
        add_project_task: AddProjectTaskModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    add_project_task.admin_id = current_user.user.user_id
    add_project_task_result = await ProjectTaskService.add_project_task_services(
        request, query_db, add_project_task
    )
    logger.info(add_project_task_result.message)

    return ResponseUtil.success(msg=add_project_task_result.message)


@project_task_controller.put(
    '',
    summary='编辑项目任务接口',
    description='用于编辑项目任务',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('project:task:edit')],
)
@ValidateFields(validate_model='edit_project_task')
@Log(title='项目任务管理', business_type=BusinessType.UPDATE)
async def edit_project_task(
        request: Request,
        edit_project_task: EditProjectTaskModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    edit_project_task_result = await ProjectTaskService.edit_project_task_services(
        request, query_db, edit_project_task
    )
    logger.info(edit_project_task_result.message)

    return ResponseUtil.success(msg=edit_project_task_result.message)


@project_task_controller.post(
    '/hours',
    summary='新增任务工时接口',
    description='用于新增任务工时记录',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('project:task:hour:add')],
)
@Log(title='任务工时管理', business_type=BusinessType.INSERT)
async def add_task_hour(
        request: Request,
        hour_data: Annotated[OaScheduleBaseModel, Body()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    新增任务工时
    
    :param request: Request 对象
    :param hour_data: 工时数据（必须包含 tid 任务ID）
    :param query_db: 数据库会话
    :param current_user: 当前用户
    :return: 操作结果
    """
    from sqlalchemy import text
    from datetime import datetime
    from utils.timeformat import int_time
    from exceptions.exception import ServiceException
    
    # 验证必须提供任务ID
    if not hour_data.tid or hour_data.tid <= 0:
        raise ServiceException(message='新增工时必须关联任务ID')
    
    logger.info(f'新增工时 - 开始处理，任务ID: {hour_data.tid}')
    
    # 先物理删除该任务下的所有工时记录
    from sqlalchemy import text as sql_text
    delete_sql = sql_text("DELETE FROM oa_schedule WHERE tid = :tid")
    await query_db.execute(delete_sql, {'tid': hour_data.tid})
    logger.info(f'新增工时 - 已删除任务 {hour_data.tid} 下的所有工时记录')
    
    # 验证时间字段
    if not hour_data.start_time or not hour_data.end_time:
        raise ServiceException(message='开始时间和结束时间不能为空')
    
    logger.info(f'新增工时 - 原始时间: start_time={hour_data.start_time} (type={type(hour_data.start_time).__name__}), end_time={hour_data.end_time} (type={type(hour_data.end_time).__name__})')
    
    # 设置创建人 ID
    if not hour_data.admin_id:
        hour_data.admin_id = current_user.user.user_id
    
    # 确保 id 为 None（新增时不应该有 id）
    hour_data.id = None
    
    # 转换时间格式为 Unix 时间戳（支持时间戳整数或字符串格式）
    def convert_to_timestamp(time_value) -> int:
        """
        将时间值转换为 Unix 时间戳
        支持：整数时间戳、字符串时间戳、日期时间字符串
        """
        if isinstance(time_value, int):
            # 已经是时间戳，直接返回
            return time_value
        elif isinstance(time_value, str):
            # 尝试判断是否为纯数字字符串（时间戳）
            if time_value.isdigit():
                return int(time_value)
            # 否则按日期时间字符串解析
            return int_time(time_value)
        else:
            # 其他类型尝试转换
            try:
                return int(time_value)
            except (ValueError, TypeError):
                return 0
    
    start_time_timestamp = convert_to_timestamp(hour_data.start_time)
    end_time_timestamp = convert_to_timestamp(hour_data.end_time)
    
    logger.info(f'新增工时 - 转换后时间戳: start_time={start_time_timestamp}, end_time={end_time_timestamp}')
    
    # 验证时间转换是否成功
    if start_time_timestamp == 0:
        raise ServiceException(message=f'开始时间格式不正确: {hour_data.start_time}')
    
    if end_time_timestamp == 0:
        raise ServiceException(message=f'结束时间格式不正确: {hour_data.end_time}')
    
    # 验证时间逻辑：结束时间必须大于或等于开始时间
    if start_time_timestamp > end_time_timestamp:
        raise ServiceException(message='结束时间不能早于开始时间')
    
    # 设置转换后的时间戳
    hour_data.start_time = start_time_timestamp
    hour_data.end_time = end_time_timestamp
    
    # 自动计算工时（小时），保留两位小数
    hour_data.labor_time = round((end_time_timestamp - start_time_timestamp) / 3600, 2)
    
    logger.info(f'新增工时 - 自动计算工时: {hour_data.labor_time} 小时')
    
    # 设置默认值
    hour_data.create_time = int(datetime.now().timestamp())
    hour_data.update_time = 0
    if not hour_data.delete_time:
        hour_data.delete_time = 0
    if not hour_data.labor_type:
        hour_data.labor_type = 1  # 默认案头工作
    if not hour_data.cid:
        hour_data.cid = 1  # 默认工作类型
    
    # 使用原生 SQL 插入数据
    sql = text("""
        INSERT INTO oa_schedule 
        (title, cid, cmid, ptid, tid, admin_id, did, start_time, end_time, labor_time, labor_type, remark, file_ids, delete_time, create_time, update_time)
        VALUES 
        (:title, :cid, :cmid, :ptid, :tid, :admin_id, :did, :start_time, :end_time, :labor_time, :labor_type, :remark, :file_ids, :delete_time, :create_time, :update_time)
    """)
    
    params = {
        'title': hour_data.title or '',
        'cid': hour_data.cid,
        'cmid': hour_data.cmid or 0,
        'ptid': hour_data.ptid or 0,
        'tid': hour_data.tid,
        'admin_id': hour_data.admin_id,
        'did': hour_data.did or 0,
        'start_time': hour_data.start_time,
        'end_time': hour_data.end_time,
        'labor_time': hour_data.labor_time,
        'labor_type': hour_data.labor_type,
        'remark': hour_data.remark or '',
        'file_ids': hour_data.file_ids or '',
        'delete_time': hour_data.delete_time,
        'create_time': hour_data.create_time,
        'update_time': hour_data.update_time
    }
    
    await query_db.execute(sql, params)
    await query_db.commit()
    
    logger.info(f'新增任务工时成功，任务ID: {hour_data.tid}, 工时: {hour_data.labor_time}小时')
    
    return ResponseUtil.success(msg='新增工时成功')


@project_task_controller.put(
    '/hour',
    summary='调整任务工时接口',
    description='用于调整（编辑）任务工时记录',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('project:task:hour:edit')],
)
@Log(title='任务工时管理', business_type=BusinessType.UPDATE)
async def adjust_task_hour(
        request: Request,
        update_data: Annotated[dict, Body(description='工时更新数据')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    编辑任务工时（使用原生SQL）
    
    :param request: Request 对象
    :param update_data: 更新数据字典
    :param query_db: 数据库会话
    :param current_user: 当前用户
    :return: 操作结果
    """
    from sqlalchemy import text
    from datetime import datetime
    
    try:
        logger.info(f'收到更新请求: {update_data}')
        
        # 验证必填字段
        if 'id' not in update_data or not update_data['id']:
            return ResponseUtil.error(msg='工时记录ID不能为空')
        
        hour_id = update_data['id']
        
        # 检查记录是否存在
        check_sql = text("SELECT id FROM oa_schedule WHERE id = :id AND delete_time = 0")
        check_result = await query_db.execute(check_sql, {'id': hour_id})
        exists = check_result.scalar()
        logger.info(f'检查记录是否存在: id={hour_id}, exists={exists}')
        
        if not exists:
            return ResponseUtil.error(msg='工时记录不存在')
        
        # 构建更新字段
        update_fields = []
        params = {'id': hour_id, 'update_time': int(datetime.now().timestamp())}
        
        # 需要更新的字段映射（支持驼峰和下划线两种格式 -> 数据库下划线）
        field_mapping = {
            # 驼峰格式
            'title': 'title',
            'cid': 'cid',
            'cmid': 'cmid',
            'ptid': 'ptid',
            'tid': 'tid',
            'adminId': 'admin_id',
            'did': 'did',
            'startTime': 'start_time',
            'endTime': 'end_time',
            'laborTime': 'labor_time',
            'laborType': 'labor_type',
            'remark': 'remark',
            'fileIds': 'file_ids',
            # 下划线格式
            'admin_id': 'admin_id',
            'start_time': 'start_time',
            'end_time': 'end_time',
            'labor_time': 'labor_time',
            'labor_type': 'labor_type',
            'file_ids': 'file_ids',
        }
        
        # 遍历前端传来的字段
        for front_key, db_key in field_mapping.items():
            if front_key in update_data:
                value = update_data[front_key]
                logger.info(f'处理字段: {front_key} -> {db_key}, 值={value}, 类型={type(value)}')
                # 特殊处理：空字符串转为空字符串，None 保持 None
                if value is None:
                    update_fields.append(f"{db_key} = NULL")
                elif isinstance(value, str):
                    update_fields.append(f"{db_key} = :{db_key}")
                    params[db_key] = value
                elif isinstance(value, (int, float)):
                    update_fields.append(f"{db_key} = :{db_key}")
                    params[db_key] = value
                else:
                    update_fields.append(f"{db_key} = :{db_key}")
                    params[db_key] = str(value)
        
        # 添加更新时间
        update_fields.append("update_time = :update_time")
        
        # 构建 SQL
        if update_fields:
            update_sql = f"""
                UPDATE oa_schedule 
                SET {', '.join(update_fields)}
                WHERE id = :id
            """
            
            logger.info(f'执行更新SQL: {update_sql}')
            logger.info(f'参数: {params}')
            
            # 执行更新
            result = await query_db.execute(text(update_sql), params)
            await query_db.commit()
            
            logger.info(f'更新结果: rowcount={result.rowcount}')
            
            if result.rowcount > 0:
                logger.info(f'修改工时 {hour_id} 成功，影响行数: {result.rowcount}')
                return ResponseUtil.success(msg='修改成功')
            else:
                return ResponseUtil.error(msg='修改失败，未影响任何行')
        else:
            return ResponseUtil.error(msg='没有要更新的字段')
            
    except Exception as e:
        await query_db.rollback()
        logger.error(f'修改工时失败: {str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'修改失败：{str(e)}')


@project_task_controller.delete(
    '/{id}',
    summary='删除项目任务接口',
    description='用于删除项目任务',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('project:task:remove')],
)
@Log(title='项目任务管理', business_type=BusinessType.DELETE)
async def delete_project_task(
        request: Request,
        id: Annotated[int, Path(description='需要删除的任务 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_project_task = DeleteProjectTaskModel(id=id)
    delete_project_task_result = await ProjectTaskService.delete_project_task_services(
        request, query_db, delete_project_task
    )
    logger.info(delete_project_task_result.message)

    return ResponseUtil.success(msg=delete_project_task_result.message)


@project_task_controller.delete(
    '/hour/{hour_id}',
    summary='删除任务工时接口',
    description='用于删除指定的工时记录',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('project:task:hour:remove')],
)
@Log(title='任务工时管理', business_type=BusinessType.DELETE)
async def delete_task_hour(
        request: Request,
        hour_id: Annotated[int, Path(description='工时记录 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """
    删除任务工时

    :param request: Request 对象
    :param hour_id: 工时记录 ID
    :param query_db: 数据库会话
    :return: 操作结果
    """
    result = await ScheduleService.del_by_id(query_db, hour_id)
    logger.info(f'删除工时 {hour_id} 成功')

    return ResponseUtil.success(msg=result.message)


@project_task_controller.get(
    '/{id}',
    summary='获取项目任务详情接口',
    description='用于获取指定项目任务的详细信息',
    response_model=DataResponseModel[ProjectTaskModel],
    dependencies=[UserInterfaceAuthDependency('project:task:query')],
)
async def query_project_task_detail(
        request: Request,
        id: Annotated[int, Path(description='任务 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_project_task_result = await ProjectTaskService.project_task_detail_services(query_db, id)

    logger.info(f'获取 id 为{id}的信息成功')

    return ResponseUtil.success(dict_content=detail_project_task_result)


@project_task_controller.get(
    '/{task_id}/hours',
    summary='获取指定任务的工时列表接口',
    description='用于获取指定任务的工时记录列表',
    response_model=PageResponseModel[OaScheduleBaseModel],
    dependencies=[UserInterfaceAuthDependency('project:task:hour:list')],
)
async def get_task_hour_list(
        request: Request,
        task_id: Annotated[int, Path(description='任务 ID')],
        schedule_page_query: Annotated[OaSchedulePageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    获取指定任务的工时列表

    :param request: Request 对象
    :param task_id: 任务 ID
    :param schedule_page_query: 查询参数
    :param query_db: 数据库会话
    :param current_user: 当前用户
    :return: 工时列表
    """
    # 设置 tid 筛选条件
    schedule_page_query.tid = task_id

    # 调用 ScheduleService 获取工时列表
    hour_list_result = await ScheduleService.get_page_list_service(
        query_db,
        schedule_page_query,
        None,  # data_scope_sql 暂时不传
        True
    )
    logger.info(f'获取任务 {task_id} 的工时列表成功')

    return ResponseUtil.success(data=hour_list_result)


@project_task_controller.get(
    '/hour/{hour_id}',
    summary='获取工时详情接口',
    description='用于获取指定工时记录的详细信息',
    response_model=DataResponseModel[OaScheduleBaseModel],
    dependencies=[UserInterfaceAuthDependency('project:task:hour:query')],
)
async def get_task_hour_detail(
        request: Request,
        hour_id: Annotated[int, Path(description='工时记录 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """
    获取工时详情

    :param request: Request 对象
    :param hour_id: 工时记录 ID
    :param query_db: 数据库会话
    :return: 工时详情
    """
    hour_detail = await ScheduleService.get_info_service(query_db, hour_id)
    logger.info(f'获取工时 {hour_id} 详情成功')

    return ResponseUtil.success(data=hour_detail)
