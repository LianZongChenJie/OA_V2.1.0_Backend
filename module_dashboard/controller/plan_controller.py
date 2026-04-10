from fastapi import File, Form, Path, Query, Request, Response, UploadFile, Body
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
from common.annotation.log_annotation import Log
from common.enums import BusinessType
from utils.log_util import logger

dashboard_plan_controller = APIRouterPro(
    prefix='/oa/plan', order_num=3, tags=['个人办公-日程安排'], dependencies=[PreAuthDependency()]
)

@dashboard_plan_controller.get(
    "/datalist",
    summary='获取日程安排列表',
    description='用于获取日程安排分页列表',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('oa:plan:list')],
)
async def get_page_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaPlanQueryModel, Query()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaPlan)],
) -> Response:
    result = await PlanService.get_page_list_service(query_db, query_object, data_scope_sql, False)
    logger.info('获取日程安排列表成功')
    return ResponseUtil.success(data=result)

@dashboard_plan_controller.get(
    "/calendar",
    summary='获取日历日程列表',
    description='用于获取日历视图的日程安排',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('oa:plan:calendar')],
)
async def get_calendar_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaPlanQueryModel, Query()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaPlan)],
) -> Response:
    result = await PlanService.get_calendar_list_service(query_db, query_object, data_scope_sql, False)
    logger.info('获取日历日程列表成功')
    return ResponseUtil.success(data=result)

@dashboard_plan_controller.post(
    "/add",
    summary='新增日程安排',
    description='用于新增日程安排',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('oa:plan:add')],
)
@Log(title='日程安排', business_type=BusinessType.INSERT)
async def add_plan(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaPlanBaseModel, Body()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    query_object.admin_id = current_user.user.user_id
    result = await PlanService.add_service(query_db, query_object)
    logger.info(result.message)
    return ResponseUtil.success(msg=result.message)

@dashboard_plan_controller.put(
    "/update",
    summary='更新日程安排',
    description='用于更新日程安排',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('oa:plan:update')],
)
@Log(title='日程安排', business_type=BusinessType.UPDATE)
async def update_plan(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: Annotated[OaPlanBaseModel, Body()],
) -> Response:
    result = await PlanService().update_service(query_db, model)
    logger.info(result.message)
    return ResponseUtil.success(msg=result.message)

@dashboard_plan_controller.get(
    "/detail/{id}",
    summary='获取日程安排详情',
    description='用于获取日程安排详情',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('oa:plan:query')],
)
async def get_plan_by_id(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result = await PlanService.get_info_service(query_db, id)
    logger.info(f'获取日程安排详情成功，ID: {id}')
    return ResponseUtil.success(data=result)

@dashboard_plan_controller.get(
    "/view/{id}",
    summary='读取日程弹层详情',
    description='用于读取日程弹层详情',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('oa:plan:query')],
)
async def view_plan(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result = await PlanService.get_info_service(query_db, id)
    logger.info(f'读取日程弹层详情成功，ID: {id}')
    return ResponseUtil.success(data=result)

@dashboard_plan_controller.delete(
    "/del/{id}",
    summary='删除日程安排',
    description='用于删除日程安排',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('oa:plan:delete')],
)
@Log(title='日程安排', business_type=BusinessType.DELETE)
async def delete_plan(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result = await PlanService.del_by_id(query_db, id)
    logger.info(result.message)
    return ResponseUtil.success(msg=result.message)
