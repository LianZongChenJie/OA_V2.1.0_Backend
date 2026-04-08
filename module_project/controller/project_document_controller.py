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
from module_project.entity.vo.project_document_vo import (
    AddProjectDocumentModel,
    DeleteProjectDocumentModel,
    EditProjectDocumentModel,
    ProjectDocumentModel,
    ProjectDocumentPageQueryModel,
)
from module_project.service.project_document_service import ProjectDocumentService
from utils.log_util import logger
from utils.response_util import ResponseUtil

project_document_controller = APIRouterPro(
    prefix='/project/document', order_num=21, tags=['项目管理 - 文档管理'], dependencies=[PreAuthDependency()]
)


@project_document_controller.get(
    '/list',
    summary='获取项目文档分页列表接口',
    description='用于获取项目文档分页列表',
    response_model=PageResponseModel[ProjectDocumentModel],
    dependencies=[UserInterfaceAuthDependency('project:document:list')],
)
async def get_project_document_list(
        request: Request,
        project_document_page_query: Annotated[ProjectDocumentPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    # 获取分页数据
    project_document_page_query_result = await ProjectDocumentService.get_project_document_list_services(
        query_db,
        project_document_page_query,
        current_user.user.user_id,
        False,  # is_project_admin 需要根据实际权限判断
        is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=project_document_page_query_result)


@project_document_controller.post(
    '',
    summary='新增项目文档接口',
    description='用于新增项目文档',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('project:document:add')],
)
@ValidateFields(validate_model='add_project_document')
@Log(title='项目文档管理', business_type=BusinessType.INSERT)
async def add_project_document(
        request: Request,
        add_project_document: AddProjectDocumentModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    add_project_document_result = await ProjectDocumentService.add_project_document_services(
        request, query_db, add_project_document, current_user.user.user_id
    )
    logger.info(add_project_document_result.message)

    return ResponseUtil.success(msg=add_project_document_result.message)


@project_document_controller.put(
    '',
    summary='编辑项目文档接口',
    description='用于编辑项目文档',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('project:document:edit')],
)
@ValidateFields(validate_model='edit_project_document')
@Log(title='项目文档管理', business_type=BusinessType.UPDATE)
async def edit_project_document(
        request: Request,
        edit_project_document: EditProjectDocumentModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    edit_project_document_result = await ProjectDocumentService.edit_project_document_services(
        request, query_db, edit_project_document, current_user.user.user_id
    )
    logger.info(edit_project_document_result.message)

    return ResponseUtil.success(msg=edit_project_document_result.message)


@project_document_controller.delete(
    '/{id}',
    summary='删除项目文档接口',
    description='用于删除项目文档',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('project:document:remove')],
)
@Log(title='项目文档管理', business_type=BusinessType.DELETE)
async def delete_project_document(
        request: Request,
        id: Annotated[int, Path(description='需要删除的文档 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    delete_project_document = DeleteProjectDocumentModel(id=id)
    delete_project_document_result = await ProjectDocumentService.delete_project_document_services(
        request, query_db, delete_project_document, current_user.user.user_id
    )
    logger.info(delete_project_document_result.message)

    return ResponseUtil.success(msg=delete_project_document_result.message)


@project_document_controller.get(
    '/{id}',
    summary='获取项目文档详情接口',
    description='用于获取指定项目文档的详细信息',
    response_model=DataResponseModel[ProjectDocumentModel],
    dependencies=[UserInterfaceAuthDependency('project:document:query')],
)
async def query_project_document_detail(
        request: Request,
        id: Annotated[int, Path(description='文档 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_project_document_result = await ProjectDocumentService.project_document_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的信息成功')

    return ResponseUtil.success(data=detail_project_document_result)
