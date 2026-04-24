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
from module_finance.entity.do.expense_do import OaExpense
from module_finance.entity.vo.expense_vo import OaExpenseBaseModel, OaExpensePageQueryModel, OaExpenseDetailModel
from module_finance.service.expense_service import OaExpenseService
from module_admin.entity.vo.user_vo import (
    CurrentUserModel
)
from utils.response_util import ResponseUtil

finance_expense_controller = APIRouterPro(
    prefix='/finance/expense', order_num=3, tags=['财务管理-报销管理'], dependencies=[PreAuthDependency()]
)

@finance_expense_controller.get(
    "/list",
    summary='获取报销管理列表',
    description='用于获取报销管理列表',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:expense:query')],
)
async def get_page_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaExpensePageQueryModel, Query()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaExpense)],
) -> Response:
    result = await OaExpenseService.get_page_list_service(query_db,query_object,data_scope_sql,True)
    return ResponseUtil.success(model_content=result)

@finance_expense_controller.get(
    "/user/list",
    summary='获取用户报销管理列表',
    description='用于用户获取报销管理列表',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:expense:query')],
)
async def get_page_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaExpensePageQueryModel, Query()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaExpense)],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    user_id = current_user.user.user_id
    query_object.admin_id = user_id
    result = await OaExpenseService.get_page_list_service(query_db,query_object,data_scope_sql,True)
    return ResponseUtil.success(model_content=result)

@finance_expense_controller.post(
    "/add",
    summary='新增报销管理',
    description='用于新增报销管理',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:expense:add')],
)
@Log(title="新增报销管理", business_type=BusinessType.INSERT)
async def add(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaExpenseDetailModel, Body()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    query_object.admin_id = current_user.user.user_id
    query_object.did = current_user.user.dept.dept_id
    result = await OaExpenseService.add_service(query_db, query_object)
    return ResponseUtil.success(msg=result.message)

@finance_expense_controller.put(
    "/update",
    summary='更新报销管理',
    description='用于更新报销管理',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:expense:update')],
)
@Log(title="更新报销管理", business_type=BusinessType.UPDATE)
async def update_expense(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: Annotated[OaExpenseDetailModel, Body()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
)->Response:
    model.admin_id = current_user.user.user_id
    model.did = current_user.user.dept.dept_id
    result = await OaExpenseService.update_service(query_db, model)
    return ResponseUtil.success(msg=result.message)

@finance_expense_controller.get(
    "/detail/{id}",
    summary='获取报销管理详情',
    description='用于获取报销管理详情',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:expense:query')],
)
async def get_expense(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result = await OaExpenseService.get_info_service(query_db, id)
    return ResponseUtil.success(data=result)

@finance_expense_controller.delete(
    "/delete/{id}",
    summary='删除报销管理',
    description='用于删除报销管理',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:expense:delete')],
)
@Log(title="删除报销管理", business_type=BusinessType.DELETE)
async def delete_expense(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result =  await OaExpenseService.del_by_id(query_db, id)
    return ResponseUtil.success(msg=result.message)

# @finance_expense_controller.put(
#     "/pass",
#     summary='审核通过',
#     description='用于审核通过',
#     response_model=None,
#     dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:expense:pass')],
# )
# async def pass_expense(
#         request: Request,
#         query_db: Annotated[AsyncSession, DBSessionDependency()],
#         data: Annotated[OaExpenseBaseModel, Body()],
#         current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
# ) -> Response:
#     userId = current_user.user.user_id
#     result =  await OaExpenseService.pass_expense(query_db, data, userId)
#     return ResponseUtil.success(msg=result.message)
#
# @finance_expense_controller.put(
#     "/reject",
#     summary='审核拒绝',
#     description='用于审核拒绝',
#     response_model=None,
#     dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:expense:reject')],
# )
# async def reject_expense(
#         request: Request,
#         query_db: Annotated[AsyncSession, DBSessionDependency()],
#         data: Annotated[OaExpenseBaseModel, Body()],
#         current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
# ) -> Response:
#     userId = current_user.user.user_id
#     result =  await OaExpenseService.reject_expense(query_db, data, userId)
#     return ResponseUtil.success(msg=result.message)
#
# @finance_expense_controller.put(
#     "/cancel",
#     summary='撤销申请',
#     description='用于撤销申请',
#     response_model=None,
#     dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:expense:cancel')],
# )
# async def cancel_expense(
#         request: Request,
#         query_db: Annotated[AsyncSession, DBSessionDependency()],
#         data: Annotated[OaExpenseBaseModel, Body()],
#         current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
# ) -> Response:
#     userId = current_user.user.user_id
#     result =  await OaExpenseService.cancel_expense(query_db, data, userId)
#     return ResponseUtil.success(msg=result.message)

@finance_expense_controller.put(
    "/pay",
    summary='打款',
    description='用于打款',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:expense:pay')],
)
@Log(title="打款", business_type=BusinessType.UPDATE)
async def pay_expense(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        data: Annotated[OaExpenseBaseModel, Body()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    userId = current_user.user.user_id
    result =  await OaExpenseService.pay_expense(query_db, data, userId)
    return ResponseUtil.success(msg=result.message)
