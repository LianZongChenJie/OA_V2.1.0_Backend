from typing import Annotated

from fastapi import Path, Query, Request, Response
from pydantic_validation_decorator import ValidateFields
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import DataResponseModel, PageResponseModel, ResponseBaseModel
from module_admin.entity.vo.customer_trace_vo import (
    AddCustomerTraceModel,
    DeleteCustomerTraceModel,
    EditCustomerTraceModel,
    CustomerTraceModel,
    CustomerTracePageQueryModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.customer_trace_service import CustomerTraceService
from utils.log_util import logger
from utils.response_util import ResponseUtil

customer_trace_controller = APIRouterPro(
    prefix='/system/customerTrace', order_num=29, tags=['系统管理 - 客户跟进记录管理'], dependencies=[PreAuthDependency()]
)


@customer_trace_controller.get(
    '/list',
    summary='获取客户跟进记录分页列表接口',
    description='用于获取客户跟进记录分页列表',
    response_model=PageResponseModel[CustomerTraceModel],
    dependencies=[UserInterfaceAuthDependency('system:customerTrace:list')],
)
async def get_system_customer_trace_list(
        request: Request,
        customer_trace_page_query: Annotated[CustomerTracePageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    # 获取分页数据
    customer_trace_page_query_result = await CustomerTraceService.get_customer_trace_list_services(
        query_db,
        customer_trace_page_query,
        current_user.user.user_id,
        current_user.user.auth_dids or '',
        current_user.user.son_dids or '',
        current_user.user.admin,
        is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=customer_trace_page_query_result)


@customer_trace_controller.post(
    '',
    summary='新增客户跟进记录接口',
    description='用于新增客户跟进记录',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:customerTrace:add')],
)
@ValidateFields(validate_model='add_customer_trace')
@Log(title='客户跟进记录管理', business_type=BusinessType.INSERT)
async def add_system_customer_trace(
        request: Request,
        add_customer_trace: AddCustomerTraceModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    add_customer_trace_result = await CustomerTraceService.add_customer_trace_services(
        request, query_db, add_customer_trace, current_user.user.user_id
    )
    logger.info(add_customer_trace_result.message)

    return ResponseUtil.success(msg=add_customer_trace_result.message)


@customer_trace_controller.put(
    '',
    summary='编辑客户跟进记录接口',
    description='用于编辑客户跟进记录',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:customerTrace:edit')],
)
@ValidateFields(validate_model='edit_customer_trace')
@Log(title='客户跟进记录管理', business_type=BusinessType.UPDATE)
async def edit_system_customer_trace(
        request: Request,
        edit_customer_trace: EditCustomerTraceModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    edit_customer_trace_result = await CustomerTraceService.edit_customer_trace_services(
        request, query_db, edit_customer_trace
    )
    logger.info(edit_customer_trace_result.message)

    return ResponseUtil.success(msg=edit_customer_trace_result.message)


@customer_trace_controller.delete(
    '/{id}',
    summary='删除客户跟进记录接口',
    description='用于删除客户跟进记录',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:customerTrace:remove')],
)
@Log(title='客户跟进记录管理', business_type=BusinessType.DELETE)
async def delete_system_customer_trace(
        request: Request,
        id: Annotated[int, Path(description='需要删除的跟进记录 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_customer_trace = DeleteCustomerTraceModel(id=id)
    delete_customer_trace_result = await CustomerTraceService.delete_customer_trace_services(
        request, query_db, delete_customer_trace
    )
    logger.info(delete_customer_trace_result.message)

    return ResponseUtil.success(msg=delete_customer_trace_result.message)


@customer_trace_controller.get(
    '/{id}',
    summary='获取客户跟进记录详情接口',
    description='用于获取指定客户跟进记录的详细信息',
    response_model=DataResponseModel[CustomerTraceModel],
    dependencies=[UserInterfaceAuthDependency('system:customerTrace:query')],
)
async def query_detail_system_customer_trace(
        request: Request,
        id: Annotated[int, Path(description='跟进记录 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_customer_trace_result = await CustomerTraceService.customer_trace_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的信息成功')

    return ResponseUtil.success(data=detail_customer_trace_result)

