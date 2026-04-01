from datetime import datetime
from typing import Any

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.customer_chance_do import CustomerChance
from module_admin.entity.vo.customer_chance_vo import CustomerChanceModel, CustomerChancePageQueryModel
from utils.page_util import PageUtil


class CustomerChanceDao:
    """
    客户机会管理模块数据库操作层
    """

    @classmethod
    async def get_customer_chance_detail_by_id(cls, db: AsyncSession, chance_id: int) -> CustomerChance | None:
        """
        根据机会 ID 获取客户机会详细信息

        :param db: orm 对象
        :param chance_id: 机会 ID
        :return: 客户机会信息对象
        """
        chance_info = (
            (await db.execute(select(CustomerChance).where(CustomerChance.id == chance_id)))
            .scalars()
            .first()
        )

        return chance_info

    @classmethod
    async def get_customer_chance_detail_by_info(cls, db: AsyncSession, chance: CustomerChanceModel) -> CustomerChance | None:
        """
        根据客户机会参数获取信息

        :param db: orm 对象
        :param chance: 客户机会参数对象
        :return: 客户机会信息对象
        """
        query_conditions = []
        if chance.id is not None:
            query_conditions.append(CustomerChance.id == chance.id)
        if chance.title:
            query_conditions.append(CustomerChance.title == chance.title)
        if chance.cid is not None:
            query_conditions.append(CustomerChance.cid == chance.cid)

        if query_conditions:
            chance_info = (
                (await db.execute(select(CustomerChance).where(and_(*query_conditions))))
                .scalars()
                .first()
            )
        else:
            chance_info = None

        return chance_info

    @classmethod
    async def get_customer_chance_list(
            cls, db: AsyncSession, query_object: CustomerChancePageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        根据查询参数获取客户机会列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 客户机会列表信息对象
        """
        query = (
            select(CustomerChance)
            .where(
                CustomerChance.delete_time == 0,
                CustomerChance.title.like(f'%{query_object.title}%') if query_object.title else True,
                CustomerChance.stage == query_object.stage if query_object.stage is not None else True,
                CustomerChance.belong_uid == query_object.belong_uid if query_object.belong_uid is not None else True,
                )
            .order_by(CustomerChance.create_time.desc())
            .distinct()
        )
        chance_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return chance_list

    @classmethod
    async def get_all_customer_chance_list(cls, db: AsyncSession) -> list[dict[str, Any]]:
        """
        获取所有客户机会列表信息

        :param db: orm 对象
        :return: 客户机会列表信息对象
        """
        query = (
            select(CustomerChance)
            .where(CustomerChance.delete_time == 0)
            .order_by(CustomerChance.create_time.desc())
            .distinct()
        )
        result = (await db.execute(query)).scalars().all()

        return [item.__dict__ for item in result if not item._sa_instance_state.deleted]

    @classmethod
    async def add_customer_chance_dao(cls, db: AsyncSession, chance: CustomerChanceModel) -> CustomerChance:
        """
        新增客户机会数据库操作

        :param db: orm 对象
        :param chance: 客户机会对象
        :return:
        """
        db_chance = CustomerChance(**chance.model_dump())
        db.add(db_chance)
        await db.flush()

        return db_chance

    @classmethod
    async def edit_customer_chance_dao(cls, db: AsyncSession, chance: dict) -> None:
        """
        编辑客户机会数据库操作

        :param db: orm 对象
        :param chance: 需要更新的客户机会字典
        :return:
        """
        await db.execute(update(CustomerChance), [chance])

    @classmethod
    async def delete_customer_chance_dao(cls, db: AsyncSession, chance: CustomerChanceModel) -> None:
        """
        删除客户机会数据库操作（逻辑删除）

        :param db: orm 对象
        :param chance: 客户机会对象
        :return:
        """
        update_time = chance.update_time if chance.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(CustomerChance)
            .where(CustomerChance.id == chance.id)
            .values(delete_time=update_time, update_time=update_time)
        )
