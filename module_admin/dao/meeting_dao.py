from datetime import datetime
from typing import Any

from sqlalchemy import and_, select, update, or_
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.meeting_do import OaMeetingRoom, OaMeetingOrder, OaMeetingRecords
from module_admin.entity.vo.meeting_vo import (
    MeetingRoomPageQueryModel,
    MeetingOrderPageQueryModel,
    MeetingRecordsPageQueryModel,
)
from utils.page_util import PageUtil


class MeetingRoomDao:
    """
    会议室管理模块数据库操作层
    """

    @classmethod
    async def get_meeting_room_detail_by_id(cls, db: AsyncSession, room_id: int) -> OaMeetingRoom | None:
        """
        根据会议室 ID 获取会议室详细信息
        """
        room_info = (
            (await db.execute(select(OaMeetingRoom).where(OaMeetingRoom.id == room_id)))
            .scalars()
            .first()
        )
        return room_info

    @classmethod
    async def get_meeting_room_detail_by_info(cls, db: AsyncSession, title: str) -> OaMeetingRoom | None:
        """
        根据会议室名称获取会议室详细信息
        """
        room_info = (
            (await db.execute(select(OaMeetingRoom).where(OaMeetingRoom.title == title, OaMeetingRoom.status != -1)))
            .scalars()
            .first()
        )
        return room_info

    @classmethod
    async def add_meeting_room_dao(cls, db: AsyncSession, room: dict) -> OaMeetingRoom:
        """
        新增会议室数据库操作
        """
        db_room_data = {k: v for k, v in room.items() if k not in ['keep_name']}
        db_room = OaMeetingRoom(**db_room_data)
        db.add(db_room)
        await db.flush()
        return db_room

    @classmethod
    async def edit_meeting_room_dao(cls, db: AsyncSession, room: dict) -> None:
        """
        编辑会议室数据库操作
        """
        db_room_data = {k: v for k, v in room.items() if k not in ['keep_name']}
        await db.execute(update(OaMeetingRoom), [db_room_data])

    @classmethod
    async def delete_meeting_room_dao(cls, db: AsyncSession, room_id: int) -> None:
        """
        删除会议室数据库操作（逻辑删除）
        """
        await db.execute(
            update(OaMeetingRoom)
            .where(OaMeetingRoom.id == room_id)
            .values(status=-1, update_time=int(datetime.now().timestamp()))
        )

    @classmethod
    async def update_meeting_room_status_dao(cls, db: AsyncSession, room_id: int, status: int) -> None:
        """
        更新会议室状态
        """
        await db.execute(
            update(OaMeetingRoom)
            .where(OaMeetingRoom.id == room_id)
            .values(status=status, update_time=int(datetime.now().timestamp()))
        )


