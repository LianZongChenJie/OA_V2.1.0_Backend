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
from module_administrative.entity.vo.overtimes_vo import (
    AddOvertimesModel,
    DeleteOvertimesModel,
    EditOvertimesModel,
    OvertimesModel,
    OvertimesPageQueryModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_administrative.service.overtimes_service import OvertimesService
from utils.log_util import logger
from utils.response_util import ResponseUtil

overtimes_controller = APIRouterPro(
    prefix='/system/overtimes', order_num=28, tags=['个人办公 - 加班记录'], dependencies=[PreAuthDependency()]
)


@overtimes_controller.get(
    '/list',
    summary='获取加班记录分页列表接口',
    description='用于获取加班记录分页列表',
    response_model=PageResponseModel[OvertimesModel],
    dependencies=[UserInterfaceAuthDependency('system:overtimes:list')],
)
async def get_overtimes_list(
        request: Request,
        overtimes_page_query: Annotated[OvertimesPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    # 获取分页数据
    overtimes_page_query_result = await OvertimesService.get_overtimes_list_services(
        query_db, overtimes_page_query, is_page=True
    )
    logger.info('获取加班记录列表成功')

    return ResponseUtil.success(model_content=overtimes_page_query_result)


@overtimes_controller.post(
    '',
    summary='新增加班记录接口',
    description='用于新增加班记录',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:overtimes:add')],
)
@ValidateFields(validate_model='add_overtimes')
@Log(title='加班记录管理', business_type=BusinessType.INSERT)
async def add_overtimes(
        request: Request,
        add_overtimes: AddOvertimesModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    if not current_user.user or not current_user.user.user_id:
        logger.error('当前用户信息异常')
        return ResponseUtil.error(msg='用户信息异常，请重新登录')
    
    user_id = current_user.user.user_id
    dept_id = current_user.user.dept_id if current_user.user.dept_id else 0
    
    add_overtimes_result = await OvertimesService.add_overtimes_services(request, query_db, add_overtimes, user_id, dept_id)
    logger.info(add_overtimes_result.message)

    return ResponseUtil.success(msg=add_overtimes_result.message)


@overtimes_controller.put(
    '',
    summary='编辑加班记录接口',
    description='用于编辑加班记录',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:overtimes:edit')],
)
@ValidateFields(validate_model='edit_overtimes')
@Log(title='加班记录管理', business_type=BusinessType.UPDATE)
async def edit_overtimes(
        request: Request,
        edit_overtimes: EditOvertimesModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    edit_overtimes_result = await OvertimesService.edit_overtimes_services(request, query_db, edit_overtimes)
    logger.info(edit_overtimes_result.message)

    return ResponseUtil.success(msg=edit_overtimes_result.message)


@overtimes_controller.delete(
    '/{id}',
    summary='删除加班记录接口',
    description='用于删除加班记录',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:overtimes:remove')],
)
@Log(title='加班记录管理', business_type=BusinessType.DELETE)
async def delete_overtimes(
        request: Request,
        id: Annotated[int, Path(description='需要删除的加班记录 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_overtimes = DeleteOvertimesModel(id=id)
    delete_overtimes_result = await OvertimesService.delete_overtimes_services(
        request, query_db, delete_overtimes
    )
    logger.info(delete_overtimes_result.message)

    return ResponseUtil.success(msg=delete_overtimes_result.message)


@overtimes_controller.get(
    '/{id}',
    summary='获取加班记录详情接口',
    description='用于获取指定加班记录的详细信息',
    response_model=DataResponseModel[OvertimesModel],
    dependencies=[UserInterfaceAuthDependency('system:overtimes:query')],
)
async def query_overtimes_detail(
        request: Request,
        id: Annotated[int, Path(description='加班记录 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_overtimes_result = await OvertimesService.overtimes_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的加班记录信息成功')

    return ResponseUtil.success(data=detail_overtimes_result)