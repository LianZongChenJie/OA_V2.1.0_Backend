from fastapi import File, Form, Path, Query, Request, Response, UploadFile,Body
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from common.aspect.data_scope import DataScopeDependency
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency, CurrentUserDependency
from common.router import APIRouterPro
from module_administrative.entity.do.note_do import OaNote
from module_administrative.entity.vo.note_vo import OaNoteBaseModel, OaNoteQueryPageModel
from module_administrative.service.note_service import NoteService
from module_admin.entity.vo.user_vo import (
    CurrentUserModel
)
from utils.camel_converter import ModelConverter
from utils.response_util import ResponseUtil

administrative_note_controller = APIRouterPro(
    prefix='/administrative/note', order_num=3, tags=['行政办公-公告列表'], dependencies=[PreAuthDependency()]
)

@administrative_note_controller.get(
    "/list",
    summary='获取公告列表列表',
    description='用于获取公告列表列表',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:note:query')],
)
async def get_page_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaNoteQueryPageModel, Query()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaNote)],
) -> Response:
    result = await NoteService.get_page_list_service(query_db,query_object,data_scope_sql,True)
    return ResponseUtil.success(model_content = result)

@administrative_note_controller.post(
    "/add",
    summary='新增公告列表',
    description='用于新增公告列表',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:note:add')],
)
async def add_note(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaNoteBaseModel, Body()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    query_object.admin_id = current_user.user.user_id
    result = await NoteService.add_service(query_db, query_object)
    return ResponseUtil.success(msg = result.message)

@administrative_note_controller.put(
    "/update",
    summary='更新公告列表',
    description='用于更新公告列表',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:note:update')],
)
async def update_note(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: Annotated[OaNoteBaseModel, Body()],
)->Response:
    result = await NoteService.update_service(query_db, model)
    return ResponseUtil.success(msg=result.message)

@administrative_note_controller.get(
    "/detail/{id}",
    summary='获取公告列表详情',
    description='用于获取公告列表详情',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:note:query')],
)
async def get_note_by_id(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result = await NoteService.get_info_service(query_db, id)
    return ResponseUtil.success(data=ModelConverter.time_format(ModelConverter.to_dict(result)))

@administrative_note_controller.delete(
    "/delete/{id}",
    summary='删除公告列表',
    description='用于删除公告列表',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:note:delete')],
)
async def delete_note(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result =  await NoteService.del_by_id(query_db, id)
    return ResponseUtil.success(msg=result.message)
