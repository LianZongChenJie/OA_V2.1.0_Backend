from typing import Annotated

from fastapi import Body, Request, Response
from pydantic_validation_decorator import ValidateFields
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import ResponseBaseModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_contract.entity.vo.contract_api_vo import SetStopModel, SetVoidModel
from module_contract.service.contract_api_service import ContractApiService
from utils.log_util import logger
from utils.response_util import ResponseUtil

contract_api_controller = APIRouterPro(
    prefix='/contract/api',
    order_num=32,
    tags=['合同API接口'],
    dependencies=[PreAuthDependency()]
)


@contract_api_controller.post(
    '/setStop',
    summary='设置合同中止接口',
    description='用于设置合同中止或反中止状态',
    response_model=ResponseBaseModel,
)
@Log(title='合同中止管理', business_type=BusinessType.UPDATE)
async def set_contract_stop(
        request: Request,
        set_stop: Annotated[SetStopModel, Body()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    设置合同中止或反中止

    :param request: Request 对象
    :param set_stop: 设置中止参数对象
    :param query_db: 数据库会话
    :param current_user: 当前用户（操作人）
    :return: 操作结果
    """
    user_id = current_user.user.user_id if current_user.user and current_user.user.user_id else 0
    set_stop_result = await ContractApiService.set_contract_stop_services(
        request, query_db, set_stop, user_id
    )
    logger.info(set_stop_result.message)

    return ResponseUtil.success(msg=set_stop_result.message)


@contract_api_controller.post(
    '/setVoid',
    summary='设置合同作废接口',
    description='用于设置合同作废或反作废状态',
    response_model=ResponseBaseModel,
)
@Log(title='合同作废管理', business_type=BusinessType.UPDATE)
async def set_contract_void(
        request: Request,
        set_void: Annotated[SetVoidModel, Body()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    设置合同作废或反作废

    :param request: Request 对象
    :param set_void: 设置作废参数对象
    :param query_db: 数据库会话
    :param current_user: 当前用户（操作人）
    :return: 操作结果
    """
    user_id = current_user.user.user_id if current_user.user and current_user.user.user_id else 0
    set_void_result = await ContractApiService.set_contract_void_services(
        request, query_db, set_void, user_id
    )
    logger.info(set_void_result.message)

    return ResponseUtil.success(msg=set_void_result.message)