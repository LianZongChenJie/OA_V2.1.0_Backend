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
from module_admin.entity.vo.purchased_cate_vo import (
    AddPurchasedCateModel,
    DeletePurchasedCateModel,
    EditPurchasedCateModel,
    PurchasedCateModel,
    PurchasedCatePageQueryModel,
    PurchasedCateTreeModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.purchased_cate_service import PurchasedCateService
from utils.log_util import logger
from utils.response_util import ResponseUtil

purchased_cate_controller = APIRouterPro(
    prefix='/system/purchasedCate', order_num=25, tags=['系统管理 - 采购品分类管理'], dependencies=[PreAuthDependency()]
)


@purchased_cate_controller.get(
    '/tree',
    summary='获取采购品分类树接口',
    description='用于获取采购品分类树形结构数据',
    response_model=list[PurchasedCateTreeModel],
    dependencies=[UserInterfaceAuthDependency('system:purchasedCate:tree')],
)
async def get_system_purchased_cate_tree(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    purchased_cate_tree_result = await PurchasedCateService.get_purchased_cate_tree_services(query_db)
    logger.info('获取成功')

    return ResponseUtil.success(data=purchased_cate_tree_result)


@purchased_cate_controller.get(
    '/list',
    summary='获取采购品分类分页列表接口',
    description='用于获取采购品分类分页列表',
    response_model=PageResponseModel[PurchasedCateModel],
    dependencies=[UserInterfaceAuthDependency('system:purchasedCate:list')],
)
async def get_system_purchased_cate_list(
        request: Request,
        purchased_cate_page_query: Annotated[PurchasedCatePageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    # 获取分页数据
    purchased_cate_page_query_result = await PurchasedCateService.get_purchased_cate_list_services(
        query_db, purchased_cate_page_query, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=purchased_cate_page_query_result)


@purchased_cate_controller.post(
    '',
    summary='新增采购品分类接口',
    description='用于新增采购品分类',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:purchasedCate:add')],
)
@ValidateFields(validate_model='add_purchased_cate')
@Log(title='采购品分类管理', business_type=BusinessType.INSERT)
async def add_system_purchased_cate(
        request: Request,
        add_purchased_cate: AddPurchasedCateModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    # 从 current_user.user.user_id 获取用户 ID
    user_id = current_user.user.user_id if current_user.user and current_user.user.user_id else 0
    add_purchased_cate_result = await PurchasedCateService.add_purchased_cate_services(
        request, query_db, add_purchased_cate, user_id
    )
    logger.info(add_purchased_cate_result.message)

    return ResponseUtil.success(msg=add_purchased_cate_result.message)


@purchased_cate_controller.put(
    '',
    summary='编辑采购品分类接口',
    description='用于编辑采购品分类',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:purchasedCate:edit')],
)
@ValidateFields(validate_model='edit_purchased_cate')
@Log(title='采购品分类管理', business_type=BusinessType.UPDATE)
async def edit_system_purchased_cate(
        request: Request,
        edit_purchased_cate: EditPurchasedCateModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    edit_purchased_cate_result = await PurchasedCateService.edit_purchased_cate_services(
        request, query_db, edit_purchased_cate
    )
    logger.info(edit_purchased_cate_result.message)

    return ResponseUtil.success(msg=edit_purchased_cate_result.message)


@purchased_cate_controller.delete(
    '/{id}',
    summary='删除采购品分类接口',
    description='用于删除采购品分类',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:purchasedCate:remove')],
)
@Log(title='采购品分类管理', business_type=BusinessType.DELETE)
async def delete_system_purchased_cate(
        request: Request,
        id: Annotated[int, Path(description='需要删除的分类 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_purchased_cate = DeletePurchasedCateModel(id=id)
    delete_purchased_cate_result = await PurchasedCateService.delete_purchased_cate_services(
        request, query_db, delete_purchased_cate
    )
    logger.info(delete_purchased_cate_result.message)

    return ResponseUtil.success(msg=delete_purchased_cate_result.message)


@purchased_cate_controller.put(
    '/set',
    summary='设置采购品分类状态接口',
    description='用于设置采购品分类状态（禁用/启用）',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:purchasedCate:edit')],
)
@Log(title='采购品分类管理', business_type=BusinessType.UPDATE)
async def set_system_purchased_cate_status(
        request: Request,
        set_purchased_cate: EditPurchasedCateModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    set_purchased_cate_result = await PurchasedCateService.set_purchased_cate_status_services(
        request, query_db, set_purchased_cate
    )
    logger.info(set_purchased_cate_result.message)

    return ResponseUtil.success(msg=set_purchased_cate_result.message)


@purchased_cate_controller.get(
    '/{id}',
    summary='获取采购品分类详情接口',
    description='用于获取指定采购品分类的详细信息',
    response_model=DataResponseModel[PurchasedCateModel],
    dependencies=[UserInterfaceAuthDependency('system:purchasedCate:query')],
)
async def query_detail_system_purchased_cate(
        request: Request,
        id: Annotated[int, Path(description='分类 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_purchased_cate_result = await PurchasedCateService.purchased_cate_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的信息成功')

    return ResponseUtil.success(data=detail_purchased_cate_result)
