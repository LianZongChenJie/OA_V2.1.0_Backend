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

from module_basicdata.entity.do.project.step_do import OaStep
from module_basicdata.entity.vo.project.step_vo import OaStepBaseModel, StepPageQueryModel
from module_basicdata.service.project.step_service import StepService
from utils.camel_converter import ModelConverter
from utils.log_util import logger
from utils.response_util import ResponseUtil

basic_project_step_controller = APIRouterPro(
    prefix='/basicdata/project/step', order_num=3, tags=['基础数据-项目模块-项目阶段'], dependencies=[PreAuthDependency()]
)

@basic_project_step_controller.get(
    "/list",
    summary='项目阶段分页列表接口',
    description='用于获取项目阶段分页列表',
    response_model=PageResponseModel[OaStepBaseModel],
    dependencies=[UserInterfaceAuthDependency('basicdata:project:step:list')],
)

async def list_page(
    page_query: Annotated[StepPageQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaStep)],
) -> Response:
    result_list = await StepService.get_page_list_service(query_db, page_query, data_scope_sql, True)
    return ResponseUtil.success(model_content=result_list)

@basic_project_step_controller.post(
    "/add",
    summary='新增项目阶段接口',
    description='用于新增项目阶段',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('basicdata:project:step:add')],
)
@Log(title="新增项目阶段", business_type=BusinessType.INSERT)
async def add_step(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: OaStepBaseModel,
) -> Response:
    result = await StepService.add_service(query_db, model)
    logger.info(result.message)
    return ResponseUtil.success(data=result.message)

@basic_project_step_controller.put(
    "/changeStatus",
    summary='修改项目阶段状态接口',
    description='用于修改项目阶段状态',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('basicdata:project:step:del')],
)
@Log(title="修改项目阶段状态", business_type=BusinessType.UPDATE)
async def change_status(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: OaStepBaseModel,
) -> Response:
    basic_result = await StepService.change_status_service(query_db, model)
    logger.info(basic_result.message)
    return ResponseUtil.success(data=basic_result.message)

@basic_project_step_controller.put(
    "/update",
    summary='修改项目阶段接口',
    description='用于修改项目阶段',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('basicdata:project:step:edit')],
)
@Log(title="修改项目阶段", business_type=BusinessType.UPDATE)
async def update_step(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: OaStepBaseModel,
) -> Response:
    basic_result = await StepService.update_service(query_db, model)
    logger.info(basic_result.message)
    return ResponseUtil.success(data=basic_result.message)

@basic_project_step_controller.get(
    "/detail/{id}",
    summary='获取项目阶段详情接口',
    description='用于获取项目阶段详情',
    response_model=OaStepBaseModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:project:step:detail')],
)
async def get_info_by_id(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: Annotated[int, Path()],
) -> Response:
    try:
        link_info = await StepService.get_info_service(query_db, id)
        return ResponseUtil.success(data=ModelConverter.time_format(ModelConverter.to_dict(link_info)))
    except Exception as e:
        logger.error(e)
        return ResponseUtil.failure("查询失败")


