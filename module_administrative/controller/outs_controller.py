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
from module_administrative.entity.vo.outs_vo import (
    AddOutsModel,
    DeleteOutsModel,
    EditOutsModel,
    OutsModel,
    OutsPageQueryModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_administrative.service.outs_service import OutsService
from utils.log_util import logger
from utils.response_util import ResponseUtil

outs_controller = APIRouterPro(
    prefix='/home/outs', order_num=12, tags=['个人办公 - 外出管理'], dependencies=[PreAuthDependency()]
)


@outs_controller.get(
    '/datalist',
    summary='获取外出分页列表接口',
    description='用于获取我的外出分页列表',
    response_model=PageResponseModel[OutsModel],
    dependencies=[UserInterfaceAuthDependency('oa:outs:list')],
)
async def get_outs_list(
        request: Request,
        outs_page_query: Annotated[OutsPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    user_id = current_user.user.user_id if current_user.user and current_user.user.user_id else 0
    outs_page_query_result = await OutsService.get_outs_list_services(
        query_db, outs_page_query, user_id, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=outs_page_query_result)


@outs_controller.post(
    '/add',
    summary='新增/编辑外出接口',
    description='用于新增或编辑外出申请',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('oa:outs:add')],
)
@ValidateFields(validate_model='add_outs')
@Log(title='外出管理', business_type=BusinessType.INSERT)
async def add_outs(
        request: Request,
        add_outs: AddOutsModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    if not current_user.user or not current_user.user.user_id:
        logger.error('当前用户信息异常')
        return ResponseUtil.error(msg='用户信息异常，请重新登录')

    user_id = current_user.user.user_id
    dept_id = current_user.user.dept_id if current_user.user.dept_id else 0

    if add_outs.id and add_outs.id > 0:
        result = await OutsService.edit_outs_services(request, query_db, add_outs)
    else:
        result = await OutsService.add_outs_services(request, query_db, add_outs, user_id, dept_id)

    logger.info(result.message)
    return ResponseUtil.success(msg=result.message)


@outs_controller.delete(
    '/del/{id}',
    summary='删除外出接口',
    description='用于删除外出申请',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('oa:outs:delete')],
)
@Log(title='外出管理', business_type=BusinessType.DELETE)
async def delete_outs(
        request: Request,
        id: Annotated[int, Path(description='需要删除的外出 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_outs_model = DeleteOutsModel(id=id)
    delete_outs_result = await OutsService.delete_outs_services(
        request, query_db, delete_outs_model
    )
    logger.info(delete_outs_result.message)

    return ResponseUtil.success(msg=delete_outs_result.message)


@outs_controller.get(
    '/view/{id}',
    summary='获取外出详情接口',
    description='用于获取指定外出的详细信息',
    response_model=DataResponseModel[OutsModel],
    dependencies=[UserInterfaceAuthDependency('oa:outs:query')],
)
async def view_outs(
        request: Request,
        id: Annotated[int, Path(description='外出 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_outs_result = await OutsService.outs_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的信息成功')

    return ResponseUtil.success(data=detail_outs_result)