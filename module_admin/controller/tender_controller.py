from datetime import datetime
from typing import Annotated, Any
from fastapi import Request, Response, Query, Path, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy import select  # 新增：导入select函数
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.encoders import jsonable_encoder
import urllib.parse

from module_admin.entity.do.tender_do import OaProjectTenderAttachment

import os
from fastapi.responses import FileResponse
from utils.file_util import UPLOAD_DIR

# 模拟缺失的模型定义（项目中已有可删除）
from pydantic import BaseModel
class UserModel(BaseModel):
    """模拟用户模型"""
    user_name: str

class CurrentUserModel(BaseModel):
    """模拟当前用户模型"""
    user: UserModel

# 原有导入
from common.annotation.log_annotation import Log
from common.aspect.data_scope import DataScopeDependency
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import DataResponseModel, DynamicResponseModel, PageResponseModel, ResponseBaseModel
from module_admin.entity.vo.tender_vo import (
    TenderModel, TenderPageQueryModel, AddTenderModel, EditTenderModel,
    DeleteTenderModel, AddTenderAttachmentModel, DeleteTenderAttachmentModel,
    TenderAttachmentModel, TenderImportResponseModel
)
from module_admin.service.tender_service import TenderService
from exceptions.exception import ServiceException  # 新增：导入自定义异常
from utils.log_util import logger
from utils.response_util import ResponseUtil

