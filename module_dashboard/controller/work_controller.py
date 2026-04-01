from fastapi import File, Form, Path, Query, Request, Response, UploadFile,Body
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from common.aspect.data_scope import DataScopeDependency
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency, CurrentUserDependency
from common.router import APIRouterPro
from module_dashboard.entity.do.work_do import OaWork
from module_dashboard.entity.vo.work_vo import OaWorkBaseModel, OaWorkPageQueryModel, OaWorkQueryModel
from module_dashboard.service.work_service import WorkService
from module_admin.entity.vo.user_vo import (
    CurrentUserModel
)
from utils.camel_converter import ModelConverter
from utils.response_util import ResponseUtil

dashboard_work_controller = APIRouterPro(
    prefix='/dashboard/work', order_num=3, tags=['个人办公-工作汇报'], dependencies=[PreAuthDependency()]
)

@dashboard_work_controller.get(
    "/list",
    summary='获取工作汇报列表',
    description='用于获取工作汇报列表',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:work:uery')],
)
async def get_page_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaWorkPageQueryModel, Query()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaWork)],
) -> Response:
    result =  await WorkService.get_page_list_service(query_db,query_object,data_scope_sql,True)
    return ResponseUtil.success(data=result)

@dashboard_work_controller.post(
    "/add",
    summary='新增工作汇报',
    description='用于新增工作汇报',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:work:add')],
)
async def add_plan(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaWorkQueryModel, Body()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    query_object.admin_id = current_user.user.user_id
    result = await WorkService.add_service(query_db, query_object)
    return ResponseUtil.success(msg=result.message)

@dashboard_work_controller.put(
    "/update",
    summary='更新工作汇报',
    description='用于更新工作汇报',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:work:update')],
)
async def update_plan(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: Annotated[OaWorkQueryModel, Body()],
)->Response:
    result = await WorkService().update_service(query_db, model)
    return ResponseUtil.success(msg=result.message)

@dashboard_work_controller.get(
    "/detail/{id}",
    summary='获取工作汇报详情',
    description='用于获取工作汇报详情',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:work:uery')],
)
async def get_plan_by_id(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result =  await WorkService.get_info_service(query_db, id)
    return ResponseUtil.success(data=ModelConverter.time_format(ModelConverter.to_dict(result)))

@dashboard_work_controller.delete(
    "/delete/{id}",
    summary='删除工作汇报',
    description='用于删除工作汇报',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:work:delete')],
)
async def delete_plan(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result =  await WorkService.del_by_id(query_db, id)
    return ResponseUtil.success(msg=result.message)
