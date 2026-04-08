"""
网盘文件管理控制器
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
from module_disk.entity.vo.disk_vo import (
    AddDiskModel,
    BackDiskModel,
    ClearDiskModel,
    DeleteDiskModel,
    DiskModel,
    DiskPageQueryModel,
    EditDiskModel,
    MoveDiskModel,
    StarDiskModel,
    UnstarDiskModel,
)
from module_disk.service.disk_service import DiskService
from utils.log_util import logger
from utils.response_util import ResponseUtil

disk_controller = APIRouterPro(
    prefix='/disk', order_num=30, tags=['网盘管理模块'], dependencies=[PreAuthDependency()]
)


@disk_controller.get(
    '/list',
    summary='获取网盘文件列表接口',
    description='用于获取网盘文件列表',
    response_model=PageResponseModel[DiskModel],
    dependencies=[UserInterfaceAuthDependency('disk:list')],
)
async def get_disk_list(
        request: Request,
        disk_page_query: Annotated[DiskPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        pid: Annotated[int, Query(description='父文件夹ID')] = 0,
        group_id: Annotated[int, Query(description='分享空间ID')] = 0,
) -> Response:
    where_conditions = await DiskService.build_query_conditions(
        disk_page_query,
        current_user.user.user_id,
        pid,
        group_id,
        disk_page_query.is_star == 1 if disk_page_query.is_star else False,
        disk_page_query.ext
    )

    disk_list_result = await DiskService.get_disk_list_services(
        query_db,
        disk_page_query,
        current_user.user.user_id,
        where_conditions,
        is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=disk_list_result)


@disk_controller.post(
    '/upload',
    summary='上传文件接口',
    description='用于上传文件到网盘',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('disk:add')],
)
@ValidateFields(validate_model='add_disk')
@Log(title='网盘文件管理', business_type=BusinessType.INSERT)
async def add_disk_upload(
        request: Request,
        add_disk: AddDiskModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    add_disk.types = 0
    add_disk_result = await DiskService.add_disk_services(
        request, query_db, add_disk, current_user.user.user_id, current_user.user.dept_id or 0
    )
    logger.info(add_disk_result.message)

    return ResponseUtil.success(msg=add_disk_result.message)


@disk_controller.post(
    '/folder',
    summary='新建文件夹接口',
    description='用于新建文件夹',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('disk:add')],
)
@ValidateFields(validate_model='add_disk')
@Log(title='网盘文件管理', business_type=BusinessType.INSERT)
async def add_disk_folder(
        request: Request,
        add_disk: AddDiskModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    add_disk.types = 2
    add_disk_result = await DiskService.add_disk_services(
        request, query_db, add_disk, current_user.user.user_id, current_user.user.dept_id or 0
    )
    logger.info(add_disk_result.message)

    return ResponseUtil.success(msg=add_disk_result.message)


@disk_controller.put(
    '/rename',
    summary='重命名文件接口',
    description='用于重命名文件或文件夹',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('disk:edit')],
)
@ValidateFields(validate_model='edit_disk')
@Log(title='网盘文件管理', business_type=BusinessType.UPDATE)
async def rename_disk(
        request: Request,
        edit_disk: EditDiskModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    edit_disk_result = await DiskService.edit_disk_services(
        request, query_db, edit_disk, current_user.user.user_id
    )
    logger.info(edit_disk_result.message)

    return ResponseUtil.success(msg=edit_disk_result.message)


@disk_controller.delete(
    '',
    summary='删除文件接口',
    description='用于删除文件或文件夹',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('disk:remove')],
)
@Log(title='网盘文件管理', business_type=BusinessType.DELETE)
async def delete_disk(
        request: Request,
        delete_disk: DeleteDiskModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    delete_disk_result = await DiskService.delete_disk_services(
        request, query_db, delete_disk, current_user.user.user_id
    )
    logger.info(delete_disk_result.message)

    return ResponseUtil.success(msg=delete_disk_result.message)


@disk_controller.post(
    '/back',
    summary='恢复文件接口',
    description='用于从回收站恢复文件',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('disk:remove')],
)
@Log(title='网盘文件管理', business_type=BusinessType.UPDATE)
async def back_disk(
        request: Request,
        back_disk: BackDiskModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    back_disk_result = await DiskService.back_disk_services(
        request, query_db, back_disk
    )
    logger.info(back_disk_result.message)

    return ResponseUtil.success(msg=back_disk_result.message)


@disk_controller.post(
    '/clear',
    summary='清除文件接口',
    description='用于彻底清除文件',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('disk:remove')],
)
@Log(title='网盘文件管理', business_type=BusinessType.DELETE)
async def clear_disk(
        request: Request,
        clear_disk: ClearDiskModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    clear_disk_result = await DiskService.clear_disk_services(
        request, query_db, clear_disk
    )
    logger.info(clear_disk_result.message)

    return ResponseUtil.success(msg=clear_disk_result.message)


@disk_controller.post(
    '/move',
    summary='移动文件接口',
    description='用于移动文件或文件夹',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('disk:edit')],
)
@Log(title='网盘文件管理', business_type=BusinessType.UPDATE)
async def move_disk(
        request: Request,
        move_disk: MoveDiskModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    move_disk_result = await DiskService.move_disk_services(
        request, query_db, move_disk
    )
    logger.info(move_disk_result.message)

    return ResponseUtil.success(msg=move_disk_result.message)


@disk_controller.post(
    '/star',
    summary='标星文件接口',
    description='用于标星重要文件',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('disk:edit')],
)
@Log(title='网盘文件管理', business_type=BusinessType.UPDATE)
async def star_disk(
        request: Request,
        star_disk: StarDiskModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    star_disk_result = await DiskService.star_disk_services(
        request, query_db, star_disk
    )
    logger.info(star_disk_result.message)

    return ResponseUtil.success(msg=star_disk_result.message)


@disk_controller.post(
    '/unstar',
    summary='取消标星接口',
    description='用于取消文件标星',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('disk:edit')],
)
@Log(title='网盘文件管理', business_type=BusinessType.UPDATE)
async def unstar_disk(
        request: Request,
        unstar_disk: UnstarDiskModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    unstar_disk_result = await DiskService.unstar_disk_services(
        request, query_db, unstar_disk
    )
    logger.info(unstar_disk_result.message)

    return ResponseUtil.success(msg=unstar_disk_result.message)


@disk_controller.get(
    '/{id}',
    summary='获取文件详情接口',
    description='用于获取指定文件的详细信息',
    response_model=DataResponseModel[DiskModel],
    dependencies=[UserInterfaceAuthDependency('disk:query')],
)
async def query_disk_detail(
        request: Request,
        id: Annotated[int, Path(description='文件 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_disk_result = await DiskService.disk_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的信息成功')

    return ResponseUtil.success(data=detail_disk_result)
