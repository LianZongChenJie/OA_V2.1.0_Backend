"""
网盘分享空间管理控制器
"""
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
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_disk.entity.vo.disk_group_vo import (
    AddDiskGroupModel,
    DeleteDiskGroupModel,
    DiskGroupModel,
    DiskGroupPageQueryModel,
    EditDiskGroupModel,
)
from module_disk.service.disk_group_service import DiskGroupService
from utils.log_util import logger
from utils.response_util import ResponseUtil

disk_group_controller = APIRouterPro(
    prefix='/disk/group', order_num=31, tags=['网盘分享空间模块'], dependencies=[PreAuthDependency()]
)


@disk_group_controller.get(
    '/list',
    summary='获取分享空间列表接口',
    description='用于获取分享空间列表',
    response_model=PageResponseModel[DiskGroupModel],
    dependencies=[UserInterfaceAuthDependency('disk:group:list')],
)
async def get_disk_group_list(
        request: Request,
        group_page_query: Annotated[DiskGroupPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    from sqlalchemy import and_
    from module_disk.entity.do.disk_group_do import OaDiskGroup

    where_conditions = [OaDiskGroup.delete_time == 0]

    if group_page_query.keywords:
        where_conditions.append(OaDiskGroup.title.like(f'%{group_page_query.keywords}%'))

    group_list_result = await DiskGroupService.get_disk_group_list_services(
        query_db,
        group_page_query,
        where_conditions,
        is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=group_list_result)


@disk_group_controller.post(
    '',
    summary='新增分享空间接口',
    description='用于新增分享空间',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('disk:group:add')],
)
@ValidateFields(validate_model='add_disk_group')
@Log(title='网盘分享空间管理', business_type=BusinessType.INSERT)
async def add_disk_group(
        request: Request,
        add_group: AddDiskGroupModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    add_group_result = await DiskGroupService.add_disk_group_services(
        request, query_db, add_group, current_user.user.user_id
    )
    logger.info(add_group_result.message)

    return ResponseUtil.success(msg=add_group_result.message)


@disk_group_controller.put(
    '',
    summary='编辑分享空间接口',
    description='用于编辑分享空间',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('disk:group:edit')],
)
@ValidateFields(validate_model='edit_disk_group')
@Log(title='网盘分享空间管理', business_type=BusinessType.UPDATE)
async def edit_disk_group(
        request: Request,
        edit_group: EditDiskGroupModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    edit_group_result = await DiskGroupService.edit_disk_group_services(
        request, query_db, edit_group, current_user.user.user_id
    )
    logger.info(edit_group_result.message)

    return ResponseUtil.success(msg=edit_group_result.message)


@disk_group_controller.delete(
    '/{id}',
    summary='删除分享空间接口',
    description='用于删除分享空间',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('disk:group:remove')],
)
@Log(title='网盘分享空间管理', business_type=BusinessType.DELETE)
async def delete_disk_group(
        request: Request,
        id: Annotated[int, Path(description='需要删除的分享空间 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    delete_group = DeleteDiskGroupModel(id=id)
    delete_group_result = await DiskGroupService.delete_disk_group_services(
        request, query_db, delete_group, current_user.user.user_id
    )
    logger.info(delete_group_result.message)

    return ResponseUtil.success(msg=delete_group_result.message)


@disk_group_controller.get(
    '/{id}',
    summary='获取分享空间详情接口',
    description='用于获取指定分享空间的详细信息',
    response_model=DataResponseModel[DiskGroupModel],
    dependencies=[UserInterfaceAuthDependency('disk:group:query')],
)
async def query_disk_group_detail(
        request: Request,
        id: Annotated[int, Path(description='分享空间 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_group_result = await DiskGroupService.disk_group_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的信息成功')

    return ResponseUtil.success(data=detail_group_result)
