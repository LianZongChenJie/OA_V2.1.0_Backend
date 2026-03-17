from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from common.aspect.data_scope import DataScopeDependency
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency
from common.router import APIRouterPro
from common.vo import PageResponseModel
from module_basicdata.entity.do.public.enterprise_do import OaEnterprise
from module_basicdata.entity.vo.public.enterprise_vo import OaEnterpriseBaseModel, OaEnterprisePageModel
from fastapi import File, Form, Path, Query, Request, Response, UploadFile
from typing import Annotated
from utils.log_util import logger

from module_basicdata.service.public.enterprise_service import EnterpriseService
from utils.response_util import ResponseUtil

flow_cate_controller = APIRouterPro(
    prefix='/basicdata/public/enterprise', order_num=3, tags=['基础数据-公共模块-审批类型'], dependencies=[PreAuthDependency()]
)

@flow_cate_controller.get(
    "/list",
    summary='获取审批类型分页列表接口',
    description='用于获取审批类型分页列表',
    response_model=PageResponseModel[OaEnterpriseBaseModel],
    dependencies=[UserInterfaceAuthDependency('basicdata:flowCate:list')],
)

async def list_page(
    flow_cate_page_query: Annotated[OaEnterprisePageModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaEnterprise)],
) -> Response:
    enterprise_list = await EnterpriseService.get_enterprise_list_service(query_db, flow_cate_page_query, data_scope_sql, True)
    return ResponseUtil.success(model_content=enterprise_list)

@flow_cate_controller.get(
    "/add",
    summary='新增审批类型接口',
    description='用于新增审批类型',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('basicdata:flowCate:add')],
)
async def add_enterprise(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    enterprise_base_model: Annotated[OaEnterpriseBaseModel, Form()],
) -> Response:
    enterprise_result = await EnterpriseService.add_enterprise_service(query_db, enterprise_base_model)
    logger.info(enterprise_result.message)
    return ResponseUtil.success(data=enterprise_result.message)

@flow_cate_controller.get(
    "/delete/{id}",
    summary='删除审批类型接口',
    description='用于删除审批类型',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('basicdata:flowCate:del')],
)
async def delete_enterprise(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: Annotated[int, Path()],
) -> Response:
    enterprise_result = await EnterpriseService.delete_enterprise_service(query_db, id)
    logger.info(enterprise_result.message)
    return ResponseUtil.success(data=enterprise_result.message)

@flow_cate_controller.get(
    "/update",
    summary='修改审批类型接口',
    description='用于修改审批类型',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('basicdata:flowCate:edit')],
)
async def update_enterprise(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    enterprise_base_model: Annotated[OaEnterpriseBaseModel, Form()],
) -> Response:
    enterprise_result = await EnterpriseService.update_enterprise_service(query_db, enterprise_base_model)
    logger.info(enterprise_result.message)
    return ResponseUtil.success(data=enterprise_result.message)


@flow_cate_controller.get(
    "/changeStatus",
    summary='启用禁用审批类型接口',
    description='用于启用禁用审批类型',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('basicdata:flowCate:edit')]
)
async def change_status_enterprise(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    enterprise_base_model: Annotated[OaEnterpriseBaseModel, Form()],
) -> Response:
    enterprise_result = await EnterpriseService.change_status_enterprise_service(query_db, enterprise_base_model)
    logger.info(enterprise_result.message)
    return ResponseUtil.success(data=enterprise_result.message)
