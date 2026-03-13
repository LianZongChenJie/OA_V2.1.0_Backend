from datetime import datetime
from typing import Annotated, Any, List
from fastapi import Request, Response, Query, Path, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.encoders import jsonable_encoder
import urllib.parse

import os
from fastapi.responses import FileResponse
from utils.file_util import UPLOAD_DIR

from common.annotation.log_annotation import Log
from common.aspect.data_scope import DataScopeDependency
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import DataResponseModel, DynamicResponseModel, PageResponseModel, ResponseBaseModel
from module_admin.entity.vo.website_account_vo import (
    WebsiteAccountModel, WebsiteAccountPageQueryModel, AddWebsiteAccountModel,
    EditWebsiteAccountModel, DeleteWebsiteAccountModel, SetWebsiteAccountStatusModel,
    WebsiteAccountImportResponseModel
)
from module_admin.service.website_account_service import WebsiteAccountService
from exceptions.exception import ServiceException
from utils.log_util import logger
from utils.response_util import ResponseUtil

tender_controller = APIRouterPro(
    prefix='/websiteaccount', order_num=100, tags=['网站账号管理'], dependencies=[PreAuthDependency()]
)

@tender_controller.get(
    '/list',
    summary='获取网站账号分页列表接口',
    description='用于获取网站账号分页列表',
    response_model=PageResponseModel[WebsiteAccountModel],
    dependencies=[UserInterfaceAuthDependency('websiteaccount:websiteaccount:list')],
)
async def get_website_account_list(
        request: Request,
        website_account_page_query: Annotated[WebsiteAccountPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """获取网站账号列表"""
    try:
        website_account_page_query_result = await WebsiteAccountService.get_website_account_list_services(
            query_db, website_account_page_query, is_page=True
        )
        logger.info('获取网站账号列表成功')

        if isinstance(website_account_page_query_result, list):
            processed_data = [
                item.model_dump(by_alias=True) if hasattr(item, 'model_dump')
                else jsonable_encoder(item)
                for item in website_account_page_query_result
            ]
            return ResponseUtil.success(data=processed_data)
        elif hasattr(website_account_page_query_result, 'model_dump'):
            return ResponseUtil.success(model_content=website_account_page_query_result)
        else:
            return ResponseUtil.success(data=website_account_page_query_result)
    except Exception as e:
        logger.error(f'获取网站账号列表失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'获取列表失败：{str(e)}')

@tender_controller.get(
    '/{account_id}',
    summary='获取网站账号详情接口',
    description='用于获取网站账号详细信息',
    response_model=DynamicResponseModel[WebsiteAccountModel],
    dependencies=[UserInterfaceAuthDependency('websiteaccount:websiteaccount:query')],
)
async def get_website_account_detail(
        request: Request,
        account_id: Annotated[int, Path(description='网站账号 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """获取网站账号详情"""
    try:
        account_detail = await WebsiteAccountService.website_account_detail_services(query_db, account_id)
        logger.info(f'获取网站账号详情成功，ID：{account_id}')

        if account_detail and hasattr(account_detail, 'model_dump'):
            return ResponseUtil.success(model_content=account_detail)
        return ResponseUtil.success(data=account_detail)
    except ServiceException as e:
        logger.error(f'获取网站账号详情失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'获取网站账号详情失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'获取详情失败：{str(e)}')

@tender_controller.post(
    '',
    summary='新增网站账号接口',
    description='用于新增网站账号',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('websiteaccount:websiteaccount:add')],
)
@Log(title='网站账号管理', business_type=BusinessType.INSERT)
async def add_website_account(
        request: Request,
        add_website_account: AddWebsiteAccountModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[Any, CurrentUserDependency()],
) -> Response:
    """新增网站账号"""
    try:
        await WebsiteAccountService.add_website_account_services(query_db, add_website_account)
        logger.info(f'用户{current_user.user.user_name if hasattr(current_user, "user") else "unknown"}新增网站账号成功')
        return ResponseUtil.success(msg='新增网站账号成功')
    except ServiceException as e:
        logger.error(f'新增网站账号失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'新增网站账号失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'新增失败：{str(e)}')

@tender_controller.put(
    '',
    summary='编辑网站账号接口',
    description='用于编辑网站账号',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('websiteaccount:websiteaccount:edit')],
)
@Log(title='网站账号管理', business_type=BusinessType.UPDATE)
async def edit_website_account(
        request: Request,
        edit_website_account: EditWebsiteAccountModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[Any, CurrentUserDependency()],
) -> Response:
    """编辑网站账号"""
    try:
        await WebsiteAccountService.edit_website_account_services(query_db, edit_website_account)
        logger.info(f'用户{current_user.user.user_name if hasattr(current_user, "user") else "unknown"}编辑网站账号成功，ID：{edit_website_account.id}')
        return ResponseUtil.success(msg='编辑网站账号成功')
    except ServiceException as e:
        logger.error(f'编辑网站账号失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'编辑网站账号失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'编辑失败：{str(e)}')

@tender_controller.delete(
    '/{ids}',
    summary='删除网站账号接口',
    description='用于删除网站账号',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('websiteaccount:websiteaccount:remove')],
)
@Log(title='网站账号管理', business_type=BusinessType.DELETE)
async def delete_website_account(
        request: Request,
        ids: Annotated[str, Path(description='需要删除的网站账号 ID，多个用逗号分隔')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[Any, CurrentUserDependency()],
) -> Response:
    """删除网站账号（软删除）"""
    try:
        delete_account_obj = DeleteWebsiteAccountModel(ids=ids)
        await WebsiteAccountService.delete_website_account_services(query_db, delete_account_obj)
        logger.info(f'用户{current_user.user.user_name if hasattr(current_user, "user") else "unknown"}删除网站账号成功，ID：{ids}')
        return ResponseUtil.success(msg='删除网站账号成功')
    except ServiceException as e:
        logger.error(f'删除网站账号失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'删除网站账号失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'删除失败：{str(e)}')

@tender_controller.put(
    '/status',
    summary='设置网站账号状态接口',
    description='用于设置网站账号的启用/禁用状态',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('websiteaccount:websiteaccount:set')],
)
@Log(title='网站账号管理', business_type=BusinessType.UPDATE)
async def set_website_account_status(
        request: Request,
        set_status: SetWebsiteAccountStatusModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[Any, CurrentUserDependency()],
) -> Response:
    """设置网站账号状态"""
    try:
        await WebsiteAccountService.set_website_account_status_services(query_db, set_status)
        logger.info(f'用户{current_user.user.user_name if hasattr(current_user, "user") else "unknown"}设置网站账号状态成功，ID：{set_status.id}')
        return ResponseUtil.success(msg='设置状态成功')
    except ServiceException as e:
        logger.error(f'设置网站账号状态失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'设置网站账号状态失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'设置失败：{str(e)}')

@tender_controller.get(
    '/import/template',
    summary='下载网站账号导入模板接口',
    description='用于下载网站账号信息Excel导入模板',
    dependencies=[UserInterfaceAuthDependency('websiteaccount:websiteaccount:import')],
)
async def download_website_account_import_template(
        request: Request,
) -> Response:
    """下载网站账号导入 Excel 模板"""
    try:
        template_file = await WebsiteAccountService.generate_website_account_import_template()
        filename = f'网站账号信息导入模板_{datetime.now().strftime("%Y%m%d")}.xlsx'
        encoded_filename = urllib.parse.quote(filename)

        response = StreamingResponse(
            template_file,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{encoded_filename}"
        response.headers["Content-Encoding"] = "identity"
        response.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        logger.info(f'下载网站账号导入模板成功，文件名：{filename}')
        return response
    except ServiceException as e:
        logger.error(f'下载模板失败：{e.message}')
        return ResponseUtil.error(msg=e.message.encode('utf-8').decode('latin-1'))
    except Exception as e:
        error_msg = f'下载失败：{str(e)}'
        logger.error(error_msg, exc_info=True)
        return ResponseUtil.error(msg=error_msg.encode('utf-8').decode('latin-1'))

@tender_controller.post(
    '/import',
    summary='导入网站账号信息接口',
    description='用于批量导入网站账号信息',
    response_model=WebsiteAccountImportResponseModel,
    dependencies=[UserInterfaceAuthDependency('websiteaccount:websiteaccount:import')],
)
@Log(title='网站账号管理', business_type=BusinessType.IMPORT)
async def import_website_account(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[Any, CurrentUserDependency()],
        file: UploadFile = File(..., description='Excel导入文件')
) -> Response:
    """批量导入网站账号信息"""
    try:
        import_result = await WebsiteAccountService.import_website_account_services(query_db, file)
        logger.info(f'用户{current_user.user.user_name if hasattr(current_user, "user") else "unknown"}导入网站账号信息成功，成功{import_result.success_count}条，失败{import_result.fail_count}条')
        return ResponseUtil.success(data=import_result.model_dump())
    except ServiceException as e:
        logger.error(f'导入网站账号信息失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'导入网站账号信息失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'导入失败：{str(e)}')
