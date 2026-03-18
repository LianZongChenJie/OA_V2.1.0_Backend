from typing import Annotated
from fastapi import File, Form, Path, Query, Request, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from utils.camel_converter import ModelConverter
from utils.log_util import logger

from common.aspect.data_scope import DataScopeDependency
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency
from common.router import APIRouterPro
from common.vo import PageResponseModel
from module_basicdata.entity.do.public.flow_module_do import FlowModule
from module_basicdata.entity.vo.public.flow_module_vo import FlowModuleModel, FlowModulePageQueryModel
from module_basicdata.service.public.flow_module_service import FlowModuleService
from utils.response_util import ResponseUtil

flow_module_controller = APIRouterPro(
    prefix='/basicdata/flowModule', order_num=3, tags=['基础数据-公共模块-消息模板'], dependencies=[PreAuthDependency()]
)

@flow_module_controller.get("/list",
                            summary = '获取消息模板分页列表接口',
                            description = '用于获取消息模板分页列表',
                            response_model = PageResponseModel[FlowModuleModel],
                            dependencies = [UserInterfaceAuthDependency('basicdata:flowModule:list')],
                            )
async def list_page(
        flow_module_page_query: Annotated[FlowModulePageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        data_scope_sql: Annotated[ColumnElement, DataScopeDependency(FlowModule)],
) -> Response:
    flow_module_list = await FlowModuleService.get_flow_module_list_services(query_db, flow_module_page_query, data_scope_sql, is_page=True)
    logger.info('获取成功')
    return ResponseUtil.success(model_content=flow_module_list)

@flow_module_controller.get("/detail/{flow_module_id}",
                            summary = '获取消息模板详情接口',
                            description = '用于获取消息模板详情',
                            response_model = FlowModuleModel,
                            dependencies = [UserInterfaceAuthDependency('basicdata:flowModule:detail')],
                            )
async def detail_page(
    request: Request,
    flow_module_id: int,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    flow_module_result = await FlowModuleService.detail_flow_module_service(query_db, flow_module_id)
    if not flow_module_result:
        return ResponseUtil.error(msg="数据不存在")
    logger.info(flow_module_result.to_dict())
    return ResponseUtil.success(data=ModelConverter.to_dict(flow_module_result, by_alias=True))

@flow_module_controller.post("/add",
                            summary = '添加消息模板接口',
                            description = '用于添加消息模板',
                            response_model = FlowModuleModel,
                            dependencies = [UserInterfaceAuthDependency('basicdata:flowModule:add')],
                            )
async def add_flow_module(
    request: Request,
    flow_module_model: FlowModuleModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    flow_module_result = await FlowModuleService.create_flow_module_service(query_db, flow_module_model)
    if not flow_module_result:
        return ResponseUtil.error(msg="添加失败")
    logger.info(flow_module_result.message)
    return ResponseUtil.success(data=flow_module_result.message)

@flow_module_controller.put("/update",
                            summary = '更新消息模板接口',
                            description = '用于更新消息模板',
                            response_model = FlowModuleModel,
                            dependencies = [UserInterfaceAuthDependency('basicdata:flowModule:update')],
                            )
async def update_flow_module(
    request: Request,
    flow_module_model: FlowModuleModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    flow_module_result = await FlowModuleService.update_flow_module_service(query_db, flow_module_model)
    if not flow_module_result:
        return ResponseUtil.error(msg="更新失败")
    logger.info(flow_module_result.message)
    return ResponseUtil.success(data=flow_module_result.message)

@flow_module_controller.delete("/delete/{flow_module_id}",
                            summary = '删除消息模板接口',
                            description = '用于删除消息模板',
                            response_model = FlowModuleModel,
                            dependencies = [UserInterfaceAuthDependency('basicdata:flowModule:delete')],
                            )
async def delete_flow_module(
    request: Request,
    flow_module_id: int,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    flow_module_result = await FlowModuleService.delete_flow_module_service(query_db, flow_module_id)
    if not flow_module_result:
        return ResponseUtil.error(msg="删除失败")
    logger.info(flow_module_result.message)
    return ResponseUtil.success(data=flow_module_result.message)

@flow_module_controller.put("/changeStatus",
                            summary = '改变消息模板状态接口',
                            description = '用于改变消息模板状态',
                            response_model = FlowModuleModel,
                            dependencies = [UserInterfaceAuthDependency('basicdata:flowModule:changeStatus')],
                            )
async def change_status_flow_module(
    request: Request,
    flow_module_model: FlowModuleModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    flow_module_result = await FlowModuleService.change_status_flow_module_service(query_db, flow_module_model)
    if not flow_module_result:
        return ResponseUtil.error(msg="状态变更失败")
    logger.info(flow_module_result.message)
    return ResponseUtil.success(data=flow_module_result.message)