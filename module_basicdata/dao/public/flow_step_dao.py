from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, update
from module_basicdata.entity.do.public.flow_step_do import OaFlowStep
from datetime import datetime


class OaFlowStepDao:
    @classmethod
    async def add(cls, db: AsyncSession, data: dict):
        db_module = OaFlowStep(**data)
        db.add(db_module)
        await db.commit()
        await db.refresh(db_module)
        return db_module

    @classmethod
    async def add_flow_step(cls, db : AsyncSession, steps:list):
        try:
            for step in steps:
                db_module = OaFlowStep(**step.model_dump(exclude_none=True))
                db.add(db_module)
            await db.commit()
            return True
        except Exception as e:
            print("error: ",e)
            return False

    @classmethod
    async def get_info_by_flow_id(cls, db: AsyncSession, id: int):
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

    @classmethod
    async def get_step_by_action_id_flow_id(cls, db : AsyncSession, action_id:int, flow_id:int, sort: int):
        query = select(OaFlowStep).where(OaFlowStep.flow_id == flow_id, OaFlowStep.action_id == action_id, OaFlowStep.sort == sort,OaFlowStep.delete_time == 0 ).order_by(desc(OaFlowStep.create_time))
        result = await db.execute(query)
        return result.scalars().first()

    @classmethod
    async def get_step_by_action_id_flow_id_list(cls, db: AsyncSession, action_id: int, flow_id: int):
        query = select(OaFlowStep).where(OaFlowStep.flow_id == flow_id, OaFlowStep.action_id == action_id, OaFlowStep.delete_time == 0).order_by(
            desc(OaFlowStep.create_time))
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def get_step_by_action_id_flow_id_sort(cls, db: AsyncSession, action_id:int, flow_id:int, sort: int):
        query = select(OaFlowStep).where(OaFlowStep.action_id==action_id, OaFlowStep.flow_id == flow_id, OaFlowStep.sort == sort)
        result = await db.execute(query)
        return result.scalars().first()

    @classmethod
    async def delete_flow_step(cls, db : AsyncSession, flow_id:int, action_id : int):
        """
        删除审核步骤
        :param db:
        :param flow_id:
        :param action_id:
        :return:
        """
        try:
            query = update(OaFlowStep).values(delete_time = int(datetime.now().timestamp())).where(OaFlowStep.flow_id == flow_id, OaFlowStep.action_id == action_id)
            await db.execute(query)
            await db.commit()
            return True
        except Exception as e:
            return False


