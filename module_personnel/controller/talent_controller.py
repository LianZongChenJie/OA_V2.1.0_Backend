from fastapi import File, Form, Path, Query, Request, Response, UploadFile
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
    query_object: OaTalentPageQueryModel,
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaTalent)],
) -> Response:
    return await TalentService.get_page_list_service(query_db,query_object,data_scope_sql,True)

@talent_controller.get(
    "/add",
    summary='新增入职申请',
    description='用于新增入职申请',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:talent:add')],
)
async def add_change(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: OaTalentBaseModel,
) -> Response:
    return await TalentService.add_service(query_db, query_object)

@talent_controller.post(
    "/update",
    summary='更新入职申请',
    description='用于更新入职申请',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:talent:update')],
)
async def update_profile(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: OaTalentBaseModel,
)->Response:
    return await TalentService().update_service(query_db, model)

@talent_controller.get(
    "/detail/{id}",
    summary='获取入职申请详情',
    description='用于获取入职申请详情',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:talent:query')],
)
async def get_profile(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    return await TalentService.get_info_service(query_db, id)

@talent_controller.get(
    "/delete/{id}",
    summary='删除入职申请',
    description='用于删除入职申请',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:talent:delete')],
)
async def delete_change(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    return await TalentService.del_by_id(query_db, id)

@talent_controller.put(
    "/pass",
    summary='审核通过',
    description='用于审核通过',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:talent:pass')],
)
async def pass_change(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        data: OaTalentBaseModel,
) -> Response:
    return await TalentService.pass_change(query_db, data)

@talent_controller.put(
    "/reject",
    summary='审核拒绝',
    description='用于审核拒绝',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:talent:reject')],
)
async def reject_change(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        data: OaTalentBaseModel,
) -> Response:
    return await TalentService.reject_change(query_db, data)

@talent_controller.put(
    "/cancel",
    summary='撤销申请',
    description='用于撤销申请',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:talent:cancel')],
)
async def cancel_change(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        data: OaTalentBaseModel,
) -> Response:
    return await TalentService.cancel_change(query_db, data)
