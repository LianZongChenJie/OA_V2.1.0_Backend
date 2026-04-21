from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from common.aspect.data_scope import DataScopeDependency
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency, CurrentUserDependency
from common.router import APIRouterPro
from common.vo import PageResponseModel
from module_basicdata.entity.do.public.flow_do import OaFlow
from module_basicdata.entity.vo.public.flow_vo import OaFlowBaseModel, OaFlowPageQueryModel, OaFlowCheckBaseModel
from typing import Annotated
from fastapi import File, Form, Path, Query, Request, Response, UploadFile,Body

from utils.camel_converter import ModelConverter
from utils.response_util import ResponseUtil
from utils.log_util import logger
from module_admin.entity.vo.user_vo import CurrentUserModel


from module_basicdata.service.public.flow_service import FlowService

flow_controller = APIRouterPro(
    prefix='/basicdata/flow', order_num=4, tags=['基础数据-公共模块-审批流程'], dependencies=[PreAuthDependency()]
)


@flow_controller.get(
    "/list",
    summary='获取审批流程分页列表接口',
    description='用于获取审批流程分页列表',
    response_model=PageResponseModel[OaFlowBaseModel],
    dependencies=[UserInterfaceAuthDependency('basicdata:flow:list')],
)
async def list_page(
    flow_cate_page_query: Annotated[OaFlowPageQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaFlow)], ) -> Response:
    flow_list = await FlowService.get_flow_list(query_db, flow_cate_page_query, data_scope_sql, is_page=True)
    logger.info('获取成功')
    return ResponseUtil.success(data=ModelConverter.convert_to_camel_case(flow_list))

@flow_controller.post(
    "/add",
    summary='新增审批流程接口',
    description='用于新增审批流程',
    response_model=OaFlowBaseModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:flow:add')],
)
async def add(
    request: Request,
    oa_flow_base_model: OaFlowBaseModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],

    current_user: Annotated[CurrentUserModel, CurrentUserDependency()]
    ) -> Response:
    oa_flow_base_model.admin_id = current_user.user.user_name
    flow_result = await FlowService.add_flow(query_db, oa_flow_base_model)
    logger.info(flow_result.message)
    return ResponseUtil.success(data=flow_result.message)

@flow_controller.get(
    "/detail/{id}",
    summary='获取审批流程详情接口',
    description='用于获取审批流程详情',
    response_model=OaFlowBaseModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:flow:detail')],
)
async def detail(
    id: Annotated[int, Path()],
    query_db: Annotated[AsyncSession, DBSessionDependency()]
    ) -> Response:
    flow_detail = await FlowService.get_flow_detail(query_db, id)
    logger.info(flow_detail.to_dict())
    return ResponseUtil.success(data=ModelConverter.to_dict(flow_detail, by_alias=True))

@flow_controller.put(
    "/update",
    summary='编辑审批流程接口',
    description='用于编辑审批流程',
    response_model=OaFlowBaseModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:flow:edit')],
)
async def update(
    request: Request,
    oa_flow_base_model: OaFlowBaseModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],

    ) -> Response:
    flow_result = await FlowService.update_flow(query_db, oa_flow_base_model)
    logger.info('更新成功')
    return ResponseUtil.success(data=flow_result.message)

@flow_controller.put(
    "/changeStatus",
    summary='修改审批流程状态接口',
    description='用于修改审批流程状态',
    response_model=bool,
    dependencies=[UserInterfaceAuthDependency('basicdata:flow:edit')],
)
async def change_status(
    request: Request,
    oa_flow_base_model: OaFlowBaseModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],

) -> Response:
    await FlowService.change_status_flow(query_db, oa_flow_base_model)
    logger.info('更新成功')
    return ResponseUtil.success(data=True)


