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
from module_admin.entity.vo.basic_user_vo import (
    AddBasicUserModel,
    DeleteBasicUserModel,
    EditBasicUserModel,
    BasicUserModel,
    BasicUserPageQueryModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.basic_user_service import BasicUserService
from utils.log_util import logger
from utils.response_util import ResponseUtil

basic_user_controller = APIRouterPro(
    prefix='/system/basicUser', order_num=22, tags=['系统管理 - 人事模块常规数据管理'], dependencies=[PreAuthDependency()]
)


@basic_user_controller.get(
    '/list',
    summary='获取人事模块常规数据分页列表接口',
    description='用于获取人事模块常规数据分页列表',
    response_model=PageResponseModel[BasicUserModel],
    dependencies=[UserInterfaceAuthDependency('system:basicUser:list')],
)
async def get_system_basic_user_list(
        request: Request,
        basic_user_page_query: Annotated[BasicUserPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    # 获取分页数据
    basic_user_page_query_result = await BasicUserService.get_basic_user_list_services(
        query_db, basic_user_page_query, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=basic_user_page_query_result)


@basic_user_controller.post(
    '',
    summary='新增人事模块常规数据接口',
    description='用于新增人事模块常规数据',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:basicUser:add')],
)
@ValidateFields(validate_model='add_basic_user')
@Log(title='人事模块常规数据管理', business_type=BusinessType.INSERT)
async def add_system_basic_user(
        request: Request,
        add_basic_user: AddBasicUserModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    add_basic_user_result = await BasicUserService.add_basic_user_services(request, query_db, add_basic_user)
    logger.info(add_basic_user_result.message)

    return ResponseUtil.success(msg=add_basic_user_result.message)


@basic_user_controller.put(
    '',
    summary='编辑人事模块常规数据接口',
    description='用于编辑人事模块常规数据',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:basicUser:edit')],
)
@ValidateFields(validate_model='edit_basic_user')
@Log(title='人事模块常规数据管理', business_type=BusinessType.UPDATE)
async def edit_system_basic_user(
        request: Request,
        edit_basic_user: EditBasicUserModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    edit_basic_user_result = await BasicUserService.edit_basic_user_services(request, query_db, edit_basic_user)
    logger.info(edit_basic_user_result.message)

    return ResponseUtil.success(msg=edit_basic_user_result.message)


@basic_user_controller.delete(
    '/{ids}',
    summary='删除人事模块常规数据接口',
    description='用于删除人事模块常规数据',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:basicUser:remove')],
)
@Log(title='人事模块常规数据管理', business_type=BusinessType.DELETE)
async def delete_system_basic_user(
        request: Request,
        ids: Annotated[str, Path(description='需要删除的数据 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_basic_user = DeleteBasicUserModel(ids=ids)
    delete_basic_user_result = await BasicUserService.delete_basic_user_services(
        request, query_db, delete_basic_user
    )
    logger.info(delete_basic_user_result.message)

    return ResponseUtil.success(msg=delete_basic_user_result.message)


@basic_user_controller.put(
    '/set',
    summary='设置人事模块常规数据状态接口',
    description='用于设置人事模块常规数据状态（禁用/启用）',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:basicUser:edit')],
)
@Log(title='人事模块常规数据管理', business_type=BusinessType.UPDATE)
async def set_system_basic_user_status(
        request: Request,
        set_basic_user: EditBasicUserModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    set_basic_user_result = await BasicUserService.set_basic_user_status_services(
        request, query_db, set_basic_user
    )
    logger.info(set_basic_user_result.message)

    return ResponseUtil.success(msg=set_basic_user_result.message)


@basic_user_controller.get(
    '/{id}',
    summary='获取人事模块常规数据详情接口',
    description='用于获取指定人事模块常规数据的详细信息',
    response_model=DataResponseModel[BasicUserModel],
    dependencies=[UserInterfaceAuthDependency('system:basicUser:query')],
)
async def query_detail_system_basic_user(
        request: Request,
        id: Annotated[int, Path(description='数据 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_basic_user_result = await BasicUserService.basic_user_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的信息成功')

    return ResponseUtil.success(data=detail_basic_user_result)

