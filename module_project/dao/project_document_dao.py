from datetime import datetime
from typing import Any

from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.user_do import SysUser
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
        from sqlalchemy import text
        
        # 构建 WHERE 条件
        conditions = ["d.delete_time = 0"]
        params = {}
        
        # 关键词搜索
        if query_object.keywords:
            conditions.append("(d.title LIKE :keywords OR d.content LIKE :keywords)")
            params['keywords'] = f"%{query_object.keywords}%"
        
        # 项目ID筛选
        if query_object.project_id:
            conditions.append("d.project_id = :project_id")
            params['project_id'] = query_object.project_id
        else:
            # 如果没有指定项目ID，则查询当前用户有权限的项目
            if not is_project_admin:
                conditions.append("d.admin_id = :user_id")
                params['user_id'] = user_id
        
        where_clause = " AND ".join(conditions)
        
        # 构建完整 SQL 查询
        sql = text(f"""
            SELECT 
                d.id,
                d.title,
                d.project_id AS projectId,
                d.content,
                d.file_ids AS fileIds,
                d.admin_id AS adminId,
                d.create_time AS createTime,
                d.update_time AS updateTime,
                d.delete_time AS deleteTime,
                p.name AS projectName,
                u.nick_name AS adminName,
                u.user_name AS userName,
                FROM_UNIXTIME(d.create_time, '%Y-%m-%d %H:%i:%s') AS createTimeStr,
                FROM_UNIXTIME(d.update_time, '%Y-%m-%d %H:%i:%s') AS updateTimeStr
            FROM oa_project_document d
            LEFT JOIN oa_project p ON d.project_id = p.id
            LEFT JOIN sys_user u ON d.admin_id = u.user_id
            WHERE {where_clause}
            ORDER BY d.create_time DESC
        """)
        
        # 执行总数查询
        count_sql = text(f"""
            SELECT COUNT(*) as total
            FROM oa_project_document d
            LEFT JOIN oa_project p ON d.project_id = p.id
            LEFT JOIN sys_user u ON d.admin_id = u.user_id
            WHERE {where_clause}
        """)
        
        # 执行总数查询
        count_result = await db.execute(count_sql, params)
        total = count_result.scalar()
        
        # 添加分页参数
        page_num = query_object.page_num if query_object.page_num else 1
        page_size = query_object.page_size if query_object.page_size else 20
        offset = (page_num - 1) * page_size
        params['limit'] = page_size
        params['offset'] = offset
        
        # 添加分页
        sql_with_limit = text(f"{sql.text} LIMIT :limit OFFSET :offset")
        
        # 执行分页查询
        result = await db.execute(sql_with_limit, params)
        rows = result.mappings().all()
        
        # 转换为字典列表并处理数据类型
        document_list = []
        for row in rows:
            doc_dict = dict(row)
            
            # 处理数值类型
            for key in ['id', 'projectId', 'adminId', 'createTime', 'updateTime', 'deleteTime']:
                if key in doc_dict and doc_dict[key] is not None:
                    doc_dict[key] = int(doc_dict[key])
            
            # 处理字符串默认值
            if 'fileIds' not in doc_dict or doc_dict['fileIds'] is None:
                doc_dict['fileIds'] = ""
            if 'content' not in doc_dict or doc_dict['content'] is None:
                doc_dict['content'] = ""
            
            document_list.append(doc_dict)
        
        # 计算是否有下一页
        has_next = page_num * page_size < total
        
        # 返回分页结果（使用驼峰命名以匹配 PageModel 的 alias）
        if is_page:
            return {
                'rows': document_list,
                'pageNum': page_num,
                'pageSize': page_size,
                'total': total,
                'hasNext': has_next
            }
        else:
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
