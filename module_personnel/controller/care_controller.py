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
from module_personnel.entity.do.care_do import OaCare
from module_personnel.entity.vo.care_vo import OaCareBaseModel, OaCarePageQueryModel
from module_personnel.service.care_service import CareService
from utils.camel_converter import ModelConverter
from utils.response_util import ResponseUtil
from module_admin.entity.vo.user_vo import (
    CurrentUserModel
)

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
    query_object: Annotated[OaCarePageQueryModel, Query()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaCare)],
) -> Response:
    result =  await CareService.get_page_list_service(query_db,query_object,data_scope_sql,True)
    return ResponseUtil.success(model_content=result)

@care_controller.post(
    "/add",
    summary='新增员工关怀',
    description='用于新增员工关怀',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:care:add')],
)
@Log(title='人事管理-员工关怀-新增',business_type=BusinessType.INSERT)
async def add_care(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaCareBaseModel, Body()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    query_object.admin_id = current_user.user.user_id
    result =  await CareService.add_service(query_db, query_object)
    return ResponseUtil.success(msg=result.message)

@care_controller.put(
    "/update",
    summary='更新员工关怀',
    description='用于更新员工关怀',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:care:update')],
)
@Log(title='人事管理-员工关怀-编辑',business_type=BusinessType.UPDATE)
async def update_care(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: OaCareBaseModel,
)->Response:
    result =  await CareService.update_service(query_db, model)
    return ResponseUtil.success(msg=result.message)

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
    result =  await CareService.get_info_service(query_db, id)
    return ResponseUtil.success(data=ModelConverter.time_format(ModelConverter.to_dict(result)))

@care_controller.delete(
    "/delete/{id}",
    summary='删除员工关怀',
    description='用于删除员工关怀',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:care:delete')],
)
@Log(title='人事管理-员工关怀-删除',business_type=BusinessType.DELETE)
async def delete_care(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result =  await CareService.del_by_id(query_db, id)
    return ResponseUtil.success(msg=result.message)
