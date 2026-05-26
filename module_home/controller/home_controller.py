from typing import Annotated

from fastapi import Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from common.vo import PageResponseModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_administrative.entity.vo.leaves_vo import LeavesModel, LeavesPageQueryModel
from module_administrative.entity.vo.trips_vo import TripsModel, TripsPageQueryModel
from module_administrative.entity.vo.outs_vo import OutsModel, OutsPageQueryModel
from module_administrative.entity.vo.overtimes_vo import OvertimesModel, OvertimesPageQueryModel
from module_administrative.service.leaves_service import LeavesService
from module_administrative.service.trips_service import TripsService
from module_administrative.service.outs_service import OutsService
from module_administrative.service.overtimes_service import OvertimesService
from utils.log_util import logger
from utils.response_util import ResponseUtil

home_controller = APIRouterPro(
    prefix='/home', order_num=2, tags=['个人办公-首页'], dependencies=[PreAuthDependency()]
)


@home_controller.get(
    '/leaves/list',
    summary='获取请假分页列表接口',
    description='用于获取我的请假申请分页列表',
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
    result = await LeavesService.get_leaves_list_services(query_db, leaves_page_query, user_id, is_page=True)
    logger.info('获取请假分页列表成功')

    return ResponseUtil.success(model_content=result)


@home_controller.get(
    '/trips/list',
    summary='获取出差分页列表接口',
    description='用于获取我的出差申请分页列表',
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
    result = await TripsService.get_trips_list_services(query_db, trips_page_query, user_id, is_page=True)
    logger.info('获取出差分页列表成功')

    return ResponseUtil.success(model_content=result)


@home_controller.get(
    '/outs/list',
    summary='获取外出分页列表接口',
    description='用于获取我的外出申请分页列表',
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
    result = await OutsService.get_outs_list_services(query_db, outs_page_query, user_id, is_page=True)
    logger.info('获取外出分页列表成功')

    return ResponseUtil.success(model_content=result)


@home_controller.get(
    '/overtimes/list',
    summary='获取加班分页列表接口',
    description='用于获取我的加班申请分页列表',
    response_model=PageResponseModel[OvertimesModel],
    dependencies=[UserInterfaceAuthDependency('system:overtimes:list')],
)
async def get_overtimes_list(
        request: Request,
        overtimes_page_query: Annotated[OvertimesPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    user_id = current_user.user.user_id if current_user.user and current_user.user.user_id else 0
    result = await OvertimesService.get_overtimes_list_services(query_db, overtimes_page_query, user_id, is_page=True)
    logger.info('获取加班分页列表成功')

    return ResponseUtil.success(model_content=result)