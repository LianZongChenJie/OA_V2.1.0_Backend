from datetime import datetime
from typing import Annotated
from fastapi import Request, Response, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import urllib.parse

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import DataResponseModel
from module_admin.entity.vo.import_vo import ImportResponseModel
from module_admin.service.admin_import_service import AdminImportService
from module_admin.service.customer_import_service import CustomerImportService
from exceptions.exception import ServiceException
from utils.log_util import logger
from utils.response_util import ResponseUtil
from module_admin.entity.vo.user_vo import CurrentUserModel


import_controller = APIRouterPro(
    prefix='/common/import', 
    order_num=99, 
    tags=['导入管理'], 
    dependencies=[PreAuthDependency()]
)


@import_controller.get(
    '/admin/template',
    summary='下载员工导入模板接口',
    description='用于下载员工信息 Excel 导入模板',
    dependencies=[UserInterfaceAuthDependency('system:user:import')],
)
async def download_admin_import_template(
    request: Request,
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """下载员工导入 Excel 模板"""
    try:
        template_file = await AdminImportService.generate_admin_import_template()
        filename = f'员工信息导入模板_{datetime.now().strftime("%Y%m%d")}.xlsx'
        encoded_filename = urllib.parse.quote(filename)

        response = StreamingResponse(
            template_file,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{encoded_filename}"
        response.headers["Content-Encoding"] = "identity"
        response.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        logger.info(f'下载员工导入模板成功，文件名：{filename}')
        return response
    except ServiceException as e:
        logger.error(f'下载模板失败：{e.message}')
        return ResponseUtil.error(msg=e.message.encode('utf-8').decode('latin-1'))
    except Exception as e:
        error_msg = f'下载失败：{str(e)}'
        logger.error(error_msg, exc_info=True)
        return ResponseUtil.error(msg=error_msg.encode('utf-8').decode('latin-1'))


@import_controller.post(
    '/admin',
    summary='导入员工信息接口',
    description='用于批量导入员工信息',
    response_model=ImportResponseModel,
    dependencies=[UserInterfaceAuthDependency('system:user:import')],
)
@Log(title='员工管理', business_type=BusinessType.IMPORT)
async def import_admin_data(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    file: Annotated[UploadFile, File(description='员工导入 Excel 文件')],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """批量导入员工信息"""
    try:
        result = await AdminImportService.import_admin_services(
            query_db=query_db,
            file=file,
            current_user_id=current_user.user.user_id
        )
        logger.info(f'导入员工数据结果：成功{result.success_count}条，失败{result.fail_count}条')
        return ResponseUtil.success(data=result.model_dump())
    except ServiceException as e:
        logger.error(f'导入员工失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        error_msg = f'导入失败：{str(e)}'
        logger.error(error_msg, exc_info=True)
        return ResponseUtil.error(msg=error_msg)


@import_controller.get(
    '/customer/template',
    summary='下载客户导入模板接口',
    description='用于下载客户信息 Excel 导入模板',
    dependencies=[UserInterfaceAuthDependency('crm:customer:import')],
)
async def download_customer_import_template(
    request: Request,
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """下载客户导入 Excel 模板"""
    try:
        template_file = await CustomerImportService.generate_customer_import_template()
        filename = f'客户信息导入模板_{datetime.now().strftime("%Y%m%d")}.xlsx'
        encoded_filename = urllib.parse.quote(filename)

        response = StreamingResponse(
            template_file,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{encoded_filename}"
        response.headers["Content-Encoding"] = "identity"
        response.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        logger.info(f'下载客户导入模板成功，文件名：{filename}')
        return response
    except ServiceException as e:
        logger.error(f'下载模板失败：{e.message}')
        return ResponseUtil.error(msg=e.message.encode('utf-8').decode('latin-1'))
    except Exception as e:
        error_msg = f'下载失败：{str(e)}'
        logger.error(error_msg, exc_info=True)
        return ResponseUtil.error(msg=error_msg.encode('utf-8').decode('latin-1'))


@import_controller.post(
    '/customer',
    summary='导入客户信息接口',
    description='用于批量导入客户信息',
    response_model=ImportResponseModel,
    dependencies=[UserInterfaceAuthDependency('crm:customer:import')],
)
@Log(title='客户管理', business_type=BusinessType.IMPORT)
async def import_customer_data(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    file: Annotated[UploadFile, File(description='客户导入 Excel 文件')],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    type: Annotated[str, Query(description='客户类型：sea 公海，other 私海')] = 'sea',
) -> Response:
    """批量导入客户信息"""
    try:
        belong_uid = current_user.user.user_id if type != 'sea' else 0
        belong_did = current_user.user.dept_id if type != 'sea' else 0
        
        result = await CustomerImportService.import_customer_services(
            query_db=query_db,
            file=file,
            current_user_id=current_user.user.user_id,
            belong_uid=belong_uid,
            belong_did=belong_did,
            customer_type=type
        )
        logger.info(f'导入客户数据结果：成功{result.success_count}条，失败{result.fail_count}条')
        return ResponseUtil.success(model_content=result)
    except ServiceException as e:
        logger.error(f'导入客户失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        error_msg = f'导入失败：{str(e)}'
        logger.error(error_msg, exc_info=True)
        return ResponseUtil.error(msg=error_msg)
