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
from module_admin.entity.vo.services_vo import (
    AddServicesModel,
    DeleteServicesModel,
    EditServicesModel,
    ServicesModel,
    ServicesPageQueryModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.services_service import ServicesService
from utils.log_util import logger
from utils.response_util import ResponseUtil

services_controller = APIRouterPro(
    prefix='/system/services', order_num=23, tags=['系统管理 - 服务管理'], dependencies=[PreAuthDependency()]
)


@services_controller.get(
    '/list',
    summary='获取服务分页列表接口',
    description='用于获取服务分页列表',
    response_model=PageResponseModel[ServicesModel],
    dependencies=[UserInterfaceAuthDependency('system:services:list')],
)
async def get_system_services_list(
        request: Request,
        services_page_query: Annotated[ServicesPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    # 获取分页数据
    services_page_query_result = await ServicesService.get_services_list_services(
        query_db, services_page_query, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=services_page_query_result)


@services_controller.post(
    '',
    summary='新增服务接口',
    description='用于新增服务',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:services:add')],
)
@ValidateFields(validate_model='add_services')
@Log(title='服务管理', business_type=BusinessType.INSERT)
async def add_system_services(
        request: Request,
        add_services: AddServicesModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    add_services_result = await ServicesService.add_services_services(request, query_db, add_services)
    logger.info(add_services_result.message)

    return ResponseUtil.success(msg=add_services_result.message)


@services_controller.put(
    '',
    summary='编辑服务接口',
    description='用于编辑服务',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:services:edit')],
)
@ValidateFields(validate_model='edit_services')
@Log(title='服务管理', business_type=BusinessType.UPDATE)
async def edit_system_services(
        request: Request,
        edit_services: EditServicesModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    edit_services_result = await ServicesService.edit_services_services(request, query_db, edit_services)
    logger.info(edit_services_result.message)

    return ResponseUtil.success(msg=edit_services_result.message)


@services_controller.delete(
    '/{ids}',
    summary='删除服务接口',
    description='用于删除服务',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:services:remove')],
)
@Log(title='服务管理', business_type=BusinessType.DELETE)
async def delete_system_services(
        request: Request,
        ids: Annotated[str, Path(description='需要删除的服务 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_services = DeleteServicesModel(ids=ids)
    delete_services_result = await ServicesService.delete_services_services(
        request, query_db, delete_services
    )
    logger.info(delete_services_result.message)

    return ResponseUtil.success(msg=delete_services_result.message)


@services_controller.put(
    '/set',
    summary='设置服务状态接口',
    description='用于设置服务状态（禁用/启用）',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:services:edit')],
)
@Log(title='服务管理', business_type=BusinessType.UPDATE)
async def set_system_services_status(
        request: Request,
        set_services: EditServicesModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    set_services_result = await ServicesService.set_services_status_services(
        request, query_db, set_services
    )
    logger.info(set_services_result.message)

    return ResponseUtil.success(msg=set_services_result.message)


@services_controller.get(
    '/{id}',
    summary='获取服务详情接口',
    description='用于获取指定服务的详细信息',
    response_model=DataResponseModel[ServicesModel],
    dependencies=[UserInterfaceAuthDependency('system:services:query')],
)
async def query_detail_system_services(
        request: Request,
        id: Annotated[int, Path(description='服务 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_services_result = await ServicesService.services_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的信息成功')

    return ResponseUtil.success(data=detail_services_result)
