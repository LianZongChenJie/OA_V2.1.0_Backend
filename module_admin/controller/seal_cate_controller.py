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
from module_admin.entity.vo.seal_cate_vo import (
    AddSealCateModel,
    DeleteSealCateModel,
    EditSealCateModel,
    SealCateModel,
    SealCatePageQueryModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.seal_cate_service import SealCateService
from utils.log_util import logger
from utils.response_util import ResponseUtil

seal_cate_controller = APIRouterPro(
    prefix='/system/sealCate', order_num=22, tags=['系统管理 - 印章类别管理'], dependencies=[PreAuthDependency()]
)


@seal_cate_controller.get(
    '/list',
    summary='获取印章类别分页列表接口',
    description='用于获取印章类别分页列表',
    response_model=PageResponseModel[SealCateModel],
    dependencies=[UserInterfaceAuthDependency('system:sealCate:list')],
)
async def get_system_seal_cate_list(
        request: Request,
        seal_cate_page_query: Annotated[SealCatePageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    # 获取分页数据
    seal_cate_page_query_result = await SealCateService.get_seal_cate_list_services(
        query_db, seal_cate_page_query, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=seal_cate_page_query_result)


@seal_cate_controller.post(
    '',
    summary='新增印章类别接口',
    description='用于新增印章类别',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:sealCate:add')],
)
@ValidateFields(validate_model='add_seal_cate')
@Log(title='印章类别管理', business_type=BusinessType.INSERT)
async def add_system_seal_cate(
        request: Request,
        add_seal_cate: AddSealCateModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    add_seal_cate_result = await SealCateService.add_seal_cate_services(request, query_db, add_seal_cate)
    logger.info(add_seal_cate_result.message)

    return ResponseUtil.success(msg=add_seal_cate_result.message)


@seal_cate_controller.put(
    '',
    summary='编辑印章类别接口',
    description='用于编辑印章类别',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:sealCate:edit')],
)
@ValidateFields(validate_model='edit_seal_cate')
@Log(title='印章类别管理', business_type=BusinessType.UPDATE)
async def edit_system_seal_cate(
        request: Request,
        edit_seal_cate: EditSealCateModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    edit_seal_cate_result = await SealCateService.edit_seal_cate_services(request, query_db, edit_seal_cate)
    logger.info(edit_seal_cate_result.message)

    return ResponseUtil.success(msg=edit_seal_cate_result.message)


@seal_cate_controller.delete(
    '/{ids}',
    summary='删除印章类别接口',
    description='用于删除印章类别',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:sealCate:remove')],
)
@Log(title='印章类别管理', business_type=BusinessType.DELETE)
async def delete_system_seal_cate(
        request: Request,
        ids: Annotated[str, Path(description='需要删除的印章类别 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_seal_cate = DeleteSealCateModel(ids=ids)
    delete_seal_cate_result = await SealCateService.delete_seal_cate_services(
        request, query_db, delete_seal_cate
    )
    logger.info(delete_seal_cate_result.message)

    return ResponseUtil.success(msg=delete_seal_cate_result.message)


@seal_cate_controller.put(
    '/set',
    summary='设置印章类别状态接口',
    description='用于设置印章类别状态（禁用/启用）',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:sealCate:edit')],
)
@Log(title='印章类别管理', business_type=BusinessType.UPDATE)
async def set_system_seal_cate_status(
        request: Request,
        set_seal_cate: EditSealCateModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    set_seal_cate_result = await SealCateService.set_seal_cate_status_services(
        request, query_db, set_seal_cate
    )
    logger.info(set_seal_cate_result.message)

    return ResponseUtil.success(msg=set_seal_cate_result.message)


@seal_cate_controller.get(
    '/{id}',
    summary='获取印章类别详情接口',
    description='用于获取指定印章类别的详细信息',
    response_model=DataResponseModel[SealCateModel],
    dependencies=[UserInterfaceAuthDependency('system:sealCate:query')],
)
async def query_detail_system_seal_cate(
        request: Request,
        id: Annotated[int, Path(description='印章类别 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_seal_cate_result = await SealCateService.seal_cate_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的信息成功')

    return ResponseUtil.success(data=detail_seal_cate_result)

