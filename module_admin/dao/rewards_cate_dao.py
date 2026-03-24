from datetime import datetime
from typing import Any

from sqlalchemy import and_, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.rewards_cate_do import SysRewardsCate
from module_admin.entity.vo.rewards_cate_vo import RewardsCateModel, RewardsCatePageQueryModel
from utils.page_util import PageUtil


class RewardsCateDao:
    """
    奖罚项目管理模块数据库操作层
    """

    @classmethod
    async def get_rewards_cate_detail_by_id(cls, db: AsyncSession, rewards_cate_id: int) -> SysRewardsCate | None:
        """
        根据奖罚项目 id 获取奖罚项目详细信息

        :param db: orm 对象
        :param rewards_cate_id: 奖罚项目 id
        :return: 奖罚项目信息对象
        """
        rewards_cate_info = (
            (await db.execute(select(SysRewardsCate).where(SysRewardsCate.id == rewards_cate_id)))
            .scalars()
            .first()
        )

        return rewards_cate_info

    @classmethod
    async def get_rewards_cate_detail_by_info(cls, db: AsyncSession, rewards_cate: RewardsCateModel) -> SysRewardsCate | None:
        """
        根据奖罚项目参数获取奖罚项目信息

        :param db: orm 对象
        :param rewards_cate: 奖罚项目参数对象
        :return: 奖罚项目信息对象
        """
        query_conditions = []
        if rewards_cate.title:
            query_conditions.append(SysRewardsCate.title == rewards_cate.title)

        if query_conditions:
            rewards_cate_info = (
                (await db.execute(select(SysRewardsCate).where(and_(*query_conditions))))
                .scalars()
                .first()
            )
        else:
            rewards_cate_info = None

        return rewards_cate_info

    @classmethod
    async def get_rewards_cate_list(
            cls, db: AsyncSession, query_object: RewardsCatePageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        根据查询参数获取奖罚项目列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 奖罚项目列表信息对象
        """
        query = (
            select(SysRewardsCate)
            .where(
                SysRewardsCate.status != -1,
                SysRewardsCate.title.like(f'%{query_object.title}%') if query_object.title else True,
                SysRewardsCate.status == query_object.status if query_object.status is not None else True,
                )
            .order_by(SysRewardsCate.id)
            .distinct()
        )
        rewards_cate_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return rewards_cate_list

    @classmethod
    async def add_rewards_cate_dao(cls, db: AsyncSession, rewards_cate: RewardsCateModel) -> SysRewardsCate:
        """
        新增奖罚项目数据库操作

        :param db: orm 对象
        :param rewards_cate: 奖罚项目对象
        :return:
        """
        db_rewards_cate = SysRewardsCate(**rewards_cate.model_dump())
        db.add(db_rewards_cate)
        await db.flush()

        return db_rewards_cate

    @classmethod
    async def edit_rewards_cate_dao(cls, db: AsyncSession, rewards_cate: dict) -> None:
        """
        编辑奖罚项目数据库操作

        :param db: orm 对象
        :param rewards_cate: 需要更新的奖罚项目字典
        :return:
        """
        await db.execute(update(SysRewardsCate), [rewards_cate])

    @classmethod
    async def delete_rewards_cate_dao(cls, db: AsyncSession, rewards_cate: RewardsCateModel) -> None:
        """
        删除奖罚项目数据库操作（逻辑删除）

        :param db: orm 对象
        :param rewards_cate: 奖罚项目对象
        :return:
        """
        update_time = rewards_cate.update_time if rewards_cate.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(SysRewardsCate)
            .where(SysRewardsCate.id.in_([rewards_cate.id]))
            .values(status=-1, update_time=update_time)
        )

    @classmethod
    async def disable_rewards_cate_dao(cls, db: AsyncSession, rewards_cate: RewardsCateModel) -> None:
        """
        禁用奖罚项目数据库操作

        :param db: orm 对象
        :param rewards_cate: 奖罚项目对象
        :return:
        """
        update_time = rewards_cate.update_time if rewards_cate.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(SysRewardsCate)
            .where(SysRewardsCate.id == rewards_cate.id)
            .values(status=0, update_time=update_time)
        )

    @classmethod
    async def enable_rewards_cate_dao(cls, db: AsyncSession, rewards_cate: RewardsCateModel) -> None:
        """
        启用奖罚项目数据库操作

        :param db: orm 对象
        :param rewards_cate: 奖罚项目对象
        :return:
        """
        update_time = rewards_cate.update_time if rewards_cate.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(SysRewardsCate)
            .where(SysRewardsCate.id == rewards_cate.id)
            .values(status=1, update_time=update_time)
        )
