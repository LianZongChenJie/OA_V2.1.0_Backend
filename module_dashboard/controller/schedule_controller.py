from fastapi import File, Form, Path, Query, Request, Response, UploadFile,Body
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from common.aspect.data_scope import DataScopeDependency
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency, CurrentUserDependency
from common.router import APIRouterPro
from module_dashboard.entity.do.schedule_do import OaSchedule
from module_dashboard.entity.vo.schedule_vo import OaSchedulePageQueryModel, OaScheduleBaseModel
from module_dashboard.service.schedule_service import ScheduleService
from module_admin.entity.vo.user_vo import (
    CurrentUserModel
)
from utils.camel_converter import ModelConverter
from utils.response_util import ResponseUtil

dashboard_schedule_controller = APIRouterPro(
    prefix='/dashboard/schedule', order_num=3, tags=['个人办公-工作记录'], dependencies=[PreAuthDependency()]
)

@dashboard_schedule_controller.get(
    "/list",
    summary='获取工作记录列表',
    description='用于获取工作记录列表',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:schedule:uery')],
)
async def get_page_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaSchedulePageQueryModel, Query()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaSchedule)],
) -> Response:
    result =  await ScheduleService.get_page_list_service(query_db,query_object,data_scope_sql,True)
    return ResponseUtil.success(data=result)

@dashboard_schedule_controller.post(
    "/add",
    summary='新增工作记录',
    description='用于新增工作记录',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:schedule:add')],
)
async def add_schedule(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaScheduleBaseModel, Body()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    query_object.admin_id = current_user.user.user_id
    result = await ScheduleService.add_service(query_db, query_object)
    return ResponseUtil.success(msg=result.message)

@dashboard_schedule_controller.put(
    "/update",
    summary='更新工作记录',
    description='用于更新工作记录',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:schedule:update')],
)
async def update_schedule(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: Annotated[OaScheduleBaseModel, Body()],
)->Response:
    result = await ScheduleService().update_service(query_db, model)
    return ResponseUtil.success(msg=result.message)

@dashboard_schedule_controller.get(
    "/detail/{id}",
    summary='获取工作记录详情',
    description='用于获取工作记录详情',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:schedule:uery')],
)
async def get_schedule_by_id(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result =  await ScheduleService.get_info_service(query_db, id)
    return ResponseUtil.success(data=ModelConverter.time_format(ModelConverter.to_dict(result)))

@dashboard_schedule_controller.delete(
    "/delete/{id}",
    summary='删除工作记录',
    description='用于删除工作记录',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:schedule:delete')],
)
async def delete_schedule(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result =  await ScheduleService.del_by_id(query_db, id)
    return ResponseUtil.success(msg=result.message)


@dashboard_schedule_controller.get(
    "/calendar/list",
    summary='获取工作记录列表',
    description='用于获取工作记录列表',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:schedule:uery')],
)
async def get_calendar_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaSchedulePageQueryModel, Query()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaSchedule)],
) -> Response:
    result =  await ScheduleService.get_calendar_list_service(query_db,query_object,data_scope_sql,True)
    return ResponseUtil.success(data=result)

@dashboard_schedule_controller.get(
    "/calendar/detail/{id}",
    summary='获取日历工作记录详情',
    description='用于获取日历工作记录详情',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:schedule:uery')],
)
async def get_calendar_schedule_by_id(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result =  await ScheduleService.get_calendar_info_service(query_db, id)
    return ResponseUtil.success(data=result)