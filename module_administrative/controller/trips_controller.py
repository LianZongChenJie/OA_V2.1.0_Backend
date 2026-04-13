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
from module_administrative.entity.vo.trips_vo import (
    AddTripsModel,
    DeleteTripsModel,
    EditTripsModel,
    TripsModel,
    TripsPageQueryModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_administrative.service.trips_service import TripsService
from utils.log_util import logger
from utils.response_util import ResponseUtil

trips_controller = APIRouterPro(
    prefix='/home/trips', order_num=11, tags=['个人办公 - 出差管理'], dependencies=[PreAuthDependency()]
)


@trips_controller.get(
    '/datalist',
    summary='获取出差分页列表接口',
    description='用于获取我的出差分页列表',
    response_model=PageResponseModel[TripsModel],
    dependencies=[UserInterfaceAuthDependency('oa:trips:list')],
)
async def get_trips_list(
        request: Request,
        trips_page_query: Annotated[TripsPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    user_id = current_user.user.user_id if current_user.user and current_user.user.user_id else 0
    trips_page_query_result = await TripsService.get_trips_list_services(
        query_db, trips_page_query, user_id, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=trips_page_query_result)


@trips_controller.post(
    '/add',
    summary='新增/编辑出差接口',
    description='用于新增或编辑出差申请',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('oa:trips:add')],
)
@ValidateFields(validate_model='add_trips')
@Log(title='出差管理', business_type=BusinessType.INSERT)
async def add_trips(
        request: Request,
        add_trips: AddTripsModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    if not current_user.user or not current_user.user.user_id:
        logger.error('当前用户信息异常')
        return ResponseUtil.error(msg='用户信息异常，请重新登录')

    user_id = current_user.user.user_id
    dept_id = current_user.user.dept_id if current_user.user.dept_id else 0

    if add_trips.id and add_trips.id > 0:
        result = await TripsService.edit_trips_services(request, query_db, add_trips)
    else:
        result = await TripsService.add_trips_services(request, query_db, add_trips, user_id, dept_id)

    logger.info(result.message)
    return ResponseUtil.success(msg=result.message)


@trips_controller.delete(
    '/del/{id}',
    summary='删除出差接口',
    description='用于删除出差申请',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('oa:trips:delete')],
)
@Log(title='出差管理', business_type=BusinessType.DELETE)
async def delete_trips(
        request: Request,
        id: Annotated[int, Path(description='需要删除的出差 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_trips_model = DeleteTripsModel(id=id)
    delete_trips_result = await TripsService.delete_trips_services(
        request, query_db, delete_trips_model
    )
    logger.info(delete_trips_result.message)

    return ResponseUtil.success(msg=delete_trips_result.message)


@trips_controller.get(
    '/view/{id}',
    summary='获取出差详情接口',
    description='用于获取指定出差的详细信息',
    response_model=DataResponseModel[TripsModel],
    dependencies=[UserInterfaceAuthDependency('oa:trips:query')],
)
async def view_trips(
        request: Request,
        id: Annotated[int, Path(description='出差 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_trips_result = await TripsService.trips_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的信息成功')

    return ResponseUtil.success(data=detail_trips_result)