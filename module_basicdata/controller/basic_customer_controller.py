from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from common.aspect.data_scope import DataScopeDependency
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency
from common.router import APIRouterPro
from common.vo import PageResponseModel
from fastapi import File, Form, Path, Query, Request, Response, UploadFile
from typing import Annotated

from module_basicdata.entity.do.custom.custome_source_do import OaCustomerSource
from module_basicdata.entity.vo.custom.basic_customer_vo import OaBasicCustomerBaseModel, OaBasicCustomerPageQueryModel
from module_basicdata.service.custom.basic_customer_service import BasicCustomerService
from utils.camel_converter import ModelConverter
from utils.log_util import logger
from utils.response_util import ResponseUtil

basic_customer_controller = APIRouterPro(
    prefix='/basicdata/customer/basic', order_num=3, tags=['基础数据-客户模块-常规数据'], dependencies=[PreAuthDependency()]
)

@basic_customer_controller.get(
    "/list",
    summary='常规数据分页列表接口',
    description='用于获取常规数据分页列表',
    response_model=PageResponseModel[OaBasicCustomerBaseModel],
    dependencies=[UserInterfaceAuthDependency('basicdata:customer:basic:list')],
)

async def list_page(
    page_query: Annotated[OaBasicCustomerPageQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaCustomerSource)],
) -> Response:
    result_list = await BasicCustomerService.get_page_list_service(query_db, page_query, data_scope_sql, True)
    return ResponseUtil.success(model_content=result_list)

@basic_customer_controller.post(
    "/add",
    summary='新增常规数据接口',
    description='用于新增常规数据',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('basicdata:customer:basic:add')],
)
async def add_industry(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: OaBasicCustomerBaseModel,
) -> Response:
    result = await BasicCustomerService.add_service(query_db, model)
    logger.info(result.message)
    return ResponseUtil.success(data=result.message)

@basic_customer_controller.put(
    "/changeStatus",
    summary='修改常规数据状态接口',
    description='用于修改常规数据状态',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('basicdata:customer:basic:del')],
)
async def change_status_industry(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: OaBasicCustomerBaseModel,
) -> Response:
    basic_result = await BasicCustomerService.change_status_service(query_db, model)
    logger.info(basic_result.message)
    return ResponseUtil.success(data=basic_result.message)

@basic_customer_controller.put(
    "/update",
    summary='修改常规数据接口',
    description='用于修改常规数据',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('basicdata:customer:basic:edit')],
)
async def update_industry(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: OaBasicCustomerBaseModel,
) -> Response:
    basic_result = await BasicCustomerService.update_service(query_db, model)
    logger.info(basic_result.message)
    return ResponseUtil.success(data=basic_result.message)

@basic_customer_controller.get(
    "/detail/{id}",
    summary='获取常规数据详情接口',
    description='用于获取常规数据详情',
    response_model=OaBasicCustomerBaseModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:customer:basic:detail')],
)
async def get_industry_info(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: Annotated[int, Path()],
) -> Response:
    try:
        link_info = await BasicCustomerService.get_info_service(query_db, id)
        return ResponseUtil.success(data=ModelConverter.time_format(ModelConverter.to_dict(link_info)))
    except Exception as e:
        logger.error(e)
        return ResponseUtil.failure("查询失败")


