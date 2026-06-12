from fastapi import File, Form, Path, Query, Request, Response, UploadFile,Body
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from common.annotation.log_annotation import Log
from common.aspect.data_scope import DataScopeDependency
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency, CurrentUserDependency
from common.enums import BusinessType
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
    dependencies=[UserInterfaceAuthDependency('administration:seal:list')],#administration:seal:apply:list
)
async def get_page_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaSealPageQueryModel, Query()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaSeal)],
) -> Response:
    result = await SealService.get_page_list_service(query_db,query_object,data_scope_sql,True)
    return ResponseUtil.success(model_content=result)

@administrative_seal_controller.post(
    "/add",
    summary='新增用章管理',
    description='用于新增用章管理',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('administration:seal:add')],
)
@Log(title="新增用章管理", business_type=BusinessType.INSERT)
async def add_seal(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaSealBaseModel, Body()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    query_object.admin_id = current_user.user.user_id
    query_object.did = current_user.user.dept_id
    result = await SealService.add_service(query_db, query_object)
    return ResponseUtil.success(msg=result.message)

@administrative_seal_controller.put(
    "/update",
    summary='更新用章管理',
    description='用于更新用章管理',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('administration:seal:update')],
)
@Log(title="更新用章管理", business_type=BusinessType.UPDATE)
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
    dependencies=[UserInterfaceAuthDependency('administration:seal:query')],
)
async def get_seal(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result = await SealService.get_info_service(query_db, id)
    return ResponseUtil.success(data=result)

@administrative_seal_controller.delete(
    "/delete/{id}",
    summary='删除用章管理',
    description='用于删除用章管理',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('administration:seal:delete')],
)
@Log(title="删除用章管理", business_type=BusinessType.DELETE)
async def delete_seal(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result =  await SealService.del_by_id(query_db, id)
    return ResponseUtil.success(msg=result.message)

@administrative_seal_controller.put(
    "/return/{id}",
    summary='还章',
    description='用于还章操作，将用章状态改为空闲',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('administration:seal:return')],
)
@Log(title="还章", business_type=BusinessType.UPDATE)
async def return_seal(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result = await SealService.return_seal_service(query_db, id)
    return ResponseUtil.success(msg=result.message)