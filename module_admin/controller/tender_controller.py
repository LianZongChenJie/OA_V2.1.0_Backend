from datetime import datetime
from typing import Annotated, Any

from fastapi import Request, Response, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.encoders import jsonable_encoder

# --- 模拟定义缺失的 CurrentUserModel ---
from pydantic import BaseModel

class UserModel(BaseModel):
    """模拟用户模型"""
    user_name: str

class CurrentUserModel(BaseModel):
    """模拟当前用户模型"""
    user: UserModel

# --- 原有导入 ---
from common.annotation.log_annotation import Log
from common.aspect.data_scope import DataScopeDependency
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import DataResponseModel, DynamicResponseModel, PageResponseModel, ResponseBaseModel
from module_admin.entity.vo.tender_vo import (
    TenderModel,
    TenderPageQueryModel,
    AddTenderModel,
    EditTenderModel,
    DeleteTenderModel,
    AddTenderAttachmentModel,
    DeleteTenderAttachmentModel,
    TenderAttachmentModel,
)
from module_admin.service.tender_service import TenderService
from utils.log_util import logger
from utils.response_util import ResponseUtil


tender_controller = APIRouterPro(
    prefix='/tender', order_num=100, tags=['招投标管理'], dependencies=[PreAuthDependency()]
)


@tender_controller.get(
    '/list',
    summary='获取投标分页列表接口',
    description='用于获取投标分页列表',
    response_model=PageResponseModel[TenderModel],
    dependencies=[UserInterfaceAuthDependency('tender:tender:list')],
)
async def get_tender_list(
        request: Request,
        tender_page_query: Annotated[TenderPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    # 获取分页数据
    tender_page_query_result = await TenderService.get_tender_list_services(
        query_db, tender_page_query, is_page=True
    )
    logger.info('获取投标列表成功')

    # 修复核心问题：处理列表类型的返回结果
    if isinstance(tender_page_query_result, list):
        # 如果返回的是列表，转换为字典列表后通过 data 参数传递
        processed_data = [
            item.model_dump(by_alias=True) if hasattr(item, 'model_dump')
            else jsonable_encoder(item)
            for item in tender_page_query_result
        ]
        return ResponseUtil.success(data=processed_data)
    elif hasattr(tender_page_query_result, 'model_dump'):
        # 如果是单个 Pydantic 模型对象，正常使用 model_content
        return ResponseUtil.success(model_content=tender_page_query_result)
    else:
        # 其他类型直接作为 data 返回
        return ResponseUtil.success(data=tender_page_query_result)


@tender_controller.get(
    '/{tender_id}',
    summary='获取投标详情接口',
    description='用于获取投标详细信息',
    response_model=DynamicResponseModel[TenderModel],  # 将 dict 改为 TenderModel
    dependencies=[UserInterfaceAuthDependency('tender:tender:query')],
)
async def get_tender_detail(
        request: Request,
        tender_id: Annotated[int, Path(description='投标 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    tender_detail = await TenderService.tender_detail_services(query_db, tender_id)
    logger.info('获取投标详情成功')

    # 统一处理详情接口的返回格式
    if tender_detail and hasattr(tender_detail, 'model_dump'):
        return ResponseUtil.success(model_content=tender_detail)
    return ResponseUtil.success(data=tender_detail)


@tender_controller.post(
    '',
    summary='新增投标接口',
    description='用于新增投标',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('tender:tender:add')],
)
@Log(title='投标管理', business_type=BusinessType.INSERT)
async def add_tender(
        request: Request,
        add_tender: AddTenderModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    add_tender.create_time = datetime.now()
    add_tender.update_time = datetime.now()
    # 调用服务层方法，返回的是 OaProjectTender 对象
    add_tender_result = await TenderService.add_tender_services(query_db, add_tender)
    logger.info('新增投标成功')

    return ResponseUtil.success(msg='新增投标成功')


@tender_controller.put(
    '',
    summary='编辑投标接口',
    description='用于编辑投标',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('tender:tender:edit')],
)
@Log(title='投标管理', business_type=BusinessType.UPDATE)
async def edit_tender(
        request: Request,
        edit_tender: EditTenderModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    edit_tender.update_time = datetime.now()
    edit_tender_result = await TenderService.edit_tender_services(query_db, edit_tender)
    logger.info('编辑投标成功')

    return ResponseUtil.success(msg='编辑投标成功')


@tender_controller.delete(
    '/{ids}',
    summary='删除投标接口',
    description='用于删除投标',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('tender:tender:remove')],
)
@Log(title='投标管理', business_type=BusinessType.DELETE)
async def delete_tender(
        request: Request,
        ids: Annotated[str, Path(description='需要删除的投标 ID，多个用逗号分隔')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    delete_tender_obj = DeleteTenderModel(
        ids=ids,
        update_by=current_user.user.user_name,
        update_time=datetime.now()
    )
    delete_tender_result = await TenderService.delete_tender_services(query_db, delete_tender_obj)
    logger.info('删除投标成功')

    return ResponseUtil.success(msg='删除投标成功')


@tender_controller.post(
    '/attachment',
    summary='新增投标附件接口',
    description='用于新增投标附件',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('tender:attachment:add')],
)
@Log(title='投标附件', business_type=BusinessType.INSERT)
async def add_tender_attachment(
        request: Request,
        attachment: AddTenderAttachmentModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    attachment_result = await TenderService.add_tender_attachment_services(query_db, attachment)
    logger.info('新增投标附件成功')

    return ResponseUtil.success(msg='新增投标附件成功')


@tender_controller.delete(
    '/attachment/{ids}',
    summary='删除投标附件接口',
    description='用于删除投标附件',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('tender:attachment:remove')],
)
@Log(title='投标附件', business_type=BusinessType.DELETE)
async def delete_tender_attachment(
        request: Request,
        ids: Annotated[str, Path(description='需要删除的附件 ID，多个用逗号分隔')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_attachment_obj = DeleteTenderAttachmentModel(ids=ids)
    delete_attachment_result = await TenderService.delete_tender_attachment_services(query_db, delete_attachment_obj)
    logger.info('删除投标附件成功')

    return ResponseUtil.success(msg='删除投标附件成功')