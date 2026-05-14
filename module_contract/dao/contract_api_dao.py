from typing import Any, Dict

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from module_contract.entity.do.contract_do import OaContract
from module_contract.entity.do.purchase_do import OaPurchase


class ContractApiDao:
    """
    合同API数据库操作层
    """

    @classmethod
    async def get_contract_by_id(cls, db: AsyncSession, contract_type: str, contract_id: int) -> Dict[str, Any] | None:
        """
        根据合同类型和ID获取合同信息

        :param db: orm 对象
        :param contract_type: 合同类型（sale/purchase）
        :param contract_id: 合同 ID
        :return: 合同信息字典
        """
        if contract_type == 'sale':
            contract_info = (
                (await db.execute(select(OaContract).where(OaContract.id == contract_id)))
                .scalars()
                .first()
            )
        else:
            contract_info = (
                (await db.execute(select(OaPurchase).where(OaPurchase.id == contract_id)))
                .scalars()
                .first()
            )

        if contract_info:
            return {c.name: getattr(contract_info, c.name) for c in contract_info.__table__.columns}
        return None

    @classmethod
    async def set_contract_stop(cls, db: AsyncSession, contract_type: str, contract_id: int, stop_data: Dict[str, Any]) -> int:
        """
        设置合同中止状态

        :param db: orm 对象
        :param contract_type: 合同类型（sale/purchase）
        :param contract_id: 合同 ID
        :param stop_data: 中止数据字典
        :return: 影响的行数
        """
        if contract_type == 'sale':
            result = await db.execute(
                update(OaContract)
                .where(OaContract.id == contract_id)
                .values(**stop_data)
            )
        else:
            result = await db.execute(
                update(OaPurchase)
                .where(OaPurchase.id == contract_id)
                .values(**stop_data)
            )

        return result.rowcount

    @classmethod
    async def set_contract_void(cls, db: AsyncSession, contract_type: str, contract_id: int, void_data: Dict[str, Any]) -> int:
        """
        设置合同作废状态

        :param db: orm 对象
        :param contract_type: 合同类型（sale/purchase）
        :param contract_id: 合同 ID
        :param void_data: 作废数据字典
        :return: 影响的行数
        """
        if contract_type == 'sale':
            result = await db.execute(
                update(OaContract)
                .where(OaContract.id == contract_id)
                .values(**void_data)
            )
        else:
            result = await db.execute(
                update(OaPurchase)
                .where(OaPurchase.id == contract_id)
                .values(**void_data)
            )

        return result.rowcount
