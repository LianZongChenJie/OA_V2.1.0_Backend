"""
在线文档管理服务层
"""
import time
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel
from exceptions.exception import ServiceException
from module_disk.dao.article_dao import ArticleDao
from module_disk.entity.do.article_do import OaArticle
from module_disk.entity.vo.article_vo import AddArticleModel, EditArticleModel
from utils.log_util import logger


class ArticleService:
    """
    在线文档管理服务层
    """

    @classmethod
    async def add_article_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddArticleModel,
            current_user_id: int
    ) -> CrudResponseModel:
        """
        新增在线文档 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增文档对象
        :param current_user_id: 当前登录用户 ID
        :return: 新增文档校验结果
        """
        try:
            current_time = int(time.time())

            add_article = OaArticle(
                name=page_object.name,
                origin_url=page_object.origin_url if page_object.origin_url else '',
                content=page_object.content if page_object.content else '',
                file_ids=page_object.file_ids if page_object.file_ids else '',
                admin_id=current_user_id,
                create_time=current_time,
                update_time=current_time,
                delete_time=0
            )

            result = await ArticleDao.add_article_dao(query_db, add_article)
            await query_db.commit()
            logger.info(f'新增在线文档成功，ID: {result.id}, 名称: {result.name}')
            return CrudResponseModel(is_success=True, message='新增成功', data={'id': result.id})
        except Exception as e:
            await query_db.rollback()
            logger.error(f'新增在线文档失败: {str(e)}')
            raise e

    @classmethod
    async def edit_article_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditArticleModel,
            current_user_id: int
    ) -> CrudResponseModel:
        """
        编辑在线文档 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑文档对象
        :param current_user_id: 当前登录用户 ID
        :return: 编辑文档校验结果
        """
        article_info = await ArticleDao.get_article_detail_by_id(query_db, page_object.id)

        if not article_info:
            raise ServiceException(message='文档不存在')

        if article_info.admin_id != current_user_id and current_user_id != 1:
            raise ServiceException(message='只有超级管理员和创建人才有权限操作')

        try:
            update_time = int(time.time())

            update_data = {}
            if page_object.name is not None:
                update_data['name'] = page_object.name
            if page_object.origin_url is not None:
                update_data['origin_url'] = page_object.origin_url
            if page_object.content is not None:
                update_data['content'] = page_object.content
            if page_object.file_ids is not None:
                update_data['file_ids'] = page_object.file_ids
            update_data['update_time'] = update_time

            await ArticleDao.edit_article_dao(query_db, page_object.id, update_data)
            await query_db.commit()
            logger.info(f'编辑在线文档成功，ID: {page_object.id}')
            return CrudResponseModel(is_success=True, message='编辑成功')
        except Exception as e:
            await query_db.rollback()
            logger.error(f'编辑在线文档失败: {str(e)}')
            raise e

    @classmethod
    async def article_detail_services(cls, query_db: AsyncSession, article_id: int) -> dict:
        """
        获取在线文档详细信息 service

        :param query_db: orm 对象
        :param article_id: 文档 id
        :return: 文档详细信息
        """
        article = await ArticleDao.get_article_detail_by_id(query_db, article_id)

        if not article:
            raise ServiceException(message='文档不存在')

        return {
            'id': article.id,
            'name': article.name,
            'origin_url': article.origin_url,
            'content': article.content,
            'file_ids': article.file_ids,
            'admin_id': article.admin_id,
            'create_time': article.create_time,
            'update_time': article.update_time,
        }
