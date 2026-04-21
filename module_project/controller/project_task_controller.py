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
    response_model=PageResponseModel[ProjectTaskModel],
    dependencies=[UserInterfaceAuthDependency('project:task:list')],
)
async def get_project_task_list(
        request: Request,
        project_task_page_query: Annotated[ProjectTaskPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    # 获取分页数据
    project_task_page_query_result = await ProjectTaskService.get_project_task_list_services(
        query_db,
        project_task_page_query,
        current_user.user.user_id,
        current_user.user.auth_dids or '',
        current_user.user.son_dids or '',
        current_user.user.admin,
        False,  # is_project_admin 需要根据实际权限判断
        is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=project_task_page_query_result)


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
    # 调用 ScheduleService 获取工时列表
    hour_list_result = await ScheduleService.get_page_list_service(
        query_db,
        schedule_page_query,
        None,  # data_scope_sql 暂时不传
        True
    )
    logger.info('获取任务工时列表成功')

    return ResponseUtil.success(data=hour_list_result)


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


@project_task_controller.put(
    '/hour',
    summary='调整任务工时接口',
    description='用于调整（新增或编辑）任务工时记录',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('project:task:hour:edit')],
)
@Log(title='任务工时管理', business_type=BusinessType.UPDATE)
async def adjust_task_hour(
        request: Request,
        hour_data: Annotated[OaScheduleBaseModel, Body()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    调整任务工时（新增或编辑）
    
    :param request: Request 对象
    :param hour_data: 工时数据
    :param query_db: 数据库会话
    :param current_user: 当前用户
    :return: 操作结果
    """
    # 设置创建人 ID
    if not hour_data.admin_id:
        hour_data.admin_id = current_user.user.user_id
    
    if hour_data.id is not None and hour_data.id > 0:
        # 编辑工时
        result = await ScheduleService.update_service(query_db, hour_data)
        logger.info(f'编辑工时 {hour_data.id} 成功')
    else:
        # 新增工时（id 为 None 或 0）
        hour_data.id = None
        result = await ScheduleService.add_service(query_db, hour_data)
        logger.info('新增工时成功')

    return ResponseUtil.success(msg=result.message)


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

    return ResponseUtil.success(data=detail_project_task_result)


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
