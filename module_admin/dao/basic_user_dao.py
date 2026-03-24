from datetime import datetime
from typing import Any

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.basic_user_do import SysBasicUser
from module_admin.entity.vo.basic_user_vo import BasicUserModel, BasicUserPageQueryModel
from utils.page_util import PageUtil


class BasicUserDao:
    """
    人事模块常规数据管理模块数据库操作层
    """

    @classmethod
    async def get_basic_user_detail_by_id(cls, db: AsyncSession, basic_user_id: int) -> SysBasicUser | None:
        """
        根据 ID 获取人事模块常规数据详细信息

        :param db: orm 对象
        :param basic_user_id: 数据 ID
        :return: 人事模块常规数据信息对象
        """
        basic_user_info = (
            (await db.execute(select(SysBasicUser).where(SysBasicUser.id == basic_user_id)))
            .scalars()
            .first()
        )

        return basic_user_info

    @classmethod
    async def get_basic_user_detail_by_info(cls, db: AsyncSession, basic_user: BasicUserModel) -> SysBasicUser | None:
        """
        根据人事模块常规数据参数获取信息

        :param db: orm 对象
        :param basic_user: 人事模块常规数据参数对象
        :return: 人事模块常规数据信息对象
        """
        query_conditions = []
        if basic_user.title:
            query_conditions.append(SysBasicUser.title == basic_user.title)

        if query_conditions:
            basic_user_info = (
                (await db.execute(select(SysBasicUser).where(and_(*query_conditions))))
                .scalars()
                .first()
            )
        else:
            basic_user_info = None

        return basic_user_info

    @classmethod
    async def get_basic_user_list(
            cls, db: AsyncSession, query_object: BasicUserPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        根据查询参数获取人事模块常规数据列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 人事模块常规数据列表信息对象
        """
        query = (
            select(SysBasicUser)
            .where(
                SysBasicUser.status != -1,
                SysBasicUser.types == query_object.types if query_object.types else True,
                SysBasicUser.title.like(f'%{query_object.title}%') if query_object.title else True,
                SysBasicUser.status == query_object.status if query_object.status is not None else True,
                )
            .order_by(SysBasicUser.create_time.asc())
            .distinct()
        )
        basic_user_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return basic_user_list

    @classmethod
    async def add_basic_user_dao(cls, db: AsyncSession, basic_user: BasicUserModel) -> SysBasicUser:
        """
        新增人事模块常规数据数据库操作

        :param db: orm 对象
        :param basic_user: 人事模块常规数据对象
        :return:
        """
        db_basic_user = SysBasicUser(**basic_user.model_dump())
        db.add(db_basic_user)
        await db.flush()

        return db_basic_user

    @classmethod
    async def edit_basic_user_dao(cls, db: AsyncSession, basic_user: dict) -> None:
        """
        编辑人事模块常规数据数据库操作

        :param db: orm 对象
        :param basic_user: 需要更新的人事模块常规数据字典
        :return:
        """
        await db.execute(update(SysBasicUser), [basic_user])

    @classmethod
    async def delete_basic_user_dao(cls, db: AsyncSession, basic_user: BasicUserModel) -> None:
        """
        删除人事模块常规数据数据库操作（逻辑删除）

        :param db: orm 对象
        :param basic_user: 人事模块常规数据对象
        :return:
        """
        update_time = basic_user.update_time if basic_user.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(SysBasicUser)
            .where(SysBasicUser.id.in_([basic_user.id]))
            .values(status=-1, update_time=update_time)
        )

    @classmethod
    async def disable_basic_user_dao(cls, db: AsyncSession, basic_user: BasicUserModel) -> None:
        """
        禁用人事模块常规数据数据库操作

        :param db: orm 对象
        :param basic_user: 人事模块常规数据对象
        :return:
        """
        update_time = basic_user.update_time if basic_user.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(SysBasicUser)
            .where(SysBasicUser.id == basic_user.id)
            .values(status=0, update_time=update_time)
        )

    @classmethod
    async def enable_basic_user_dao(cls, db: AsyncSession, basic_user: BasicUserModel) -> None:
        """
        启用人事模块常规数据数据库操作

        :param db: orm 对象
        :param basic_user: 人事模块常规数据对象
        :return:
        """
        update_time = basic_user.update_time if basic_user.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(SysBasicUser)
            .where(SysBasicUser.id == basic_user.id)
            .values(status=1, update_time=update_time)
        )

