from typing import Annotated

from fastapi import Path, Query, Request, Response
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
    prefix='/project/task', order_num=2, tags=['项目任务管理模块'], dependencies=[PreAuthDependency()]
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
