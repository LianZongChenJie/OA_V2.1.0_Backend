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
from module_admin.entity.vo.customer_vo import (
    AddCustomerModel,
    DeleteCustomerModel,
    EditCustomerModel,
    CustomerModel,
    CustomerPageQueryModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.customer_service import CustomerService
from utils.log_util import logger
from utils.response_util import ResponseUtil

customer_controller = APIRouterPro(
    prefix='/system/customer', order_num=27, tags=['系统管理 - 客户管理'], dependencies=[PreAuthDependency()]
)


@customer_controller.get(
    '/list',
    summary='获取客户分页列表接口',
    description='用于获取客户分页列表',
    response_model=PageResponseModel[CustomerModel],
    dependencies=[UserInterfaceAuthDependency('system:customer:list')],
)
async def get_system_customer_list(
        request: Request,
        customer_page_query: Annotated[CustomerPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    user_id = current_user.user.user_id if current_user.user and current_user.user.user_id else 0
    customer_page_query_result = await CustomerService.get_customer_list_services(
        query_db, customer_page_query, user_id, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=customer_page_query_result)


@customer_controller.post(
    '',
    summary='新增客户接口',
    description='用于新增客户',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:customer:add')],
)
@ValidateFields(validate_model='add_customer')
@Log(title='客户管理', business_type=BusinessType.INSERT)
async def add_system_customer(
        request: Request,
        add_customer: AddCustomerModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    add_customer_result = await CustomerService.add_customer_services(
        request, query_db, add_customer, current_user.user.user_id
    )
    logger.info(add_customer_result.message)

    return ResponseUtil.success(msg=add_customer_result.message)


@customer_controller.put(
    '',
    summary='编辑客户接口',
    description='用于编辑客户',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:customer:edit')],
)
@ValidateFields(validate_model='edit_customer')
@Log(title='客户管理', business_type=BusinessType.UPDATE)
async def edit_system_customer(
        request: Request,
        edit_customer: EditCustomerModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    edit_customer_result = await CustomerService.edit_customer_services(request, query_db, edit_customer)
    logger.info(edit_customer_result.message)

    return ResponseUtil.success(msg=edit_customer_result.message)


@customer_controller.delete(
    '/{id}',
    summary='删除客户接口',
    description='用于删除客户',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:customer:remove')],
)
@Log(title='客户管理', business_type=BusinessType.DELETE)
async def delete_system_customer(
        request: Request,
        id: Annotated[int, Path(description='需要删除的客户 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_customer = DeleteCustomerModel(id=id)
    delete_customer_result = await CustomerService.delete_customer_services(
        request, query_db, delete_customer
    )
    logger.info(delete_customer_result.message)

    return ResponseUtil.success(msg=delete_customer_result.message)


@customer_controller.get(
    '/{id}',
    summary='获取客户详情接口',
    description='用于获取指定客户的详细信息',
    response_model=DataResponseModel[CustomerModel],
    dependencies=[UserInterfaceAuthDependency('system:customer:query')],
)
async def query_detail_system_customer(
        request: Request,
        id: Annotated[int, Path(description='客户 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_customer_result = await CustomerService.customer_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的信息成功')

    return ResponseUtil.success(data=detail_customer_result)
