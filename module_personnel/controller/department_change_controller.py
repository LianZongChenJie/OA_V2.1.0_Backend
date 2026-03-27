from fastapi import File, Form, Path, Query, Request, Response, UploadFile
from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from common.aspect.data_scope import DataScopeDependency
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency
from common.router import APIRouterPro
from module_personnel.entity.do.department_change_do import OaDepartmentChange
from module_personnel.entity.vo.department_change_vo import OaDepartmentChangePageQueryModel, OaDepartmentChangeBassModel
from module_personnel.service.department_change_service import DepartmentChangeService

dept_change_controller = APIRouterPro(
    prefix='/personnel/deptChange', order_num=3, tags=['人事管理-人事调动'], dependencies=[PreAuthDependency()]
)

@dept_change_controller.get(
    "/list",
    summary='获取人事调动列表',
    description='用于获取人事调动列表',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:deptChange:query')],
)
async def get_page_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: OaDepartmentChangePageQueryModel,
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaDepartmentChange)],
) -> Response:
    return await DepartmentChangeService.get_page_list_service(query_db,query_object,data_scope_sql,True)

@dept_change_controller.get(
    "/add",
    summary='新增人事调动',
    description='用于新增人事调动',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:deptChange:add')],
)
async def add_change(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: OaDepartmentChangeBassModel,
) -> Response:
    return await DepartmentChangeService.add_service(query_db, query_object)

@dept_change_controller.post(
    "/update",
    summary='更新人事调动',
    description='用于更新人事调动',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:deptChange:update')],
)
async def update_profile(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: OaDepartmentChangeBassModel,
)->Response:
    return await DepartmentChangeService().update_service(query_db, model)

@dept_change_controller.get(
    "/detail/{id}",
    summary='获取人事调动详情',
    description='用于获取人事调动详情',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:deptChange:query')],
)
async def get_profile(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    return await DepartmentChangeService.get_info_service(query_db, id)

@dept_change_controller.get(
    "/delete/{id}",
    summary='删除人事调动',
    description='用于删除人事调动',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:deptChange:delete')],
)
async def delete_change(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    return await DepartmentChangeService.del_by_id(query_db, id)

@dept_change_controller.put(
    "/pass",
    summary='审核通过',
    description='用于审核通过',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:deptChange:pass')],
)
async def pass_change(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        data: OaDepartmentChangeBassModel,
) -> Response:
    return await DepartmentChangeService.pass_change(query_db, data)

@dept_change_controller.put(
    "/reject",
    summary='审核拒绝',
    description='用于审核拒绝',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:deptChange:reject')],
)
async def reject_change(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        data: OaDepartmentChangeBassModel,
) -> Response:
    return await DepartmentChangeService.reject_change(query_db, data)

@dept_change_controller.put(
    "/cancel",
    summary='撤销申请',
    description='用于撤销申请',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:deptChange:cancel')],
)
async def cancel_change(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        data: OaDepartmentChangeBassModel,
) -> Response:
    return await DepartmentChangeService.cancel_change(query_db, data)
