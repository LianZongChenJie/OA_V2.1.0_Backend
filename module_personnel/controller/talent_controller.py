from fastapi import File, Form, Path, Query, Request, Response, UploadFile, Body
from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from common.aspect.data_scope import DataScopeDependency
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency
from common.router import APIRouterPro
from module_personnel.entity.do.talent_do import OaTalent
from module_personnel.entity.vo.talent_vo import OaTalentBaseModel, OaTalentPageQueryModel
from module_personnel.service.talent_service import TalentService
from utils.response_util import ResponseUtil

talent_controller = APIRouterPro(
    prefix='/personnel/talent', order_num=3, tags=['人事管理-入职申请'], dependencies=[PreAuthDependency()]
)

@talent_controller.get(
    "/list",
    summary='获取入职申请列表',
    description='用于获取入职申请列表',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:talent:query')],
)
async def get_page_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaTalentPageQueryModel, Query()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaTalent)],
) -> Response:
    result = await TalentService.get_page_list_service(query_db,query_object,data_scope_sql,True)
    return ResponseUtil.success(model_content=result)

@talent_controller.post(
    "/add",
    summary='新增入职申请',
    description='用于新增入职申请',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:talent:add')],
)
async def add_talent(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaTalentBaseModel, Body()],
) -> Response:
    result=  await TalentService.add_service(query_db, query_object)
    return ResponseUtil.success(msg=result.message)

@talent_controller.put(
    "/update",
    summary='更新入职申请',
    description='用于更新入职申请',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:talent:update')],
)
async def update_talent(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: Annotated[OaTalentBaseModel, Body()],
)->Response:
    result = await TalentService.update_service(query_db, model)
    return ResponseUtil.success(msg=result.message)

@talent_controller.get(
    "/detail/{id}",
    summary='获取入职申请详情',
    description='用于获取入职申请详情',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:talent:query')],
)
async def get_talent(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result =  await TalentService.get_info_service(query_db, id)
    return ResponseUtil.success(data=result)

@talent_controller.delete(
    "/delete/{id}",
    summary='删除入职申请',
    description='用于删除入职申请',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:talent:delete')],
)
async def delete_talent(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result = await TalentService.del_by_id(query_db, id)
    return ResponseUtil.success(msg=result.message)

@talent_controller.put(
    "/review",
    summary='审核',
    description='用于审核入职申请',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:talent:pass')],
)
async def review(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        data: Annotated[OaTalentBaseModel, Body()],
) -> Response:
    return await TalentService.review(query_db, data)