# 路由定义
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
    """获取投标分页列表"""
    try:
        tender_page_query_result = await TenderService.get_tender_list_services(
            query_db, tender_page_query, is_page=True
        )
        logger.info('获取投标列表成功')

        # 统一处理返回结果
        if isinstance(tender_page_query_result, list):
            processed_data = [
                item.model_dump(by_alias=True) if hasattr(item, 'model_dump')
                else jsonable_encoder(item)
                for item in tender_page_query_result
            ]
            return ResponseUtil.success(data=processed_data)
        elif hasattr(tender_page_query_result, 'model_dump'):
            return ResponseUtil.success(model_content=tender_page_query_result)
        else:
            return ResponseUtil.success(data=tender_page_query_result)
    except Exception as e:
        logger.error(f'获取投标列表失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'获取列表失败：{str(e)}')

@tender_controller.get(
    '/{tender_id}',
    summary='获取投标详情接口',
    description='用于获取投标详细信息',
    response_model=DynamicResponseModel[TenderModel],
    dependencies=[UserInterfaceAuthDependency('tender:tender:query')],
)
async def get_tender_detail(
        request: Request,
        tender_id: Annotated[int, Path(description='投标 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """获取投标详情"""
    try:
        tender_detail = await TenderService.tender_detail_services(query_db, tender_id)
        logger.info(f'获取投标详情成功，ID：{tender_id}')

        if tender_detail and hasattr(tender_detail, 'model_dump'):
            return ResponseUtil.success(model_content=tender_detail)
        return ResponseUtil.success(data=tender_detail)
    except ServiceException as e:
        logger.error(f'获取投标详情失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'获取投标详情失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'获取详情失败：{str(e)}')

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
    """新增投标"""
    try:
        add_tender.create_time = datetime.now()
        add_tender.update_time = datetime.now()
        await TenderService.add_tender_services(query_db, add_tender)
        logger.info(f'用户{current_user.user.user_name}新增投标成功')
        return ResponseUtil.success(msg='新增投标成功')
    except ServiceException as e:
        logger.error(f'新增投标失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'新增投标失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'新增失败：{str(e)}')

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
    """编辑投标"""
    try:
        edit_tender.update_time = datetime.now()
        await TenderService.edit_tender_services(query_db, edit_tender)
        logger.info(f'用户{current_user.user.user_name}编辑投标成功，ID：{edit_tender.id}')
        return ResponseUtil.success(msg='编辑投标成功')
    except ServiceException as e:
        logger.error(f'编辑投标失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'编辑投标失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'编辑失败：{str(e)}')

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
    """删除投标（软删除）"""
    try:
        delete_tender_obj = DeleteTenderModel(
            ids=ids,
            update_by=current_user.user.user_name,
            update_time=datetime.now()
        )
        await TenderService.delete_tender_services(query_db, delete_tender_obj)
        logger.info(f'用户{current_user.user.user_name}删除投标成功，ID：{ids}')
        return ResponseUtil.success(msg='删除投标成功')
    except ServiceException as e:
        logger.error(f'删除投标失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'删除投标失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'删除失败：{str(e)}')

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
    """新增投标附件"""
    try:
        await TenderService.add_tender_attachment_services(query_db, attachment)
        logger.info(f'新增投标附件成功，投标ID：{attachment.project_tender_id}')
        return ResponseUtil.success(msg='新增投标附件成功')
    except ServiceException as e:
        logger.error(f'新增投标附件失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'新增投标附件失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'新增附件失败：{str(e)}')

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
    """删除投标附件（软删除）"""
    try:
        delete_attachment_obj = DeleteTenderAttachmentModel(ids=ids)
        await TenderService.delete_tender_attachment_services(query_db, delete_attachment_obj)
        logger.info(f'删除投标附件成功，ID：{ids}')
        return ResponseUtil.success(msg='删除投标附件成功')
    except ServiceException as e:
        logger.error(f'删除投标附件失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'删除投标附件失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'删除附件失败：{str(e)}')

@tender_controller.get(
    '/import/template',
    summary='下载投标导入模板接口',
    description='用于下载投标信息Excel导入模板',
    dependencies=[UserInterfaceAuthDependency('tender:tender:import')],
)
async def download_tender_import_template(
        request: Request,
) -> Response:
    """下载投标导入Excel模板（修复中文编码问题）"""
    try:
        template_file = await TenderService.generate_tender_import_template()
        filename = f'投标信息导入模板_{datetime.now().strftime("%Y%m%d")}.xlsx'
        encoded_filename = urllib.parse.quote(filename)

        response = StreamingResponse(
            template_file,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{encoded_filename}"
        response.headers["Content-Encoding"] = "identity"
        response.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        logger.info(f'下载投标导入模板成功，文件名：{filename}')
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
    summary='导入投标信息接口',
    description='用于批量导入投标信息',
    response_model=TenderImportResponseModel,
    dependencies=[UserInterfaceAuthDependency('tender:tender:import')],
)
@Log(title='投标管理', business_type=BusinessType.IMPORT)
async def import_tender(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        file: UploadFile = File(..., description='Excel导入文件')
) -> Response:
    """批量导入投标信息"""
    try:
        import_result = await TenderService.import_tender_services(query_db, file)
        logger.info(f'用户{current_user.user.user_name}导入投标信息成功，成功{import_result.success_count}条，失败{import_result.fail_count}条')
        return ResponseUtil.success(data=import_result.model_dump())
    except ServiceException as e:
        logger.error(f'导入投标信息失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'导入投标信息失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'导入失败：{str(e)}')



@tender_controller.post(
    '/attachment/upload',
    summary='上传投标附件接口',
    description='用于上传投标附件（支持单文件上传）',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('tender:attachment:upload')],
)
@Log(title='投标附件', business_type=BusinessType.INSERT)
async def upload_tender_attachment(
        request: Request,
        project_tender_id: Annotated[int, Query(..., description='投标ID')],
        file: Annotated[UploadFile, File(..., description='附件文件')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        sort: Annotated[int, Query(description='排序值')] = 0,
) -> Response:
    """上传投标附件"""
    try:
        # 调用Service层上传逻辑
        upload_result = await TenderService.upload_tender_attachment_services(
            query_db, project_tender_id, sort, file
        )

        # 正确从data字段获取文件信息（Service层返回的CrudResponseModel结构）
        file_data = upload_result.result if upload_result.result else {}

        # 构造前端需要的回显数据
        response_data = {
            "file_name": file_data.get("file_name", ""),
            "file_path": file_data.get("file_path", ""),
            "file_size": file_data.get("file_size", 0),
            "file_ext": file_data.get("file_ext", ""),
            "file_mime": file_data.get("file_mime", ""),
            "sort": file_data.get("sort", sort),
            "attachment_id": file_data.get("attachment_id", "")  # 可选：如果DAO层返回了附件ID，可补充
        }

        logger.info(f'投标附件上传成功，文件名：{file_data.get("file_name", "")}，投标ID：{project_tender_id}')
        return ResponseUtil.success(msg="上传成功", data=response_data)

    # 针对性捕获ServiceException（业务异常）
    except ServiceException as e:
        logger.error(f'投标附件上传失败：{e.message}')
        return ResponseUtil.error(msg=e.message)

    # 捕获其他未知异常
    except Exception as e:
        error_msg = f'附件上传失败：{str(e)}'
        logger.error(error_msg, exc_info=True)
        return ResponseUtil.error(msg=error_msg)



@tender_controller.get(
    '/attachment/download/{attachment_id}',
    summary='下载投标附件接口',
    description='用于下载投标附件',
    dependencies=[UserInterfaceAuthDependency('tender:attachment:download')],
)
async def download_tender_attachment(
        request: Request,
        attachment_id: Annotated[int, Path(description='附件ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """下载投标附件"""
    try:
        # 查询附件信息
        query = select(OaProjectTenderAttachment).where(
            OaProjectTenderAttachment.id == attachment_id,
            OaProjectTenderAttachment.delete_time == 0
        )
        attachment = (await query_db.execute(query)).scalars().first()

        if not attachment:
            logger.warning(f'附件不存在或已删除，ID：{attachment_id}')
            return ResponseUtil.error(msg='附件不存在或已删除')

        # 拼接绝对路径
        absolute_path = os.path.join(UPLOAD_DIR, attachment.file_path)
        if not os.path.exists(absolute_path):
            logger.error(f'附件文件不存在，路径：{absolute_path}')
            return ResponseUtil.error(msg='附件文件已被删除')

        # 处理中文文件名编码
        encoded_filename = urllib.parse.quote(attachment.file_name)

        # 返回文件响应
        response = FileResponse(
            path=absolute_path,
            media_type=attachment.file_mime or 'application/octet-stream',
            filename=attachment.file_name
        )
        response.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{encoded_filename}"

        logger.info(f'下载附件成功，ID：{attachment_id}，文件名：{attachment.file_name}')
        return response
    except Exception as e:
        logger.error(f'下载附件失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'下载失败：{str(e)}')