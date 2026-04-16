from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,desc,func, update

from module_admin.entity.do.user_do import SysUser
from module_personnel.entity.vo.flow_record_vo import OaFlowRecordBaseModel
from module_personnel.entity.do.flow_record_do import OaFlowRecord
from typing import Any



class FlowRecordDao:
    """审批记录DAO"""

    @classmethod
    async def add(cls, db:AsyncSession, model:OaFlowRecordBaseModel):
        db_model = OaFlowRecord(**model.model_dump(exclude={"id", "check_time"}, exclude_none=True), check_time=model.check_time)
        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)
        return db_model

    @classmethod
    async def get_records_by_action_id(cls, db: AsyncSession, action_id: int, flow_id: int) -> OaFlowRecordBaseModel | list[OaFlowRecordBaseModel] | None:
        """获取审批记录"""
        query = select(OaFlowRecord).filter(OaFlowRecord.action_id == action_id,OaFlowRecord.flow_id == flow_id).order_by(desc(OaFlowRecord.check_time))
        records = (await db.execute(query)).scalars().all()
        return records

    @classmethod
    async def get_count_by_action_id_flow_id_step_id(cls, db: AsyncSession, action_id: int, flow_id: int, step_id: int) -> int:
        """
        获取同意步骤审批记录数量
        :param db:
        :param action_id:
        :param flow_id:
        :param step_id:
        :return:
        """
        query = select(func.count()).select_from(OaFlowRecord).where(OaFlowRecord.action_id == action_id,OaFlowRecord.flow_id == flow_id, OaFlowRecord.step_id == step_id)
        result = await db.execute(query)
        return result.scalars()
    @classmethod
    async def delete_flow_info(cls, db: AsyncSession, flow_id: int, action_id: int):
        """
        删除流程记录
        """
        query = update(OaFlowRecord).where(OaFlowRecord.flow_id == flow_id, OaFlowRecord.action_id == action_id, OaFlowRecord.step_id == action_id)
        await db.execute(query)
        await db.commit()


    @classmethod
    async def get_flow_record_by_action_table(cls, db: AsyncSession, action_id: int, check_table:str) -> list[dict[str, Any]] | None:
        """
        获取流程记录
        :param db:
        :param action_id:
        :param check_table:
        :return:
        """
        query = select(OaFlowRecord, SysUser.nick_name).join(SysUser, OaFlowRecord.check_uid == SysUser.id, isouter=True).where(OaFlowRecord.action_id == action_id, OaFlowRecord.check_table == check_table)
        result = await db.execute(query)
        return result.mappings().all()
    @classmethod
    async def get_flow_record_by_check_uid_step_id(cls, db: AsyncSession, check_uid: int, step_id: int) -> list[dict[str, Any]] | None:
        """
        获取流程记录
        :param db:
        :param check_uid:
        :param step_id:
        :return:
        """
        query = select(OaFlowRecord).where(OaFlowRecord.check_uid == check_uid, OaFlowRecord.step_id == step_id)
        result = await db.execute(query)
        return result.mappings().all()

    @classmethod
    async def get_records_by_action_id_flow_id(cls, db: AsyncSession, action_id: int, flow_id: int) -> OaFlowRecordBaseModel | \
                                                                                               list[
                                                                                                   OaFlowRecordBaseModel] | None:
        """获取审批记录"""
        query = select(OaFlowRecord).filter(OaFlowRecord.action_id == action_id,
                                            OaFlowRecord.flow_id == flow_id).order_by(desc(OaFlowRecord.check_time))
        records = (await db.execute(query)).mappings().all()
        return records