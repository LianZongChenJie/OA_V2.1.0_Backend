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
from module_admin.entity.vo.property_unit_vo import (
    AddPropertyUnitModel,
    DeletePropertyUnitModel,
    EditPropertyUnitModel,
    PropertyUnitModel,
    PropertyUnitPageQueryModel,
)
from module_admin.service.property_unit_service import PropertyUnitService
from utils.log_util import logger
from utils.response_util import ResponseUtil

property_unit_controller = APIRouterPro(
    prefix='/system/propertyUnit', order_num=25, tags=['系统管理 - 资产单位管理'], dependencies=[PreAuthDependency()]
)


@property_unit_controller.get(
    '/list',
    summary='获取资产单位分页列表接口',
    description='用于获取资产单位分页列表',
    response_model=PageResponseModel[PropertyUnitModel],
    dependencies=[UserInterfaceAuthDependency('system:propertyUnit:list')],
)
async def get_system_property_unit_list(
        request: Request,
        property_unit_page_query: Annotated[PropertyUnitPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    # 获取分页数据
    property_unit_page_query_result = await PropertyUnitService.get_property_unit_list_services(
        query_db, property_unit_page_query, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=property_unit_page_query_result)


@property_unit_controller.get(
    '/all',
    summary='获取所有资产单位列表接口',
    description='用于获取所有资产单位列表（不分页）',
    response_model=DataResponseModel[list[PropertyUnitModel]],
    dependencies=[UserInterfaceAuthDependency('system:propertyUnit:list')],
)
async def get_system_property_unit_all(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    # 获取所有数据
    property_unit_all_result = await PropertyUnitService.get_all_property_unit_list_services(query_db)
    logger.info('获取成功')

    return ResponseUtil.success(data=property_unit_all_result)


@property_unit_controller.post(
    '',
    summary='新增资产单位接口',
    description='用于新增资产单位',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:propertyUnit:add')],
)
@ValidateFields(validate_model='add_property_unit')
@Log(title='资产单位管理', business_type=BusinessType.INSERT)
async def add_system_property_unit(
        request: Request,
        add_property_unit: AddPropertyUnitModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    add_property_unit_result = await PropertyUnitService.add_property_unit_services(request, query_db, add_property_unit)
    logger.info(add_property_unit_result.message)

    return ResponseUtil.success(msg=add_property_unit_result.message)


@property_unit_controller.put(
    '',
    summary='编辑资产单位接口',
    description='用于编辑资产单位',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:propertyUnit:edit')],
)
@ValidateFields(validate_model='edit_property_unit')
@Log(title='资产单位管理', business_type=BusinessType.UPDATE)
async def edit_system_property_unit(
        request: Request,
        edit_property_unit: EditPropertyUnitModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    edit_property_unit_result = await PropertyUnitService.edit_property_unit_services(request, query_db, edit_property_unit)
    logger.info(edit_property_unit_result.message)

    return ResponseUtil.success(msg=edit_property_unit_result.message)


@property_unit_controller.delete(
    '/{id}',
    summary='删除资产单位接口',
    description='用于删除资产单位',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:propertyUnit:remove')],
)
@Log(title='资产单位管理', business_type=BusinessType.DELETE)
async def delete_system_property_unit(
        request: Request,
        id: Annotated[int, Path(description='需要删除的单位 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_property_unit = DeletePropertyUnitModel(id=id)
    delete_property_unit_result = await PropertyUnitService.delete_property_unit_services(
        request, query_db, delete_property_unit
    )
    logger.info(delete_property_unit_result.message)

    return ResponseUtil.success(msg=delete_property_unit_result.message)


@property_unit_controller.put(
    '/set',
    summary='设置资产单位状态接口',
    description='用于设置资产单位状态（禁用/启用）',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:propertyUnit:edit')],
)
@Log(title='资产单位管理', business_type=BusinessType.UPDATE)
async def set_system_property_unit_status(
        request: Request,
        set_property_unit: EditPropertyUnitModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    set_property_unit_result = await PropertyUnitService.set_property_unit_status_services(
        request, query_db, set_property_unit
    )
    logger.info(set_property_unit_result.message)

    return ResponseUtil.success(msg=set_property_unit_result.message)


@property_unit_controller.get(
    '/{id}',
    summary='获取资产单位详情接口',
    description='用于获取指定资产单位的详细信息',
    response_model=DataResponseModel[PropertyUnitModel],
    dependencies=[UserInterfaceAuthDependency('system:propertyUnit:query')],
)
async def query_detail_system_property_unit(
        request: Request,
        id: Annotated[int, Path(description='单位 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_property_unit_result = await PropertyUnitService.property_unit_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的信息成功')

    return ResponseUtil.success(data=detail_property_unit_result)