class MeetingOrderDao:
    """
    会议室预定模块数据库操作层
    """

    @classmethod
    async def get_meeting_order_detail_by_id(cls, db: AsyncSession, order_id: int) -> OaMeetingOrder | None:
        """
        根据预定 ID 获取预定详细信息
        """
        order_info = (
            (await db.execute(select(OaMeetingOrder).where(OaMeetingOrder.id == order_id)))
            .scalars()
            .first()
        )
        return order_info

    @classmethod
    async def get_meeting_order_list(
            cls, db: AsyncSession, query_object: MeetingOrderPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict]:
        """
        根据查询参数获取预定列表信息
        """
        from module_admin.entity.do.user_do import SysUser
        from module_admin.entity.do.dept_do import SysDept

        query = (
            select(OaMeetingOrder,
                   OaMeetingRoom.title.label('room_name'),
                   SysUser.nick_name.label('admin_name'),
                   SysDept.dept_name.label('dept_name'))
            .join(OaMeetingRoom, OaMeetingRoom.id == OaMeetingOrder.room_id, isouter=True)
            .join(SysUser, SysUser.user_id == OaMeetingOrder.admin_id, isouter=True)
            .join(SysDept, SysDept.dept_id == OaMeetingOrder.did, isouter=True)
            .where(OaMeetingOrder.delete_time == 0)
        )

        if query_object.room_id:
            query = query.where(OaMeetingOrder.room_id == query_object.room_id)

        if query_object.check_status:
            query = query.where(OaMeetingOrder.check_status == query_object.check_status)

        if query_object.keywords:
            query = query.where(
                or_(
                    OaMeetingOrder.title.like(f'%{query_object.keywords}%'),
                    OaMeetingRoom.title.like(f'%{query_object.keywords}%'),
                )
            )

        if query_object.diff_time:
            try:
                time_range = query_object.diff_time.split('~')
                if len(time_range) == 2:
                    begin_timestamp = int(datetime.fromisoformat(time_range[0]).timestamp())
                    end_timestamp = int(datetime.fromisoformat(time_range[1]).timestamp())
                    query = query.where(
                        and_(
                            OaMeetingOrder.start_date >= begin_timestamp,
                            OaMeetingOrder.end_date <= end_timestamp,
                            )
                    )
            except ValueError:
                pass

        query = query.order_by(OaMeetingOrder.id.desc())

        order_list: PageModel | list[dict] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return order_list

    @classmethod
    async def check_time_conflict(
            cls, db: AsyncSession, room_id: int, start_date: int, end_date: int, order_id: int = None
    ) -> int:
        """
        检查时间冲突
        """
        # 基础条件
        base_conditions = [
            OaMeetingOrder.room_id == room_id,
            OaMeetingOrder.delete_time == 0,
            OaMeetingOrder.check_status == 2
        ]
        
        # 三种冲突情况
        conflict1 = and_(
            *base_conditions,
            OaMeetingOrder.start_date >= start_date,
            OaMeetingOrder.start_date < end_date,
        )
        
        conflict2 = and_(
            *base_conditions,
            OaMeetingOrder.end_date > start_date,
            OaMeetingOrder.end_date <= end_date,
        )
        
        conflict3 = and_(
            *base_conditions,
            OaMeetingOrder.start_date <= start_date,
            OaMeetingOrder.end_date >= end_date,
        )
        
        # 合并所有冲突条件
        count_query = select(OaMeetingOrder).where(
            or_(conflict1, conflict2, conflict3)
        )
        
        if order_id:
            count_query = count_query.where(OaMeetingOrder.id != order_id)
        
        result = await db.execute(count_query)
        return len(result.fetchall())

    @classmethod
    async def check_duplicate_order(
            cls, db: AsyncSession, room_id: int, title: str, start_date: int, end_date: int
    ) -> int:
        """
        检查是否存在重复的预定记录（同一会议室、同一主题、同一时间段）
        仅检查待审核和已通过的状态
        """
        query = select(OaMeetingOrder).where(
            OaMeetingOrder.room_id == room_id,
            OaMeetingOrder.title == title,
            OaMeetingOrder.delete_time == 0,
            OaMeetingOrder.check_status.in_([1, 2]),  # 待审核或已通过
            or_(
                # 完全重叠
                and_(
                    OaMeetingOrder.start_date <= start_date,
                    OaMeetingOrder.end_date >= end_date,
                ),
                # 部分重叠 - 开始时间在范围内
                and_(
                    OaMeetingOrder.start_date >= start_date,
                    OaMeetingOrder.start_date < end_date,
                ),
                # 部分重叠 - 结束时间在范围内
                and_(
                    OaMeetingOrder.end_date > start_date,
                    OaMeetingOrder.end_date <= end_date,
                ),
            )
        )
        
        result = await db.execute(query)
        return len(result.fetchall())

    @classmethod
    async def add_meeting_order_dao(cls, db: AsyncSession, order: dict) -> OaMeetingOrder:
        """
        新增预定数据库操作
        """
        db_order_data = {k: v for k, v in order.items() if k not in ['room_name', 'admin_name', 'dept_name']}
        db_order = OaMeetingOrder(**db_order_data)
        db.add(db_order)
        await db.flush()
        return db_order

    @classmethod
    async def edit_meeting_order_dao(cls, db: AsyncSession, order: dict) -> None:
        """
        编辑预定数据库操作
        """
        db_order_data = {k: v for k, v in order.items() if k not in ['room_name', 'admin_name', 'dept_name']}
        await db.execute(update(OaMeetingOrder), [db_order_data])

    @classmethod
    async def delete_meeting_order_dao(cls, db: AsyncSession, order_id: int) -> None:
        """
        删除预定数据库操作（逻辑删除）
        """
        await db.execute(
            update(OaMeetingOrder)
            .where(OaMeetingOrder.id == order_id)
            .values(delete_time=int(datetime.now().timestamp()))
        )


