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
from module_admin.entity.vo.customer_chance_vo import (
    AddCustomerChanceModel,
    DeleteCustomerChanceModel,
    EditCustomerChanceModel,
    CustomerChanceModel,
    CustomerChancePageQueryModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.customer_chance_service import CustomerChanceService
from utils.log_util import logger
from utils.response_util import ResponseUtil

customer_chance_controller = APIRouterPro(
    prefix='/system/customerChance', order_num=24, tags=['系统管理 - 客户机会管理'], dependencies=[PreAuthDependency()]
)


@customer_chance_controller.get(
    '/list',
    summary='获取客户机会分页列表接口',
    description='用于获取客户机会分页列表',
    response_model=PageResponseModel[CustomerChanceModel],
    dependencies=[UserInterfaceAuthDependency('system:customerChance:list')],
)
async def get_system_customer_chance_list(
        request: Request,
        customer_chance_page_query: Annotated[CustomerChancePageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    # 获取分页数据
    customer_chance_page_query_result = await CustomerChanceService.get_customer_chance_list_services(
        query_db, customer_chance_page_query, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=customer_chance_page_query_result)


@customer_chance_controller.post(
    '',
    summary='新增客户机会接口',
    description='用于新增客户机会',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:customerChance:add')],
)
@ValidateFields(validate_model='add_customer_chance')
@Log(title='客户机会管理', business_type=BusinessType.INSERT)
async def add_system_customer_chance(
        request: Request,
        add_customer_chance: AddCustomerChanceModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    add_customer_chance_result = await CustomerChanceService.add_customer_chance_services(
        request, query_db, add_customer_chance, current_user.user.user_id
    )
    logger.info(add_customer_chance_result.message)

    return ResponseUtil.success(msg=add_customer_chance_result.message)


@customer_chance_controller.put(
    '',
    summary='编辑客户机会接口',
    description='用于编辑客户机会',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:customerChance:edit')],
)
@ValidateFields(validate_model='edit_customer_chance')
@Log(title='客户机会管理', business_type=BusinessType.UPDATE)
async def edit_system_customer_chance(
        request: Request,
        edit_customer_chance: EditCustomerChanceModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    edit_customer_chance_result = await CustomerChanceService.edit_customer_chance_services(
        request, query_db, edit_customer_chance
    )
    logger.info(edit_customer_chance_result.message)

    return ResponseUtil.success(msg=edit_customer_chance_result.message)


@customer_chance_controller.delete(
    '/{id}',
    summary='删除客户机会接口',
    description='用于删除客户机会',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:customerChance:remove')],
)
@Log(title='客户机会管理', business_type=BusinessType.DELETE)
async def delete_system_customer_chance(
        request: Request,
        id: Annotated[int, Path(description='需要删除的机会 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_customer_chance = DeleteCustomerChanceModel(id=id)
    delete_customer_chance_result = await CustomerChanceService.delete_customer_chance_services(
        request, query_db, delete_customer_chance
    )
    logger.info(delete_customer_chance_result.message)

    return ResponseUtil.success(msg=delete_customer_chance_result.message)


@customer_chance_controller.get(
    '/{id}',
    summary='获取客户机会详情接口',
    description='用于获取指定客户机会的详细信息',
    response_model=DataResponseModel[CustomerChanceModel],
    dependencies=[UserInterfaceAuthDependency('system:customerChance:query')],
)
async def query_detail_system_customer_chance(
        request: Request,
        id: Annotated[int, Path(description='机会 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_customer_chance_result = await CustomerChanceService.customer_chance_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的信息成功')

    return ResponseUtil.success(data=detail_customer_chance_result)
