from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from module_admin.entity.do.resume_do import ResumeInfo, ResumeAttachment, ResumeRecommend, ResumeEmailTemplate
from module_admin.entity.vo.resume_vo import (
    ResumePageQueryModel, AddResumeModel, EditResumeModel,
    ResumeRecommendModel, AddEmailTemplateModel, EditEmailTemplateModel,
    ResumeRecommendPageQueryModel
)


class ResumeDao:
    """
    简历管理数据访问层
    """

    @classmethod
    async def get_resume_list(
            cls, query_db: AsyncSession, query_object: ResumePageQueryModel, is_page: bool = False
    ) -> Tuple[List[dict], int] | List[ResumeInfo]:
        """
        获取简历列表
        """
        # 创建子查询获取每个简历最新的推荐记录
        latest_recommend_subq = select(
            ResumeRecommend.resume_id,
            ResumeRecommend.project_name.label('project_name'),
            ResumeRecommend.customer_name.label('customer_name'),
            func.max(ResumeRecommend.recommend_time).label('latest_time')
        ).where(ResumeRecommend.delete_time == 0)
        latest_recommend_subq = latest_recommend_subq.group_by(ResumeRecommend.resume_id).subquery('latest_recommend')

        # 创建最终查询，关联推荐记录
        query = select(
            ResumeInfo,
            latest_recommend_subq.c.project_name,
            latest_recommend_subq.c.customer_name
        ).select_from(
            ResumeInfo.__table__.outerjoin(
                latest_recommend_subq,
                ResumeInfo.id == latest_recommend_subq.c.resume_id
            )
        ).where(ResumeInfo.delete_time == 0)

        if query_object.name:
            query = query.filter(ResumeInfo.name.like(f'%{query_object.name}%'))
        if query_object.phone:
            query = query.filter(ResumeInfo.phone.like(f'%{query_object.phone}%'))
        if query_object.status:
            query = query.filter(ResumeInfo.status == query_object.status)
        # 新增筛选条件
        if query_object.age_min:
            query = query.filter(ResumeInfo.age >= query_object.age_min)
        if query_object.age_max:
            query = query.filter(ResumeInfo.age <= query_object.age_max)
        if query_object.education:
            query = query.filter(ResumeInfo.education == query_object.education)
        if query_object.graduate_year_min:
            query = query.filter(ResumeInfo.graduate_year >= query_object.graduate_year_min)
        if query_object.graduate_year_max:
            query = query.filter(ResumeInfo.graduate_year <= query_object.graduate_year_max)
        if query_object.is_entry is not None:
            query = query.filter(ResumeInfo.is_entry == query_object.is_entry)
        if query_object.recommender_id:
            query = query.filter(ResumeInfo.recommender_id == query_object.recommender_id)

        if is_page:
            total = await query_db.scalar(select(func.count()).select_from(query.subquery()))
            query = query.offset((query_object.page_num - 1) * query_object.page_size).limit(query_object.page_size)
            result = (await query_db.execute(query)).mappings().all()
            return result, total
        else:
            result = (await query_db.execute(query)).mappings().all()
            return result

    @classmethod
    async def get_resume_detail_by_id(cls, query_db: AsyncSession, resume_id: int) -> Optional[ResumeInfo]:
        """
        根据ID获取简历详情
        """
        query = select(ResumeInfo).where(ResumeInfo.id == resume_id, ResumeInfo.delete_time == 0)
        return (await query_db.execute(query)).scalars().first()

    @classmethod
    async def get_resume_by_idcard(cls, query_db: AsyncSession, idcard: str) -> Optional[ResumeInfo]:
        """
        根据身份证号获取简历
        """
        query = select(ResumeInfo).where(ResumeInfo.idcard == idcard, ResumeInfo.delete_time == 0)
        return (await query_db.execute(query)).scalars().first()

    @classmethod
    async def get_resume_attachments(cls, query_db: AsyncSession, resume_id: int) -> List[ResumeAttachment]:
        """
        获取简历附件列表
        """
        query = select(ResumeAttachment).where(
            ResumeAttachment.resume_id == resume_id,
            ResumeAttachment.delete_time == 0
        ).order_by(ResumeAttachment.sort)
        return (await query_db.execute(query)).scalars().all()

    @classmethod
    async def add_resume_dao(cls, query_db: AsyncSession, page_object: AddResumeModel) -> ResumeInfo:
        """
        新增简历
        """
        resume_info = ResumeInfo(
            name=page_object.name,
            phone=page_object.phone,
            sex=page_object.sex or '0',
            idcard=page_object.idcard or '',
            email=page_object.email or '',
            city=page_object.city or '',
            city_id=page_object.city_id or '',
            remark=page_object.remark or '',
            # 新增时如果不传状态，默认设置为'0'(初始状态)
            status=page_object.status if page_object.status is not None else '0',
            education=page_object.education or '',
            graduate_school=page_object.graduate_school or '',
            graduate_year=page_object.graduate_year,
            age=page_object.age,
            entry_project_name=page_object.entry_project_name or '',
            recommend_customer_id=page_object.recommend_customer_id,
            recommend_customer_name=page_object.recommend_customer_name or '',
            create_time=datetime.now(),
            update_time=datetime.now(),
            delete_time=0
        )
        query_db.add(resume_info)
        await query_db.flush()
        return resume_info

    @classmethod
    async def add_resume_attachment_dao(cls, query_db: AsyncSession, resume_id: int, attachment):
        """
        新增简历附件
        """
        attachment_info = ResumeAttachment(
            resume_id=resume_id,
            file_name=attachment.file_name or '',
            file_path=attachment.file_path or '',
            file_size=attachment.file_size or 0,
            file_ext=attachment.file_ext or '',
            file_mime=attachment.file_mime or '',
            sort=attachment.sort or 0,
            delete_time=0
        )
        query_db.add(attachment_info)

    @classmethod
    async def release_resume_dao(cls, query_db: AsyncSession, resume_id: int, status: str = '5'):
        """
        释放简历
        """
        await query_db.execute(
            update(ResumeInfo)
            .where(ResumeInfo.id == resume_id, ResumeInfo.delete_time == 0)
            .values({
                'status': status,
                'update_time': datetime.now()
            })
        )

    @classmethod
    async def edit_resume_dao(cls, query_db: AsyncSession, page_object: EditResumeModel):
        """
        编辑简历
        """
        update_data = {
            'name': page_object.name,
            'phone': page_object.phone,
            'update_time': datetime.now()
        }
        
        # 只有在字段有值时才更新，避免覆盖原有数据
        if page_object.sex is not None:
            update_data['sex'] = page_object.sex
        if page_object.idcard is not None:
            update_data['idcard'] = page_object.idcard
        if page_object.email is not None:
            update_data['email'] = page_object.email
        if page_object.city is not None:
            update_data['city'] = page_object.city
        if page_object.city_id is not None:
            update_data['city_id'] = page_object.city_id
        if page_object.remark is not None:
            update_data['remark'] = page_object.remark
        if page_object.status is not None:
            update_data['status'] = page_object.status
        if page_object.education is not None:
            update_data['education'] = page_object.education
        if page_object.graduate_school is not None:
            update_data['graduate_school'] = page_object.graduate_school
        if page_object.graduate_year is not None:
            update_data['graduate_year'] = page_object.graduate_year
        if page_object.age is not None:
            update_data['age'] = page_object.age
        if page_object.entry_project_name is not None:
            update_data['entry_project_name'] = page_object.entry_project_name
        if page_object.recommend_customer_id is not None:
            update_data['recommend_customer_id'] = page_object.recommend_customer_id
        if page_object.recommend_customer_name is not None:
            update_data['recommend_customer_name'] = page_object.recommend_customer_name
        
        await query_db.execute(
            update(ResumeInfo).where(ResumeInfo.id == page_object.id).values(update_data)
        )

    @classmethod
    async def update_resume_status_dao(cls, query_db: AsyncSession, resume_id: int, status: str):
        """
        更新简历状态
        """
        await query_db.execute(
            update(ResumeInfo).where(ResumeInfo.id == resume_id).values({
                'status': status,
                'update_time': datetime.now()
            })
        )

    @classmethod
    async def update_resume_user_id_dao(cls, query_db: AsyncSession, resume_id: int, user_id: int):
        """
        更新简历关联用户ID
        """
        await query_db.execute(
            update(ResumeInfo).where(ResumeInfo.id == resume_id).values({
                'user_id': user_id,
                'status': '4',  # 4表示已入职
                'update_time': datetime.now()
            })
        )

    @classmethod
    async def batch_delete_tender_attachments_dao(cls, query_db: AsyncSession, attachment_ids: List[int], delete_time: int):
        """
        批量删除简历附件（软删除）
        """
        await query_db.execute(
            update(ResumeAttachment)
            .where(ResumeAttachment.id.in_(attachment_ids))
            .values(delete_time=delete_time)
        )

    @classmethod
    async def delete_resume_dao(cls, query_db: AsyncSession, resume_ids: List[int], delete_time: int):
        """
        删除简历（软删除）
        """
        await query_db.execute(
            update(ResumeInfo).where(ResumeInfo.id.in_(resume_ids)).values({
                'delete_time': delete_time,
                'update_time': datetime.now()
            })
        )

    @classmethod
    async def recommend_resume_dao(cls, query_db: AsyncSession, page_object: ResumeRecommendModel, project_name: str = None, customer_name: str = None):
        """
        推荐简历到项目/客户
        """
        # 更新简历状态，使用传入的status值，不传则默认'2'（已通过）
        update_data = {
            'status': page_object.status,
            'recommender_id': page_object.recommender_id,
            'recommender_name': page_object.recommender_name,
            'recommend_time': datetime.now(),
            'update_time': datetime.now()
        }
        if page_object.project_id:
            update_data['recommend_project_id'] = page_object.project_id
        if page_object.customer_id:
            update_data['recommend_customer_id'] = page_object.customer_id
        if page_object.customer_name:
            update_data['recommend_customer_name'] = page_object.customer_name

        await query_db.execute(
            update(ResumeInfo)
            .where(ResumeInfo.id == page_object.resume_id)
            .values(update_data)
        )

        # 添加推荐记录
        recommend_info = ResumeRecommend(
            resume_id=page_object.resume_id,
            project_id=page_object.project_id or 0,
            project_name=project_name or '',
            customer_id=page_object.customer_id,
            customer_name=page_object.customer_name or '',
            recommender_id=page_object.recommender_id,
            recommender_name=page_object.recommender_name,
            recommend_time=datetime.now(),
            status=page_object.status if page_object.status else '推荐中',
            remark=page_object.remark or ''
        )
        query_db.add(recommend_info)
        await query_db.flush()
        return recommend_info

    @classmethod
    async def get_resume_recommend_list(
            cls, query_db: AsyncSession, query_object: ResumeRecommendPageQueryModel, is_page: bool = False
    ) -> Tuple[List[dict], int] | List[ResumeRecommend]:
        """
        获取简历推荐记录列表
        """
        query = select(ResumeRecommend).where(ResumeRecommend.delete_time == 0)

        if query_object.resume_id:
            query = query.filter(ResumeRecommend.resume_id == query_object.resume_id)
        if query_object.project_name:
            query = query.filter(ResumeRecommend.project_name.like(f'%{query_object.project_name}%'))
        if query_object.recommender_name:
            query = query.filter(ResumeRecommend.recommender_name.like(f'%{query_object.recommender_name}%'))

        query = query.order_by(ResumeRecommend.recommend_time.desc())

        if is_page:
            total = await query_db.scalar(select(func.count()).select_from(query.subquery()))
            query = query.offset((query_object.page_num - 1) * query_object.page_size).limit(query_object.page_size)
            result = (await query_db.execute(query)).scalars().all()
            return result, total
        else:
            result = (await query_db.execute(query)).scalars().all()
            return result

    @classmethod
    async def add_email_template_dao(cls, query_db: AsyncSession, page_object: AddEmailTemplateModel) -> ResumeEmailTemplate:
        """
        新增邮件模板
        """
        # 如果设为默认，取消其他默认模板
        if page_object.is_default == 1:
            await query_db.execute(
                update(ResumeEmailTemplate).values(is_default=0)
            )

        template_info = ResumeEmailTemplate(
            template_name=page_object.template_name,
            template_content=page_object.template_content,
            subject=page_object.subject or '',
            is_default=page_object.is_default or 0,
            create_time=datetime.now(),
            update_time=datetime.now()
        )
        query_db.add(template_info)
        await query_db.flush()
        return template_info

    @classmethod
    async def get_email_template_list(cls, query_db: AsyncSession, page_num: int = 1, page_size: int = 10) -> dict:
        """
        获取邮件模板列表（分页）
        """
        # 查询总数
        total = await query_db.scalar(select(func.count(ResumeEmailTemplate.id)))
        total = total or 0

        # 查询分页数据
        query = select(ResumeEmailTemplate).order_by(
            ResumeEmailTemplate.is_default.desc(),
            ResumeEmailTemplate.create_time.desc()
        ).offset((page_num - 1) * page_size).limit(page_size)
        result = await query_db.execute(query)
        rows = result.scalars().all()

        return {
            'rows': rows,
            'total': total,
            'page_num': page_num,
            'page_size': page_size
        }

    @classmethod
    async def get_email_template_by_id(cls, query_db: AsyncSession, template_id: int) -> Optional[ResumeEmailTemplate]:
        """
        根据ID获取邮件模板
        """
        query = select(ResumeEmailTemplate).where(ResumeEmailTemplate.id == template_id)
        return (await query_db.execute(query)).scalars().first()

    @classmethod
    async def get_default_email_template(cls, query_db: AsyncSession) -> Optional[ResumeEmailTemplate]:
        """
        获取默认邮件模板
        """
        query = select(ResumeEmailTemplate).where(ResumeEmailTemplate.is_default == 1)
        return (await query_db.execute(query)).scalars().first()

    @classmethod
    async def edit_email_template_dao(cls, query_db: AsyncSession, page_object: EditEmailTemplateModel):
        """
        编辑邮件模板
        """
        # 如果设为默认，取消其他默认模板
        if page_object.is_default == 1:
            await query_db.execute(
                update(ResumeEmailTemplate).values(is_default=0)
            )

        await query_db.execute(
            update(ResumeEmailTemplate)
            .where(ResumeEmailTemplate.id == page_object.id)
            .values({
                'template_name': page_object.template_name,
                'template_content': page_object.template_content,
                'subject': page_object.subject or '',
                'is_default': page_object.is_default or 0,
                'update_time': datetime.now()
            })
        )

    @classmethod
    async def delete_email_template_dao(cls, query_db: AsyncSession, template_ids: List[int]):
        """
        删除邮件模板
        """
        await query_db.execute(
            delete(ResumeEmailTemplate).where(ResumeEmailTemplate.id.in_(template_ids))
        )

    @classmethod
    async def entry_project_dao(cls, query_db: AsyncSession, resume_id: int, project_id: int, project_name: str):
        """
        入场项目
        """
        await query_db.execute(
            update(ResumeInfo)
            .where(ResumeInfo.id == resume_id)
            .values({
                'is_entry': 1,
                'entry_project_id': project_id,
                'entry_time': datetime.now(),
                'update_time': datetime.now()
            })
        )