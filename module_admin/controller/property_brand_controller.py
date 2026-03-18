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
from module_admin.entity.vo.property_brand_vo import (
    AddPropertyBrandModel,
    DeletePropertyBrandModel,
    EditPropertyBrandModel,
    PropertyBrandModel,
    PropertyBrandPageQueryModel,
)
from module_admin.service.property_brand_service import PropertyBrandService
from utils.log_util import logger
from utils.response_util import ResponseUtil

property_brand_controller = APIRouterPro(
    prefix='/system/propertyBrand', order_num=24, tags=['系统管理 - 资产品牌管理'], dependencies=[PreAuthDependency()]
)


@property_brand_controller.get(
    '/list',
    summary='获取资产品牌分页列表接口',
    description='用于获取资产品牌分页列表',
    response_model=PageResponseModel[PropertyBrandModel],
    dependencies=[UserInterfaceAuthDependency('system:propertyBrand:list')],
)
async def get_system_property_brand_list(
        request: Request,
        property_brand_page_query: Annotated[PropertyBrandPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    # 获取分页数据
    property_brand_page_query_result = await PropertyBrandService.get_property_brand_list_services(
        query_db, property_brand_page_query, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=property_brand_page_query_result)


@property_brand_controller.get(
    '/all',
    summary='获取所有资产品牌列表接口',
    description='用于获取所有资产品牌列表（不分页）',
    response_model=DataResponseModel[list[PropertyBrandModel]],
    dependencies=[UserInterfaceAuthDependency('system:propertyBrand:list')],
)
async def get_system_property_brand_all(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    # 获取所有数据
    property_brand_all_result = await PropertyBrandService.get_all_property_brand_list_services(query_db)
    logger.info('获取成功')

    return ResponseUtil.success(data=property_brand_all_result)


@property_brand_controller.post(
    '',
    summary='新增资产品牌接口',
    description='用于新增资产品牌',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:propertyBrand:add')],
)
@ValidateFields(validate_model='add_property_brand')
@Log(title='资产品牌管理', business_type=BusinessType.INSERT)
async def add_system_property_brand(
        request: Request,
        add_property_brand: AddPropertyBrandModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    add_property_brand_result = await PropertyBrandService.add_property_brand_services(request, query_db, add_property_brand)
    logger.info(add_property_brand_result.message)

    return ResponseUtil.success(msg=add_property_brand_result.message)


@property_brand_controller.put(
    '',
    summary='编辑资产品牌接口',
    description='用于编辑资产品牌',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:propertyBrand:edit')],
)
@ValidateFields(validate_model='edit_property_brand')
@Log(title='资产品牌管理', business_type=BusinessType.UPDATE)
async def edit_system_property_brand(
        request: Request,
        edit_property_brand: EditPropertyBrandModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    edit_property_brand_result = await PropertyBrandService.edit_property_brand_services(request, query_db, edit_property_brand)
    logger.info(edit_property_brand_result.message)

    return ResponseUtil.success(msg=edit_property_brand_result.message)


@property_brand_controller.delete(
    '/{id}',
    summary='删除资产品牌接口',
    description='用于删除资产品牌',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:propertyBrand:remove')],
)
@Log(title='资产品牌管理', business_type=BusinessType.DELETE)
async def delete_system_property_brand(
        request: Request,
        id: Annotated[int, Path(description='需要删除的品牌 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_property_brand = DeletePropertyBrandModel(id=id)
    delete_property_brand_result = await PropertyBrandService.delete_property_brand_services(
        request, query_db, delete_property_brand
    )
    logger.info(delete_property_brand_result.message)

    return ResponseUtil.success(msg=delete_property_brand_result.message)


@property_brand_controller.put(
    '/set',
    summary='设置资产品牌状态接口',
    description='用于设置资产品牌状态（禁用/启用）',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:propertyBrand:edit')],
)
@Log(title='资产品牌管理', business_type=BusinessType.UPDATE)
async def set_system_property_brand_status(
        request: Request,
        set_property_brand: EditPropertyBrandModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    set_property_brand_result = await PropertyBrandService.set_property_brand_status_services(
        request, query_db, set_property_brand
    )
    logger.info(set_property_brand_result.message)

    return ResponseUtil.success(msg=set_property_brand_result.message)


@property_brand_controller.get(
    '/{id}',
    summary='获取资产品牌详情接口',
    description='用于获取指定资产品牌的详细信息',
    response_model=DataResponseModel[PropertyBrandModel],
    dependencies=[UserInterfaceAuthDependency('system:propertyBrand:query')],
)
async def query_detail_system_property_brand(
        request: Request,
        id: Annotated[int, Path(description='品牌 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_property_brand_result = await PropertyBrandService.property_brand_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的信息成功')

    return ResponseUtil.success(data=detail_property_brand_result)
