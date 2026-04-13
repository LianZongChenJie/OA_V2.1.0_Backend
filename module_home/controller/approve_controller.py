from typing import Annotated

from fastapi import Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from common.vo import PageResponseModel, ResponseBaseModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_home.entity.vo.approve_vo import ApprovePageQueryModel
from module_home.service.approve_service import ApproveService
from utils.log_util import logger
from utils.response_util import ResponseUtil

approve_controller = APIRouterPro(
    prefix='/home/approve', order_num=1, tags=['个人办公 - 统一审批'], dependencies=[PreAuthDependency()]
)


@approve_controller.get(
    '/mylist',
    summary='获取我申请的审批列表',
    description='用于获取我申请的所有审批记录',
    response_model=PageResponseModel,
    dependencies=[UserInterfaceAuthDependency('home:approve:mylist')],
)
async def get_my_approve_list(
        request: Request,
        query_object: Annotated[ApprovePageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    user_id = current_user.user.user_id if current_user.user and current_user.user.user_id else 0
    result = await ApproveService.get_my_approve_list_services(query_db, query_object, user_id)
    logger.info('获取我申请的审批列表成功')

    return ResponseUtil.success(data=result)


@approve_controller.get(
    '/checklist',
    summary='获取待我审核/我已审核的审批列表',
    description='用于获取待我审核或我已审核的审批记录',
    response_model=PageResponseModel,
    dependencies=[UserInterfaceAuthDependency('home:approve:checklist')],
)
async def get_check_approve_list(
        request: Request,
        query_object: Annotated[ApprovePageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    user_id = current_user.user.user_id if current_user.user and current_user.user.user_id else 0
    result = await ApproveService.get_check_approve_list_services(query_db, query_object, user_id)
    logger.info('获取待我审核/我已审核的审批列表成功')

    return ResponseUtil.success(data=result)


@approve_controller.get(
    '/copylist',
    summary='获取抄送给我的审批列表',
    description='用于获取抄送给我的审批记录',
    response_model=PageResponseModel,
    dependencies=[UserInterfaceAuthDependency('home:approve:copylist')],
)
async def get_copy_approve_list(
        request: Request,
        query_object: Annotated[ApprovePageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    user_id = current_user.user.user_id if current_user.user and current_user.user.user_id else 0
    result = await ApproveService.get_copy_approve_list_services(query_db, query_object, user_id)
    logger.info('获取抄送给我的审批列表成功')

    return ResponseUtil.success(data=result)