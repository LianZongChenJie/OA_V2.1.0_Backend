# module_contract/service/contract_attachment_service.py
import logging
import os
from datetime import datetime
from typing import Any

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel
from exceptions.exception import ServiceException
from module_contract.dao.contract_attachment_dao import ContractAttachmentDao
from module_contract.entity.vo.contract_vo import (
    AddContractAttachmentModel,
    ContractAttachmentModel,
    DeleteContractAttachmentModel,
)
from utils.file_util import (
    CONTRACT_UPLOAD_DIR,
    ALLOWED_EXTENSIONS,
    allowed_file,
    generate_contract_file_path,
    generate_contract_file_path_without_id,
    save_upload_file,
    get_file_ext,
)

# 初始化日志器
logger = logging.getLogger(__name__)


class ContractAttachmentService:
    """
    销售合同附件管理模块业务逻辑层
    """

    @classmethod
    async def upload_attachment_services(
            cls, file: UploadFile
    ) -> CrudResponseModel:
        """
        上传合同附件（仅上传文件，不关联数据库）
        文件关联逻辑由前端在新增合同信息接口中处理

        :param file: 上传的文件对象
        :return: 上传结果
        """
        # 1. 校验文件格式
        logger.info(f'校验文件格式：{file.filename}')
        if not allowed_file(file.filename):
            raise ServiceException(
                message=f'文件格式不支持，仅支持：{", ".join(ALLOWED_EXTENSIONS)}，当前文件：{file.filename}'
            )

        absolute_path = None
        try:
            # 2. 生成文件存储路径（使用临时目录，不依赖合同ID）
            logger.info(f'生成文件存储路径：{file.filename}')
            relative_path, absolute_path = generate_contract_file_path_without_id(file.filename)
            logger.info(f'文件存储路径：相对路径={relative_path}，绝对路径={absolute_path}')

            # 确保目录存在
            file_dir = os.path.dirname(absolute_path)
            if not os.path.exists(file_dir):
                os.makedirs(file_dir, exist_ok=True)
                logger.info(f'创建目录：{file_dir}')

            # 3. 保存文件到本地
            logger.info(f'保存文件到本地：{absolute_path}')
            file_size = await save_upload_file(file, absolute_path)
            logger.info(f'文件保存成功，大小：{file_size} 字节')

            # 返回文件信息，供前端后续关联使用
            return CrudResponseModel(
                is_success=True,
                message='附件上传成功',
                result={
                    'fileName': file.filename,
                    'filePath': relative_path,
                    'fileSize': file_size,
                    'fileExt': get_file_ext(file.filename) or '',
                    'fileMime': file.content_type or 'application/octet-stream'
                }
            )
        except Exception as e:
            logger.error(f'附件上传失败：{str(e)}', exc_info=True)

            # 上传失败时删除已保存的文件
            if absolute_path and os.path.exists(absolute_path):
                os.remove(absolute_path)
                logger.info(f'删除已保存的文件：{absolute_path}')

            raise ServiceException(message=f'附件上传失败：{str(e)}') from e

    @classmethod
    async def get_attachment_list_services(
            cls, query_db: AsyncSession, contract_id: int
    ) -> list[dict[str, Any]]:
        """
        获取合同附件列表

        :param query_db: orm 对象
        :param contract_id: 合同ID
        :return: 附件列表
        """
        attachments = await ContractAttachmentDao.get_attachment_list(query_db, contract_id)

        result = []
        for attachment in attachments:
            attachment_dict = {
                'id': attachment.id,
                'contractId': attachment.contract_id,
                'fileName': attachment.file_name,
                'filePath': attachment.file_path,
                'fileSize': attachment.file_size,
                'fileExt': attachment.file_ext,
                'fileMime': attachment.file_mime,
                'sort': attachment.sort,
                'deleteTime': attachment.delete_time,
            }
            result.append(attachment_dict)

        return result

    @classmethod
    async def get_attachment_detail_services(
            cls, query_db: AsyncSession, attachment_id: int
    ) -> dict[str, Any]:
        """
        获取附件详情

        :param query_db: orm 对象
        :param attachment_id: 附件ID
        :return: 附件详情
        """
        attachment = await ContractAttachmentDao.get_attachment_by_id(query_db, attachment_id)

        if not attachment:
            raise ServiceException(message='附件不存在')

        return {
            'id': attachment.id,
            'contractId': attachment.contract_id,
            'fileName': attachment.file_name,
            'filePath': attachment.file_path,
            'fileSize': attachment.file_size,
            'fileExt': attachment.file_ext,
            'fileMime': attachment.file_mime,
            'sort': attachment.sort,
            'deleteTime': attachment.delete_time,
        }

    @classmethod
    async def add_attachment_services(
            cls, query_db: AsyncSession, page_object: AddContractAttachmentModel
    ) -> CrudResponseModel:
        """
        新增合同附件

        :param query_db: orm 对象
        :param page_object: 新增附件模型
        :return: 新增结果
        """
        try:
            # 构建附件数据
            attachment_data = {
                'contract_id': page_object.contract_id,
                'file_name': page_object.file_name,
                'file_path': page_object.file_path,
                'file_size': page_object.file_size or 0,
                'file_ext': page_object.file_ext or '',
                'file_mime': page_object.file_mime or '',
                'sort': page_object.sort or 0,
                'delete_time': 0,
            }

            await ContractAttachmentDao.add_attachment(query_db, attachment_data)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增附件成功')
        except Exception as e:
            await query_db.rollback()
            logger.error(f'新增附件失败：{str(e)}', exc_info=True)
            raise ServiceException(message=f'新增附件失败：{str(e)}') from e

    @classmethod
    async def delete_attachment_services(
            cls, query_db: AsyncSession, page_object: DeleteContractAttachmentModel
    ) -> CrudResponseModel:
        """
        删除合同附件（软删除）

        :param query_db: orm 对象
        :param page_object: 删除附件模型
        :return: 删除结果
        """
        if not page_object.ids:
            raise ServiceException(message='传入附件 id 为空')

        try:
            attachment_ids = [int(id_str.strip()) for id_str in page_object.ids.split(',') if id_str.strip()]
            if not attachment_ids:
                raise ServiceException(message='附件ID格式错误，应为数字，多个用逗号分隔')

            await ContractAttachmentDao.delete_attachment(query_db, attachment_ids)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='删除附件成功')
        except ValueError:
            raise ServiceException(message='附件ID必须为数字，多个用逗号分隔')
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f'删除附件失败：{str(e)}') from e

    @classmethod
    async def get_attachment_for_download(
            cls, query_db: AsyncSession, attachment_id: int
    ):
        """
        获取附件信息用于下载

        :param query_db: orm 对象
        :param attachment_id: 附件ID
        :return: 附件对象
        """
        attachment = await ContractAttachmentDao.get_attachment_by_id(query_db, attachment_id)
        if not attachment:
            raise ServiceException(message='附件不存在或已删除')
        return attachment
