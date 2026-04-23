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
from module_finance.entity.do.loan_do import OaLoan
from module_finance.entity.vo.loan_vo import OaLoanPageQueryModel, OaLoanBaseModel
from module_finance.service.loan_service import OaLoanService
from module_admin.entity.vo.user_vo import (
    CurrentUserModel
)
from utils.response_util import ResponseUtil

finance_loan_controller = APIRouterPro(
    prefix='/finance/loan', order_num=3, tags=['财务管理-借支管理'], dependencies=[PreAuthDependency()]
)

@finance_loan_controller.get(
    "/list",
    summary='获取借支管理列表',
    description='用于获取借支管理列表',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:loan:query')],
)
async def get_page_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaLoanPageQueryModel, Query()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaLoan)],
) -> Response:
    result = await OaLoanService.get_page_list_service(query_db,query_object,data_scope_sql,True)
    return ResponseUtil.success(model_content=result)

@finance_loan_controller.get(
    "/user/list",
    summary='获取用户借支管理列表',
    description='用于用户获取借支管理列表',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:loan:query')],
)
async def get_page_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaLoanPageQueryModel, Query()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaLoan)],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    user_id = current_user.user.user_id
    query_object.admin_id = user_id
    result = await OaLoanService.get_page_list_service(query_db,query_object,data_scope_sql,True)
    return ResponseUtil.success(model_content=result)

@finance_loan_controller.post(
    "/add",
    summary='新增借支管理',
    description='用于新增借支管理',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:loan:add')],
)
@Log(title='借支管理-新增',business_type=BusinessType.INSERT)
async def add_loan(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaLoanBaseModel, Body()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    query_object.admin_id = current_user.user.user_id
    query_object.did = current_user.user.dept_id
    result = await OaLoanService.add_service(query_db, query_object)
    return ResponseUtil.success(msg=result.message)

@finance_loan_controller.put(
    "/update",
    summary='更新借支管理',
    description='用于更新借支管理',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:loan:update')],
)
@Log(title='借支管理-编辑',business_type=BusinessType.UPDATE)
async def update_loan(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: Annotated[OaLoanBaseModel, Body()],
)->Response:
    result = await OaLoanService().update_service(query_db, model)
    return ResponseUtil.success(msg=result.message)

@finance_loan_controller.get(
    "/detail/{id}",
    summary='获取借支管理详情',
    description='用于获取借支管理详情',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:loan:query')],
)
async def get_loan(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result = await OaLoanService.get_info_service(query_db, id)
    return ResponseUtil.success(data=result)

@finance_loan_controller.delete(
    "/delete/{id}",
    summary='删除借支管理',
    description='用于删除借支管理',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:loan:delete')],
)
@Log(title='借支管理-删除',business_type=BusinessType.DELETE)
async def delete_loan(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result =  await OaLoanService.del_by_id(query_db, id)
    return ResponseUtil.success(msg=result.message)

# @finance_loan_controller.put(
#     "/pass",
#     summary='审核通过',
#     description='用于审核通过',
#     response_model=None,
#     dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:loan:pass')],
# )
# async def pass_loan(
#         request: Request,
#         query_db: Annotated[AsyncSession, DBSessionDependency()],
#         data: Annotated[OaLoanBaseModel, Body()],
#         current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
# ) -> Response:
#     userId = current_user.user.user_id
#     result =  await OaLoanService.pass_loan(query_db, data, userId)
#     return ResponseUtil.success(msg=result.message)
#
# @finance_loan_controller.put(
#     "/reject",
#     summary='审核拒绝',
#     description='用于审核拒绝',
#     response_model=None,
#     dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:loan:reject')],
# )
# async def reject_loan(
#         request: Request,
#         query_db: Annotated[AsyncSession, DBSessionDependency()],
#         data: Annotated[OaLoanBaseModel, Body()],
#         current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
# ) -> Response:
#     userId = current_user.user.user_id
#     result =  await OaLoanService.reject_loan(query_db, data, userId)
#     return ResponseUtil.success(msg=result.message)
#
# @finance_loan_controller.put(
#     "/cancel",
#     summary='撤销申请',
#     description='用于撤销申请',
#     response_model=None,
#     dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:loan:cancel')],
# )
# async def cancel_loan(
#         request: Request,
#         query_db: Annotated[AsyncSession, DBSessionDependency()],
#         data: Annotated[OaLoanBaseModel, Body()],
#         current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
# ) -> Response:
#     userId = current_user.user.user_id
#     result =  await OaLoanService.cancel_loan(query_db, data, userId)
#     return ResponseUtil.success(msg=result.message)

@finance_loan_controller.put(
    "/pay",
    summary='打款',
    description='用于打款',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:loan:pay')],
)
@Log(title='借支管理-打款',business_type=BusinessType.UPDATE)
async def pay_loan(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        data: Annotated[OaLoanBaseModel, Body()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    userId = current_user.user.user_id
    result =  await OaLoanService.pay_loan(query_db, data, userId)
    return ResponseUtil.success(msg=result.message)

@finance_loan_controller.put(
    "/back",
    summary='还款',
    description='用于还款',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:loan:back')],
)
@Log(title='借支管理-还款',business_type=BusinessType.UPDATE)
async def back_loan(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        data: Annotated[OaLoanBaseModel, Body()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    userId = current_user.user.user_id
    result =  await OaLoanService.back_loan(query_db, data, userId)
    return ResponseUtil.success(msg=result.message)