from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from module_personnel.entity.vo.flow_record_vo import OaFlowRecordBaseModel
from module_personnel.entity.do.flow_record_do import OaFlowRecord



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
        query = select(OaFlowRecord).filter(OaFlowRecord.action_id == action_id,OaFlowRecord.flow_id == flow_id).order_by(OaFlowRecord.check_time.desc())
        record = (await db.execute(query)).scalars().all()
        return record
