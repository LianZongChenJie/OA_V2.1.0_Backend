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
from module_admin.entity.vo.property_vo import (
    AddPropertyModel,
    DeletePropertyModel,
    EditPropertyModel,
    PropertyModel,
    PropertyPageQueryModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.property_service import PropertyService
from utils.log_util import logger
from utils.response_util import ResponseUtil

property_controller = APIRouterPro(
    prefix='/system/property', order_num=26, tags=['系统管理 - 资产管理'], dependencies=[PreAuthDependency()]
)

@property_controller.get(
    '/list',
    summary='获取资产分页列表接口',
    description='用于获取资产分页列表',
    response_model=PageResponseModel[PropertyModel],
    dependencies=[UserInterfaceAuthDependency('system:property:list')],
)
async def get_system_property_list(
        request: Request,
        property_page_query: Annotated[PropertyPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    # 获取分页数据
    property_page_query_result = await PropertyService.get_property_list_services(
        query_db, property_page_query, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=property_page_query_result)


@property_controller.get(
    '/all',
    summary='获取所有资产列表接口',
    description='用于获取所有资产列表（不分页）',
    response_model=DataResponseModel[list[PropertyModel]],
    dependencies=[UserInterfaceAuthDependency('system:property:list')],
)
async def get_system_property_all(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    # 获取所有数据
    property_all_result = await PropertyService.get_all_property_list_services(query_db)
    logger.info('获取成功')

    return ResponseUtil.success(data=property_all_result)


@property_controller.post(
    '',
    summary='新增资产接口',
    description='用于新增资产',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:property:add')],
)
@ValidateFields(validate_model='add_property')
@Log(title='资产管理', business_type=BusinessType.INSERT)
async def add_system_property(
        request: Request,
        add_property: AddPropertyModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    add_property.admin_id = current_user.user.user_id
    add_property_result = await PropertyService.add_property_services(request, query_db, add_property)
    logger.info(add_property_result.message)

    return ResponseUtil.success(msg=add_property_result.message)


@property_controller.put(
    '',
    summary='编辑资产接口',
    description='用于编辑资产',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:property:edit')],
)
@ValidateFields(validate_model='edit_property')
@Log(title='资产管理', business_type=BusinessType.UPDATE)
async def edit_system_property(
        request: Request,
        edit_property: EditPropertyModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    edit_property_result = await PropertyService.edit_property_services(request, query_db, edit_property)
    logger.info(edit_property_result.message)

    return ResponseUtil.success(msg=edit_property_result.message)


@property_controller.delete(
    '/{id}',
    summary='删除资产接口',
    description='用于删除资产',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:property:remove')],
)
@Log(title='资产管理', business_type=BusinessType.DELETE)
async def delete_system_property(
        request: Request,
        id: Annotated[int, Path(description='需要删除的资产 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_property = DeletePropertyModel(id=id)
    delete_property_result = await PropertyService.delete_property_services(
        request, query_db, delete_property
    )
    logger.info(delete_property_result.message)

    return ResponseUtil.success(msg=delete_property_result.message)


@property_controller.put(
    '/set',
    summary='设置资产状态接口',
    description='用于设置资产状态（禁用/启用）',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:property:edit')],
)
@Log(title='资产管理', business_type=BusinessType.UPDATE)
async def set_system_property_status(
        request: Request,
        set_property: EditPropertyModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    set_property_result = await PropertyService.set_property_status_services(
        request, query_db, set_property
    )
    logger.info(set_property_result.message)

    return ResponseUtil.success(msg=set_property_result.message)


@property_controller.get(
    '/{id}',
    summary='获取资产详情接口',
    description='用于获取指定资产的详细信息',
    response_model=DataResponseModel[PropertyModel],
    dependencies=[UserInterfaceAuthDependency('system:property:query')],
)
async def query_detail_system_property(
        request: Request,
        id: Annotated[int, Path(description='资产 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_property_result = await PropertyService.property_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的信息成功')

    return ResponseUtil.success(data=detail_property_result)