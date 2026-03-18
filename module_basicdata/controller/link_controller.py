from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from common.aspect.data_scope import DataScopeDependency
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency
from common.router import APIRouterPro
from common.vo import PageResponseModel
from module_basicdata.entity.do.public.enterprise_do import OaEnterprise
from module_basicdata.entity.do.public.lnks_do import OaLinks
from module_basicdata.entity.vo.public.enterprise_vo import OaEnterpriseBaseModel, OaEnterprisePageModel
from fastapi import File, Form, Path, Query, Request, Response, UploadFile
from typing import Annotated

from module_basicdata.entity.vo.public.links_vo import OaLinksBaseModel, OaLinksPageQueryModel
from module_basicdata.service.public.link_service import LinksService
from utils.camel_converter import ModelConverter
from utils.log_util import logger
from utils.response_util import ResponseUtil
link_controller = APIRouterPro(
    prefix='/basicdata/public/links', order_num=3, tags=['基础数据-公共模块-在线工具'], dependencies=[PreAuthDependency()]
)

@link_controller.get(
    "/list",
    summary='获取审批类型分页列表接口',
    description='用于获取审批类型分页列表',
    response_model=PageResponseModel[OaLinksBaseModel],
    dependencies=[UserInterfaceAuthDependency('basicdata:links:list')],
)

async def list_page(
    link_page_query: Annotated[OaLinksPageQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaLinks)],
) -> Response:
    enterprise_list = await LinksService.get_link_list_service(query_db, link_page_query, data_scope_sql, True)
    return ResponseUtil.success(model_content=enterprise_list)

@link_controller.post(
    "/add",
    summary='新增审批类型接口',
    description='用于新增审批类型',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('basicdata:links:add')],
)
async def add_link(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    links_base_model: OaLinksBaseModel,
) -> Response:
    enterprise_result = await LinksService.add_link_service(query_db, links_base_model)
    logger.info(enterprise_result.message)
    return ResponseUtil.success(data=enterprise_result.message)

@link_controller.delete(
    "/delete/{id}",
    summary='删除审批类型接口',
    description='用于删除审批类型',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('basicdata:links:del')],
)
async def delete_link(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: Annotated[int, Path()],
) -> Response:
    enterprise_result = await LinksService.delete_link_service(query_db, id)
    logger.info(enterprise_result.message)
    return ResponseUtil.success(data=enterprise_result.message)

@link_controller.put(
    "/update",
    summary='修改审批类型接口',
    description='用于修改审批类型',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('basicdata:links:edit')],
)
async def update_link(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    enterprise_base_model: OaLinksBaseModel,
) -> Response:
    enterprise_result = await LinksService.update_link_service(query_db, enterprise_base_model)
    logger.info(enterprise_result.message)
    return ResponseUtil.success(data=enterprise_result.message)

@link_controller.get(
    "/detail/{id}",
    summary='获取审批类型详情接口',
    description='用于获取审批类型详情',
    response_model=OaLinksBaseModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:links:detail')],
)
async def get_link_info(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: Annotated[int, Path()],
) -> Response:
    try:
        link_info = await LinksService.get_link_info_service(query_db, id)
        return ResponseUtil.success(data=ModelConverter.to_dict(link_info, by_alias=True))
    except Exception as e:
        logger.error(e)
        return ResponseUtil.failure("查询失败")
