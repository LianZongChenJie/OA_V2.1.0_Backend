from fastapi import File, Form, Path, Query, Request, Response, UploadFile, Body
from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from common.aspect.data_scope import DataScopeDependency
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency, CurrentUserDependency
from common.router import APIRouterPro
from module_personnel.entity.do.personnel_quit_do import OaPersonalQuit
from module_personnel.entity.vo.personnel_quit_vo import OaPersonnelQuitPageQueryModel, OaPersonalQuitBaseModel
from module_personnel.service.personnel_quit_service import PersonnelQuitService
from utils.response_util import ResponseUtil
from module_admin.entity.vo.user_vo import (
    CurrentUserModel
)

personnel_quit_controller = APIRouterPro(
    prefix='/personnel/quit', order_num=3, tags=['人事管理-离职申请'], dependencies=[PreAuthDependency()]
)

@personnel_quit_controller.get(
    "/list",
    summary='获取离职申请列表',
    description='用于获取离职申请列表',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:quit:query')],
)
async def get_page_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaPersonnelQuitPageQueryModel, Query()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaPersonalQuit)],
) -> Response:
    result =  await PersonnelQuitService.get_page_list_service(query_db,query_object,data_scope_sql,True)
    return ResponseUtil.success(model_content=result)

@personnel_quit_controller.post(
    "/add",
    summary='新增离职申请',
    description='用于新增离职申请',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:quit:add')],
)
async def add_quit(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaPersonalQuitBaseModel, Body()],
) -> Response:
    result = await PersonnelQuitService.add_service(query_db, query_object)
    return ResponseUtil.success(msg=result.message)

@personnel_quit_controller.put(
    "/update",
    summary='更新离职申请',
    description='用于更新离职申请',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:quit:update')],
)
async def update_quit(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: Annotated[OaPersonalQuitBaseModel, Body()],
)->Response:
    result = await PersonnelQuitService().update_service(query_db, model)
    return ResponseUtil.success(msg=result.message)

@personnel_quit_controller.get(
    "/detail/{id}",
    summary='获取离职申请详情',
    description='用于获取离职申请详情',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:quit:query')],
)
async def get_quit(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result = await PersonnelQuitService.get_info_service(query_db, id)
    return ResponseUtil.success(model_content=result)

@personnel_quit_controller.delete(
    "/delete/{id}",
    summary='删除离职申请',
    description='用于删除离职申请',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:quit:delete')],
)
async def delete_quit(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result = await PersonnelQuitService.del_by_id(query_db, id)
    return ResponseUtil.success(msg=result.message)

@personnel_quit_controller.put(
    "/review",
    summary='审核',
    description='用于审核',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:quit:pass')],
)
async def review(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        data: Annotated[OaPersonalQuitBaseModel, Body()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    data.check_last_uid = current_user.user.user_id
    result = await PersonnelQuitService.review(query_db, data)
    return ResponseUtil.success(msg=result.message)
