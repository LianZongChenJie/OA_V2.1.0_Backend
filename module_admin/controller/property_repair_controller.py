from typing import Annotated

from fastapi import Path, Query, Request, Response
from pydantic_validation_decorator import ValidateFields
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import DataResponseModel, PageResponseModel, ResponseBaseModel
from module_admin.entity.vo.property_repair_vo import (
    AddPropertyRepairModel,
    DeletePropertyRepairModel,
    EditPropertyRepairModel,
    PropertyRepairModel,
    PropertyRepairPageQueryModel,
)
from module_admin.service.property_repair_service import PropertyRepairService
from utils.log_util import logger
from utils.response_util import ResponseUtil

property_repair_controller = APIRouterPro(
    prefix='/system/property/repair', order_num=27, tags=['系统管理 - 维修记录'], dependencies=[PreAuthDependency()]
)

@property_repair_controller.get(
    '/list',
    summary='获取维修记录分页列表接口',
    description='用于获取维修记录分页列表',
    response_model=PageResponseModel[PropertyRepairModel],
    dependencies=[UserInterfaceAuthDependency('system:property:repair:list')],
)
async def get_property_repair_list(
        request: Request,
        property_repair_page_query: Annotated[PropertyRepairPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    # 获取分页数据
    repair_page_query_result = await PropertyRepairService.get_property_repair_list_services(
        query_db, property_repair_page_query, is_page=True
    )
    logger.info('获取维修记录列表成功')

    return ResponseUtil.success(model_content=repair_page_query_result)


@property_repair_controller.post(
    '',
    summary='新增维修记录接口',
    description='用于新增维修记录',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:property:repair:add')],
)
@ValidateFields(validate_model='add_property_repair')
@Log(title='维修记录管理', business_type=BusinessType.INSERT)
async def add_property_repair(
        request: Request,
        add_property_repair: AddPropertyRepairModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    add_property_repair_result = await PropertyRepairService.add_property_repair_services(request, query_db, add_property_repair)
    logger.info(add_property_repair_result.message)

    return ResponseUtil.success(msg=add_property_repair_result.message)


@property_repair_controller.put(
    '',
    summary='编辑维修记录接口',
    description='用于编辑维修记录',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:property:repair:edit')],
)
@ValidateFields(validate_model='edit_property_repair')
@Log(title='维修记录管理', business_type=BusinessType.UPDATE)
async def edit_property_repair(
        request: Request,
        edit_property_repair: EditPropertyRepairModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    edit_property_repair_result = await PropertyRepairService.edit_property_repair_services(request, query_db, edit_property_repair)
    logger.info(edit_property_repair_result.message)

    return ResponseUtil.success(msg=edit_property_repair_result.message)


@property_repair_controller.delete(
    '/{id}',
    summary='删除维修记录接口',
    description='用于删除维修记录',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:property:repair:remove')],
)
@Log(title='维修记录管理', business_type=BusinessType.DELETE)
async def delete_property_repair(
        request: Request,
        id: Annotated[int, Path(description='需要删除的维修记录 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_property_repair = DeletePropertyRepairModel(id=id)
    delete_property_repair_result = await PropertyRepairService.delete_property_repair_services(
        request, query_db, delete_property_repair
    )
    logger.info(delete_property_repair_result.message)

    return ResponseUtil.success(msg=delete_property_repair_result.message)


@property_repair_controller.get(
    '/{id}',
    summary='获取维修记录详情接口',
    description='用于获取指定维修记录的详细信息',
    response_model=DataResponseModel[PropertyRepairModel],
    dependencies=[UserInterfaceAuthDependency('system:property:repair:query')],
)
async def query_property_repair_detail(
        request: Request,
        id: Annotated[int, Path(description='维修记录 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_property_repair_result = await PropertyRepairService.property_repair_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的维修记录信息成功')

    return ResponseUtil.success(data=detail_property_repair_result)
