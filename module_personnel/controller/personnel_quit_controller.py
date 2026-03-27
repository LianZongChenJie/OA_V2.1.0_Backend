from fastapi import File, Form, Path, Query, Request, Response, UploadFile
from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from common.aspect.data_scope import DataScopeDependency
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency
from common.router import APIRouterPro
from module_personnel.entity.do.personnel_quit_do import OaPersonalQuit
from module_personnel.entity.vo.personnel_quit_vo import OaPersonnelQuitPageQueryModel, OaPersonalQuitBaseModel
from module_personnel.service.personnel_quit_service import PersonnelQuitService

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
    query_object: OaPersonnelQuitPageQueryModel,
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaPersonalQuit)],
) -> Response:
    return await PersonnelQuitService.get_page_list_service(query_db,query_object,data_scope_sql,True)

@personnel_quit_controller.get(
    "/add",
    summary='新增离职申请',
    description='用于新增离职申请',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:quit:add')],
)
async def add_change(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: OaPersonalQuitBaseModel,
) -> Response:
    return await PersonnelQuitService.add_service(query_db, query_object)

@personnel_quit_controller.post(
    "/update",
    summary='更新离职申请',
    description='用于更新离职申请',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:quit:update')],
)
async def update_profile(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: OaPersonalQuitBaseModel,
)->Response:
    return await PersonnelQuitService().update_service(query_db, model)

@personnel_quit_controller.get(
    "/detail/{id}",
    summary='获取离职申请详情',
    description='用于获取离职申请详情',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:quit:query')],
)
async def get_profile(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    return await PersonnelQuitService.get_info_service(query_db, id)

@personnel_quit_controller.get(
    "/delete/{id}",
    summary='删除离职申请',
    description='用于删除离职申请',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:quit:delete')],
)
async def delete_change(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    return await PersonnelQuitService.del_by_id(query_db, id)

@personnel_quit_controller.put(
    "/pass",
    summary='审核通过',
    description='用于审核通过',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:quit:pass')],
)
async def pass_change(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        data: OaPersonalQuitBaseModel,
) -> Response:
    return await PersonnelQuitService.pass_change(query_db, data)

@personnel_quit_controller.put(
    "/reject",
    summary='审核拒绝',
    description='用于审核拒绝',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:quit:reject')],
)
async def reject_change(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        data: OaPersonalQuitBaseModel,
) -> Response:
    return await PersonnelQuitService.reject_change(query_db, data)

@personnel_quit_controller.put(
    "/cancel",
    summary='撤销申请',
    description='用于撤销申请',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:quit:cancel')],
)
async def cancel_change(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        data: OaPersonalQuitBaseModel,
) -> Response:
    return await PersonnelQuitService.cancel_change(query_db, data)
