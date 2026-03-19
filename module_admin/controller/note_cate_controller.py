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
from module_admin.entity.vo.note_cate_vo import (
    AddNoteCateModel,
    DeleteNoteCateModel,
    EditNoteCateModel,
    NoteCateModel,
    NoteCatePageQueryModel,
    SetNoteCateModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.note_cate_service import NoteCateService
from utils.log_util import logger
from utils.response_util import ResponseUtil

note_cate_controller = APIRouterPro(
    prefix='/system/noteCate', order_num=22, tags=['系统管理 - 公告分类管理'], dependencies=[PreAuthDependency()]
)


@note_cate_controller.get(
    '/list',
    summary='获取公告分类分页列表接口',
    description='用于获取公告分类分页列表',
    response_model=PageResponseModel[NoteCateModel],
    dependencies=[UserInterfaceAuthDependency('system:noteCate:list')],
)
async def get_system_note_cate_list(
        request: Request,
        note_cate_page_query: Annotated[NoteCatePageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    # 获取分页数据
    note_cate_page_query_result = await NoteCateService.get_note_cate_list_services(
        query_db, note_cate_page_query, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=note_cate_page_query_result)


@note_cate_controller.post(
    '',
    summary='新增公告分类接口',
    description='用于新增公告分类',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:noteCate:add')],
)
@ValidateFields(validate_model='add_note_cate')
@Log(title='公告分类管理', business_type=BusinessType.INSERT)
async def add_system_note_cate(
        request: Request,
        add_note_cate: AddNoteCateModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    add_note_cate_result = await NoteCateService.add_note_cate_services(request, query_db, add_note_cate)
    logger.info(add_note_cate_result.message)

    return ResponseUtil.success(msg=add_note_cate_result.message)


@note_cate_controller.put(
    '',
    summary='编辑公告分类接口',
    description='用于编辑公告分类',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:noteCate:edit')],
)
@ValidateFields(validate_model='edit_note_cate')
@Log(title='公告分类管理', business_type=BusinessType.UPDATE)
async def edit_system_note_cate(
        request: Request,
        edit_note_cate: EditNoteCateModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    edit_note_cate_result = await NoteCateService.edit_note_cate_services(request, query_db, edit_note_cate)
    logger.info(edit_note_cate_result.message)

    return ResponseUtil.success(msg=edit_note_cate_result.message)


@note_cate_controller.delete(
    '',
    summary='删除公告分类接口',
    description='用于删除公告分类',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:noteCate:remove')],
)
@Log(title='公告分类管理', business_type=BusinessType.DELETE)
async def delete_system_note_cate(
        request: Request,
        id: Annotated[int, Query(description='公告分类 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_note_cate_result = await NoteCateService.delete_note_cate_services(
        request, query_db, DeleteNoteCateModel(id=id)
    )
    logger.info(delete_note_cate_result.message)

    return ResponseUtil.success(msg=delete_note_cate_result.message)


@note_cate_controller.put(
    '/set',
    summary='设置公告分类状态接口',
    description='用于设置公告分类状态（禁用/启用）',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:noteCate:edit')],
)
@Log(title='公告分类管理', business_type=BusinessType.UPDATE)
async def set_system_note_cate_status(
        request: Request,
        set_note_cate: SetNoteCateModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    set_note_cate_result = await NoteCateService.set_note_cate_status_services(
        request, query_db, set_note_cate
    )
    logger.info(set_note_cate_result.message)

    return ResponseUtil.success(msg=set_note_cate_result.message)


@note_cate_controller.get(
    '/{id}',
    summary='获取公告分类详情接口',
    description='用于获取指定公告分类的详细信息',
    response_model=DataResponseModel[NoteCateModel],
    dependencies=[UserInterfaceAuthDependency('system:noteCate:query')],
)
async def query_detail_system_note_cate(
        request: Request,
        id: Annotated[int, Path(description='公告分类 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_note_cate_result = await NoteCateService.note_cate_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的信息成功')

    return ResponseUtil.success(data=detail_note_cate_result)

