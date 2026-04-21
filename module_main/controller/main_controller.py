from fastapi import File, Form, Path, Query, Request, Response, UploadFile,Body
from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency, CurrentUserDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from module_main.service.main_service import MainService
from utils.response_util import ResponseUtil
from module_admin.entity.vo.user_vo import (
    CurrentUserModel
)

from common.annotation.log_annotation import Log

main_controller = APIRouterPro(
    prefix='/main', order_num=3, tags=['主页'], dependencies=[PreAuthDependency()]
)

@main_controller.get(
    "/count",
    summary='获取首页我的报销开票等数据统计信息',
    description='用于获取首页我的报销开票等数据统计信息',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:mian:query')],
)
@Log(title='主页', business_type=BusinessType.OTHER)
async def get_count(
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    首页我的报销开票等数据统计信息
    :param request:
    :param query_db:
    :param id:
    :param current_user:
    :return:
    """
    user_id = current_user.user.user_id
    result =  await MainService.get_count(query_db, user_id)
    return ResponseUtil.success(data=result)

@main_controller.get(
    "/awaitReview",
    summary='获取首页我的报销开票等数据统计信息',
    description='用于获取首页我的报销开票等数据统计信息',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:mian:query')],
)
@Log(title='主页', business_type=BusinessType.OTHER)
async def get_await_review(
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    首页我的待审核数据
    :param request:
    :param query_db:
    :param id:
    :param current_user:
    :return:
    """
    user_id = current_user.user.user_id
    result =  await MainService.get_await_review(query_db, user_id)
    return ResponseUtil.success(data=result)

@main_controller.get(
    "/getViewLog",
    summary='获取最近30天用户操作日志数据',
    description='获取最近30天用户操作日志数据',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:mian:query')],
)
# @Log(title='主页', business_type=BusinessType.OTHER)
async def get_view_log(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
)->Response:
    result =  await MainService.get_view_log(query_db)
    return ResponseUtil.success(data=result)

@main_controller.get(
    "/getLastData",
    summary='获取用户昨天和今天操作数据统计',
    description='获取用户昨天和今天操作数据统计',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:mian:query')],
)
async def get_last_data(
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
)->Response:
    user_name = current_user.user.user_name
    result =  await MainService.get_last_data(query_db, user_name)
    return ResponseUtil.success(data=result)
