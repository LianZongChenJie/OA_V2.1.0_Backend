from typing import Annotated

from fastapi import File, Form, Path, Query, Request, Response, UploadFile
from fastapi.responses import StreamingResponse
from pydantic_validation_decorator import ValidateFields
from sqlalchemy.sql import ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession
from common.aspect.data_scope import DataScopeDependency
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency, CurrentUserDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import PageResponseModel, ResponseBaseModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_basicdata.entity.do.public.template_do import OaTemplate
from module_basicdata.entity.vo.public.template_vo import TemplateRowModel, TemplatePageQueryModel, TemplateBaseModel
from module_basicdata.service.public.template_service import TemplateService
from utils.log_util import logger
from utils.response_util import ResponseUtil
from common.annotation.log_annotation import Log

template_controller = APIRouterPro(
    prefix='/basicdata/template', order_num=3, tags=['基础数据-公共模块-消息模板'], dependencies=[PreAuthDependency()]
)


@template_controller.get(
    '/list',
    summary='获取消息模板分页列表接口',
    description='用于获取消息模板分页列表',
    response_model=PageResponseModel[TemplateRowModel],
    dependencies=[UserInterfaceAuthDependency('basicdata:template:list')],
)
async def get_system_template_list(
    request: Request,
    template_page_query: Annotated[TemplatePageQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaTemplate)],
) -> Response:
    # 获取分页数据
    template_page_query_result = await TemplateService.get_user_list_services(
        query_db, template_page_query, data_scope_sql, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=template_page_query_result)

@template_controller.post(
    '/add',
    summary='新增消息模板接口',
    description='新增消息模板接口',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:template:add')],
)
# @ValidateFields(validate_model='add_template')
@Log(title='基础数据-公共数据-消息模板', business_type=BusinessType.INSERT)
async def add_basicdata_template(
    request: Request,
    add_template: TemplateBaseModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()]
) -> Response:
    add_template.admin_id = current_user.user.user_name
    add_template_result = await TemplateService.add_template_services(query_db, add_template)
    logger.info(add_template_result.message)

    return ResponseUtil.success(msg=add_template_result.message)

@template_controller.put(
    '/update',
    summary='更新消息模板接口',
    description='更新消息模板接口',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:template:update')],
)
async def update_basicdata_template(
    request: Request,
    add_template: TemplateBaseModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()]
) -> Response:
    add_template.admin_id = current_user.user.user_name
    add_template_result = await TemplateService.update_template_services(query_db, add_template)
    logger.info(add_template_result.message)

    return ResponseUtil.success(msg=add_template_result.message)

@template_controller.get(
    '/detail/{templateId}',
    summary='获取消息模板详情接口',
    description='获取消息模板详情接口',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:template:detail')],
)
async def get_basicdata_template_detail(
    request: Request,
    templateId: int,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    template_result = await TemplateService.detail_template_services(query_db, templateId)
    if not template_result:
        return ResponseUtil.error(msg="数据不存在")
    logger.info(template_result.to_dict())
    return ResponseUtil.success(data=template_result.to_dict())

@template_controller.delete(
    '/delete/{templateId}',
    summary='删除消息模板接口',
    description='删除消息模板接口',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:template:delete')],
)
async def del_basicdata_template(
    request: Request,
    templateId: int,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    template_result = await TemplateService.delete_template_services(query_db, templateId)
    logger.info(template_result)

    return ResponseUtil.success(msg="删除成功")