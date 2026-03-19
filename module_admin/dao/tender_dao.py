from datetime import datetime
from typing import Any

from sqlalchemy import and_, delete, desc, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.tender_do import OaProjectTender, OaProjectTenderAttachment
from module_admin.entity.vo.tender_vo import (
    TenderPageQueryModel, AddTenderModel, EditTenderModel, DeleteTenderModel,
    AddTenderAttachmentModel, DeleteTenderAttachmentModel,
)
from utils.page_util import PageUtil

class TenderDao:
    """招投标管理模块数据库操作层"""

    @classmethod
    async def get_tender_list(
            cls, db: AsyncSession, query_object: TenderPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """获取投标信息列表"""
        query = select(OaProjectTender).where(OaProjectTender.delete_time == 0)

        # 添加查询条件
        if query_object.month and query_object.month.strip():
            query = query.where(OaProjectTender.month.like(f'%{query_object.month.strip()}%'))
        if query_object.customer_name and query_object.customer_name.strip():
            query = query.where(OaProjectTender.customer_name.like(f'%{query_object.customer_name.strip()}%'))
        if query_object.project_name and query_object.project_name.strip():
            query = query.where(OaProjectTender.project_name.like(f'%{query_object.project_name.strip()}%'))
        if query_object.tender_leader and query_object.tender_leader.strip():
            query = query.where(OaProjectTender.tender_leader.like(f'%{query_object.tender_leader.strip()}%'))
        if query_object.is_tender_submitted:
            query = query.where(OaProjectTender.is_tender_submitted == query_object.is_tender_submitted)
        if query_object.bid_result and query_object.bid_result.strip():
            query = query.where(OaProjectTender.bid_result.like(f'%{query_object.bid_result.strip()}%'))

        # 时间条件处理
        if query_object.begin_time and query_object.end_time:
            try:
                begin_datetime = datetime.fromisoformat(query_object.begin_time)
                end_datetime = datetime.fromisoformat(query_object.end_time)
                query = query.where(
                    and_(
                        OaProjectTender.create_time >= begin_datetime,
                        OaProjectTender.create_time <= end_datetime,
                        )
                )
            except ValueError:
                pass

        # 排序
        query = query.order_by(desc(OaProjectTender.sort), desc(OaProjectTender.id))

        if is_page:
            result = await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size)
        else:
            result = (await db.execute(query)).scalars().all()

        return result

    @classmethod
    async def get_tender_detail_by_id(cls, db: AsyncSession, tender_id: int) -> OaProjectTender | None:
        """根据 ID 获取投标信息详情"""
        query = select(OaProjectTender).where(
            OaProjectTender.id == tender_id, OaProjectTender.delete_time == 0
        )
        result = (await db.execute(query)).scalars().first()
        return result

    @classmethod
    async def add_tender_dao(cls, db: AsyncSession, tender: AddTenderModel) -> OaProjectTender:
        """新增投标信息"""
        db_tender = OaProjectTender(**tender.model_dump(exclude_unset=True, by_alias=True))
        db.add(db_tender)
        await db.flush()
        await db.refresh(db_tender)
        return db_tender

    @classmethod
    async def edit_tender_dao(cls, db: AsyncSession, tender: EditTenderModel) -> OaProjectTender:
        """编辑投标信息"""
        edit_data = tender.model_dump(exclude_unset=True, exclude={'id'}, by_alias=True)
        
        # MySQL 不支持 RETURNING 子句，需要先更新再查询
        query = (
            update(OaProjectTender)
            .where(OaProjectTender.id == tender.id, OaProjectTender.delete_time == 0)
            .values(**edit_data)
        )
        await db.execute(query)
        await db.flush()
        
        # 重新查询获取更新后的数据
        updated_tender = await cls.get_tender_detail_by_id(db, tender.id)
        return updated_tender

    @classmethod
    async def delete_tender_dao(cls, db: AsyncSession, tender_ids: list[int], delete_time: int):
        """软删除投标信息"""
        stmt = update(OaProjectTender).where(OaProjectTender.id.in_(tender_ids)).values(
            delete_time=delete_time,
            update_time=datetime.now()
        )
        await db.execute(stmt)

    @classmethod
    async def get_tender_attachments(cls, db: AsyncSession, project_tender_id: int) -> list[OaProjectTenderAttachment]:
        """根据投标 ID 获取附件列表"""
        query = select(OaProjectTenderAttachment).where(
            OaProjectTenderAttachment.project_tender_id == project_tender_id,
            OaProjectTenderAttachment.delete_time == 0
        ).order_by(OaProjectTenderAttachment.sort)
        result = (await db.execute(query)).scalars().all()
        return result

    @classmethod
    async def add_tender_attachment_dao(
            cls, db: AsyncSession, attachment: AddTenderAttachmentModel
    ) -> OaProjectTenderAttachment:
        """新增投标附件"""
        db_attachment = OaProjectTenderAttachment(**attachment.model_dump(by_alias=True))
        db.add(db_attachment)
        await db.flush()
        await db.refresh(db_attachment)
        return db_attachment

    @classmethod
    async def delete_tender_attachment_dao(
            cls, db: AsyncSession, attachment: DeleteTenderAttachmentModel
    ) -> bool:
        """删除投标附件（软删除）"""
        attachment_id_list = [int(id.strip()) for id in attachment.ids.split(',') if id.strip()]

        query = (
            update(OaProjectTenderAttachment)
            .where(
                OaProjectTenderAttachment.id.in_(attachment_id_list),
                OaProjectTenderAttachment.delete_time == 0
            )
            .values(delete_time=int(datetime.now().timestamp() * 1000))
        )
        await db.execute(query)
        return True