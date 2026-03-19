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
from module_admin.entity.vo.product_cate_vo import (
    AddProductCateModel,
    DeleteProductCateModel,
    EditProductCateModel,
    ProductCateModel,
    ProductCatePageQueryModel,
    ProductCateTreeModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.product_cate_service import ProductCateService
from utils.log_util import logger
from utils.response_util import ResponseUtil

product_cate_controller = APIRouterPro(
    prefix='/system/productCate', order_num=24, tags=['系统管理 - 产品分类管理'], dependencies=[PreAuthDependency()]
)


@product_cate_controller.get(
    '/tree',
    summary='获取产品分类树接口',
    description='用于获取产品分类树形结构数据',
    response_model=list[ProductCateTreeModel],
    dependencies=[UserInterfaceAuthDependency('system:productCate:tree')],
)
async def get_system_product_cate_tree(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    product_cate_tree_result = await ProductCateService.get_product_cate_tree_services(query_db)
    logger.info('获取成功')

    return ResponseUtil.success(data=product_cate_tree_result)


@product_cate_controller.get(
    '/list',
    summary='获取产品分类分页列表接口',
    description='用于获取产品分类分页列表',
    response_model=PageResponseModel[ProductCateModel],
    dependencies=[UserInterfaceAuthDependency('system:productCate:list')],
)
async def get_system_product_cate_list(
        request: Request,
        product_cate_page_query: Annotated[ProductCatePageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    # 获取分页数据
    product_cate_page_query_result = await ProductCateService.get_product_cate_list_services(
        query_db, product_cate_page_query, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=product_cate_page_query_result)


@product_cate_controller.post(
    '',
    summary='新增产品分类接口',
    description='用于新增产品分类',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:productCate:add')],
)
@ValidateFields(validate_model='add_product_cate')
@Log(title='产品分类管理', business_type=BusinessType.INSERT)
async def add_system_product_cate(
        request: Request,
        add_product_cate: AddProductCateModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    # 从 current_user.user.user_id 获取用户 ID
    user_id = current_user.user.user_id if current_user.user and current_user.user.user_id else 0
    add_product_cate_result = await ProductCateService.add_product_cate_services(
        request, query_db, add_product_cate, user_id
    )
    logger.info(add_product_cate_result.message)

    return ResponseUtil.success(msg=add_product_cate_result.message)


@product_cate_controller.put(
    '',
    summary='编辑产品分类接口',
    description='用于编辑产品分类',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:productCate:edit')],
)
@ValidateFields(validate_model='edit_product_cate')
@Log(title='产品分类管理', business_type=BusinessType.UPDATE)
async def edit_system_product_cate(
        request: Request,
        edit_product_cate: EditProductCateModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    edit_product_cate_result = await ProductCateService.edit_product_cate_services(
        request, query_db, edit_product_cate
    )
    logger.info(edit_product_cate_result.message)

    return ResponseUtil.success(msg=edit_product_cate_result.message)


@product_cate_controller.delete(
    '/{id}',
    summary='删除产品分类接口',
    description='用于删除产品分类',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:productCate:remove')],
)
@Log(title='产品分类管理', business_type=BusinessType.DELETE)
async def delete_system_product_cate(
        request: Request,
        id: Annotated[int, Path(description='需要删除的产品分类 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_product_cate = DeleteProductCateModel(id=id)
    delete_product_cate_result = await ProductCateService.delete_product_cate_services(
        request, query_db, delete_product_cate
    )
    logger.info(delete_product_cate_result.message)

    return ResponseUtil.success(msg=delete_product_cate_result.message)


@product_cate_controller.put(
    '/set',
    summary='设置产品分类状态接口',
    description='用于设置产品分类状态（禁用/启用）',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:productCate:edit')],
)
@Log(title='产品分类管理', business_type=BusinessType.UPDATE)
async def set_system_product_cate_status(
        request: Request,
        set_product_cate: EditProductCateModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    set_product_cate_result = await ProductCateService.set_product_cate_status_services(
        request, query_db, set_product_cate
    )
    logger.info(set_product_cate_result.message)

    return ResponseUtil.success(msg=set_product_cate_result.message)


@product_cate_controller.get(
    '/{id}',
    summary='获取产品分类详情接口',
    description='用于获取指定产品分类的详细信息',
    response_model=DataResponseModel[ProductCateModel],
    dependencies=[UserInterfaceAuthDependency('system:productCate:query')],
)
async def query_detail_system_product_cate(
        request: Request,
        id: Annotated[int, Path(description='产品分类 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_product_cate_result = await ProductCateService.product_cate_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的信息成功')

    return ResponseUtil.success(data=detail_product_cate_result)

