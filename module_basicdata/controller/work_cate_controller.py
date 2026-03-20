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

from module_basicdata.entity.do.project.work_cate_do import OaWorkCate
from module_basicdata.entity.vo.project.work_cate_vo import WorkCatePageQueryModel, OaWorkCateBaseModel
from module_basicdata.service.project.work_cate_service import WorkCateService
from utils.camel_converter import ModelConverter
from utils.log_util import logger
from utils.response_util import ResponseUtil

basic_project_workCate_controller = APIRouterPro(
    prefix='/basicdata/project/workCate', order_num=3, tags=['基础数据-项目模块-工作类别'], dependencies=[PreAuthDependency()]
)

@basic_project_workCate_controller.get(
    "/list",
    summary='工作类别分页列表接口',
    description='用于获取工作类别分页列表',
    response_model=PageResponseModel[OaWorkCateBaseModel],
    dependencies=[UserInterfaceAuthDependency('basicdata:project:step:list')],
)

async def list_page(
    page_query: Annotated[WorkCatePageQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaWorkCate)],
) -> Response:
    result_list = await WorkCateService.get_page_list_service(query_db, page_query, data_scope_sql, True)
    return ResponseUtil.success(model_content=result_list)

@basic_project_workCate_controller.post(
    "/add",
    summary='新增工作类别接口',
    description='用于新增工作类别',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('basicdata:project:step:add')],
)
async def add_industry(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: OaWorkCateBaseModel,
) -> Response:
    result = await WorkCateService.add_service(query_db, model)
    logger.info(result.message)
    return ResponseUtil.success(data=result.message)

@basic_project_workCate_controller.put(
    "/changeStatus",
    summary='修改工作类别状态接口',
    description='用于修改工作类别状态',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('basicdata:project:step:del')],
)
async def change_status_industry(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: OaWorkCateBaseModel,
) -> Response:
    basic_result = await WorkCateService.change_status_service(query_db, model)
    logger.info(basic_result.message)
    return ResponseUtil.success(data=basic_result.message)

@basic_project_workCate_controller.put(
    "/update",
    summary='修改工作类别接口',
    description='用于修改工作类别',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('basicdata:project:step:edit')],
)
async def update_industry(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: OaWorkCateBaseModel,
) -> Response:
    basic_result = await WorkCateService.update_service(query_db, model)
    logger.info(basic_result.message)
    return ResponseUtil.success(data=basic_result.message)

@basic_project_workCate_controller.get(
    "/detail/{id}",
    summary='获取工作类别详情接口',
    description='用于获取工作类别详情',
    response_model=OaWorkCateBaseModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:project:step:detail')],
)
async def get_info_by_id(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: Annotated[int, Path()],
) -> Response:
    try:
        link_info = await WorkCateService.get_info_service(query_db, id)
        return ResponseUtil.success(data=ModelConverter.time_format(ModelConverter.to_dict(link_info)))
    except Exception as e:
        logger.error(e)
        return ResponseUtil.failure("查询失败")


