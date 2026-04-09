"""
在线文档管理模块数据库操作层
"""
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from module_disk.entity.do.article_do import OaArticle


class ArticleDao:
    """
    在线文档管理模块数据库操作层
    """

    @classmethod
    async def get_article_detail_by_id(cls, db: AsyncSession, article_id: int) -> OaArticle | None:
        """
        根据文档 id 获取文档详细信息

        :param db: orm 对象
        :param article_id: 文档 id
        :return: 文档信息对象
        """
        article_info = (
            (await db.execute(select(OaArticle).where(OaArticle.id == article_id)))
            .scalars()
            .first()
        )
        return article_info

    @classmethod
    async def add_article_dao(cls, db: AsyncSession, article: OaArticle) -> OaArticle:
        """
        新增在线文档数据库操作

        :param db: orm 对象
        :param article: 文档对象
        :return: 文档对象
        """
        db.add(article)
        await db.flush()
        return article

    @classmethod
    async def edit_article_dao(cls, db: AsyncSession, article_id: int, update_data: dict) -> None:
        """
        编辑在线文档数据库操作

        :param db: orm 对象
        :param article_id: 文档 ID
        :param update_data: 需要更新的字段字典
        :return: None
        """
        await db.execute(
            update(OaArticle)
            .where(OaArticle.id == article_id)
            .values(**update_data)
        )
