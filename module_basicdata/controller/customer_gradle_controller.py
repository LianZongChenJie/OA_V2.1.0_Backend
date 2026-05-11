from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from common.annotation.log_annotation import Log
from common.aspect.data_scope import DataScopeDependency
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency
from common.enums import BusinessType
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
    summary='客户等级分页列表接口',
    description='用于获取客户等级分页列表',
    response_model=PageResponseModel[OaCustomerGradeBaseModel],
    dependencies=[UserInterfaceAuthDependency('basicdata:finance:gradle:list')],
)

async def list_page(
    link_page_query: Annotated[OaCustomerGradePageQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaCustomerGrade)],
) -> Response:
    gradle_list = await CustomerGradleService.get_page_list_service(query_db, link_page_query, data_scope_sql, True)
    return ResponseUtil.success(model_content=gradle_list)

@gradle_controller.post(
    "/add",
    summary='新增客户等级接口',
    description='用于新增客户等级',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('basicdata:finance:gradle:add')],
)
@Log(title="新增客户等级", business_type=BusinessType.INSERT)
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
    summary='修改客户等级状态接口',
    description='用于修改客户等级状态',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('basicdata:finance:gradle:del')],
)
@Log(title="修改客户等级状态", business_type=BusinessType.UPDATE)
async def change_status_industry(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: OaCustomerGradeBaseModel,
) -> Response:
    gradle_result = await CustomerGradleService.change_status_service(query_db, model)
    logger.info(gradle_result.message)
    return ResponseUtil.success(data=gradle_result.message)

@gradle_controller.put(
    "/update",
    summary='修改客户等级接口',
    description='用于修改客户等级',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('basicdata:finance:gradle:edit')],
)
@Log(title="修改客户等级", business_type=BusinessType.UPDATE)
async def update_industry(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: OaCustomerGradeBaseModel,
) -> Response:
    gradle_result = await CustomerGradleService.update_service(query_db, model)
    logger.info(gradle_result.message)
    return ResponseUtil.success(data=gradle_result.message)

@gradle_controller.get(
    "/detail/{id}",
    summary='获取客户等级详情接口',
    description='用于获取客户等级详情',
    response_model=OaCustomerGradeBaseModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:finance:gradle:detail')],
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


