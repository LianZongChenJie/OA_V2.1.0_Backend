from fastapi import File, Form, Path, Query, Request, Response, UploadFile,Body
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from common.aspect.data_scope import DataScopeDependency
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency, CurrentUserDependency
from common.router import APIRouterPro
from module_administrative.entity.do.seal_do import OaSeal
from module_administrative.entity.vo.seal_vo import OaSealPageQueryModel, OaSealBaseModel
from module_administrative.service.seal_service import SealService
from module_admin.entity.vo.user_vo import (
    CurrentUserModel
)
from utils.response_util import ResponseUtil

administrative_seal_controller = APIRouterPro(
    prefix='/administrative/seal', order_num=3, tags=['行政办公-用章管理'], dependencies=[PreAuthDependency()]
)

@administrative_seal_controller.get(
    "/list",
    summary='获取用章管理列表',
    description='用于获取用章管理列表',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:seal:query')],
)
async def get_page_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaSealPageQueryModel, Query()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaSeal)],
) -> Response:
    result = await SealService.get_page_list_service(query_db,query_object,data_scope_sql,True)
    return ResponseUtil.success(model_content=result.message)

@administrative_seal_controller.post(
    "/add",
    summary='新增用章管理',
    description='用于新增用章管理',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:seal:add')],
)
async def add_change(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaSealBaseModel, Body()],
) -> Response:
    result = await SealService.add_service(query_db, query_object)
    return ResponseUtil.success(msg=result.message)

@administrative_seal_controller.put(
    "/update",
    summary='更新用章管理',
    description='用于更新用章管理',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:seal:update')],
)
async def update_seal(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: Annotated[OaSealBaseModel, Body()],
)->Response:
    result = await SealService().update_service(query_db, model)
    return ResponseUtil.success(msg=result.message)

@administrative_seal_controller.get(
    "/detail/{id}",
    summary='获取用章管理详情',
    description='用于获取用章管理详情',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:seal:query')],
)
async def get_profile(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result = await SealService.get_info_service(query_db, id)
    return ResponseUtil.success(model_content=result.model)

@administrative_seal_controller.delete(
    "/delete/{id}",
    summary='删除用章管理',
    description='用于删除用章管理',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:seal:delete')],
)
async def delete_seal(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result =  await SealService.del_by_id(query_db, id)
    return ResponseUtil.success(msg=result.message)

@administrative_seal_controller.put(
    "/pass",
    summary='审核通过',
    description='用于审核通过',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:seal:pass')],
)
async def pass_seal(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        data: Annotated[OaSealBaseModel, Body()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    userId = current_user.user.user_id
    result =  await SealService.pass_seal(query_db, data, userId)
    return ResponseUtil.success(msg=result.message)

@administrative_seal_controller.put(
    "/reject",
    summary='审核拒绝',
    description='用于审核拒绝',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:seal:reject')],
)
async def reject_seal(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        data: Annotated[OaSealBaseModel, Body()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    userId = current_user.user.user_id
    result =  await SealService.reject_seal(query_db, data, userId)
    return ResponseUtil.success(msg=result.message)

@administrative_seal_controller.put(
    "/cancel",
    summary='撤销申请',
    description='用于撤销申请',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:seal:cancel')],
)
async def cancel_seal(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        data: Annotated[OaSealBaseModel, Body()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    userId = current_user.user.user_id
    result =  await SealService.cancel_seal(query_db, data, userId)
    return ResponseUtil.success(msg=result.message)
