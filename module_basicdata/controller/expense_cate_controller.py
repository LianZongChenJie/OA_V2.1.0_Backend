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

from module_basicdata.entity.do.finance.expense_cate import OaExpenseCate
from module_basicdata.entity.vo.finance.expense_cate_vo import OaExpenseCateBaseModel, ExpenseCatePageQueryModel
from module_basicdata.service.finance.expense_service import ExpenseCateService
from utils.camel_converter import ModelConverter
from utils.log_util import logger
from utils.response_util import ResponseUtil

expense_cate_controller = APIRouterPro(
    prefix='/basicdata/finance/reimbursement', order_num=3, tags=['基础数据-财务模块-报销类型'], dependencies=[PreAuthDependency()]
)

@expense_cate_controller.get(
    "/list",
    summary='报销类型分页列表接口',
    description='用于获取报销类型分页列表',
    response_model=PageResponseModel[OaExpenseCateBaseModel],
    dependencies=[UserInterfaceAuthDependency('basicdata:finance:expense_cate:list')],
)

async def list_page(
    link_page_query: Annotated[ExpenseCatePageQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaExpenseCate)],
) -> Response:
    expense_cate_list = await ExpenseCateService.get_cost_cate_list_service(query_db, link_page_query, data_scope_sql, True)
    return ResponseUtil.success(model_content=expense_cate_list)

@expense_cate_controller.post(
    "/add",
    summary='新增报销类型接口',
    description='用于新增报销类型',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('basicdata:finance:expense_cate:add')],
)
async def add_expense_cate(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    expense_cate_base_model: OaExpenseCateBaseModel,
) -> Response:
    expense_cate_result = await ExpenseCateService.add_expense_cate_service(query_db, expense_cate_base_model)
    logger.info(expense_cate_result.message)
    return ResponseUtil.success(data=expense_cate_result.message)

@expense_cate_controller.put(
    "/changeStatus",
    summary='修改报销类型状态接口',
    description='用于修改报销类型状态',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('basicdata:finance:expense_cate:del')],
)
async def change_status_expense_cate(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: OaExpenseCateBaseModel,
) -> Response:
    cost_cate_result = await ExpenseCateService.change_status_expense_cate_service(query_db, model)
    logger.info(cost_cate_result.message)
    return ResponseUtil.success(data=cost_cate_result.message)

@expense_cate_controller.put(
    "/update",
    summary='修改报销类型接口',
    description='用于修改报销类型',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('basicdata:finance:expense_cate:edit')],
)
async def update_expense_cate(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    cost_cate_base_model: OaExpenseCateBaseModel,
) -> Response:
    expense_cate_result = await ExpenseCateService.update_expense_cate_service(query_db, cost_cate_base_model)
    logger.info(expense_cate_result.message)
    return ResponseUtil.success(data=expense_cate_result.message)

@expense_cate_controller.get(
    "/detail/{id}",
    summary='获取报销类型详情接口',
    description='用于获取报销类型详情',
    response_model=OaExpenseCateBaseModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:finance:expense_cate:detail')],
)
async def get_cost_expense_info(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: Annotated[int, Path()],
) -> Response:
    try:
        link_info = await ExpenseCateService.get_expense_cate_info_service(query_db, id)
        return ResponseUtil.success(data=ModelConverter.to_dict(link_info, by_alias=True))
    except Exception as e:
        logger.error(e)
        return ResponseUtil.failure("查询失败")
