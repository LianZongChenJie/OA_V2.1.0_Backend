from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, asc, or_, and_
from sqlalchemy.sql import ColumnElement, func
from common.vo import PageModel
from module_admin.entity.do.oa_admin_do import OaAdmin
from utils.page_util import PageUtil
from module_dashboard.entity.vo.work_vo import OaWorkBaseModel, OaWorkPageQueryModel
from module_dashboard.entity.do.work_do import OaWork
from module_dashboard.entity.do.work_record_do import OaWorkRecord
from typing import Any
from datetime import datetime


class WorkDao:
    @classmethod
    async def get_send_list(cls, db: AsyncSession, query_object: OaWorkPageQueryModel,
                            data_scope_sql: ColumnElement,
                            is_page: bool = False) -> PageModel | list[dict[str, Any]]:
        """
        获取我发出的汇报列表
        """
        query = select(OaWork, OaAdmin.name.label('person_name')).join(
            OaAdmin, OaAdmin.id == OaWork.admin_id, isouter=True
        )

        conditions = []
        conditions.append(OaWork.delete_time == 0)
        conditions.append(OaWork.admin_id == query_object.admin_id)

        if query_object.types:
            conditions.append(OaWork.types == query_object.types)

        if query_object.keywords:
            conditions.append(OaWork.works.like(f'%{query_object.keywords}%'))

        if query_object.diff_time:
            try:
                time_range = query_object.diff_time.split('~')
                if len(time_range) == 2:
                    start_timestamp = int(datetime.fromisoformat(time_range[0]).timestamp())
                    end_timestamp = int(datetime.fromisoformat(time_range[1] + ' 23:59:59').timestamp())
                    conditions.append(OaWork.start_date.between(start_timestamp, end_timestamp))
            except ValueError:
                pass

        if data_scope_sql is not None:
            conditions.append(data_scope_sql)

        if conditions:
            query = query.where(*conditions)

        query = query.order_by(asc(OaWork.start_date))

        page_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return page_list

    @classmethod
    async def get_accept_list(cls, db: AsyncSession, query_object: OaWorkPageQueryModel,
                              data_scope_sql: ColumnElement,
                              is_page: bool = False) -> PageModel | list[dict[str, Any]]:
        """
        获取我接收的汇报列表
        """
        query = (
            select(OaWorkRecord, OaWork, 
                   OaAdmin.name.label('from_name'),
                   OaAdmin2.name.label('to_name'))
            .join(OaWork, OaWorkRecord.work_id == OaWork.id, isouter=True)
            .join(OaAdmin, OaAdmin.id == OaWorkRecord.from_uid, isouter=True)
            .join(OaAdmin2, OaAdmin2.id == OaWorkRecord.to_uid, isouter=True)
        )

        conditions = []
        conditions.append(OaWorkRecord.delete_time == 0)
        conditions.append(OaWorkRecord.to_uid == query_object.admin_id)

        if query_object.read == 1:
            conditions.append(OaWorkRecord.read_time == 0)
        elif query_object.read == 2:
            conditions.append(OaWorkRecord.read_time > 0)

        if query_object.types:
            conditions.append(OaWork.types == query_object.types)

        if query_object.keywords:
            conditions.append(OaWork.works.like(f'%{query_object.keywords}%'))

        if query_object.diff_time:
            try:
                time_range = query_object.diff_time.split('~')
                if len(time_range) == 2:
                    start_timestamp = int(datetime.fromisoformat(time_range[0]).timestamp())
                    end_timestamp = int(datetime.fromisoformat(time_range[1] + ' 23:59:59').timestamp())
                    conditions.append(OaWorkRecord.send_time.between(start_timestamp, end_timestamp))
            except ValueError:
                pass

        if conditions:
            query = query.where(*conditions)

        query = query.order_by(asc(OaWorkRecord.send_time))

        page_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return page_list

    @classmethod
    async def add(cls, db: AsyncSession, model: OaWorkBaseModel):
        db_model = OaWork(**model.model_dump(exclude={"id", "create_time","start_date", "end_date", "send_time", "update_time"}, exclude_none=True),
                                 create_time=model.create_time, start_date=model.start_date, end_date=model.end_date, send_time=model.send_time, update_time=model.update_time)
        db.add(db_model)
        await db.flush()
        return db_model

    @classmethod
    async def update(cls, db: AsyncSession, model: OaWorkBaseModel):
        result = await db.execute(
            update(OaWork)
            .values(
                **model.model_dump(exclude={"id", "update_time", "start_date", "end_date", "send_time"}, exclude_none=True),
                update_time=model.update_time, start_date=model.start_date, end_date=model.end_date, send_time=model.send_time
            )
            .where(OaWork.id == model.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def get_info_by_id(cls, db: AsyncSession, id: int):
        query = (select(OaWork, OaAdmin.name.label('person_name'))
        .join(OaAdmin, OaAdmin.id == OaWork.admin_id, isouter=True)
        .where(
            OaWork.id == id))
        result = await db.execute(query)
        info = result.first()
        return info

    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        current_time = int(datetime.now().timestamp())
        result = await db.execute(update(OaWork).values(delete_time=current_time).where(OaWork.id == id))
        await db.execute(update(OaWorkRecord).values(delete_time=current_time).where(OaWorkRecord.work_id == id))
        await db.commit()
        return result.rowcount

    @classmethod
    async def add_work_records(cls, db: AsyncSession, records: list[dict]):
        """
        批量添加工作汇报发送记录
        """
        if records:
            db_records = [OaWorkRecord(**record) for record in records]
            db.add_all(db_records)
            await db.flush()

    @classmethod
    async def update_send_time(cls, db: AsyncSession, work_id: int, send_time: int):
        """
        更新汇报发送时间
        """
        await db.execute(
            update(OaWork)
            .values(send_time=send_time)
            .where(OaWork.id == work_id)
        )

    @classmethod
    async def check_work_record(cls, db: AsyncSession, work_id: int, to_uid: int):
        """
        检查工作汇报记录是否存在
        """
        query = select(OaWorkRecord).where(
            OaWorkRecord.work_id == work_id,
            OaWorkRecord.to_uid == to_uid,
            OaWorkRecord.delete_time == 0
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def update_read_time(cls, db: AsyncSession, work_id: int, to_uid: int, read_time: int):
        """
        更新阅读时间
        """
        await db.execute(
            update(OaWorkRecord)
            .values(read_time=read_time)
            .where(
                OaWorkRecord.work_id == work_id,
                OaWorkRecord.to_uid == to_uid
            )
        )

    @classmethod
    async def get_read_user_ids(cls, db: AsyncSession, work_id: int):
        """
        获取已读用户ID列表
        """
        query = select(OaWorkRecord.to_uid).where(
            OaWorkRecord.work_id == work_id,
            OaWorkRecord.read_time > 0,
            OaWorkRecord.delete_time == 0
        )
        result = await db.execute(query)
        return result.scalars().all()