class MeetingRecordsDao:
    """
    会议纪要模块数据库操作层
    """

    @classmethod
    async def get_meeting_records_detail_by_id(cls, db: AsyncSession, records_id: int) -> OaMeetingRecords | None:
        """
        根据会议纪要 ID 获取详细信息
        """
        records_info = (
            (await db.execute(select(OaMeetingRecords).where(OaMeetingRecords.id == records_id)))
            .scalars()
            .first()
        )
        return records_info

    @classmethod
    async def get_meeting_records_list(
            cls, db: AsyncSession, query_object: MeetingRecordsPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict]:
        """
        根据查询参数获取会议纪要列表信息
        """
        from sqlalchemy.orm import aliased
        from module_admin.entity.do.user_do import SysUser
        from module_admin.entity.do.dept_do import SysDept

        anchor_user = aliased(SysUser, name='anchor')
        recorder_user = aliased(SysUser, name='recorder')

        query = (
            select(OaMeetingRecords,
                   OaMeetingRoom.title.label('room_name'),
                   anchor_user.nick_name.label('anchor_name'),
                   recorder_user.nick_name.label('recorder_name'),
                   SysDept.dept_name.label('dept_name'))
            .join(OaMeetingRoom, OaMeetingRoom.id == OaMeetingRecords.room_id, isouter=True)
            .join(anchor_user, anchor_user.user_id == OaMeetingRecords.anchor_id, isouter=True)
            .join(recorder_user, recorder_user.user_id == OaMeetingRecords.recorder_id, isouter=True)
            .join(SysDept, SysDept.dept_id == OaMeetingRecords.did, isouter=True)
            .where(OaMeetingRecords.delete_time == 0)
        )

        if query_object.anchor_id:
            query = query.where(OaMeetingRecords.anchor_id == query_object.anchor_id)

        if query_object.keywords:
            query = query.where(OaMeetingRecords.title.like(f'%{query_object.keywords}%'))

        if query_object.diff_time:
            try:
                time_range = query_object.diff_time.split('~')
                if len(time_range) == 2:
                    begin_timestamp = int(datetime.fromisoformat(time_range[0]).timestamp())
                    end_timestamp = int(datetime.fromisoformat(time_range[1] + ' 23:59:59').timestamp())
                    query = query.where(
                        and_(
                            OaMeetingRecords.meeting_date >= begin_timestamp,
                            OaMeetingRecords.meeting_date <= end_timestamp,
                            )
                    )
            except ValueError:
                pass

        query = query.order_by(OaMeetingRecords.id.desc())

        records_list: PageModel | list[dict] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return records_list

    @classmethod
    async def add_meeting_records_dao(cls, db: AsyncSession, records: dict) -> OaMeetingRecords:
        """
        新增会议纪要数据库操作
        """
        db_records_data = {k: v for k, v in records.items() if k not in ['order_title', 'anchor_name', 'recorder_name', 'room_name', 'dept_name']}
        db_records = OaMeetingRecords(**db_records_data)
        db.add(db_records)
        await db.flush()
        return db_records

    @classmethod
    async def edit_meeting_records_dao(cls, db: AsyncSession, records: dict) -> None:
        """
        编辑会议纪要数据库操作
        """
        db_records_data = {k: v for k, v in records.items() if k not in ['order_title', 'anchor_name', 'recorder_name', 'room_name', 'dept_name']}
        await db.execute(update(OaMeetingRecords), [db_records_data])

    @classmethod
    async def delete_meeting_records_dao(cls, db: AsyncSession, records_id: int) -> None:
        """
        删除会议纪要数据库操作（逻辑删除）
        """
        await db.execute(
            update(OaMeetingRecords)
            .where(OaMeetingRecords.id == records_id)
            .values(delete_time=int(datetime.now().timestamp()))
        )

    @classmethod
    async def check_duplicate_records(
            cls, db: AsyncSession, room_id: int, meeting_date: int, records_id: int = None
    ) -> int:
        """
        检查是否存在重复的会议纪要（同一会议室、同一会议时间）
        """
        query = select(OaMeetingRecords).where(
            OaMeetingRecords.room_id == room_id,
            OaMeetingRecords.meeting_date == meeting_date,
            OaMeetingRecords.delete_time == 0
        )
        
        if records_id:
            query = query.where(OaMeetingRecords.id != records_id)
        
        result = await db.execute(query)
        return len(result.fetchall())
