from fastapi import File, Form, Path, Query, Request, Response, UploadFile
from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from common.aspect.data_scope import DataScopeDependency
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency
from common.router import APIRouterPro
from module_personnel.entity.do.care_do import OaCare
from module_personnel.entity.vo.care_vo import OaCareBaseModel, OaCarePageQueryModel
from module_personnel.service.care_service import CareService

care_controller = APIRouterPro(
    prefix='/personnel/care', order_num=3, tags=['人事管理-员工关怀'], dependencies=[PreAuthDependency()]
)

@care_controller.get(
    "/list",
    summary='获取员工关怀列表',
    description='用于获取员工关怀列表',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:care:query')],
)
async def get_page_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: OaCarePageQueryModel,
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaCare)],
) -> Response:
    return await CareService.get_page_list_service(query_db,query_object,data_scope_sql,True)

@care_controller.get(
    "/add",
    summary='新增员工关怀',
    description='用于新增员工关怀',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:care:add')],
)
async def add_change(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: OaCareBaseModel,
) -> Response:
    return await CareService.add_service(query_db, query_object)

@care_controller.post(
    "/update",
    summary='更新员工关怀',
    description='用于更新员工关怀',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:care:update')],
)
async def update_profile(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: OaCareBaseModel,
)->Response:
    return await CareService().update_service(query_db, model)

@care_controller.get(
    "/detail/{id}",
    summary='获取员工关怀详情',
    description='用于获取员工关怀详情',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:care:query')],
)
async def get_detail(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    return await CareService.get_info_service(query_db, id)

@care_controller.get(
    "/delete/{id}",
    summary='删除员工关怀',
    description='用于删除员工关怀',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:care:delete')],
)
async def delete_change(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    return await CareService.del_by_id(query_db, id)
