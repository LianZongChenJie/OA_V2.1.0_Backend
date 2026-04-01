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

from module_basicdata.entity.do.finance.cost_cate_do import OaCostCate
from module_basicdata.entity.vo.finance.cost_cate_vo import CostCatePageQueryModel, OaCostCateBaseModel
from module_basicdata.service.finance.cost_cate_service import CostCateService
from utils.camel_converter import ModelConverter
from utils.log_util import logger
from utils.response_util import ResponseUtil

cost_cate_controller = APIRouterPro(
    prefix='/basicdata/finance', order_num=3, tags=['基础数据-财务模块-报销类型'], dependencies=[PreAuthDependency()]
)

@cost_cate_controller.get(
    "/list",
    summary='报销类型分页列表接口',
    description='用于获取报销类型分页列表',
    response_model=PageResponseModel[OaCostCateBaseModel],
    dependencies=[UserInterfaceAuthDependency('basicdata:finance:cost_cate:list')],
)

async def list_page(
    link_page_query: Annotated[CostCatePageQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaCostCate)],
) -> Response:
    cost_cate_list = await CostCateService.get_cost_cate_list_service(query_db, link_page_query, data_scope_sql, True)
    return ResponseUtil.success(model_content=cost_cate_list)

@cost_cate_controller.post(
    "/add",
    summary='新增报销类型接口',
    description='用于新增报销类型',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('basicdata:finance:cost_cate:add')],
)
async def add_cost_cate(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    cost_cate_base_model: OaCostCateBaseModel,
) -> Response:
    cost_cate_result = await CostCateService.add_cost_cate_service(query_db, cost_cate_base_model)
    logger.info(cost_cate_result.message)
    return ResponseUtil.success(data=cost_cate_result.message)

@cost_cate_controller.put(
    "/changeStatus",
    summary='修改报销类型状态接口',
    description='用于修改报销类型状态',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('basicdata:finance:cost_cate:del')],
)
async def change_cost_cate(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: OaCostCateBaseModel,
) -> Response:
    cost_cate_result = await CostCateService.change_status_cost_cate_service(query_db, model)
    logger.info(cost_cate_result.message)
    return ResponseUtil.success(data=cost_cate_result.message)

@cost_cate_controller.put(
    "/update",
    summary='修改报销类型接口',
    description='用于修改报销类型',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('basicdata:finance:cost_cate:edit')],
)
async def update_cost_cate(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    cost_cate_base_model: OaCostCateBaseModel,
) -> Response:
    cost_cate_result = await CostCateService.update_cost_cate_service(query_db, cost_cate_base_model)
    logger.info(cost_cate_result.message)
    return ResponseUtil.success(data=cost_cate_result.message)

@cost_cate_controller.get(
    "/detail/{id}",
    summary='获取报销类型详情接口',
    description='用于获取报销类型详情',
    response_model=OaCostCateBaseModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:finance:cost_cate:detail')],
)
async def get_cost_cate_info(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: Annotated[int, Path()],
) -> Response:
    try:
        link_info = await CostCateService.get_cost_cate_info_service(query_db, id)
        return ResponseUtil.success(data=ModelConverter.to_dict(link_info, by_alias=True))
    except Exception as e:
        logger.error(e)
        return ResponseUtil.failure("查询失败")
