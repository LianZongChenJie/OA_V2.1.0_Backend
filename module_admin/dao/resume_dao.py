from typing import List, Optional, Tuple

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.do.resume_do import ResumeInfo, ResumeAttachment
from module_admin.entity.vo.resume_vo import ResumePageQueryModel, AddResumeModel, EditResumeModel


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
        query = select(ResumeInfo).where(ResumeInfo.delete_time == 0)

        if query_object.name:
            query = query.filter(ResumeInfo.name.like(f'%{query_object.name}%'))
        if query_object.phone:
            query = query.filter(ResumeInfo.phone.like(f'%{query_object.phone}%'))
        if query_object.status:
            query = query.filter(ResumeInfo.status == query_object.status)

        if is_page:
            total = await query_db.scalar(select(func.count()).select_from(query.subquery()))
            query = query.offset((query_object.page_num - 1) * query_object.page_size).limit(query_object.page_size)
            result = (await query_db.execute(query)).scalars().all()
            return result, total
        else:
            result = (await query_db.execute(query)).scalars().all()
            return result

    @classmethod
    async def get_resume_detail_by_id(cls, query_db: AsyncSession, resume_id: int) -> Optional[ResumeInfo]:
        """
        根据ID获取简历详情
        """
        query = select(ResumeInfo).where(ResumeInfo.id == resume_id, ResumeInfo.delete_time == 0)
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
            remark=page_object.remark or '',
            status=page_object.status or '已投递',
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
    async def edit_resume_dao(cls, query_db: AsyncSession, page_object: EditResumeModel):
        """
        编辑简历
        """
        update_data = {
            'name': page_object.name,
            'phone': page_object.phone,
            'sex': page_object.sex or '0',
            'idcard': page_object.idcard or '',
            'email': page_object.email or '',
            'city': page_object.city or '',
            'remark': page_object.remark or '',
            'status': page_object.status or '已投递',
            'update_time': datetime.now()
        }
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
                'status': '已入职',
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


from datetime import datetime
