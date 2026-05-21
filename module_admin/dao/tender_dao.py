from datetime import datetime
from typing import Any
import logging

from sqlalchemy import and_, delete, desc, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.tender_do import OaProjectTender, OaProjectTenderAttachment
from module_admin.entity.vo.tender_vo import (
    TenderPageQueryModel, AddTenderModel, EditTenderModel, DeleteTenderModel,
    AddTenderAttachmentModel, DeleteTenderAttachmentModel,
)
from utils.page_util import PageUtil

logger = logging.getLogger(__name__)

class TenderDao:
    """招投标管理模块数据库操作层"""

    @classmethod
    async def get_tender_list(
            cls, db: AsyncSession, query_object: TenderPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """获取投标信息列表"""
        from module_admin.entity.do.user_do import SysUser
        
        try:
            query = select(OaProjectTender).where(OaProjectTender.delete_time == 0)

            # 添加查询条件
            if query_object.month and query_object.month.strip():
                query = query.where(OaProjectTender.month.like(f'%{query_object.month.strip()}%'))
            if query_object.customer_name and query_object.customer_name.strip():
                query = query.where(OaProjectTender.customer_name.like(f'%{query_object.customer_name.strip()}%'))
            if query_object.project_name and query_object.project_name.strip():
                query = query.where(OaProjectTender.project_name.like(f'%{query_object.project_name.strip()}%'))
            if query_object.tender_leader and query_object.tender_leader.strip():
                try:
                    # 根据username查找用户姓名
                    user_result = await db.execute(
                        select(SysUser.nick_name)
                        .where(SysUser.user_name == query_object.tender_leader.strip())
                    )
                    user_name = user_result.scalar_one_or_none()
                    # 如果找到用户姓名，用姓名查询；否则用传入的值直接查询
                    if user_name:
                        query = query.where(OaProjectTender.tender_leader.like(f'%{user_name}%'))
                    else:
                        query = query.where(OaProjectTender.tender_leader.like(f'%{query_object.tender_leader.strip()}%'))
                except Exception as e:
                    logger.warning(f'查询用户信息失败，使用原始值查询：{str(e)}')
                    query = query.where(OaProjectTender.tender_leader.like(f'%{query_object.tender_leader.strip()}%'))
            
            # 处理枚举字段查询 - 确保值为 '是' 或 '否'
            if query_object.is_tender_submitted:
                valid_values = ['是', '否']
                if query_object.is_tender_submitted in valid_values:
                    query = query.where(OaProjectTender.is_tender_submitted == query_object.is_tender_submitted)
                else:
                    logger.warning(f'无效的is_tender_submitted值: {query_object.is_tender_submitted}，跳过该条件')
            
            if query_object.bid_result and query_object.bid_result.strip():
                query = query.where(OaProjectTender.bid_result.like(f'%{query_object.bid_result.strip()}%'))

            # 开标日期条件处理（使用 begin_time 和 end_time 参数）
            if query_object.begin_time and query_object.end_time:
                try:
                    bid_opening_start = datetime.strptime(query_object.begin_time, '%Y-%m-%d').date()
                    bid_opening_end = datetime.strptime(query_object.end_time, '%Y-%m-%d').date()
                    query = query.where(
                        and_(
                            OaProjectTender.bid_opening_date >= bid_opening_start,
                            OaProjectTender.bid_opening_date <= bid_opening_end,
                        )
                    )
                except ValueError as e:
                    logger.warning(f'日期格式错误：{str(e)}')
                    pass

            # 排序
            query = query.order_by(desc(OaProjectTender.sort), desc(OaProjectTender.id))

            if is_page:
                result = await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, is_page=True)
            else:
                result = (await db.execute(query)).scalars().all()

            return result
        except Exception as e:
            logger.error(f'获取投标列表失败：{str(e)}', exc_info=True)
            raise

    @classmethod
    async def get_tender_detail_by_id(cls, db: AsyncSession, tender_id: int) -> OaProjectTender | None:
        """根据 ID 获取投标信息详情"""
        query = select(OaProjectTender).where(
            OaProjectTender.id == tender_id, OaProjectTender.delete_time == 0
        )
        result = (await db.execute(query)).scalars().first()
        return result

    @classmethod
    async def get_tender_by_project_name(cls, db: AsyncSession, project_name: str, exclude_id: int = None) -> OaProjectTender | None:
        """根据项目名称查询投标信息（用于验重）"""
        query = select(OaProjectTender).where(
            OaProjectTender.project_name == project_name,
            OaProjectTender.delete_time == 0
        )
        if exclude_id:
            query = query.where(OaProjectTender.id != exclude_id)
        result = (await db.execute(query)).scalars().first()
        return result

    @classmethod
    async def add_tender_dao(cls, db: AsyncSession, tender: AddTenderModel) -> OaProjectTender:
        """新增投标信息"""
        # 排除 attachments 和 tender_leader_id 字段，因为数据库模型中没有这些字段
        # 使用 by_alias=False 确保使用下划线命名（与数据库模型一致）
        tender_data = tender.model_dump(exclude_unset=True, exclude={'attachments', 'tender_leader_id'}, by_alias=False)
        db_tender = OaProjectTender(**tender_data)
        db.add(db_tender)
        await db.flush()
        await db.refresh(db_tender)
        return db_tender

    @classmethod
    async def edit_tender_dao(cls, db: AsyncSession, tender: EditTenderModel) -> OaProjectTender:
        """编辑投标信息"""
        # 使用 by_alias=False 确保使用下划线命名（与数据库模型一致）
        # 排除 id、attachments 和 tender_leader_id 字段（tender_leader_id 为预留字段，数据库中不存在）
        edit_data = tender.model_dump(exclude_unset=True, exclude={'id', 'attachments', 'tender_leader_id'}, by_alias=False)
        
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
        # 构建数据字典，只包含数据库表存在的字段
        attachment_data = {
            'project_tender_id': attachment.project_tender_id,
            'file_name': attachment.file_name,
            'file_path': attachment.file_path,
        }
        
        # 可选字段，只有在有值时才添加
        if attachment.file_size is not None:
            attachment_data['file_size'] = attachment.file_size
        if attachment.file_ext is not None:
            attachment_data['file_ext'] = attachment.file_ext
        if attachment.file_mime is not None:
            attachment_data['file_mime'] = attachment.file_mime
        if attachment.sort is not None:
            attachment_data['sort'] = attachment.sort
        if attachment.delete_time is not None:
            attachment_data['delete_time'] = attachment.delete_time
        
        db_attachment = OaProjectTenderAttachment(**attachment_data)
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

    @classmethod
    async def batch_delete_tender_attachments_dao(
            cls, db: AsyncSession, attachment_ids: list[int], delete_time: int
    ) -> bool:
        """批量删除投标附件（软删除）"""
        if not attachment_ids:
            return True

        query = (
            update(OaProjectTenderAttachment)
            .where(
                OaProjectTenderAttachment.id.in_(attachment_ids),
                OaProjectTenderAttachment.delete_time == 0
            )
            .values(delete_time=delete_time * 1000)
        )
        await db.execute(query)
        return True

    @classmethod
    async def batch_delete_tender_attachments_dao(
            cls, db: AsyncSession, attachment_ids: list[int], delete_time: int
    ) -> bool:
        """批量删除投标附件（软删除）"""
        if not attachment_ids:
            return True

        query = (
            update(OaProjectTenderAttachment)
            .where(
                OaProjectTenderAttachment.id.in_(attachment_ids),
                OaProjectTenderAttachment.delete_time == 0
            )
            .values(delete_time=delete_time * 1000)
        )
        await db.execute(query)
        return True