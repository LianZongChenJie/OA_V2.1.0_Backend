"""
在线文档管理控制器
"""
from typing import Annotated

from fastapi import Path, Request, Response
from pydantic_validation_decorator import ValidateFields
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import DataResponseModel, ResponseBaseModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_disk.entity.vo.article_vo import AddArticleModel, EditArticleModel
from module_disk.service.article_service import ArticleService
from utils.log_util import logger
from utils.response_util import ResponseUtil

article_controller = APIRouterPro(
    prefix='/disk/article', order_num=31, tags=['网盘管理 - 在线文档'], dependencies=[PreAuthDependency()]
)


@article_controller.post(
    '',
    summary='新增在线文档接口',
    description='用于新增在线文档',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('disk:article:add')],
)
@ValidateFields(validate_model='add_article')
@Log(title='在线文档管理', business_type=BusinessType.INSERT)
async def add_article(
        request: Request,
        add_article: AddArticleModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    add_article_result = await ArticleService.add_article_services(
        request, query_db, add_article, current_user.user.user_id
    )
    logger.info(add_article_result.message)

    return ResponseUtil.success(msg=add_article_result.message, data=add_article_result.data)


@article_controller.put(
    '',
    summary='编辑在线文档接口',
    description='用于编辑在线文档',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('disk:article:edit')],
)
@ValidateFields(validate_model='edit_article')
@Log(title='在线文档管理', business_type=BusinessType.UPDATE)
async def edit_article(
        request: Request,
        edit_article: EditArticleModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    edit_article_result = await ArticleService.edit_article_services(
        request, query_db, edit_article, current_user.user.user_id
    )
    logger.info(edit_article_result.message)

    return ResponseUtil.success(msg=edit_article_result.message)


@article_controller.get(
    '/{id}',
    summary='获取在线文档详情接口',
    description='用于获取指定在线文档的详细信息',
    response_model=DataResponseModel[dict],
    dependencies=[UserInterfaceAuthDependency('disk:article:query')],
)
async def query_article_detail(
        request: Request,
        id: Annotated[int, Path(description='文档 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_article_result = await ArticleService.article_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的在线文档信息成功')

    return ResponseUtil.success(data=detail_article_result)
