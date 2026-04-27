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
from module_project.entity.vo.project_vo import (
    AddProjectModel,
    DeleteProjectModel,
    EditProjectModel,
    ProjectModel,
    ProjectPageQueryModel,
)
from module_project.service.project_service import ProjectService
from utils.log_util import logger
from utils.response_util import ResponseUtil

project_controller = APIRouterPro(
    prefix='/project', order_num=1, tags=['项目管理模块'], dependencies=[PreAuthDependency()]
)


@project_controller.get(
    '/list',
    summary='获取项目分页列表接口',
    description='用于获取项目分页列表',
    dependencies=[UserInterfaceAuthDependency('project:list')],
)
async def get_project_list(
        request: Request,
        project_page_query: Annotated[ProjectPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    # 获取分页数据
    project_page_query_result = await ProjectService.get_project_list_services(
        query_db,
        project_page_query,
        current_user.user.user_id,
        current_user.user.auth_dids or '',
        current_user.user.son_dids or '',
        current_user.user.admin,
        False,  # is_project_admin 需要根据实际权限判断
        is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(dict_content=project_page_query_result)


@project_controller.post(
    '',
    summary='新增项目接口',
    description='用于新增项目',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('project:add')],
)
@ValidateFields(validate_model='add_project')
@Log(title='项目管理', business_type=BusinessType.INSERT)
async def add_project(
        request: Request,
        add_project: AddProjectModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    add_project.admin_id = current_user.user.user_id
    add_project_result = await ProjectService.add_project_services(
        request, query_db, add_project
    )
    logger.info(add_project_result.message)

    return ResponseUtil.success(msg=add_project_result.message)


@project_controller.put(
    '',
    summary='编辑项目接口',
    description='用于编辑项目',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('project:edit')],
)
@ValidateFields(validate_model='edit_project')
@Log(title='项目管理', business_type=BusinessType.UPDATE)
async def edit_project(
        request: Request,
        edit_project: EditProjectModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    edit_project_result = await ProjectService.edit_project_services(
        request, query_db, edit_project
    )
    logger.info(edit_project_result.message)

    return ResponseUtil.success(msg=edit_project_result.message)


@project_controller.put(
    '/status',
    summary='修改项目状态接口',
    description='用于修改项目状态',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('project:edit')],
)
@Log(title='项目管理', business_type=BusinessType.UPDATE)
async def update_project_status(
        request: Request,
        status_data: Annotated[dict, Body(description='包含项目ID和状态的数据')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    修改项目状态
    
    :param request: Request 对象
    :param status_data: 包含 id 和 status 的字典
    :param query_db: 数据库会话
    :param current_user: 当前用户
    :return: 操作结果
    """
    from sqlalchemy import text
    from datetime import datetime
    
    project_id = status_data.get('id')
    status = status_data.get('status')
    
    if not project_id:
        from exceptions.exception import ServiceException
        raise ServiceException(message='项目ID不能为空')
    
    if status is None:
        from exceptions.exception import ServiceException
        raise ServiceException(message='项目状态不能为空')
    
    # 验证状态值的有效性（根据实际业务调整）
    if status not in [1, 2, 3, 4, 5]:
        from exceptions.exception import ServiceException
        raise ServiceException(message='无效的项目状态')
    
    update_time = int(datetime.now().timestamp())
    
    # 使用原生 SQL 更新项目状态
    sql = text("""
        UPDATE oa_project 
        SET status = :status, update_time = :update_time 
        WHERE id = :project_id AND delete_time = 0
    """)
    
    await query_db.execute(sql, {
        'status': status,
        'update_time': update_time,
        'project_id': project_id
    })
    await query_db.commit()
    
    logger.info(f'修改项目 {project_id} 状态为 {status} 成功')
    
    return ResponseUtil.success(msg='修改项目状态成功')


@project_controller.delete(
    '/{id}',
    summary='删除项目接口',
    description='用于删除项目',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('project:remove')],
)
@Log(title='项目管理', business_type=BusinessType.DELETE)
async def delete_project(
        request: Request,
        id: Annotated[int, Path(description='需要删除的项目 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_project = DeleteProjectModel(id=id)
    delete_project_result = await ProjectService.delete_project_services(
        request, query_db, delete_project
    )
    logger.info(delete_project_result.message)

    return ResponseUtil.success(msg=delete_project_result.message)


@project_controller.get(
    '/{id}',
    summary='获取项目详情接口',
    description='用于获取指定项目的详细信息',
    response_model=DataResponseModel[ProjectModel],
    dependencies=[UserInterfaceAuthDependency('project:query')],
)
async def query_project_detail(
        request: Request,
        id: Annotated[int, Path(description='项目 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_project_result = await ProjectService.project_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的信息成功')

    return ResponseUtil.success(data=detail_project_result)
