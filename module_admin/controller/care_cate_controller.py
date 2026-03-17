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
from module_admin.entity.vo.care_cate_vo import (
    AddCareCateModel,
    DeleteCareCateModel,
    EditCareCateModel,
    CareCateModel,
    CareCatePageQueryModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.care_cate_service import CareCateService
from utils.log_util import logger
from utils.response_util import ResponseUtil

care_cate_controller = APIRouterPro(
    prefix='/system/careCate', order_num=21, tags=['系统管理 - 关怀项目管理'], dependencies=[PreAuthDependency()]
)


@care_cate_controller.get(
    '/list',
    summary='获取关怀项目分页列表接口',
    description='用于获取关怀项目分页列表',
    response_model=PageResponseModel[CareCateModel],
    dependencies=[UserInterfaceAuthDependency('system:careCate:list')],
)
async def get_system_care_cate_list(
        request: Request,
        care_cate_page_query: Annotated[CareCatePageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    # 获取分页数据
    care_cate_page_query_result = await CareCateService.get_care_cate_list_services(
        query_db, care_cate_page_query, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=care_cate_page_query_result)


@care_cate_controller.post(
    '',
    summary='新增关怀项目接口',
    description='用于新增关怀项目',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:careCate:add')],
)
@ValidateFields(validate_model='add_care_cate')
@Log(title='关怀项目管理', business_type=BusinessType.INSERT)
async def add_system_care_cate(
        request: Request,
        add_care_cate: AddCareCateModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    add_care_cate_result = await CareCateService.add_care_cate_services(request, query_db, add_care_cate)
    logger.info(add_care_cate_result.message)

    return ResponseUtil.success(msg=add_care_cate_result.message)


@care_cate_controller.put(
    '',
    summary='编辑关怀项目接口',
    description='用于编辑关怀项目',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:careCate:edit')],
)
@ValidateFields(validate_model='edit_care_cate')
@Log(title='关怀项目管理', business_type=BusinessType.UPDATE)
async def edit_system_care_cate(
        request: Request,
        edit_care_cate: EditCareCateModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    edit_care_cate_result = await CareCateService.edit_care_cate_services(request, query_db, edit_care_cate)
    logger.info(edit_care_cate_result.message)

    return ResponseUtil.success(msg=edit_care_cate_result.message)


@care_cate_controller.delete(
    '/{ids}',
    summary='删除关怀项目接口',
    description='用于删除关怀项目',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:careCate:remove')],
)
@Log(title='关怀项目管理', business_type=BusinessType.DELETE)
async def delete_system_care_cate(
        request: Request,
        ids: Annotated[str, Path(description='需要删除的关怀项目 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_care_cate = DeleteCareCateModel(ids=ids)
    delete_care_cate_result = await CareCateService.delete_care_cate_services(
        request, query_db, delete_care_cate
    )
    logger.info(delete_care_cate_result.message)

    return ResponseUtil.success(msg=delete_care_cate_result.message)


@care_cate_controller.put(
    '/set',
    summary='设置关怀项目状态接口',
    description='用于设置关怀项目状态（禁用/启用）',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:careCate:edit')],
)
@Log(title='关怀项目管理', business_type=BusinessType.UPDATE)
async def set_system_care_cate_status(
        request: Request,
        set_care_cate: EditCareCateModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    set_care_cate_result = await CareCateService.set_care_cate_status_services(
        request, query_db, set_care_cate
    )
    logger.info(set_care_cate_result.message)

    return ResponseUtil.success(msg=set_care_cate_result.message)


@care_cate_controller.get(
    '/{id}',
    summary='获取关怀项目详情接口',
    description='用于获取指定关怀项目的详细信息',
    response_model=DataResponseModel[CareCateModel],
    dependencies=[UserInterfaceAuthDependency('system:careCate:query')],
)
async def query_detail_system_care_cate(
        request: Request,
        id: Annotated[int, Path(description='关怀项目 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_care_cate_result = await CareCateService.care_cate_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的信息成功')

    return ResponseUtil.success(data=detail_care_cate_result)

