from fastapi import File, Form, Path, Query, Request, Response, UploadFile
from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from common.aspect.data_scope import DataScopeDependency
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency
from common.router import APIRouterPro
from module_personnel.entity.do.black_list_do import OaBlacklist
from module_personnel.entity.vo.black_list_vo import OaBlacklistBaseModel, OaBlacklistPageQueryModel
from module_personnel.service.black_list_service import BlackListService

black_list_controller = APIRouterPro(
    prefix='/personnel/blackList', order_num=3, tags=['人事管理-人员黑名单'], dependencies=[PreAuthDependency()]
)

@black_list_controller.get(
    "/list",
    summary='获取人员黑名单列表',
    description='用于获取人员黑名单列表',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:blackList:query')],
)
async def get_page_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: OaBlacklistPageQueryModel,
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaBlacklist)],
) -> Response:
    return await BlackListService.get_page_list_service(query_db,query_object,data_scope_sql,True)

@black_list_controller.get(
    "/add",
    summary='新增人员黑名单',
    description='用于新增人员黑名单',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:blackList:add')],
)
async def add_change(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: OaBlacklistBaseModel,
) -> Response:
    return await BlackListService.add_service(query_db, query_object)

@black_list_controller.post(
    "/update",
    summary='更新人员黑名单',
    description='用于更新人员黑名单',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:blackList:update')],
)
async def update_profile(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: OaBlacklistBaseModel,
)->Response:
    return await BlackListService().update_service(query_db, model)

@black_list_controller.get(
    "/detail/{id}",
    summary='获取人员黑名单详情',
    description='用于获取人员黑名单详情',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:blackList:query')],
)
async def get_detail(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    return await BlackListService.get_info_service(query_db, id)

@black_list_controller.get(
    "/delete/{id}",
    summary='删除人员黑名单',
    description='用于删除人员黑名单',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:blackList:delete')],
)
async def delete_change(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    return await BlackListService.del_by_id(query_db, id)
