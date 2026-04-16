from datetime import datetime
from typing import Any

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from module_project.entity.do.project_step_do import OaProjectStep
from module_project.entity.do.project_step_record_do import OaProjectStepRecord


class ProjectStepDao:
    """
    项目阶段模块数据库操作层
    """

    @classmethod
    async def get_steps_by_project_id(cls, db: AsyncSession, project_id: int) -> list[OaProjectStep]:
        """
        根据项目ID获取阶段列表

        :param db: orm 对象
        :param project_id: 项目ID
        :return: 阶段列表
        """
        query = (
            select(OaProjectStep)
            .where(
                OaProjectStep.project_id == project_id,
                OaProjectStep.delete_time == 0
            )
            .order_by(OaProjectStep.sort.asc())
        )
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def add_step(cls, db: AsyncSession, step_data: dict) -> OaProjectStep:
        """
        新增阶段

        :param db: orm 对象
        :param step_data: 阶段数据
        :return: 阶段对象
        """
        db_step = OaProjectStep(**step_data)
        db.add(db_step)
        await db.flush()
        return db_step

    @classmethod
    async def update_step(cls, db: AsyncSession, step_id: int, step_data: dict) -> None:
        """
        更新阶段

        :param db: orm 对象
        :param step_id: 阶段ID
        :param step_data: 更新数据
        :return:
        """
        await db.execute(
            update(OaProjectStep)
            .where(OaProjectStep.id == step_id)
            .values(**step_data)
        )

    @classmethod
    async def delete_step(cls, db: AsyncSession, step_id: int) -> None:
        """
        删除阶段（逻辑删除）

        :param db: orm 对象
        :param step_id: 阶段ID
        :return:
        """
        delete_time = int(datetime.now().timestamp())
        await db.execute(
            update(OaProjectStep)
            .where(OaProjectStep.id == step_id)
            .values(delete_time=delete_time, update_time=delete_time)
        )

    @classmethod
    async def delete_steps_by_project_id(cls, db: AsyncSession, project_id: int) -> None:
        """
        根据项目ID删除所有阶段（逻辑删除）

        :param db: orm 对象
        :param project_id: 项目ID
        :return:
        """
        delete_time = int(datetime.now().timestamp())
        await db.execute(
            update(OaProjectStep)
            .where(
                OaProjectStep.project_id == project_id,
                OaProjectStep.delete_time == 0
            )
            .values(delete_time=delete_time, update_time=delete_time)
        )

    @classmethod
    async def add_step_record(cls, db: AsyncSession, record_data: dict) -> OaProjectStepRecord:
        """
        添加阶段确认记录

        :param db: orm 对象
        :param record_data: 记录数据
        :return: 记录对象
        """
        db_record = OaProjectStepRecord(**record_data)
        db.add(db_record)
        await db.flush()
        return db_record

    @classmethod
    async def get_records_by_step_id(cls, db: AsyncSession, step_id: int) -> list[OaProjectStepRecord]:
        """
        根据阶段ID获取确认记录

        :param db: orm 对象
        :param step_id: 阶段ID
        :return: 记录列表
        """
        query = (
            select(OaProjectStepRecord)
            .where(
                OaProjectStepRecord.step_id == step_id,
                OaProjectStepRecord.delete_time == 0
            )
            .order_by(OaProjectStepRecord.check_time.desc())
        )
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def set_current_step(cls, db: AsyncSession, project_id: int, step_id: int) -> None:
        """
        设置当前阶段

        :param db: orm 对象
        :param project_id: 项目ID
        :param step_id: 阶段ID
        :return:
        """
        # 先将该项目的所有阶段设置为非当前
        await db.execute(
            update(OaProjectStep)
            .where(OaProjectStep.project_id == project_id)
            .values(is_current=0)
        )

        # 设置指定阶段为当前
        if step_id > 0:
            await db.execute(
                update(OaProjectStep)
                .where(OaProjectStep.id == step_id)
                .values(is_current=1)
            )