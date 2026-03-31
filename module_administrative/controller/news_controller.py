from fastapi import File, Form, Path, Query, Request, Response, UploadFile,Body
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from common.aspect.data_scope import DataScopeDependency
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency, CurrentUserDependency
from common.router import APIRouterPro
from module_administrative.entity.do.news_do import OaNews
from module_administrative.entity.vo.new_vo import OaNewsBaseModel, OaNewsQueryPageModel
from module_administrative.service.new_service import NewsService
from module_admin.entity.vo.user_vo import (
    CurrentUserModel
)
from utils.response_util import ResponseUtil

administrative_news_controller = APIRouterPro(
    prefix='/administrative/news', order_num=3, tags=['行政办公-公司新闻'], dependencies=[PreAuthDependency()]
)

@administrative_news_controller.get(
    "/list",
    summary='获取公司新闻列表',
    description='用于获取公司新闻列表',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:news:query')],
)
async def get_page_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaNewsQueryPageModel, Query()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaNews)],
) -> Response:
    return await NewsService.get_page_list_service(query_db,query_object,data_scope_sql,True)

@administrative_news_controller.post(
    "/add",
    summary='新增公司新闻',
    description='用于新增公司新闻',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:news:add')],
)
async def add_news(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaNewsBaseModel, Body()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    query_object.admin_id = current_user.user.user_id
    return await NewsService.add_service(query_db, query_object)

@administrative_news_controller.put(
    "/update",
    summary='更新公司新闻',
    description='用于更新公司新闻',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:news:update')],
)
async def update_news(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: Annotated[OaNewsBaseModel, Body()],
)->Response:
    return await NewsService().update_service(query_db, model)

@administrative_news_controller.get(
    "/detail/{id}",
    summary='获取公司新闻详情',
    description='用于获取公司新闻详情',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:news:query')],
)
async def get_news_by_id(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    return await NewsService.get_info_service(query_db, id)

@administrative_news_controller.delete(
    "/delete/{id}",
    summary='删除公司新闻',
    description='用于删除公司新闻',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:news:delete')],
)
async def delete_news(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result =  await NewsService.del_by_id(query_db, id)
    return ResponseUtil.success(msg=result.message)
