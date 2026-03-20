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
from module_admin.entity.vo.supplier_vo import (
    AddSupplierModel,
    DeleteSupplierModel,
    EditSupplierModel,
    SupplierModel,
    SupplierPageQueryModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.supplier_service import SupplierService
from utils.log_util import logger
from utils.response_util import ResponseUtil

supplier_controller = APIRouterPro(
    prefix='/system/supplier', order_num=24, tags=['系统管理 - 供应商管理'], dependencies=[PreAuthDependency()]
)


@supplier_controller.get(
    '/list',
    summary='获取供应商分页列表接口',
    description='用于获取供应商分页列表',
    response_model=PageResponseModel[SupplierModel],
    dependencies=[UserInterfaceAuthDependency('system:supplier:list')],
)
async def get_system_supplier_list(
        request: Request,
        supplier_page_query: Annotated[SupplierPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    # 获取分页数据
    supplier_page_query_result = await SupplierService.get_supplier_list_services(
        query_db, supplier_page_query, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=supplier_page_query_result)


@supplier_controller.post(
    '',
    summary='新增供应商接口',
    description='用于新增供应商',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:supplier:add')],
)
@ValidateFields(validate_model='add_supplier')
@Log(title='供应商管理', business_type=BusinessType.INSERT)
async def add_system_supplier(
        request: Request,
        add_supplier: AddSupplierModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    add_supplier_result = await SupplierService.add_supplier_services(request, query_db, add_supplier)
    logger.info(add_supplier_result.message)

    return ResponseUtil.success(msg=add_supplier_result.message)


@supplier_controller.put(
    '',
    summary='编辑供应商接口',
    description='用于编辑供应商',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:supplier:edit')],
)
@ValidateFields(validate_model='edit_supplier')
@Log(title='供应商管理', business_type=BusinessType.UPDATE)
async def edit_system_supplier(
        request: Request,
        edit_supplier: EditSupplierModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    edit_supplier_result = await SupplierService.edit_supplier_services(request, query_db, edit_supplier)
    logger.info(edit_supplier_result.message)

    return ResponseUtil.success(msg=edit_supplier_result.message)


@supplier_controller.delete(
    '/{ids}',
    summary='删除供应商接口',
    description='用于删除供应商',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:supplier:remove')],
)
@Log(title='供应商管理', business_type=BusinessType.DELETE)
async def delete_system_supplier(
        request: Request,
        ids: Annotated[str, Path(description='需要删除的供应商 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_supplier = DeleteSupplierModel(ids=ids)
    delete_supplier_result = await SupplierService.delete_supplier_services(
        request, query_db, delete_supplier
    )
    logger.info(delete_supplier_result.message)

    return ResponseUtil.success(msg=delete_supplier_result.message)


@supplier_controller.put(
    '/set',
    summary='设置供应商状态接口',
    description='用于设置供应商状态（禁用/启用）',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:supplier:edit')],
)
@Log(title='供应商管理', business_type=BusinessType.UPDATE)
async def set_system_supplier_status(
        request: Request,
        set_supplier: EditSupplierModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    set_supplier_result = await SupplierService.set_supplier_status_services(
        request, query_db, set_supplier
    )
    logger.info(set_supplier_result.message)

    return ResponseUtil.success(msg=set_supplier_result.message)


@supplier_controller.get(
    '/{id}',
    summary='获取供应商详情接口',
    description='用于获取指定供应商的详细信息',
    response_model=DataResponseModel[SupplierModel],
    dependencies=[UserInterfaceAuthDependency('system:supplier:query')],
)
async def query_detail_system_supplier(
        request: Request,
        id: Annotated[int, Path(description='供应商 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_supplier_result = await SupplierService.supplier_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的信息成功')

    return ResponseUtil.success(data=detail_supplier_result)
