from datetime import datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_administrative.entity.do.trips_do import OaTrips
from module_administrative.entity.vo.trips_vo import TripsModel, TripsPageQueryModel
from utils.page_util import PageUtil
from utils.log_util import logger


class TripsDao:
    """
    出差管理模块数据库操作层
    """

    @classmethod
    async def get_trips_detail_by_id(cls, db: AsyncSession, trips_id: int) -> OaTrips | None:
        """
        根据出差 id 获取出差详细信息

        :param db: orm 对象
        :param trips_id: 出差 id
        :return: 出差信息对象
        """
        trips_info = (
            (await db.execute(select(OaTrips).where(OaTrips.id == trips_id)))
            .scalars()
            .first()
        )

        return trips_info

    @classmethod
    async def get_trips_list(
            cls, db: AsyncSession, query_object: TripsPageQueryModel, user_id: int, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        根据查询参数获取出差列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param user_id: 当前用户 ID
        :param is_page: 是否开启分页
        :return: 出差列表信息对象
        """
        query = select(OaTrips).where(
            OaTrips.delete_time == 0,
            OaTrips.admin_id == user_id
        )

        if query_object.keywords:
            query = query.where(
                OaTrips.reason.like(f'%{query_object.keywords}%')
            )

        query = query.order_by(OaTrips.create_time.desc()).distinct()

        trips_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return trips_list

    @classmethod
    async def add_trips_dao(cls, db: AsyncSession, trips: dict | TripsModel) -> OaTrips:
        """
        新增出差数据库操作

        :param db: orm 对象
        :param trips: 出差对象或字典
        :return:
        """
        if isinstance(trips, TripsModel):
            trips_dict = {
                k: v for k, v in trips.model_dump().items()
                if k not in {'admin_name', 'dept_name'}
            }
        else:
            trips_dict = trips

        logger.info(f"DAO层接收到的出差数据 - admin_id: {trips_dict.get('admin_id')}, did: {trips_dict.get('did')}")

        db_trips = OaTrips(**trips_dict)
        db.add(db_trips)
        await db.flush()

        return db_trips

    @classmethod
    async def edit_trips_dao(cls, db: AsyncSession, trips_id: int, trips: dict) -> None:
        """
        编辑出差数据库操作

        :param db: orm 对象
        :param trips_id: 出差 ID
        :param trips: 需要更新的出差字典
        :return:
        """
        await db.execute(
            update(OaTrips)
            .where(OaTrips.id == trips_id)
            .values(**trips)
        )

    @classmethod
    async def delete_trips_dao(cls, db: AsyncSession, trips: TripsModel) -> None:
        """
        删除出差数据库操作（逻辑删除）

        :param db: orm 对象
        :param trips: 出差对象
        :return:
        """
        update_time = trips.update_time if trips.update_time is not None else int(datetime.now().timestamp())
        delete_time = update_time
        await db.execute(
            update(OaTrips)
            .where(OaTrips.id.in_([trips.id]))
            .values(delete_time=delete_time, update_time=update_time)
        )