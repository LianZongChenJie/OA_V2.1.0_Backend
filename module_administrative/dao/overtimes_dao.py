from datetime import datetime
from typing import Any

from sqlalchemy import and_, select, update, or_
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_administrative.entity.do.overtimes_do import OaOvertimes
from module_administrative.entity.vo.overtimes_vo import OvertimesPageQueryModel
from utils.page_util import PageUtil


class OvertimesDao:
    """
    加班记录管理模块数据库操作层
    """

    @classmethod
    async def get_overtimes_detail_by_id(cls, db: AsyncSession, overtimes_id: int) -> OaOvertimes | None:
        """
        根据加班记录 ID 获取加班记录详细信息

        :param db: orm 对象
        :param overtimes_id: 加班记录 ID
        :return: 加班记录信息对象
        """
        overtimes_info = (
            (await db.execute(select(OaOvertimes).where(OaOvertimes.id == overtimes_id)))
            .scalars()
            .first()
        )

        return overtimes_info

    @classmethod
    async def get_overtimes_list(
            cls, db: AsyncSession, query_object: OvertimesPageQueryModel, user_id: int, is_page: bool = False
    ) -> PageModel | list[dict]:
        """
        根据查询参数获取加班记录列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param user_id: 当前用户 ID
        :param is_page: 是否开启分页
        :return: 加班记录列表信息对象
        """
        query = select(OaOvertimes).where(OaOvertimes.delete_time == 0)

        # 根据 tab 标签页筛选
        if query_object.tab is not None:
            if query_object.tab == 1:
                # 我申请的：查询当前用户创建的记录
                query = query.where(OaOvertimes.admin_id == user_id)
            elif query_object.tab == 2:
                # 待我审批：查询当前用户是审批人，且状态为审核中的记录
                query = query.where(
                    OaOvertimes.check_uids.like(f'%{user_id}%'),
                    OaOvertimes.check_status == 1
                )
            elif query_object.tab == 3:
                # 我已审批：查询当前用户在历史审批人中，且状态为已通过
                query = query.where(
                    OaOvertimes.check_history_uids.like(f'%{user_id}%'),
                    OaOvertimes.check_status == 2
                )
        else:
            # 默认查询我申请的
            query = query.where(OaOvertimes.admin_id == user_id)

        # 关键词搜索（搜索ID或加班原因）
        if query_object.keywords:
            query = query.where(
                or_(
                    OaOvertimes.id.like(f'%{query_object.keywords}%'),
                    OaOvertimes.reason.like(f'%{query_object.keywords}%'),
                )
            )

        # 审核状态筛选
        if query_object.check_status is not None:
            query = query.where(OaOvertimes.check_status == query_object.check_status)

        # 创建人ID筛选
        if query_object.admin_id is not None and query_object.admin_id > 0:
            query = query.where(OaOvertimes.admin_id == query_object.admin_id)

        # 时间范围查询（基于开始日期）
        if query_object.begin_time and query_object.end_time:
            try:
                begin_timestamp = int(datetime.fromisoformat(query_object.begin_time).timestamp())
                end_timestamp = int(datetime.fromisoformat(query_object.end_time + ' 23:59:59').timestamp())
                query = query.where(
                    and_(
                        OaOvertimes.start_date >= begin_timestamp,
                        OaOvertimes.start_date <= end_timestamp,
                    )
                )
            except ValueError:
                pass

        query = query.order_by(OaOvertimes.id.desc())

        overtimes_list: PageModel | list[dict] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return overtimes_list

    @classmethod
    async def add_overtimes_dao(cls, db: AsyncSession, overtimes: dict) -> OaOvertimes:
        """
        新增加班记录数据库操作

        :param db: orm 对象
        :param overtimes: 加班记录字典
        :return:
        """
        db_overtimes = OaOvertimes(**overtimes)
        db.add(db_overtimes)
        await db.flush()

        return db_overtimes

    @classmethod
    async def edit_overtimes_dao(cls, db: AsyncSession, overtimes_id: int, overtimes: dict) -> None:
        """
        编辑加班记录数据库操作

        :param db: orm 对象
        :param overtimes_id: 加班记录 ID
        :param overtimes: 需要更新的加班记录字典
        :return:
        """
        await db.execute(
            update(OaOvertimes)
            .where(OaOvertimes.id == overtimes_id)
            .values(**overtimes)
        )

    @classmethod
    async def delete_overtimes_dao(cls, db: AsyncSession, overtimes_id: int) -> None:
        """
        删除加班记录数据库操作（逻辑删除）

        :param db: orm 对象
        :param overtimes_id: 加班记录 ID
        :return:
        """
        await db.execute(
            update(OaOvertimes)
            .where(OaOvertimes.id == overtimes_id)
            .values(delete_time=int(datetime.now().timestamp()))
        )