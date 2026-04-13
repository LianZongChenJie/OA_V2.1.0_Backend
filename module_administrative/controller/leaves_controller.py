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
from module_administrative.entity.vo.leaves_vo import (
    AddLeavesModel,
    DeleteLeavesModel,
    EditLeavesModel,
    LeavesModel,
    LeavesPageQueryModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_administrative.service.leaves_service import LeavesService
from utils.log_util import logger
from utils.response_util import ResponseUtil

leaves_controller = APIRouterPro(
    prefix='/home/leaves', order_num=10, tags=['个人办公 - 请假管理'], dependencies=[PreAuthDependency()]
)


@leaves_controller.get(
    '/datalist',
    summary='获取请假分页列表接口',
    description='用于获取我的请假分页列表',
    response_model=PageResponseModel[LeavesModel],
    dependencies=[UserInterfaceAuthDependency('oa:leaves:list')],
)
async def get_leaves_list(
        request: Request,
        leaves_page_query: Annotated[LeavesPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    user_id = current_user.user.user_id if current_user.user and current_user.user.user_id else 0
    leaves_page_query_result = await LeavesService.get_leaves_list_services(
        query_db, leaves_page_query, user_id, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=leaves_page_query_result)


@leaves_controller.post(
    '/add',
    summary='新增/编辑请假接口',
    description='用于新增或编辑请假申请',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('oa:leaves:add')],
)
@ValidateFields(validate_model='add_leaves')
@Log(title='请假管理', business_type=BusinessType.INSERT)
async def add_leaves(
        request: Request,
        add_leaves: AddLeavesModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    if not current_user.user or not current_user.user.user_id:
        logger.error('当前用户信息异常')
        return ResponseUtil.error(msg='用户信息异常，请重新登录')
    
    user_id = current_user.user.user_id
    dept_id = current_user.user.dept_id if current_user.user.dept_id else 0
    
    if add_leaves.id and add_leaves.id > 0:
        result = await LeavesService.edit_leaves_services(request, query_db, add_leaves)
    else:
        result = await LeavesService.add_leaves_services(request, query_db, add_leaves, user_id, dept_id)
    
    logger.info(result.message)
    return ResponseUtil.success(msg=result.message)


@leaves_controller.delete(
    '/del/{id}',
    summary='删除请假接口',
    description='用于删除请假申请',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('oa:leaves:delete')],
)
@Log(title='请假管理', business_type=BusinessType.DELETE)
async def delete_leaves(
        request: Request,
        id: Annotated[int, Path(description='需要删除的请假 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_leaves_model = DeleteLeavesModel(id=id)
    delete_leaves_result = await LeavesService.delete_leaves_services(
        request, query_db, delete_leaves_model
    )
    logger.info(delete_leaves_result.message)

    return ResponseUtil.success(msg=delete_leaves_result.message)


@leaves_controller.get(
    '/view/{id}',
    summary='获取请假详情接口',
    description='用于获取指定请假的详细信息',
    response_model=DataResponseModel[LeavesModel],
    dependencies=[UserInterfaceAuthDependency('oa:leaves:query')],
)
async def view_leaves(
        request: Request,
        id: Annotated[int, Path(description='请假 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_leaves_result = await LeavesService.leaves_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的信息成功')

    return ResponseUtil.success(data=detail_leaves_result)