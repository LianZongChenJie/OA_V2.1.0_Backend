# module_contract/dao/contract_attachment_dao.py
from datetime import datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from module_contract.entity.do.contract_attachment_do import OaContractAttachment


class ContractAttachmentDao:
    """
    销售合同附件管理模块数据库操作层
    """

    @classmethod
    async def get_attachment_list(
            cls, db: AsyncSession, contract_id: int
    ) -> list[OaContractAttachment]:
        """
        根据合同ID获取附件列表

        :param db: orm 对象
        :param contract_id: 合同ID
        :return: 附件列表
        """
        query = select(OaContractAttachment).where(
            OaContractAttachment.contract_id == contract_id,
            OaContractAttachment.delete_time == 0
        ).order_by(OaContractAttachment.sort, OaContractAttachment.id)

        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def get_attachment_by_id(
            cls, db: AsyncSession, attachment_id: int
    ) -> OaContractAttachment | None:
        """
        根据附件ID获取附件详情

        :param db: orm 对象
        :param attachment_id: 附件ID
        :return: 附件对象
        """
        query = select(OaContractAttachment).where(
            OaContractAttachment.id == attachment_id,
            OaContractAttachment.delete_time == 0
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def add_attachment(
            cls, db: AsyncSession, attachment_data: dict
    ) -> OaContractAttachment:
        """
        新增附件

        :param db: orm 对象
        :param attachment_data: 附件数据字典
        :return: 新增的附件对象
        """
        db_model = OaContractAttachment(**attachment_data)
        db.add(db_model)
        await db.flush()
        await db.refresh(db_model)
        return db_model

    @classmethod
    async def delete_attachment(
            cls, db: AsyncSession, attachment_ids: list[int]
    ) -> bool:
        """
        删除附件（软删除）

        :param db: orm 对象
        :param attachment_ids: 附件ID列表
        :return: 是否成功
        """
        if not attachment_ids:
            return True

        query = (
            update(OaContractAttachment)
            .where(
                OaContractAttachment.id.in_(attachment_ids),
                OaContractAttachment.delete_time == 0
            )
            .values(delete_time=int(datetime.now().timestamp() * 1000))
        )
        await db.execute(query)
        return True

    @classmethod
    async def batch_delete_attachment(
            cls, db: AsyncSession, attachment_ids: list[int], delete_time: int
    ) -> bool:
        """
        批量删除附件（软删除）

        :param db: orm 对象
        :param attachment_ids: 附件ID列表
        :param delete_time: 删除时间
        :return: 是否成功
        """
        if not attachment_ids:
            return True

        query = (
            update(OaContractAttachment)
            .where(
                OaContractAttachment.id.in_(attachment_ids),
                OaContractAttachment.delete_time == 0
            )
            .values(delete_time=delete_time * 1000)
        )
        await db.execute(query)
        return True
