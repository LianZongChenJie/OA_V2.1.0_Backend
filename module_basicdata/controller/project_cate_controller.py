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

from module_basicdata.entity.do.project.project_cate_do import OaProjectCate
from module_basicdata.entity.vo.project.project_cate_vo import OaProjectCateBaseModel, ProjectCatePageQueryModel
from module_basicdata.service.project.project_cate_service import ProjectCateService
from utils.camel_converter import ModelConverter
from utils.log_util import logger
from utils.response_util import ResponseUtil

basic_project_cate_controller = APIRouterPro(
    prefix='/basicdata/project/cate', order_num=3, tags=['基础数据-项目模块-项目分类'], dependencies=[PreAuthDependency()]
)

@basic_project_cate_controller.get(
    "/list",
    summary='常规数据分页列表接口',
    description='用于获取常规数据分页列表',
    response_model=PageResponseModel[OaProjectCateBaseModel],
    dependencies=[UserInterfaceAuthDependency('basicdata:project:cate:list')],
)

async def list_page(
    page_query: Annotated[ProjectCatePageQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaProjectCate)],
) -> Response:
    result_list = await ProjectCateService.get_page_list_service(query_db, page_query, data_scope_sql, True)
    return ResponseUtil.success(model_content=result_list)

@basic_project_cate_controller.post(
    "/add",
    summary='新增常规数据接口',
    description='用于新增常规数据',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('basicdata:project:cate:add')],
)
async def add_industry(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: OaProjectCateBaseModel,
) -> Response:
    result = await ProjectCateService.add_service(query_db, model)
    logger.info(result.message)
    return ResponseUtil.success(data=result.message)

@basic_project_cate_controller.put(
    "/changeStatus",
    summary='修改常规数据状态接口',
    description='用于修改常规数据状态',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('basicdata:project:cate:del')],
)
async def change_status_industry(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: OaProjectCateBaseModel,
) -> Response:
    basic_result = await ProjectCateService.change_status_service(query_db, model)
    logger.info(basic_result.message)
    return ResponseUtil.success(data=basic_result.message)

@basic_project_cate_controller.put(
    "/update",
    summary='修改常规数据接口',
    description='用于修改常规数据',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('basicdata:project:cate:edit')],
)
async def update_industry(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: OaProjectCateBaseModel,
) -> Response:
    basic_result = await ProjectCateService.update_service(query_db, model)
    logger.info(basic_result.message)
    return ResponseUtil.success(data=basic_result.message)

@basic_project_cate_controller.get(
    "/detail/{id}",
    summary='获取常规数据详情接口',
    description='用于获取常规数据详情',
    response_model=OaProjectCateBaseModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:project:cate:detail')],
)
async def get_info_by_id(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: Annotated[int, Path()],
) -> Response:
    try:
        link_info = await ProjectCateService.get_info_service(query_db, id)
        return ResponseUtil.success(data=ModelConverter.time_format(ModelConverter.to_dict(link_info)))
    except Exception as e:
        logger.error(e)
        return ResponseUtil.failure("查询失败")


