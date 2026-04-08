from datetime import datetime
from typing import Any

from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_project.entity.do.project_do import OaProject
from module_project.entity.do.project_document_do import OaProjectDocument
from module_project.entity.vo.project_document_vo import ProjectDocumentPageQueryModel
from utils.page_util import PageUtil


class ProjectDocumentDao:
    """
    项目文档管理模块数据库操作层
    """

    @classmethod
    async def get_project_document_detail_by_id(cls, db: AsyncSession, document_id: int) -> OaProjectDocument | None:
        """
        根据文档 id 获取文档详细信息

        :param db: orm 对象
        :param document_id: 文档 id
        :return: 文档信息对象
        """
        document_info = (
            (await db.execute(select(OaProjectDocument).where(OaProjectDocument.id == document_id)))
            .scalars()
            .first()
        )

        return document_info

    @classmethod
    async def get_project_document_list(
            cls, db: AsyncSession, query_object: ProjectDocumentPageQueryModel, 
            user_id: int, is_project_admin: bool = False, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        根据查询参数获取项目文档列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param user_id: 当前用户ID
        :param is_project_admin: 是否是项目管理
        :param is_page: 是否开启分页
        :return: 项目文档列表信息对象
        """
        # 构建基础查询
        query = select(OaProjectDocument)

        # 构建条件列表
        conditions = []
        conditions.append(OaProjectDocument.delete_time == 0)

        # 关键词搜索
        if query_object.keywords:
            conditions.append(
                or_(
                    OaProjectDocument.title.like(f'%{query_object.keywords}%'),
                    OaProjectDocument.content.like(f'%{query_object.keywords}%')
                )
            )

        # 项目ID筛选
        if query_object.project_id:
            conditions.append(OaProjectDocument.project_id == query_object.project_id)
        else:
            # 如果没有指定项目ID，则查询当前用户有权限的项目
            # 这里简化处理，实际应该查询用户参与的项目
            if not is_project_admin:
                conditions.append(
                    or_(
                        OaProjectDocument.admin_id == user_id,
                        # 实际应该关联查询用户参与的项目
                        # OaProjectDocument.project_id.in_(user_project_ids)
                    )
                )

        # 应用所有条件
        if conditions:
            query = query.where(*conditions)

        # 排序
        query = query.order_by(OaProjectDocument.create_time.desc())

        # 分页查询
        document_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return document_list

    @classmethod
    async def add_project_document_dao(cls, db: AsyncSession, document: OaProjectDocument) -> OaProjectDocument:
        """
        新增项目文档数据库操作

        :param db: orm 对象
        :param document: 文档对象
        :return:
        """
        db.add(document)
        await db.flush()

        return document

    @classmethod
    async def edit_project_document_dao(cls, db: AsyncSession, document_id: int, document_data: dict) -> None:
        """
        编辑项目文档数据库操作

        :param db: orm 对象
        :param document_id: 文档ID
        :param document_data: 需要更新的文档数据
        :return:
        """
        await db.execute(
            update(OaProjectDocument)
            .where(OaProjectDocument.id == document_id)
            .values(**document_data)
        )

    @classmethod
    async def delete_project_document_dao(cls, db: AsyncSession, document_id: int, delete_time: int) -> None:
        """
        删除项目文档数据库操作（逻辑删除）

        :param db: orm 对象
        :param document_id: 文档ID
        :param delete_time: 删除时间
        :return:
        """
        await db.execute(
            update(OaProjectDocument)
            .where(OaProjectDocument.id == document_id)
            .values(delete_time=delete_time)
        )
