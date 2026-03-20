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
from module_admin.entity.vo.purchased_vo import (
    AddPurchasedModel,
    DeletePurchasedModel,
    EditPurchasedModel,
    PurchasedModel,
    PurchasedPageQueryModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.purchased_service import PurchasedService
from utils.log_util import logger
from utils.response_util import ResponseUtil

purchased_controller = APIRouterPro(
    prefix='/system/purchased', order_num=26, tags=['系统管理 - 采购品管理'], dependencies=[PreAuthDependency()]
)


@purchased_controller.get(
    '/list',
    summary='获取采购品分页列表接口',
    description='用于获取采购品分页列表',
    response_model=PageResponseModel[PurchasedModel],
    dependencies=[UserInterfaceAuthDependency('system:purchased:list')],
)
async def get_system_purchased_list(
        request: Request,
        purchased_page_query: Annotated[PurchasedPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    # 获取分页数据
    purchased_page_query_result = await PurchasedService.get_purchased_list_services(
        query_db, purchased_page_query, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=purchased_page_query_result)


@purchased_controller.post(
    '',
    summary='新增采购品接口',
    description='用于新增采购品',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:purchased:add')],
)
@ValidateFields(validate_model='add_purchased')
@Log(title='采购品管理', business_type=BusinessType.INSERT)
async def add_system_purchased(
        request: Request,
        add_purchased: AddPurchasedModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    # 从 current_user.user.user_id 获取用户 ID
    user_id = current_user.user.user_id if current_user.user and current_user.user.user_id else 0
    add_purchased_result = await PurchasedService.add_purchased_services(
        request, query_db, add_purchased, user_id
    )
    logger.info(add_purchased_result.message)

    return ResponseUtil.success(msg=add_purchased_result.message)


@purchased_controller.put(
    '',
    summary='编辑采购品接口',
    description='用于编辑采购品',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:purchased:edit')],
)
@ValidateFields(validate_model='edit_purchased')
@Log(title='采购品管理', business_type=BusinessType.UPDATE)
async def edit_system_purchased(
        request: Request,
        edit_purchased: EditPurchasedModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    edit_purchased_result = await PurchasedService.edit_purchased_services(request, query_db, edit_purchased)
    logger.info(edit_purchased_result.message)

    return ResponseUtil.success(msg=edit_purchased_result.message)


@purchased_controller.delete(
    '/{ids}',
    summary='删除采购品接口',
    description='用于删除采购品',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:purchased:remove')],
)
@Log(title='采购品管理', business_type=BusinessType.DELETE)
async def delete_system_purchased(
        request: Request,
        ids: Annotated[str, Path(description='需要删除的采购品 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_purchased = DeletePurchasedModel(ids=ids)
    delete_purchased_result = await PurchasedService.delete_purchased_services(
        request, query_db, delete_purchased
    )
    logger.info(delete_purchased_result.message)

    return ResponseUtil.success(msg=delete_purchased_result.message)


@purchased_controller.put(
    '/set',
    summary='设置采购品状态接口',
    description='用于设置采购品状态（禁用/启用）',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:purchased:edit')],
)
@Log(title='采购品管理', business_type=BusinessType.UPDATE)
async def set_system_purchased_status(
        request: Request,
        set_purchased: EditPurchasedModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    set_purchased_result = await PurchasedService.set_purchased_status_services(
        request, query_db, set_purchased
    )
    logger.info(set_purchased_result.message)

    return ResponseUtil.success(msg=set_purchased_result.message)


@purchased_controller.get(
    '/{id}',
    summary='获取采购品详情接口',
    description='用于获取指定采购品的详细信息',
    response_model=DataResponseModel[PurchasedModel],
    dependencies=[UserInterfaceAuthDependency('system:purchased:query')],
)
async def query_detail_system_purchased(
        request: Request,
        id: Annotated[int, Path(description='采购品 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_purchased_result = await PurchasedService.purchased_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的信息成功')

    return ResponseUtil.success(data=detail_purchased_result)
