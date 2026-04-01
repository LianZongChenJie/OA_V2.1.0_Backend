from fastapi import File, Form, Path, Query, Request, Response, UploadFile,Body
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from common.aspect.data_scope import DataScopeDependency
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency, CurrentUserDependency
from common.router import APIRouterPro
from module_dashboard.entity.do.plan_do import OaPlan
from module_dashboard.entity.vo.plan_vo import OaPlanQueryModel, OaPlanBaseModel
from module_dashboard.service.plan_service import PlanService
from module_admin.entity.vo.user_vo import (
    CurrentUserModel
)
from utils.camel_converter import ModelConverter
from utils.response_util import ResponseUtil

dashboard_plan_controller = APIRouterPro(
    prefix='/dashboard/plan', order_num=3, tags=['个人办公-日程安排'], dependencies=[PreAuthDependency()]
)

@dashboard_plan_controller.get(
    "/list",
    summary='获取日程安排列表',
    description='用于获取日程安排列表',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:plan:uery')],
)
async def get_page_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaPlanQueryModel, Query()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaPlan)],
) -> Response:
    result =  await PlanService.get_page_list_service(query_db,query_object,data_scope_sql,False)
    return ResponseUtil.success(data=result)

@dashboard_plan_controller.post(
    "/add",
    summary='新增日程安排',
    description='用于新增日程安排',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:plan:add')],
)
async def add_plan(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaPlanBaseModel, Body()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    query_object.admin_id = current_user.user.user_id
    result = await PlanService.add_service(query_db, query_object)
    return ResponseUtil.success(msg=result.message)

@dashboard_plan_controller.put(
    "/update",
    summary='更新日程安排',
    description='用于更新日程安排',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:plan:update')],
)
async def update_plan(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: Annotated[OaPlanBaseModel, Body()],
)->Response:
    result = await PlanService().update_service(query_db, model)
    return ResponseUtil.success(msg=result.message)

@dashboard_plan_controller.get(
    "/detail/{id}",
    summary='获取日程安排详情',
    description='用于获取日程安排详情',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:plan:uery')],
)
async def get_plan_by_id(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result =  await PlanService.get_info_service(query_db, id)
    return ResponseUtil.success(data=ModelConverter.time_format(ModelConverter.to_dict(result)))

@dashboard_plan_controller.delete(
    "/delete/{id}",
    summary='删除日程安排',
    description='用于删除日程安排',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:plan:delete')],
)
async def delete_plan(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result =  await PlanService.del_by_id(query_db, id)
    return ResponseUtil.success(msg=result.message)


@dashboard_plan_controller.get(
    "/calendar/list",
    summary='获取日程安排列表',
    description='用于获取日程安排列表',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:plan:uery')],
)
async def get_calendar_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaPlanQueryModel, Query()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaPlan)],
) -> Response:
    result =  await PlanService.get_calendar_list_service(query_db,query_object,data_scope_sql,False)
    return ResponseUtil.success(data=result)

@dashboard_plan_controller.get(
    "/calendar/detail/{id}",
    summary='获取日历日程安排详情',
    description='用于获取日历日程安排详情',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:plan:uery')],
)
async def get_calendar_plan_by_id(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result =  await PlanService.get_calendar_info_service(query_db, id)
    return ResponseUtil.success(data=result)