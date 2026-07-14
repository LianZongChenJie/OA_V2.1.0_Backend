"""
简历知识库模块数据库操作层
"""
from typing import Any

from sqlalchemy import and_, or_, select, update, text
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_resume_kb.entity.do.resume_do import OaResume, OaResumeWork, OaResumeProject
from module_resume_kb.entity.vo.resume_vo import ResumePageQueryModel
from utils.page_util import PageUtil


class ResumeDao:
    """
    简历知识库模块数据库操作层
    """

    @classmethod
    async def get_resume_detail_by_id(cls, db: AsyncSession, resume_id: int) -> OaResume | None:
        """
        根据简历 id 获取简历详细信息

        :param db: orm 对象
        :param resume_id: 简历 id
        :return: 简历信息对象
        """
        resume_info = (
            (await db.execute(select(OaResume).where(OaResume.id == resume_id, OaResume.status == 1)))
            .scalars()
            .first()
        )
        return resume_info

    @classmethod
    async def get_resume_detail_by_uuid(cls, db: AsyncSession, resume_uuid: str) -> OaResume | None:
        """
        根据简历 uuid 获取简历详细信息

        :param db: orm 对象
        :param resume_uuid: 简历 uuid
        :return: 简历信息对象
        """
        resume_info = (
            (await db.execute(select(OaResume).where(OaResume.resume_uuid == resume_uuid, OaResume.status == 1)))
            .scalars()
            .first()
        )
        return resume_info

    @classmethod
    async def get_resume_list(
            cls, db: AsyncSession, query_object: ResumePageQueryModel,
            where_conditions: list, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        根据查询参数获取简历列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param where_conditions: 查询条件列表
        :param is_page: 是否开启分页
        :return: 简历列表信息对象
        """
        # 处理项目经验关键词搜索（需要关联表查询）
        resume_ids_from_project = None
        if query_object.project_keyword:
            project_keyword = f'%{query_object.project_keyword}%'
            project_query = select(OaResumeProject.resume_id).where(
                or_(
                    OaResumeProject.project_name.like(project_keyword),
                    OaResumeProject.description.like(project_keyword),
                )
            ).distinct()
            project_result = await db.execute(project_query)
            resume_ids_from_project = [row[0] for row in project_result.fetchall()]
            if resume_ids_from_project:
                where_conditions.append(OaResume.id.in_(resume_ids_from_project))
            else:
                # 无匹配项目，返回空结果
                where_conditions.append(OaResume.id == -1)

        # 处理工作经历中的公司/职位搜索（需要关联表查询）
        if query_object.company:
            company_keyword = f'%{query_object.company}%'
            work_query = select(OaResumeWork.resume_id).where(
                or_(
                    OaResumeWork.company.like(company_keyword),
                    OaResumeWork.description.like(company_keyword),
                )
            ).distinct()
            work_result = await db.execute(work_query)
            resume_ids_from_work = [row[0] for row in work_result.fetchall()]
            # 如果主表 current_company 已匹配，则取并集；否则只取关联表结果
            if resume_ids_from_work:
                where_conditions.append(
                    or_(
                        OaResume.current_company.like(company_keyword),
                        OaResume.id.in_(resume_ids_from_work),
                    )
                )

        if query_object.position:
            position_keyword = f'%{query_object.position}%'
            work_pos_query = select(OaResumeWork.resume_id).where(
                OaResumeWork.position.like(position_keyword)
            ).distinct()
            work_pos_result = await db.execute(work_pos_query)
            resume_ids_from_position = [row[0] for row in work_pos_result.fetchall()]
            if resume_ids_from_position:
                where_conditions.append(
                    or_(
                        OaResume.current_position.like(position_keyword),
                        OaResume.id.in_(resume_ids_from_position),
                    )
                )

        query = select(OaResume).where(*where_conditions)
        query = query.order_by(OaResume.create_time.desc())

        resume_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return resume_list

    @classmethod
    async def build_query_conditions(
            cls, query_object: ResumePageQueryModel, user_id: int
    ) -> list:
        """
        构建简历查询条件

        :param query_object: 查询参数对象
        :param user_id: 当前用户ID
        :return: 查询条件列表
        """
        conditions = []
        conditions.append(OaResume.status == 1)

        # 姓名模糊匹配
        if query_object.name:
            conditions.append(OaResume.name.like(f'%{query_object.name}%'))

        # 学历筛选（支持模糊匹配）
        if query_object.education:
            conditions.append(OaResume.education.like(f'%{query_object.education}%'))

        # 年龄范围筛选
        if query_object.min_age is not None:
            conditions.append(OaResume.age >= query_object.min_age)
        if query_object.max_age is not None:
            conditions.append(OaResume.age <= query_object.max_age)

        # 专业关键词筛选
        if query_object.major:
            conditions.append(OaResume.major.like(f'%{query_object.major}%'))

        # 技能关键词筛选（JSON数组中匹配）
        if query_object.skill:
            conditions.append(OaResume.technical_skills.like(f'%{query_object.skill}%'))

        # 公司名称筛选（当前公司）——关联表查询在 get_resume_list 中处理
        if query_object.company:
            company_keyword = f'%{query_object.company}%'
            conditions.append(OaResume.current_company.like(company_keyword))

        # 职位关键词筛选（当前职位）——关联表查询在 get_resume_list 中处理
        if query_object.position:
            position_keyword = f'%{query_object.position}%'
            conditions.append(OaResume.current_position.like(position_keyword))

        # 项目经验关键词筛选——关联表查询在 get_resume_list 中处理
        if query_object.project_keyword:
            pass  # 条件在 get_resume_list 中通过关联表查询处理

        # 全文关键词筛选（姓名、全文、公司、职位、专业、学校、学历、技能、邮箱、手机等）
        if query_object.keyword:
            keyword = f'%{query_object.keyword}%'
            conditions.append(
                or_(
                    OaResume.name.like(keyword),
                    OaResume.full_text.like(keyword),
                    OaResume.current_company.like(keyword),
                    OaResume.current_position.like(keyword),
                    OaResume.major.like(keyword),
                    OaResume.school.like(keyword),
                    OaResume.education.like(keyword),
                    OaResume.technical_skills.like(keyword),
                    OaResume.email.like(keyword),
                    OaResume.phone.like(keyword),
                    OaResume.tags.like(keyword),
                )
            )

        return conditions

    @classmethod
    async def add_resume_dao(cls, db: AsyncSession, resume: OaResume) -> OaResume:
        """
        新增简历数据库操作

        :param db: orm 对象
        :param resume: 简历对象
        :return: 简历对象
        """
        db.add(resume)
        await db.flush()
        # 必须 refresh 以确保 resume.id 被正确填充（自增主键）
        # 否则后续的 work/project 子表 resume_id 会为空
        await db.refresh(resume)
        return resume

    @classmethod
    async def add_resume_work_dao(cls, db: AsyncSession, work: OaResumeWork) -> OaResumeWork:
        """
        新增工作经历数据库操作

        :param db: orm 对象
        :param work: 工作经历对象
        :return: 工作经历对象
        """
        db.add(work)
        await db.flush()
        return work

    @classmethod
    async def add_resume_project_dao(cls, db: AsyncSession, project: OaResumeProject) -> OaResumeProject:
        """
        新增项目经验数据库操作

        :param db: orm 对象
        :param project: 项目经验对象
        :return: 项目经验对象
        """
        db.add(project)
        await db.flush()
        return project

    @classmethod
    async def delete_resume_dao(cls, db: AsyncSession, resume_id: int) -> None:
        """
        删除简历（逻辑删除）

        :param db: orm 对象
        :param resume_id: 简历ID
        :return: None
        """
        await db.execute(
            update(OaResume)
            .where(OaResume.id == resume_id)
            .values(status=0)
        )

    @classmethod
    async def get_work_experiences(cls, db: AsyncSession, resume_id: int) -> list[OaResumeWork]:
        """
        获取工作经历列表

        :param db: orm 对象
        :param resume_id: 简历ID
        :return: 工作经历列表
        """
        result = await db.execute(
            select(OaResumeWork)
            .where(OaResumeWork.resume_id == resume_id)
            .order_by(OaResumeWork.sort.asc())
        )
        return list(result.scalars().all())

    @classmethod
    async def get_project_experiences(cls, db: AsyncSession, resume_id: int) -> list[OaResumeProject]:
        """
        获取项目经验列表

        :param db: orm 对象
        :param resume_id: 简历ID
        :return: 项目经验列表
        """
        result = await db.execute(
            select(OaResumeProject)
            .where(OaResumeProject.resume_id == resume_id)
            .order_by(OaResumeProject.sort.asc())
        )
        return list(result.scalars().all())
