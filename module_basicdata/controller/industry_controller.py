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

from module_basicdata.entity.do.custom.industry_do import OaIndustry
from module_basicdata.entity.vo.custom.industry_vo import OaIndustryBaseModel, IndustryPageQueryModel
from module_basicdata.service.custom.industry_service import IndustryService
from utils.camel_converter import ModelConverter
from utils.log_util import logger
from utils.response_util import ResponseUtil

industry_controller = APIRouterPro(
    prefix='/basicdata/customer/industry', order_num=3, tags=['基础数据-客户模块-行业类型'], dependencies=[PreAuthDependency()]
)

@industry_controller.get(
    "/list",
    summary='行业类型分页列表接口',
    description='用于获取行业类型分页列表',
    response_model=PageResponseModel[OaIndustryBaseModel],
    dependencies=[UserInterfaceAuthDependency('basicdata:finance:cost_cate:list')],
)

async def list_page(
    link_page_query: Annotated[IndustryPageQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaIndustry)],
) -> Response:
    cost_cate_list = await IndustryService.get_industry_list_service(query_db, link_page_query, data_scope_sql, True)
    return ResponseUtil.success(model_content=cost_cate_list)

@industry_controller.post(
    "/add",
    summary='新增行业类型接口',
    description='用于新增行业类型',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('basicdata:finance:cost_cate:add')],
)
async def add_industry(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: OaIndustryBaseModel,
) -> Response:
    result = await IndustryService.add_industry_service(query_db, model)
    logger.info(result.message)
    return ResponseUtil.success(data=result.message)

@industry_controller.put(
    "/changeStatus",
    summary='修改行业类型状态接口',
    description='用于修改行业类型状态',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('basicdata:finance:cost_cate:del')],
)
async def change_status_industry(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: OaIndustryBaseModel,
) -> Response:
    cost_cate_result = await IndustryService.change_status_industry_service(query_db, model)
    logger.info(cost_cate_result.message)
    return ResponseUtil.success(data=cost_cate_result.message)

@industry_controller.put(
    "/update",
    summary='修改行业类型接口',
    description='用于修改行业类型',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('basicdata:finance:cost_cate:edit')],
)
async def update_industry(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: OaIndustryBaseModel,
) -> Response:
    cost_cate_result = await IndustryService.update_industry_service(query_db, model)
    logger.info(cost_cate_result.message)
    return ResponseUtil.success(data=cost_cate_result.message)

@industry_controller.get(
    "/detail/{id}",
    summary='获取行业类型详情接口',
    description='用于获取行业类型详情',
    response_model=OaIndustryBaseModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:finance:cost_cate:detail')],
)
async def get_industry_info(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: Annotated[int, Path()],
) -> Response:
    try:
        link_info = await IndustryService.get_industry_info_service(query_db, id)
        return ResponseUtil.success(data=ModelConverter.time_format(ModelConverter.to_dict(link_info)))
    except Exception as e:
        logger.error(e)
        return ResponseUtil.failure("查询失败")


