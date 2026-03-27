from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement
from fastapi import File, Form, Path, Query, Request, Response, UploadFile
from typing import Annotated

from common.vo import PageResponseModel
from utils.camel_converter import ModelConverter
from utils.log_util import logger
from common.aspect.data_scope import DataScopeDependency
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency
from common.router import APIRouterPro
from module_basicdata.entity.do.public.flow_cate_do import OaFlowCate
from module_basicdata.entity.vo.public.flow_cate_vo import FlowCatePageQueryModel, OaFlowCateModel
from module_basicdata.service.public.flow_cate_service import FlowCateService
from utils.response_util import ResponseUtil

flow_cate_controller = APIRouterPro(
    prefix='/basicdata/flowCate', order_num=3, tags=['基础数据-公共模块-审批类型'], dependencies=[PreAuthDependency()]
)

@flow_cate_controller.get(
    "/list",
    summary='获取审批类型分页列表接口',
    description='用于获取审批类型分页列表',
    response_model=PageResponseModel[OaFlowCateModel],
    dependencies=[UserInterfaceAuthDependency('basicdata:flowCate:list')],
)
async def list_page(
    flow_cate_page_query: Annotated[FlowCatePageQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaFlowCate)],
) -> Response:
    flow_cate_list = await FlowCateService.get_flow_cate_list_services(query_db, flow_cate_page_query, data_scope_sql, is_page=True)
    logger.info('获取成功')
    return ResponseUtil.success(model_content=flow_cate_list)


@flow_cate_controller.post(
    "/add",
    summary='新增审批类型接口',
    description='用于新增审批类型',
    response_model=OaFlowCateModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:flowCate:add')],
)
async def add_flow_cate(
    request: Request,
    oa_flow_cate_model: OaFlowCateModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    flow_cate_result = await FlowCateService.add_flow_cate_service(query_db, oa_flow_cate_model)
    logger.info(flow_cate_result.message)
    return ResponseUtil.success(data=flow_cate_result.message)


@flow_cate_controller.put(
    "/update",
    summary='修改审批类型接口',
    description='用于修改审批类型',
    response_model=OaFlowCateModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:flowCate:edit')],
)
async def update_flow_cate(
    request: Request,
    oa_flow_cate_model: OaFlowCateModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    flow_cate_result = await FlowCateService.update_flow_cate_service(query_db, oa_flow_cate_model)
    logger.info(flow_cate_result.message)
    return ResponseUtil.success(data=flow_cate_result.message)

@flow_cate_controller.delete(
    "/delete/{flow_id}",
    summary='删除审批类型接口',
    description='用于删除审批类型',
    response_model=OaFlowCateModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:flowCate:del')],
)
async def delete_flow_cate(
    request: Request,
    flow_id: int,
    query_db: Annotated[AsyncSession, DBSessionDependency()]
) -> Response:
    flow_cate_result = await FlowCateService.delete_flow_cate_service(query_db, flow_id)
    if flow_cate_result:
        return ResponseUtil.success(data=flow_cate_result.message)
    else:
        return ResponseUtil.error(msg="未找到该数据")


@flow_cate_controller.get(
    "/detail/{flow_id}",
    summary='获取审批类型详情接口',
    description='用于获取审批类型详情',
    response_model=OaFlowCateModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:flowCate:view')],
)
async def get_flow_cate(
    request: Request,
    flow_id: int,
    query_db: Annotated[AsyncSession, DBSessionDependency()]
):
    flow_cate_result = await FlowCateService.get_flow_cate_info_service(query_db, flow_id)
    if flow_cate_result:
        logger.info(flow_cate_result.to_dict())
        return ResponseUtil.success(data=ModelConverter.to_dict(flow_cate_result, by_alias=True))
    else:
        return ResponseUtil.error(msg="未找到该数据")

@flow_cate_controller.put(
    "/changeStatus",
    summary='改变审批类型状态接口',
    description='用于改变审批类型状态',
    response_model=OaFlowCateModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:flowCate:changeStatus')],
)
async def change_status(
    request: Request,
    oa_flow_cate_model: OaFlowCateModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()]
):
    flow_cate_result = await FlowCateService.change_status_flow_cate_service(query_db, oa_flow_cate_model)
    if flow_cate_result:
        return ResponseUtil.success(data=flow_cate_result.message)
    else:
        return ResponseUtil.error(msg="状态变更失败")

@flow_cate_controller.get(
    "/getByName",
    summary='根据名称获取审批类型信息接口',
    description='用于根据名称获取审批类型信息',
    response_model=OaFlowCateModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:flowCate:view')],
)
async def get_flow_cate_by_name(
    request: Request,
    name: str,
    query_db: Annotated[AsyncSession, DBSessionDependency()]
)-> Response:
    flow_cate_result = await FlowCateService.get_flow_cate_info_by_name_service(query_db, name)
    if flow_cate_result:
        logger.info(flow_cate_result.to_dict())
        return ResponseUtil.success(data=ModelConverter.to_dict(flow_cate_result, by_alias=True))
    else:
        return ResponseUtil.error(msg="未找到该数据")