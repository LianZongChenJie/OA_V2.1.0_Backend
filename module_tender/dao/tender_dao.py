"""
招标文件智能生成模块 DAO 层
"""
from sqlalchemy import desc, func, and_, select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from exceptions.exception import ServiceException
from module_tender.entity.do.tender_do import OaTenderDocument, OaTenderRequirement, OaBidPersonnelMapping
from module_tender.entity.vo.tender_vo import TenderDocumentPageQueryModel
from module_resume_kb.entity.do.resume_do import OaResume
from utils.log_util import logger
from utils.page_util import PageUtil
from utils.time_format_util import TimeFormatUtil


class TenderDao:
    """招标文件DAO"""

    @classmethod
    async def create_tender_document(cls, db: AsyncSession, tender: OaTenderDocument) -> OaTenderDocument:
        """创建招标文件记录"""
        try:
            db.add(tender)
            await db.flush()
            await db.refresh(tender)
            return tender
        except Exception as e:
            logger.error(f'创建招标文件记录失败: {str(e)}')
            raise ServiceException(message=f'创建招标文件记录失败: {str(e)}')

    @classmethod
    async def update_tender_document(cls, db: AsyncSession, tender_id: int, **kwargs) -> None:
        """更新招标文件记录"""
        tender = await db.get(OaTenderDocument, tender_id)
        if tender:
            for key, value in kwargs.items():
                if hasattr(tender, key):
                    setattr(tender, key, value)
            tender.update_time = TimeFormatUtil.get_current_timestamp()
            await db.flush()

    @classmethod
    async def get_tender_document_list(
        cls,
        db: AsyncSession,
        query_object: TenderDocumentPageQueryModel,
        is_page: bool = False
    ) -> PageModel | list:
        """获取招标文件列表"""
        query = select(OaTenderDocument)

        if query_object.tender_name:
            query = query.where(OaTenderDocument.tender_name.like(f'%{query_object.tender_name}%'))
        if query_object.tender_code:
            query = query.where(OaTenderDocument.tender_code.like(f'%{query_object.tender_code}%'))
        if query_object.company_name:
            query = query.where(OaTenderDocument.company_name.like(f'%{query_object.company_name}%'))

        query = query.order_by(desc(OaTenderDocument.create_time))

        return await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

    @classmethod
    async def get_tender_detail_by_id(cls, db: AsyncSession, tender_id: int) -> OaTenderDocument | None:
        """获取招标文件详情"""
        return await db.get(OaTenderDocument, tender_id)

    @classmethod
    async def delete_tender_document(cls, db: AsyncSession, tender_id: int) -> None:
        """删除招标文件（物理删除，关联数据一并删除）"""
        tender = await db.get(OaTenderDocument, tender_id)
        if tender:
            # 删除关联要求
            await db.execute(
                delete(OaTenderRequirement).where(OaTenderRequirement.tender_id == tender_id)
            )
            # 删除关联映射
            await db.execute(
                delete(OaBidPersonnelMapping).where(OaBidPersonnelMapping.tender_id == tender_id)
            )
            # 删除招标文件
            await db.delete(tender)
            await db.flush()

    @classmethod
    async def create_requirement(cls, db: AsyncSession, requirement: OaTenderRequirement) -> OaTenderRequirement:
        """创建招标要求记录"""
        db.add(requirement)
        await db.flush()
        await db.refresh(requirement)
        return requirement

    @classmethod
    async def batch_create_requirements(cls, db: AsyncSession, requirements: list[OaTenderRequirement]) -> int:
        """批量创建招标要求记录"""
        for req in requirements:
            db.add(req)
        await db.flush()
        return len(requirements)

    @classmethod
    async def get_requirements_by_tender_id(cls, db: AsyncSession, tender_id: int) -> list[OaTenderRequirement]:
        """获取招标文件的结构化要求列表"""
        result = await db.execute(
            select(OaTenderRequirement)
            .where(OaTenderRequirement.tender_id == tender_id)
            .order_by(OaTenderRequirement.id)
        )
        return result.scalars().all()

    @classmethod
    async def delete_requirements_by_tender_id(cls, db: AsyncSession, tender_id: int) -> None:
        """删除招标文件的所有要求"""
        await db.execute(
            delete(OaTenderRequirement).where(OaTenderRequirement.tender_id == tender_id)
        )
        await db.flush()

    @classmethod
    async def create_mapping(cls, db: AsyncSession, mapping: OaBidPersonnelMapping) -> OaBidPersonnelMapping:
        """创建人员映射记录"""
        db.add(mapping)
        await db.flush()
        await db.refresh(mapping)
        return mapping

    @classmethod
    async def batch_create_mappings(cls, db: AsyncSession, mappings: list[OaBidPersonnelMapping]) -> int:
        """批量创建人员映射记录"""
        for m in mappings:
            db.add(m)
        await db.flush()
        return len(mappings)

    @classmethod
    async def get_mappings_by_tender_id(cls, db: AsyncSession, tender_id: int) -> list:
        """获取招标文件的匹配结果列表（关联简历信息）"""
        result = await db.execute(
            select(
                OaBidPersonnelMapping,
                OaResume.name,
                OaResume.gender,
                OaResume.age,
                OaResume.education,
                OaResume.work_years,
                OaResume.current_company,
                OaResume.current_position,
                OaResume.technical_skills,
                OaResume.certifications,
            )
            .outerjoin(OaResume, OaBidPersonnelMapping.resume_id == OaResume.id)
            .where(OaBidPersonnelMapping.tender_id == tender_id)
            .order_by(OaBidPersonnelMapping.sort_order)
        )
        return result.all()

    @classmethod
    async def delete_mappings_by_tender_id(cls, db: AsyncSession, tender_id: int) -> None:
        """删除招标文件的所有匹配记录"""
        await db.execute(
            delete(OaBidPersonnelMapping).where(OaBidPersonnelMapping.tender_id == tender_id)
        )
        await db.flush()

    @classmethod
    async def get_mapping_by_id(cls, db: AsyncSession, mapping_id: int) -> OaBidPersonnelMapping | None:
        """获取映射记录"""
        return await db.get(OaBidPersonnelMapping, mapping_id)

    @classmethod
    async def update_mapping_selection(cls, db: AsyncSession, mapping_id: int, is_selected: int) -> None:
        """更新映射选中状态"""
        mapping = await db.get(OaBidPersonnelMapping, mapping_id)
        if mapping:
            mapping.is_selected = is_selected
            await db.flush()

    @classmethod
    async def get_selected_mappings(cls, db: AsyncSession, tender_id: int) -> list:
        """获取已选中的映射列表（关联简历信息）"""
        result = await db.execute(
            select(
                OaBidPersonnelMapping,
                OaResume.name,
                OaResume.gender,
                OaResume.age,
                OaResume.education,
                OaResume.work_years,
                OaResume.current_company,
                OaResume.current_position,
                OaResume.technical_skills,
                OaResume.certifications,
                OaResume.major,
                OaResume.school,
            )
            .outerjoin(OaResume, OaBidPersonnelMapping.resume_id == OaResume.id)
            .where(
                and_(
                    OaBidPersonnelMapping.tender_id == tender_id,
                    OaBidPersonnelMapping.is_selected == 1
                )
            )
            .order_by(OaBidPersonnelMapping.sort_order)
        )
        return result.all()

    @classmethod
    async def count_selected(cls, db: AsyncSession, tender_id: int) -> int:
        """统计已选中人数"""
        result = await db.scalar(
            func.count(OaBidPersonnelMapping.id)
            .select()
            .where(
                and_(
                    OaBidPersonnelMapping.tender_id == tender_id,
                    OaBidPersonnelMapping.is_selected == 1
                )
            )
        )
        return result or 0
