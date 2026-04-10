from typing import Annotated

from fastapi import Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import PreAuthDependency
from common.router import APIRouterPro
from common.vo import PageResponseModel
from module_admin.entity.vo.user_vo import ContactsBookPageQueryModel
from module_admin.service.contacts_book_service import ContactsBookService
from utils.log_util import logger
from utils.response_util import ResponseUtil

contacts_book_controller = APIRouterPro(
    prefix='/home/index', order_num=100, tags=['首页 - 通讯录'], dependencies=[PreAuthDependency()]
)


@contacts_book_controller.get(
    '/contacts_book',
    summary='获取通讯录列表接口',
    description='用于获取企业通讯录员工列表',
    response_model=PageResponseModel[ContactsBookPageQueryModel],
)
async def get_contacts_book(
    request: Request,
    contacts_query: Annotated[ContactsBookPageQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """
    获取通讯录列表

    :param request: Request 对象
    :param contacts_query: 查询参数
    :param query_db: 数据库会话
    :return: 通讯录列表
    """
    contacts_result = await ContactsBookService.get_contacts_book_list_services(
        query_db, contacts_query, is_page=True
    )
    logger.info('获取通讯录列表成功')

    return ResponseUtil.success(model_content=contacts_result)
