"""
投标文件知识库模块 DAO 层
"""
import time

from sqlalchemy import desc, func, and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from exceptions.exception import ServiceException
from module_bid_kb.entity.do.bid_do import OaBidDocument
from module_bid_kb.entity.vo.bid_vo import BidDocumentPageQueryModel
from module_resume_kb.entity.do.resume_do import OaResume
from utils.log_util import logger
from utils.page_util import PageUtil


class BidDao:
    """投标文件DAO"""

    @classmethod
    async def create_bid_document(cls, db: AsyncSession, bid: OaBidDocument) -> OaBidDocument:
        """创建投标文件记录"""
        try:
            db.add(bid)
            await db.flush()
            # 不使用 refresh，直接返回对象（flush后主键已填充）
            return bid
        except Exception as e:
            logger.error(f'创建投标文件记录失败: {str(e)}')
            raise ServiceException(message=f'创建投标文件记录失败: {str(e)}')

    @classmethod
    async def update_resume_count(cls, db: AsyncSession, bid_id: int, count: int) -> None:
        """更新简历数量"""
        try:
            # 直接使用 update 语句而不是先 get 再 flush
            stmt = (
                update(OaBidDocument)
                .where(OaBidDocument.id == bid_id)
                .values(resume_count=count, update_time=int(time.time()))
            )
            await db.execute(stmt)
            await db.flush()
        except Exception as e:
            logger.error(f'更新简历数量失败: bid_id={bid_id}, count={count}, error={str(e)}')
            raise

    @classmethod
    async def get_bid_document_list(
        cls,
        db: AsyncSession,
        query_object: BidDocumentPageQueryModel,
        is_page: bool = False
    ) -> PageModel | list[dict]:
        """获取投标文件列表"""
        query = select(OaBidDocument).where(OaBidDocument.status < 9)

        if query_object.bid_name:
            query = query.where(OaBidDocument.bid_name.like(f'%{query_object.bid_name}%'))
        if query_object.bid_code:
            query = query.where(OaBidDocument.bid_code.like(f'%{query_object.bid_code}%'))
        if query_object.company_name:
            query = query.where(OaBidDocument.company_name.like(f'%{query_object.company_name}%'))

        query = query.order_by(desc(OaBidDocument.create_time))

        return await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

    @classmethod
    async def get_bid_detail_by_id(cls, db: AsyncSession, bid_id: int) -> OaBidDocument | None:
        """获取投标文件详情"""
        return await db.get(OaBidDocument, bid_id)

    @classmethod
    async def get_bid_related_resumes(cls, db: AsyncSession, bid_id: int) -> list[OaResume]:
        """获取投标文件关联的简历列表"""
        result = await db.execute(
            select(OaResume)
            .where(
                and_(
                    OaResume.source_type == 2,
                    OaResume.source_id == bid_id,
                    OaResume.status == 1
                )
            )
            .order_by(OaResume.create_time)
        )
        return result.scalars().all()

    @classmethod
    async def delete_bid_document(cls, db: AsyncSession, bid_id: int) -> None:
        """删除投标文件（软删除）"""
        bid = await db.get(OaBidDocument, bid_id)
        if bid:
            bid.status = 9
            bid.update_time = int(time.time())
            await db.flush()

    @classmethod
    async def count_bid_resumes(cls, db: AsyncSession, bid_id: int) -> int:
        """统计投标文件关联的简历数量"""
        result = await db.scalar(
            func.count(OaResume.id)
            .select()
            .where(
                and_(
                    OaResume.source_type == 2,
                    OaResume.source_id == bid_id,
                    OaResume.status == 1
                )
            )
        )
        return result or 0