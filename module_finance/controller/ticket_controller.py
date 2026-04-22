from fastapi import File, Form, Path, Query, Request, Response, UploadFile,Body
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from common.aspect.data_scope import DataScopeDependency
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency, CurrentUserDependency
from common.router import APIRouterPro
from module_finance.entity.do.ticket_do import OaTicket
from module_finance.entity.vo.ticket_vo import OaTicketBaseModel, OaTicketPageQueryModel, OaTicketPaymentBaseModel
from module_finance.service.ticket_service import TicketService
from module_admin.entity.vo.user_vo import (
    CurrentUserModel
)
from utils.response_util import ResponseUtil

finance_invoice_controller = APIRouterPro(
    prefix='/finance/ticket', order_num=3, tags=['财务管理-收票管理'], dependencies=[PreAuthDependency()]
)

@finance_invoice_controller.get(
    "/list",
    summary='获取收票管理列表',
    description='用于获取收票管理列表',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:payment:query')],
)
async def get_page_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaTicketPageQueryModel, Query()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaTicket)],
) -> Response:
    result = await TicketService.get_page_list_service(query_db,query_object,data_scope_sql,True)
    return ResponseUtil.success(model_content=result)

@finance_invoice_controller.get(
    "/user/list",
    summary='获取用户收票管理列表',
    description='用于用户获取收票管理列表',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:payment:query')],
)
async def get_page_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaTicketPageQueryModel, Query()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaTicket)],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    user_id = current_user.user.user_id
    query_object.admin_id = user_id
    result = await TicketService.get_page_list_service(query_db,query_object,data_scope_sql,True)
    return ResponseUtil.success(model_content=result)

@finance_invoice_controller.post(
    "/add",
    summary='新增收票管理',
    description='用于新增收票管理',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:payment:add')],
)
async def add(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaTicketBaseModel, Body()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    query_object.admin_id = current_user.user.user_id
    query_object.did = current_user.user.dept.dept_id
    result = await TicketService.add_service(query_db, query_object)
    return ResponseUtil.success(msg=result.message)

@finance_invoice_controller.put(
    "/add",
    summary='更新收票管理',
    description='用于更新收票管理',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:payment:update')],
)
async def add_ticket(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: Annotated[OaTicketBaseModel, Body()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
)->Response:
    model.admin_id = current_user.user.user_id
    model.did = current_user.user.dept.dept_id
    result = await TicketService().add_service(query_db, model)
    return ResponseUtil.success(msg=result.message)

@finance_invoice_controller.get(
    "/detail/{id}",
    summary='获取收票管理详情',
    description='用于获取收票管理详情',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:payment:query')],
)
async def get_expense(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result = await TicketService.get_info_service(query_db, id)
    return ResponseUtil.success(data=result)

@finance_invoice_controller.delete(
    "/delete/{id}",
    summary='删除收票管理',
    description='用于删除收票管理',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:payment:delete')],
)
async def delete_expense(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result =  await TicketService.del_by_id(query_db, id)
    return ResponseUtil.success(msg=result.message)

# @finance_invoice_controller.put(
#     "/review",
#     summary='审核',
#     description='用于审核',
#     response_model=None,
#     dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:payment:pass')],
# )
# async def review(
#         request: Request,
#         query_db: Annotated[AsyncSession, DBSessionDependency()],
#         data: Annotated[OaTicketBaseModel, Body()],
#         current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
# ) -> Response:
#     userId = current_user.user.user_id
#     result =  await TicketService.review(query_db, data, userId)
#     return ResponseUtil.success(msg=result.message)

@finance_invoice_controller.put(
    "/pay",
    summary='打款',
    description='用于打款',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:payment:pay')],
)
async def payment(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        data: Annotated[OaTicketBaseModel, Body()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    userId = current_user.user.user_id
    result =  await TicketService.payment(query_db, data, userId)
    return ResponseUtil.success(msg=result.message)

@finance_invoice_controller.put(
    "/openStatus",
    summary='开票状态',
    description='用于开票状态',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:payment:edit')],
)
async def open_status(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        data: Annotated[OaTicketBaseModel, Body()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    data.admin_id = current_user.user.user_id
    result =  await TicketService.open_status(query_db, data)
    return ResponseUtil.success(msg=result.message)




# ------------------------------------  收票付款管理  ------------------------------------
@finance_invoice_controller.post(
    "/add_payment",
    summary='添加收票付款记录',
    description='用于添加收票付款记录',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:payment:add')],
)
async def add_payment(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        data: Annotated[list[OaTicketPaymentBaseModel], Body()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    userId = current_user.user.user_id
    result =  await TicketService.payment_add(query_db, data, userId)
    return ResponseUtil.success(msg=result.message)

@finance_invoice_controller.delete(
    "/delete_payment",
    summary='删除收票付款记录',
    description='用于删除收票付款记录',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:payment:delete')],
)
async def delete_payment(
        request: Request,
        ids: Annotated[str, Query(description='要删除的ID，多个用逗号分隔')],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    income_ids = [int(i) for i in ids.split(',')]
    result =  await TicketService.payment_del(query_db, income_ids)
    return ResponseUtil.success(msg=result.message)

@finance_invoice_controller.get(
    "/payment/detail/{invoice_id}",
    summary='获取收票付款记录',
    description='用于获取收票付款记录',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:payment:query')],
)
async def get_income_detail(
        request: Request,
        invoice_id: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
)->Response:
    result =  await TicketService.ticket_get_payment(query_db, invoice_id)
    return ResponseUtil.success(data=result)

