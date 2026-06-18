# module_contract/controller/contract_attachment_controller.py
import os
import urllib.parse
from typing import Annotated

from fastapi import File, Path, Query, Request, Response, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import DataResponseModel, ResponseBaseModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_contract.entity.do.contract_attachment_do import OaContractAttachment
from module_contract.entity.vo.contract_vo import (
    AddContractAttachmentModel,
    DeleteContractAttachmentModel,
)
from module_contract.service.contract_attachment_service import ContractAttachmentService
from exceptions.exception import ServiceException
from utils.file_util import CONTRACT_UPLOAD_DIR
from utils.log_util import logger
from utils.response_util import ResponseUtil

# 合同附件路由前缀
contract_attachment_controller = APIRouterPro(
    prefix='/system/contract',
    order_num=30,
    tags=['系统管理 - 合同附件管理'],
    dependencies=[PreAuthDependency()]
)


@contract_attachment_controller.post(
    '/attachment/upload',
    summary='上传合同附件接口',
    description='用于上传合同附件（支持单文件上传，仅上传文件，不关联数据库）',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:contract:add')],
)
@Log(title='合同附件', business_type=BusinessType.INSERT)
async def upload_contract_attachment(
        request: Request,
        file: Annotated[UploadFile, File(..., description='附件文件')],
) -> Response:
    """上传合同附件（仅上传文件，文件关联由前端在新增合同接口中处理）"""
    try:
        # 调用Service层上传逻辑
        upload_result = await ContractAttachmentService.upload_attachment_services(file)

        # 正确从result字段获取文件信息
        file_data = upload_result.result if upload_result.result else {}

        # 构造前端需要的回显数据（驼峰命名）
        response_data = {
            "fileName": file_data.get("fileName", ""),
            "filePath": file_data.get("filePath", ""),
            "fileSize": file_data.get("fileSize", 0),
            "fileExt": file_data.get("fileExt", ""),
            "fileMime": file_data.get("fileMime", "")
        }

        logger.info(f'合同附件上传成功，文件名：{file_data.get("fileName", "")}')
        return ResponseUtil.success(msg="上传成功", data=response_data)

    except ServiceException as e:
        logger.error(f'合同附件上传失败：{e.message}')
        return ResponseUtil.error(msg=e.message)

    except Exception as e:
        error_msg = f'附件上传失败：{str(e)}'
        logger.error(error_msg, exc_info=True)
        return ResponseUtil.error(msg=error_msg)


@contract_attachment_controller.get(
    '/attachment/list',
    summary='获取合同附件列表接口',
    description='根据合同ID获取该合同的所有附件列表',
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('system:contract:query')],
)
async def get_contract_attachment_list(
        request: Request,
        contract_id: Annotated[int, Query(description='合同ID', alias='contractId')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """获取合同附件列表"""
    try:
        attachment_list = await ContractAttachmentService.get_attachment_list_services(
            query_db, contract_id
        )
        logger.info(f'获取合同 {contract_id} 的附件列表成功，共 {len(attachment_list)} 条记录')
        return ResponseUtil.success(data=attachment_list)
    except ServiceException as e:
        logger.error(f'获取附件列表失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'获取附件列表失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'获取列表失败：{str(e)}')


@contract_attachment_controller.get(
    '/attachment/{attachment_id}',
    summary='获取合同附件详情接口',
    description='根据附件ID获取附件详细信息',
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('system:contract:query')],
)
async def get_contract_attachment_detail(
        request: Request,
        attachment_id: Annotated[int, Path(description='附件ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """获取附件详情"""
    try:
        attachment_detail = await ContractAttachmentService.get_attachment_detail_services(
            query_db, attachment_id
        )
        logger.info(f'获取附件 {attachment_id} 的详情成功')
        return ResponseUtil.success(data=attachment_detail)
    except ServiceException as e:
        logger.error(f'获取附件详情失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'获取附件详情失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'获取详情失败：{str(e)}')


@contract_attachment_controller.post(
    '/attachment',
    summary='新增合同附件接口',
    description='用于新增合同附件',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:contract:add')],
)
@Log(title='合同附件', business_type=BusinessType.INSERT)
async def add_contract_attachment(
        request: Request,
        attachment: AddContractAttachmentModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """新增合同附件"""
    try:
        await ContractAttachmentService.add_attachment_services(query_db, attachment)
        logger.info(f'新增合同附件成功，合同ID：{attachment.contract_id}')
        return ResponseUtil.success(msg='新增合同附件成功')
    except ServiceException as e:
        logger.error(f'新增合同附件失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'新增合同附件失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'新增附件失败：{str(e)}')


@contract_attachment_controller.delete(
    '/attachment/{ids}',
    summary='删除合同附件接口',
    description='用于删除合同附件',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:contract:remove')],
)
@Log(title='合同附件', business_type=BusinessType.DELETE)
async def delete_contract_attachment(
        request: Request,
        ids: Annotated[str, Path(description='需要删除的附件 ID，多个用逗号分隔')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """删除合同附件（软删除）"""
    try:
        delete_attachment_obj = DeleteContractAttachmentModel(ids=ids)
        await ContractAttachmentService.delete_attachment_services(query_db, delete_attachment_obj)
        logger.info(f'删除合同附件成功，ID：{ids}')
        return ResponseUtil.success(msg='删除合同附件成功')
    except ServiceException as e:
        logger.error(f'删除合同附件失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'删除合同附件失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'删除附件失败：{str(e)}')


@contract_attachment_controller.get(
    '/attachment/download/{attachment_id}',
    summary='下载合同附件接口',
    description='用于下载合同附件',
    dependencies=[UserInterfaceAuthDependency('system:contract:query')],
)
async def download_contract_attachment(
        request: Request,
        attachment_id: Annotated[int, Path(description='附件ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """下载合同附件"""
    try:
        # 查询附件信息
        query = select(OaContractAttachment).where(
            OaContractAttachment.id == attachment_id,
            OaContractAttachment.delete_time == 0
        )
        attachment = (await query_db.execute(query)).scalars().first()

        if not attachment:
            logger.warning(f'附件不存在或已删除，ID：{attachment_id}')
            return ResponseUtil.error(msg='附件不存在或已删除')

        # 拼接绝对路径
        absolute_path = os.path.join(CONTRACT_UPLOAD_DIR, attachment.file_path)
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
