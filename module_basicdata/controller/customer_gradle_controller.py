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

from module_basicdata.entity.do.custom.customer_gradle_do import OaCustomerGrade
from module_basicdata.entity.vo.custom.customer_gradle_vo import OaCustomerGradeBaseModel, OaCustomerGradePageQueryModel
from module_basicdata.service.custom.custome_gradle_service import CustomerGradleService
from utils.camel_converter import ModelConverter
from utils.log_util import logger
from utils.response_util import ResponseUtil

gradle_controller = APIRouterPro(
    prefix='/basicdata/customer/gradle', order_num=3, tags=['基础数据-客户模块-客户级别'], dependencies=[PreAuthDependency()]
)

@gradle_controller.get(
    "/list",
    summary='行业类型分页列表接口',
    description='用于获取行业类型分页列表',
    response_model=PageResponseModel[OaCustomerGradeBaseModel],
    dependencies=[UserInterfaceAuthDependency('basicdata:finance:cost_cate:list')],
)

async def list_page(
    link_page_query: Annotated[OaCustomerGradePageQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaCustomerGrade)],
) -> Response:
    cost_cate_list = await CustomerGradleService.get_page_list_service(query_db, link_page_query, data_scope_sql, True)
    return ResponseUtil.success(model_content=cost_cate_list)

@gradle_controller.post(
    "/add",
    summary='新增行业类型接口',
    description='用于新增行业类型',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('basicdata:finance:cost_cate:add')],
)
async def add_industry(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: OaCustomerGradeBaseModel,
) -> Response:
    result = await CustomerGradleService.add_service(query_db, model)
    logger.info(result.message)
    return ResponseUtil.success(data=result.message)

@gradle_controller.put(
    "/changeStatus",
    summary='修改行业类型状态接口',
    description='用于修改行业类型状态',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('basicdata:finance:cost_cate:del')],
)
async def change_status_industry(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: OaCustomerGradeBaseModel,
) -> Response:
    cost_cate_result = await CustomerGradleService.change_status_service(query_db, model)
    logger.info(cost_cate_result.message)
    return ResponseUtil.success(data=cost_cate_result.message)

@gradle_controller.put(
    "/update",
    summary='修改行业类型接口',
    description='用于修改行业类型',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('basicdata:finance:cost_cate:edit')],
)
async def update_industry(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: OaCustomerGradeBaseModel,
) -> Response:
    cost_cate_result = await CustomerGradleService.update_service(query_db, model)
    logger.info(cost_cate_result.message)
    return ResponseUtil.success(data=cost_cate_result.message)

@gradle_controller.get(
    "/detail/{id}",
    summary='获取行业类型详情接口',
    description='用于获取行业类型详情',
    response_model=OaCustomerGradeBaseModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:finance:cost_cate:detail')],
)
async def get_industry_info(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: Annotated[int, Path()],
) -> Response:
    try:
        link_info = await CustomerGradleService.get_info_service(query_db, id)
        return ResponseUtil.success(data=ModelConverter.time_format(ModelConverter.to_dict(link_info)))
    except Exception as e:
        logger.error(e)
        return ResponseUtil.failure("查询失败")


