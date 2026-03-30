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
from module_admin.entity.vo.customer_contact_vo import (
    AddCustomerContactModel,
    DeleteCustomerContactModel,
    EditCustomerContactModel,
    CustomerContactModel,
    CustomerContactPageQueryModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.customer_contact_service import CustomerContactService
from utils.log_util import logger
from utils.response_util import ResponseUtil

customer_contact_controller = APIRouterPro(
    prefix='/system/customer-contact', order_num=28, tags=['系统管理 - 客户联系人管理'], dependencies=[PreAuthDependency()]
)


@customer_contact_controller.get(
    '/list',
    summary='获取联系人分页列表接口',
    description='用于获取联系人分页列表',
    response_model=PageResponseModel[CustomerContactModel],
    dependencies=[UserInterfaceAuthDependency('system:customer-contact:list')],
)
async def get_system_customer_contact_list(
        request: Request,
        customer_contact_page_query: Annotated[CustomerContactPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    user_id = current_user.user.user_id if current_user.user and current_user.user.user_id else 0
    customer_contact_page_query_result = await CustomerContactService.get_customer_contact_list_services(
        query_db, customer_contact_page_query, user_id, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=customer_contact_page_query_result)


@customer_contact_controller.post(
    '',
    summary='新增联系人接口',
    description='用于新增联系人',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:customer-contact:add')],
)
@ValidateFields(validate_model='add_customer_contact')
@Log(title='客户联系人管理', business_type=BusinessType.INSERT)
async def add_system_customer_contact(
        request: Request,
        add_customer_contact: AddCustomerContactModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    add_customer_contact_result = await CustomerContactService.add_customer_contact_services(
        request, query_db, add_customer_contact, current_user.user.user_id
    )
    logger.info(add_customer_contact_result.message)

    return ResponseUtil.success(msg=add_customer_contact_result.message)


@customer_contact_controller.put(
    '',
    summary='编辑联系人接口',
    description='用于编辑联系人',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:customer-contact:edit')],
)
@ValidateFields(validate_model='edit_customer_contact')
@Log(title='客户联系人管理', business_type=BusinessType.UPDATE)
async def edit_system_customer_contact(
        request: Request,
        edit_customer_contact: EditCustomerContactModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    edit_customer_contact_result = await CustomerContactService.edit_customer_contact_services(
        request, query_db, edit_customer_contact
    )
    logger.info(edit_customer_contact_result.message)

    return ResponseUtil.success(msg=edit_customer_contact_result.message)


@customer_contact_controller.delete(
    '/{id}',
    summary='删除联系人接口',
    description='用于删除联系人',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:customer-contact:remove')],
)
@Log(title='客户联系人管理', business_type=BusinessType.DELETE)
async def delete_system_customer_contact(
        request: Request,
        id: Annotated[int, Path(description='需要删除的联系人 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_customer_contact = DeleteCustomerContactModel(id=id)
    delete_customer_contact_result = await CustomerContactService.delete_customer_contact_services(
        request, query_db, delete_customer_contact
    )
    logger.info(delete_customer_contact_result.message)

    return ResponseUtil.success(msg=delete_customer_contact_result.message)


@customer_contact_controller.get(
    '/{id}',
    summary='获取联系人详情接口',
    description='用于获取指定联系人的详细信息',
    response_model=DataResponseModel[CustomerContactModel],
    dependencies=[UserInterfaceAuthDependency('system:customer-contact:query')],
)
async def query_detail_system_customer_contact(
        request: Request,
        id: Annotated[int, Path(description='联系人 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_customer_contact_result = await CustomerContactService.customer_contact_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的信息成功')

    return ResponseUtil.success(data=detail_customer_contact_result)

