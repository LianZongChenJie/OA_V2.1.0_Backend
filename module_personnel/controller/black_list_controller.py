from fastapi import File, Form, Path, Query, Request, Response, UploadFile,Body
from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from common.aspect.data_scope import DataScopeDependency
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency, CurrentUserDependency
from common.router import APIRouterPro
from module_personnel.entity.do.black_list_do import OaBlacklist
from module_personnel.entity.vo.black_list_vo import OaBlacklistBaseModel, OaBlacklistPageQueryModel
from module_personnel.service.black_list_service import BlackListService

from utils.camel_converter import ModelConverter
from utils.response_util import ResponseUtil
from module_admin.entity.vo.user_vo import (
    CurrentUserModel
)


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
    query_object: Annotated[OaBlacklistPageQueryModel, Query()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaBlacklist)],
) -> Response:
    result =  await BlackListService.get_page_list_service(query_db,query_object,data_scope_sql,True)
    return ResponseUtil.success(model_content=result)

@black_list_controller.post(
    "/add",
    summary='新增人员黑名单',
    description='用于新增人员黑名单',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:blackList:add')],
)
async def add_black_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaBlacklistBaseModel, Body()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    query_object.admin_id = current_user.user.user_id
    result =  await BlackListService.add_service(query_db, query_object)
    return ResponseUtil.success(msg=result.message)

@black_list_controller.put(
    "/update",
    summary='更新人员黑名单',
    description='用于更新人员黑名单',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:blackList:update')],
)
async def update_black_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: Annotated[OaBlacklistBaseModel, Body()],
)->Response:
    result =  await BlackListService.update_service(query_db, model)
    return ResponseUtil.success(msg=result.message)

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
    result =  await BlackListService.get_info_service(query_db, id)
    return ResponseUtil.success(data=ModelConverter.time_format(ModelConverter.to_dict(result)))

@black_list_controller.delete(
    "/delete/{id}",
    summary='删除人员黑名单',
    description='用于删除人员黑名单',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:blackList:delete')],
)
async def delete_black_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result =  await BlackListService.del_by_id(query_db, id)
    return ResponseUtil.success(msg=result.message)
