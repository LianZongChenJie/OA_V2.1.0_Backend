from sqlalchemy.ext.asyncio import AsyncSession
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency, CurrentUserDependency
from common.router import APIRouterPro
from common.vo import PageResponseModel
from module_basicdata.entity.vo.public.flow_vo import OaFlowBaseModel, OaFlowCheckBaseModel
from typing import Annotated
from fastapi import File, Form, Path, Query, Request, Response, UploadFile,Body

from module_basicdata.service.public.check_service import CheckService
from utils.camel_converter import ModelConverter
from utils.response_util import ResponseUtil
from module_admin.entity.vo.user_vo import CurrentUserModel


flow_check_controller = APIRouterPro(
    prefix='/basicdata/check', order_num=4, tags=['基础数据-公共模块-审批流程相关'], dependencies=[PreAuthDependency()]
)


@flow_check_controller.put(
    "",
    summary='审核',
    description='用于获取审批流程分页列表',
    response_model=PageResponseModel[OaFlowBaseModel],
    dependencies=[UserInterfaceAuthDependency('basicdata:flow:check')],
)
async def flow_check(
    flow_query: Annotated[OaFlowCheckBaseModel, Body()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()]
) -> Response:
    user_id = current_user.user.user_id
    result = await CheckService.flow_check(query_db, flow_query, user_id)
    return ResponseUtil.success(msg=result.message)

@flow_check_controller.get(
    "/getFlow",
    summary='通过审核表名称获取审核流程',
    description='通过审核表名称获取审核流程',
    response_model=OaFlowBaseModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:flow:query')],
)
async def get_flow(
    check_name: str,
    query_db: Annotated[AsyncSession, DBSessionDependency()]
    ) -> Response:
    flow_result = await CheckService.get_flow(query_db, check_name)
    return ResponseUtil.success(data=ModelConverter.convert_to_camel_case(flow_result.to_dict()))


@flow_check_controller.get(
    "/getFlowCheckUser",
    summary='获取审核步骤人员',
    description='获取审核步骤人员',
    response_model=OaFlowBaseModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:flow:query')],
)
async def get_flow_check_user(
    flow_id: int,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()]
    ) -> Response:
    user_id = current_user.user.user_id
    flow_result = await CheckService.get_flow_user(query_db, flow_id, user_id)
    return ResponseUtil.success(data=flow_result)

@flow_check_controller.post(
    "/submitCheck",
    summary='提交审核',
    description='提交审核',
    response_model=OaFlowBaseModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:flow:submitCheck')],
)
async def submit(
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_model: Annotated[OaFlowCheckBaseModel, Body()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()]
    ) -> Response:
    user_id = current_user.user.user_id
    result = await CheckService.submit_check(query_db, query_model, user_id)
    return ResponseUtil.success(msg=result.message)

@flow_check_controller.get(
    "/getFlowNodes",
    summary='获取审核节点',
    description='获取审核节点',
    response_model=OaFlowBaseModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:flow:query')],
)
async def get_flow_nodes(
    check_table: str,
    action_id: int,
    flow_id: int,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()]
)->Response:
    user_id = current_user.user.user_id
    dept_id = current_user.user.dept_id
    result = await CheckService.get_flow_nodes(query_db, check_table, action_id, flow_id, dept_id, user_id)
    return ResponseUtil.success(data=result)

@flow_check_controller.put(
    "/skipCheck",
    summary='跳过审核步骤',
    description='跳过审核步骤',
    response_model=PageResponseModel[OaFlowBaseModel],
    dependencies=[UserInterfaceAuthDependency('basicdata:flow:check')],
)
async def skip_check(
    flow_query: Annotated[OaFlowCheckBaseModel, Body()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()]
) -> Response:
    user_id = current_user.user.user_id
    result = await CheckService.skip_check(query_db, flow_query, user_id)
    return ResponseUtil.success(msg=result.message)

