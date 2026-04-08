from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_project.dao.project_document_dao import ProjectDocumentDao
from module_project.entity.do.project_document_do import OaProjectDocument
from module_project.entity.vo.project_document_vo import (
    AddProjectDocumentModel,
    DeleteProjectDocumentModel,
    EditProjectDocumentModel,
    ProjectDocumentModel,
    ProjectDocumentPageQueryModel,
)
from utils.common_util import CamelCaseUtil
from utils.log_util import logger


class ProjectDocumentService:
    """
    项目文档管理服务层
    """

    @classmethod
    async def get_project_document_list_services(
            cls, query_db: AsyncSession, query_object: ProjectDocumentPageQueryModel,
            user_id: int, is_project_admin: bool = False, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取项目文档列表信息 service

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param user_id: 当前用户ID
        :param is_project_admin: 是否是项目管理
        :param is_page: 是否开启分页
        :return: 项目文档列表信息对象
        """
        document_list_result = await ProjectDocumentDao.get_project_document_list(
            query_db, query_object, user_id, is_project_admin, is_page
        )

        return document_list_result

    @classmethod
    async def add_project_document_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddProjectDocumentModel, current_user_id: int
    ) -> CrudResponseModel:
        """
        新增项目文档信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增文档对象
        :param current_user_id: 当前登录用户 ID
        :return: 新增文档校验结果
        """
        try:
            current_time = int(datetime.now().timestamp())
            
            add_document = OaProjectDocument(
                title=page_object.title,
                content=page_object.content if page_object.content else '',
                md_content=page_object.md_content if page_object.md_content else '',
                project_id=page_object.project_id if page_object.project_id else 0,
                did=page_object.did if page_object.did else 0,
                admin_id=current_user_id,
                file_ids=page_object.file_ids if page_object.file_ids else '',
                create_time=current_time,
                update_time=current_time,
                delete_time=0
            )
            
            await ProjectDocumentDao.add_project_document_dao(query_db, add_document)
            await query_db.flush()
            logger.info(f'新增项目文档成功，ID: {add_document.id}')
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            logger.error(f'新增项目文档失败: {str(e)}')
            raise e

    @classmethod
    async def edit_project_document_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditProjectDocumentModel, current_user_id: int
    ) -> CrudResponseModel:
        """
        编辑项目文档信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑文档对象
        :param current_user_id: 当前登录用户 ID
        :return: 编辑文档校验结果
        """
        document_info = await cls.project_document_detail_services(query_db, page_object.id)

        if not document_info or not document_info.id:
            raise ServiceException(message='文档不存在')

        # 检查权限：只有创建人可以编辑
        if document_info.admin_id != current_user_id:
            raise ServiceException(message='你不是该文档的创建人，无权限编辑')

        try:
            update_time = int(datetime.now().timestamp())
            
            # 构建更新数据
            update_data = {}
            if page_object.title is not None:
                update_data['title'] = page_object.title
            if page_object.content is not None:
                update_data['content'] = page_object.content
            if page_object.md_content is not None:
                update_data['md_content'] = page_object.md_content
            if page_object.project_id is not None:
                update_data['project_id'] = page_object.project_id
            if page_object.did is not None:
                update_data['did'] = page_object.did
            if page_object.file_ids is not None:
                update_data['file_ids'] = page_object.file_ids
            
            update_data['update_time'] = update_time
            
            await ProjectDocumentDao.edit_project_document_dao(query_db, page_object.id, update_data)
            await query_db.commit()
            logger.info(f'编辑项目文档成功，ID: {page_object.id}')
            return CrudResponseModel(is_success=True, message='更新成功')
        except Exception as e:
            await query_db.rollback()
            logger.error(f'编辑项目文档失败: {str(e)}')
            raise e

    @classmethod
    async def delete_project_document_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeleteProjectDocumentModel, current_user_id: int
    ) -> CrudResponseModel:
        """
        删除项目文档信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 删除文档对象
        :param current_user_id: 当前登录用户 ID
        :return: 删除文档校验结果
        """
        document_info = await cls.project_document_detail_services(query_db, page_object.id)

        if not document_info or not document_info.id:
            raise ServiceException(message='文档不存在')

        # 检查权限：只有创建人可以删除
        if document_info.admin_id != current_user_id:
            raise ServiceException(message='你不是该文档的创建人，无权限删除')

        try:
            delete_time = int(datetime.now().timestamp())
            await ProjectDocumentDao.delete_project_document_dao(query_db, page_object.id, delete_time)
            await query_db.commit()
            logger.info(f'删除项目文档成功，ID: {page_object.id}')
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await query_db.rollback()
            logger.error(f'删除项目文档失败: {str(e)}')
            raise e

    @classmethod
    async def project_document_detail_services(cls, query_db: AsyncSession, document_id: int) -> ProjectDocumentModel:
        """
        获取项目文档详细信息 service

        :param query_db: orm 对象
        :param document_id: 文档 id
        :return: 文档 id 对应的信息
        """
        document = await ProjectDocumentDao.get_project_document_detail_by_id(query_db, document_id)
        
        if not document:
            return ProjectDocumentModel()
        
        # 手动构建字典，避免触发懒加载
        document_dict = {
            'id': document.id,
            'project_id': document.project_id,
            'admin_id': document.admin_id,
            'title': document.title,
            'did': document.did,
            'file_ids': document.file_ids,
            'content': document.content,
            'md_content': document.md_content,
            'create_time': document.create_time,
            'update_time': document.update_time,
            'delete_time': document.delete_time,
        }
        
        result = ProjectDocumentModel(**document_dict)
        return result
