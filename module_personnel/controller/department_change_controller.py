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
from module_personnel.entity.do.department_change_do import OaDepartmentChange
from module_personnel.entity.vo.department_change_vo import OaDepartmentChangePageQueryModel, OaDepartmentChangeBassModel
from module_personnel.service.department_change_service import DepartmentChangeService
from utils.response_util import ResponseUtil
from module_admin.entity.vo.user_vo import (
    CurrentUserModel
)

dept_change_controller = APIRouterPro(
    prefix='/personnel/deptChange', order_num=3, tags=['人事管理-人事调动'], dependencies=[PreAuthDependency()]
)

@dept_change_controller.get(
    "/list",
    summary='获取人事调动列表',
    description='用于获取人事调动列表',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('personnel:deptChange:list')],
)
async def get_page_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaDepartmentChangePageQueryModel, Query()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaDepartmentChange)],
) -> Response:
    result =  await DepartmentChangeService.get_page_list_service(query_db,query_object,data_scope_sql,True)
    return ResponseUtil.success(model_content=result)

@dept_change_controller.post(
    "/add",
    summary='新增人事调动',
    description='用于新增人事调动',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('personnel:deptChange:add')],
)
@Log(title='人事管理-人事调动-新增',business_type=BusinessType.INSERT)
async def add_change(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaDepartmentChangeBassModel, Body()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    query_object.admin_id = current_user.user.user_id
    result =  await DepartmentChangeService.add_service(query_db, query_object)
    return ResponseUtil.success(msg=result.message)

@dept_change_controller.put(
    "/update",
    summary='更新人事调动',
    description='用于更新人事调动',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('personnel:deptChange:update')],
)
@Log(title='人事管理-人事调动-更新',business_type=BusinessType.UPDATE)
async def update_change(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: Annotated[OaDepartmentChangeBassModel, Body()],
)->Response:
    result =  await DepartmentChangeService().update_service(query_db, model)
    return ResponseUtil.success(msg=result.message)

@dept_change_controller.get(
    "/detail/{id}",
    summary='获取人事调动详情',
    description='用于获取人事调动详情',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('personnel:deptChange:query')],
)
async def get_change(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result =  await DepartmentChangeService.get_info_service(query_db, id)
    return ResponseUtil.success(data=result)

@dept_change_controller.delete(
    "/delete/{id}",
    summary='删除人事调动',
    description='用于删除人事调动',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('personnel:deptChange:delete')],
)
@Log(title='人事管理-人事调动-删除',business_type=BusinessType.DELETE)
async def delete_change(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result =  await DepartmentChangeService.del_by_id(query_db, id)
    return ResponseUtil.success(msg=result.message)
@dept_change_controller.put(
    "/change",
    summary='交接人事调动',
    description='用于交接人事调动',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('personnel:deptChange:change')],
)
@Log(title='人事管理-人事调动-调动',business_type=BusinessType.UPDATE)
async def change_change(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    change_model: Annotated[OaDepartmentChangeBassModel, Body()],
)->Response:
    result =  await DepartmentChangeService.change(query_db, change_model.id)
    return ResponseUtil.success(msg=result.message)
