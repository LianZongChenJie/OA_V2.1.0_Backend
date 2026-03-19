from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement
from fastapi import Path, Query, Request, Response
from typing import Annotated

from common.vo import PageResponseModel, DataResponseModel, ResponseBaseModel
from common.annotation.log_annotation import Log
from common.aspect.data_scope import DataScopeDependency
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from module_admin.entity.do.basic_adm_do import OaBasicAdm
from module_admin.entity.vo.basic_adm_vo import BasicAdmPageQueryModel, OaBasicAdmModel, DeleteBasicAdmModel, EditBasicAdmModel
from module_admin.service.basic_adm_service import BasicAdmService
from utils.log_util import logger
from utils.response_util import ResponseUtil

basic_adm_controller = APIRouterPro(
    prefix='/basicdata/basicAdm', order_num=10, tags=['基础数据 - 行政模块常规数据'], dependencies=[PreAuthDependency()]
)


@basic_adm_controller.get(
    "/list",
    summary='获取行政模块常规数据分页列表接口',
    description='用于获取行政模块常规数据分页列表',
    response_model=PageResponseModel[OaBasicAdmModel],
    dependencies=[UserInterfaceAuthDependency('basicdata:basicAdm:list')],
)
async def list_page(
        basic_adm_page_query: Annotated[BasicAdmPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaBasicAdm)],
) -> Response:
    basic_adm_list = await BasicAdmService.get_basic_adm_list_services(query_db, basic_adm_page_query, data_scope_sql, is_page=True)
    logger.info('获取成功')
    return ResponseUtil.success(model_content=basic_adm_list)


@basic_adm_controller.post(
    "/add",
    summary='新增行政模块常规数据接口',
    description='用于新增行政模块常规数据',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:basicAdm:add')],
)
@Log(title='行政模块常规数据', business_type=BusinessType.INSERT)
async def add_basic_adm(
        request: Request,
        oa_basic_adm_model: OaBasicAdmModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    basic_adm_result = await BasicAdmService.add_basic_adm_service(request, query_db, oa_basic_adm_model)
    logger.info(basic_adm_result.message)
    return ResponseUtil.success(msg=basic_adm_result.message)


@basic_adm_controller.put(
    "/update",
    summary='修改行政模块常规数据接口',
    description='用于修改行政模块常规数据',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:basicAdm:edit')],
)
@Log(title='行政模块常规数据', business_type=BusinessType.UPDATE)
async def update_basic_adm(
        request: Request,
        oa_basic_adm_model: OaBasicAdmModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    basic_adm_result = await BasicAdmService.update_basic_adm_service(request, query_db, oa_basic_adm_model)
    logger.info(basic_adm_result.message)
    return ResponseUtil.success(msg=basic_adm_result.message)


@basic_adm_controller.delete(
    "/delete/{id}",
    summary='删除行政模块常规数据接口',
    description='用于删除行政模块常规数据',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:basicAdm:del')],
)
@Log(title='行政模块常规数据', business_type=BusinessType.DELETE)
async def delete_basic_adm(
        request: Request,
        id: Annotated[int, Path(description='行政模块常规数据 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()]
) -> Response:
    basic_adm_result = await BasicAdmService.delete_basic_adm_service(request, query_db, DeleteBasicAdmModel(ids=str(id)))
    logger.info(basic_adm_result.message)
    return ResponseUtil.success(msg=basic_adm_result.message)


@basic_adm_controller.get(
    "/detail/{id}",
    summary='获取行政模块常规数据详情接口',
    description='用于获取行政模块常规数据详情',
    response_model=DataResponseModel[OaBasicAdmModel],
    dependencies=[UserInterfaceAuthDependency('basicdata:basicAdm:view')],
)
async def get_basic_adm(
        request: Request,
        id: Annotated[int, Path(description='行政模块常规数据 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()]
) -> Response:
    basic_adm_result = await BasicAdmService.basic_adm_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的信息成功')
    return ResponseUtil.success(data=basic_adm_result)


@basic_adm_controller.put(
    "/changeStatus",
    summary='改变行政模块常规数据状态接口',
    description='用于改变行政模块常规数据状态',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:basicAdm:changeStatus')],
)
@Log(title='行政模块常规数据', business_type=BusinessType.UPDATE)
async def change_status(
        request: Request,
        oa_basic_adm_model: OaBasicAdmModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()]
) -> Response:
    basic_adm_result = await BasicAdmService.set_basic_adm_status_services(request, query_db, EditBasicAdmModel(id=oa_basic_adm_model.id, status=oa_basic_adm_model.status))
    logger.info(basic_adm_result.message)
    return ResponseUtil.success(msg=basic_adm_result.message)

