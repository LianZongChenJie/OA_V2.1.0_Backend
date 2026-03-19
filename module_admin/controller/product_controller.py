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
from module_admin.entity.vo.product_vo import (
    AddProductModel,
    DeleteProductModel,
    EditProductModel,
    ProductModel,
    ProductPageQueryModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.product_service import ProductService
from utils.log_util import logger
from utils.response_util import ResponseUtil

product_controller = APIRouterPro(
    prefix='/system/product', order_num=25, tags=['系统管理 - 产品管理'], dependencies=[PreAuthDependency()]
)


@product_controller.get(
    '/list',
    summary='获取产品分页列表接口',
    description='用于获取产品分页列表',
    response_model=PageResponseModel[ProductModel],
    dependencies=[UserInterfaceAuthDependency('system:product:list')],
)
async def get_system_product_list(
        request: Request,
        product_page_query: Annotated[ProductPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    # 获取分页数据
    product_page_query_result = await ProductService.get_product_list_services(
        query_db, product_page_query, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=product_page_query_result)


@product_controller.post(
    '',
    summary='新增产品接口',
    description='用于新增产品',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:product:add')],
)
@ValidateFields(validate_model='add_product')
@Log(title='产品管理', business_type=BusinessType.INSERT)
async def add_system_product(
        request: Request,
        add_product: AddProductModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    user_id = current_user.user.user_id if current_user.user and current_user.user.user_id else 0
    add_product_result = await ProductService.add_product_services(
        request, query_db, add_product, user_id
    )
    logger.info(add_product_result.message)

    return ResponseUtil.success(msg=add_product_result.message)


@product_controller.put(
    '',
    summary='编辑产品接口',
    description='用于编辑产品',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:product:edit')],
)
@ValidateFields(validate_model='edit_product')
@Log(title='产品管理', business_type=BusinessType.UPDATE)
async def edit_system_product(
        request: Request,
        edit_product: EditProductModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    edit_product_result = await ProductService.edit_product_services(request, query_db, edit_product)
    logger.info(edit_product_result.message)

    return ResponseUtil.success(msg=edit_product_result.message)


@product_controller.delete(
    '/{id}',
    summary='删除产品接口',
    description='用于删除产品',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:product:remove')],
)
@Log(title='产品管理', business_type=BusinessType.DELETE)
async def delete_system_product(
        request: Request,
        id: Annotated[int, Path(description='需要删除的产品 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_product = DeleteProductModel(id=id)
    delete_product_result = await ProductService.delete_product_services(
        request, query_db, delete_product
    )
    logger.info(delete_product_result.message)

    return ResponseUtil.success(msg=delete_product_result.message)


@product_controller.put(
    '/set',
    summary='设置产品状态接口',
    description='用于设置产品状态（禁用/启用）',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:product:edit')],
)
@Log(title='产品管理', business_type=BusinessType.UPDATE)
async def set_system_product_status(
        request: Request,
        set_product: EditProductModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    set_product_result = await ProductService.set_product_status_services(
        request, query_db, set_product
    )
    logger.info(set_product_result.message)

    return ResponseUtil.success(msg=set_product_result.message)


@product_controller.get(
    '/{id}',
    summary='获取产品详情接口',
    description='用于获取指定产品的详细信息',
    response_model=DataResponseModel[ProductModel],
    dependencies=[UserInterfaceAuthDependency('system:product:query')],
)
async def query_detail_system_product(
        request: Request,
        id: Annotated[int, Path(description='产品 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_product_result = await ProductService.product_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的信息成功')

    return ResponseUtil.success(data=detail_product_result)

