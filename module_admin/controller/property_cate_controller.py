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
from module_admin.entity.vo.property_cate_vo import (
    AddPropertyCateModel,
    DeletePropertyCateModel,
    EditPropertyCateModel,
    PropertyCateModel,
    PropertyCatePageQueryModel,
    PropertyCateTreeModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.property_cate_service import PropertyCateService
from utils.log_util import logger
from utils.response_util import ResponseUtil

property_cate_controller = APIRouterPro(
    prefix='/system/propertyCate', order_num=23, tags=['系统管理 - 资产分类管理'], dependencies=[PreAuthDependency()]
)


@property_cate_controller.get(
    '/tree',
    summary='获取资产分类树接口',
    description='用于获取资产分类树形结构数据',
    response_model=DataResponseModel[list[PropertyCateTreeModel]],
    dependencies=[UserInterfaceAuthDependency('system:propertyCate:list')],
)
async def get_system_property_cate_tree(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    # 获取树形数据
    property_cate_tree_result = await PropertyCateService.get_property_cate_tree_services(query_db)
    logger.info('获取成功')

    return ResponseUtil.success(data=property_cate_tree_result)


@property_cate_controller.get(
    '/list',
    summary='获取资产分类分页列表接口',
    description='用于获取资产分类分页列表',
    response_model=PageResponseModel[PropertyCateModel],
    dependencies=[UserInterfaceAuthDependency('system:propertyCate:list')],
)
async def get_system_property_cate_list(
        request: Request,
        property_cate_page_query: Annotated[PropertyCatePageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    # 获取分页数据
    property_cate_page_query_result = await PropertyCateService.get_property_cate_list_services(
        query_db, property_cate_page_query, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=property_cate_page_query_result)


@property_cate_controller.post(
    '',
    summary='新增资产分类接口',
    description='用于新增资产分类',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:propertyCate:add')],
)
@ValidateFields(validate_model='add_property_cate')
@Log(title='资产分类管理', business_type=BusinessType.INSERT)
async def add_system_property_cate(
        request: Request,
        add_property_cate: AddPropertyCateModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    add_property_cate.admin_id = current_user.user.user_id
    add_property_cate_result = await PropertyCateService.add_property_cate_services(request, query_db, add_property_cate)
    logger.info(add_property_cate_result.message)

    return ResponseUtil.success(msg=add_property_cate_result.message)


@property_cate_controller.put(
    '',
    summary='编辑资产分类接口',
    description='用于编辑资产分类',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:propertyCate:edit')],
)
@ValidateFields(validate_model='edit_property_cate')
@Log(title='资产分类管理', business_type=BusinessType.UPDATE)
async def edit_system_property_cate(
        request: Request,
        edit_property_cate: EditPropertyCateModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    edit_property_cate_result = await PropertyCateService.edit_property_cate_services(request, query_db, edit_property_cate)
    logger.info(edit_property_cate_result.message)

    return ResponseUtil.success(msg=edit_property_cate_result.message)


@property_cate_controller.delete(
    '/{id}',
    summary='删除资产分类接口',
    description='用于删除资产分类',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:propertyCate:remove')],
)
@Log(title='资产分类管理', business_type=BusinessType.DELETE)
async def delete_system_property_cate(
        request: Request,
        id: Annotated[int, Path(description='需要删除的分类 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_property_cate = DeletePropertyCateModel(id=id)
    delete_property_cate_result = await PropertyCateService.delete_property_cate_services(
        request, query_db, delete_property_cate
    )
    logger.info(delete_property_cate_result.message)

    return ResponseUtil.success(msg=delete_property_cate_result.message)


@property_cate_controller.put(
    '/set',
    summary='设置资产分类状态接口',
    description='用于设置资产分类状态（禁用/启用）',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:propertyCate:edit')],
)
@Log(title='资产分类管理', business_type=BusinessType.UPDATE)
async def set_system_property_cate_status(
        request: Request,
        set_property_cate: EditPropertyCateModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    set_property_cate_result = await PropertyCateService.set_property_cate_status_services(
        request, query_db, set_property_cate
    )
    logger.info(set_property_cate_result.message)

    return ResponseUtil.success(msg=set_property_cate_result.message)


@property_cate_controller.get(
    '/{id}',
    summary='获取资产分类详情接口',
    description='用于获取指定资产分类的详细信息',
    response_model=DataResponseModel[PropertyCateModel],
    dependencies=[UserInterfaceAuthDependency('system:propertyCate:query')],
)
async def query_detail_system_property_cate(
        request: Request,
        id: Annotated[int, Path(description='分类 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_property_cate_result = await PropertyCateService.property_cate_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的信息成功')

    return ResponseUtil.success(data=detail_property_cate_result)

