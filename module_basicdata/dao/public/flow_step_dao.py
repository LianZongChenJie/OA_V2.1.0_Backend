from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from module_basicdata.entity.do.public.flow_step_do import OaFlowStep


class OaFlowStepDao:
    @classmethod
    async def add(cls, db : AsyncSession, data:OaFlowStep):
        db_module = OaFlowStep(**data.model_dump())
        db.add(db_module)
        await db.commit()
        await db.refresh(db_module)
        return db_module

    @classmethod
    async def get_info_by_flow_id(cls, db : AsyncSession, id:int):
        query_flow_step_info = (
            (
                await db.execute(
                    select(OaFlowStep)
                    .where(OaFlowStep.flow_id == id).order_by(desc(OaFlowStep.create_time))
                    .distinct()
                )
            )
            .scalars()
            .first()
        )
        return query_flow_step_info