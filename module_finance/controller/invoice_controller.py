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
from module_finance.entity.do.invoice_do import OaInvoice
from module_finance.entity.vo.invoice_vo import OaInvoiceBaseModel, OaInvoicePageQueryModel, OaInvoiceDetailModel, \
    OaInvoiceIncomeBaseModel
from module_finance.service.invoice_service import InvoiceService
from module_admin.entity.vo.user_vo import (
    CurrentUserModel
)
from utils.response_util import ResponseUtil

finance_invoice_controller = APIRouterPro(
    prefix='/finance/invoice', order_num=3, tags=['财务管理-开票管理'], dependencies=[PreAuthDependency()]
)

@finance_invoice_controller.get(
    "/list",
    summary='获取开票管理列表',
    description='用于获取开票管理列表',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:invoice:query')],
)
async def get_page_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaInvoicePageQueryModel, Query()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaInvoice)],
) -> Response:
    result = await InvoiceService.get_page_list_service(query_db,query_object,data_scope_sql,True)
    return ResponseUtil.success(model_content=result)

@finance_invoice_controller.get(
    "/user/list",
    summary='获取用户开票管理列表',
    description='用于用户获取开票管理列表',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:invoice:query')],
)
async def get_page_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaInvoicePageQueryModel, Query()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaInvoice)],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    user_id = current_user.user.user_id
    query_object.admin_id = user_id
    result = await InvoiceService.get_page_list_service(query_db,query_object,data_scope_sql,True)
    return ResponseUtil.success(model_content=result)

@finance_invoice_controller.post(
    "/add",
    summary='新增开票管理',
    description='用于新增开票管理',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:invoice:add')],
)
@Log(title='开票管理-新增',business_type=BusinessType.INSERT)
async def add(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaInvoiceBaseModel, Body()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    query_object.admin_id = current_user.user.user_id
    query_object.did = current_user.user.dept.dept_id
    result = await InvoiceService.add_service(query_db, query_object)
    return ResponseUtil.success(msg=result.message)

@finance_invoice_controller.put(
    "/add",
    summary='更新开票管理',
    description='用于更新开票管理',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:invoice:update')],
)
@Log(title='开票管理-更新',business_type=BusinessType.UPDATE)
async def update_expense(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: Annotated[OaInvoiceBaseModel, Body()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
)->Response:
    model.admin_id = current_user.user.user_id
    model.did = current_user.user.dept.dept_id
    result = await InvoiceService().add_service(query_db, model)
    return ResponseUtil.success(msg=result.message)

@finance_invoice_controller.get(
    "/detail/{id}",
    summary='获取开票管理详情',
    description='用于获取开票管理详情',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:invoice:query')],
)
async def get_expense(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result = await InvoiceService.get_info_service(query_db, id)
    return ResponseUtil.success(data=result)

@finance_invoice_controller.delete(
    "/delete/{id}",
    summary='删除开票管理',
    description='用于删除开票管理',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:invoice:delete')],
)
@Log(title='开票管理-删除',business_type=BusinessType.DELETE)
async def delete_invoice(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result =  await InvoiceService.del_by_id(query_db, id)
    return ResponseUtil.success(msg=result.message)

# @finance_invoice_controller.put(
#     "/review",
#     summary='审核',
#     description='用于审核',
#     response_model=None,
#     dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:invoice:pass')],
# )
# async def review(
#         request: Request,
#         query_db: Annotated[AsyncSession, DBSessionDependency()],
#         data: Annotated[OaInvoiceBaseModel, Body()],
#         current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
# ) -> Response:
#     userId = current_user.user.user_id
#     result =  await InvoiceService.review(query_db, data, userId)
#     return ResponseUtil.success(msg=result.message)

# @finance_invoice_controller.put(
#     "/pay",
#     summary='打款',
#     description='用于打款',
#     response_model=None,
#     dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:invoice:pay')],
# )
# @Log(title='开票管理-打款',business_type=BusinessType.UPDATE)
# async def payment(
#         request: Request,
#         query_db: Annotated[AsyncSession, DBSessionDependency()],
#         data: Annotated[OaInvoiceBaseModel, Body()],
#         current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
# ) -> Response:
#     userId = current_user.user.user_id
#     result =  await InvoiceService.payment(query_db, data, userId)
#     return ResponseUtil.success(msg=result.message)

@finance_invoice_controller.put(
    "/openStatus",
    summary='开票状态',
    description='用于开票状态',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:invoice:edit')],
)
@Log(title='开票管理-开票状态',business_type=BusinessType.UPDATE)
async def open_status(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        data: Annotated[OaInvoiceBaseModel, Body()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    data.open_admin_id = current_user.user.user_id
    result =  await InvoiceService.open_status(query_db, data)
    return ResponseUtil.success(msg=result.message)




# ------------------------------------  发票回款管理  ------------------------------------
@finance_invoice_controller.post(
    "/add_income",
    summary='添加发票回款记录',
    description='用于添加发票回款记录',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:invoice:add')],
)
@Log(title='开票管理-添加发票回款记录',business_type=BusinessType.INSERT)
async def add_income(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        data: Annotated[list[OaInvoiceIncomeBaseModel], Body()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    userId = current_user.user.user_id
    result =  await InvoiceService.income_add(query_db, data, userId)
    return ResponseUtil.success(msg=result.message)

@finance_invoice_controller.delete(
    "/delete_income",
    summary='删除发票回款记录',
    description='用于删除发票回款记录',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:invoice:delete')],
)
@Log(title='开票管理-删除发票回款记录',business_type=BusinessType.DELETE)
async def delete_income(
        request: Request,
        ids: Annotated[str, Query(description='要删除的ID，多个用逗号分隔')],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    income_ids = [int(i) for i in ids.split(',')]
    result =  await InvoiceService.income_del(query_db, income_ids)
    return ResponseUtil.success(msg=result.message)

@finance_invoice_controller.get(
    "/income/detail/{invoice_id}",
    summary='获取发票回款记录',
    description='用于获取发票回款记录',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:invoice:query')],
)
async def get_income_detail(
        request: Request,
        invoice_id: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
)->Response:
    result =  await InvoiceService.income_get_incomes(query_db, invoice_id)
    return ResponseUtil.success(data=result)

