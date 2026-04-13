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
from module_admin.entity.vo.official_docs_vo import (
    AddOfficialDocsModel,
    DeleteOfficialDocsModel,
    EditOfficialDocsModel,
    OfficialDocsModel,
    OfficialDocsPageQueryModel,
    PendingOfficialDocsModel,
    ReviewedOfficialDocsModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.official_docs_service import OfficialDocsService
from utils.log_util import logger
from utils.response_util import ResponseUtil

official_controller = APIRouterPro(
    prefix='/system/official', order_num=26, tags=['系统管理 - 公文管理'], dependencies=[PreAuthDependency()]
)


@official_controller.get(
    '/list',
    summary='获取公文分页列表接口',
    description='用于获取公文分页列表',
    response_model=PageResponseModel[OfficialDocsModel],
    dependencies=[UserInterfaceAuthDependency('system:official:list')],
)
async def get_system_official_list(
        request: Request,
        official_page_query: Annotated[OfficialDocsPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    user_id = current_user.user.user_id if current_user.user and current_user.user.user_id else 0
    official_page_query_result = await OfficialDocsService.get_official_docs_list_services(
        query_db, official_page_query, is_page=True, user_id=user_id
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=official_page_query_result)


@official_controller.get(
    '/pending',
    summary='获取待审公文分页列表接口',
    description='用于获取待我审批的公文分页列表',
    response_model=PageResponseModel[OfficialDocsModel],
    dependencies=[UserInterfaceAuthDependency('system:official:pending')],
)
async def get_system_pending_official_list(
        request: Request,
        pending_query: Annotated[PendingOfficialDocsModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    user_id = current_user.user.user_id if current_user.user and current_user.user.user_id else 0
    pending_query_result = await OfficialDocsService.get_pending_docs_list_services(
        query_db, pending_query, user_id, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=pending_query_result)


@official_controller.get(
    '/reviewed',
    summary='获取已审公文分页列表接口',
    description='用于获取我已审批的公文分页列表',
    response_model=PageResponseModel[OfficialDocsModel],
    dependencies=[UserInterfaceAuthDependency('system:official:reviewed')],
)
async def get_system_reviewed_official_list(
        request: Request,
        reviewed_query: Annotated[ReviewedOfficialDocsModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    user_id = current_user.user.user_id if current_user.user and current_user.user.user_id else 0
    reviewed_query_result = await OfficialDocsService.get_reviewed_docs_list_services(
        query_db, reviewed_query, user_id, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=reviewed_query_result)


@official_controller.post(
    '',
    summary='新增公文接口',
    description='用于新增公文',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:official:add')],
)
@ValidateFields(validate_model='add_official_docs')
@Log(title='公文管理', business_type=BusinessType.INSERT)
async def add_system_official(
        request: Request,
        add_official: AddOfficialDocsModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    user_id = current_user.user.user_id if current_user.user and current_user.user.user_id else 0
    add_official_result = await OfficialDocsService.add_official_docs_services(
        request, query_db, add_official, user_id
    )
    logger.info(add_official_result.message)

    return ResponseUtil.success(msg=add_official_result.message)


@official_controller.put(
    '',
    summary='编辑公文接口',
    description='用于编辑公文',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:official:edit')],
)
@ValidateFields(validate_model='edit_official_docs')
@Log(title='公文管理', business_type=BusinessType.UPDATE)
async def edit_system_official(
        request: Request,
        edit_official: EditOfficialDocsModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    edit_official_result = await OfficialDocsService.edit_official_docs_services(request, query_db, edit_official)
    logger.info(edit_official_result.message)

    return ResponseUtil.success(msg=edit_official_result.message)


@official_controller.delete(
    '/{id}',
    summary='删除公文接口',
    description='用于删除公文',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:official:remove')],
)
@Log(title='公文管理', business_type=BusinessType.DELETE)
async def delete_system_official(
        request: Request,
        id: Annotated[int, Path(description='需要删除的公文 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_official = DeleteOfficialDocsModel(id=id)
    delete_official_result = await OfficialDocsService.delete_official_docs_services(
        request, query_db, delete_official
    )
    logger.info(delete_official_result.message)

    return ResponseUtil.success(msg=delete_official_result.message)


@official_controller.get(
    '/{id}',
    summary='获取公文详情接口',
    description='用于获取指定公文的详细信息',
    response_model=DataResponseModel[OfficialDocsModel],
    dependencies=[UserInterfaceAuthDependency('system:official:query')],
)
async def query_detail_system_official(
        request: Request,
        id: Annotated[int, Path(description='公文 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_official_result = await OfficialDocsService.official_docs_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的信息成功')

    return ResponseUtil.success(data=detail_official_result)
