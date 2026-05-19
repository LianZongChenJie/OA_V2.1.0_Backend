from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from module_project.entity.do.project_user_do import OaProjectUser


class ProjectUserDao:
    """
    项目成员数据库操作层
    """

    @classmethod
    async def get_users_by_project_id(cls, db: AsyncSession, project_id: int) -> list[OaProjectUser]:
        """
        根据项目ID获取成员列表

        :param db: orm 对象
        :param project_id: 项目ID
        :return: 成员列表
        """
        query = select(OaProjectUser).where(
            OaProjectUser.project_id == project_id,
            OaProjectUser.delete_time == 0
        )
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def delete_users_by_project_id(cls, db: AsyncSession, project_id: int, delete_time: int) -> int:
        """
        删除项目的所有成员（逻辑删除）

        :param db: orm 对象
        :param project_id: 项目ID
        :param delete_time: 删除时间
        :return: 影响行数
        """
        result = await db.execute(
            update(OaProjectUser)
            .values(delete_time=delete_time)
            .where(
                and_(
                    OaProjectUser.project_id == project_id,
                    OaProjectUser.delete_time == 0
                )
            )
        )
        return result.rowcount

    @classmethod
    async def add_user(cls, db: AsyncSession, user_data: dict) -> OaProjectUser:
        """
        新增项目成员

        :param db: orm 对象
        :param user_data: 成员数据
        :return: 成员对象
        """
        db_user = OaProjectUser(**user_data)
        db.add(db_user)
        await db.flush()
        return db_user

    @classmethod
    async def batch_add_users(cls, db: AsyncSession, users_list: list[dict]) -> list[OaProjectUser]:
        """
        批量新增项目成员

        :param db: orm 对象
        :param users_list: 成员数据列表
        :return: 成员对象列表
        """
        added_users = []
        for user_data in users_list:
            db_user = await cls.add_user(db, user_data)
            added_users.append(db_user)
        return added_users
