from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc, or_, and_
from sqlalchemy.sql import ColumnElement, func
from common.vo import PageModel
from utils.page_util import PageUtil
from module_dashboard.entity.vo.plan_vo import OaPlanQueryModel, OaPlanBaseModel
from module_dashboard.entity.do.plan_do import OaPlan
from typing import Any
from datetime import datetime


class PlanDao:
    @classmethod
    async def get_page_list(cls, db: AsyncSession, query_object: OaPlanQueryModel,
                            data_scope_sql: ColumnElement,
                            is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:

        from module_admin.entity.do.oa_admin_do import OaAdmin

        query = select(OaPlan, OaAdmin.name.label('create_admin')).join(
            OaAdmin, OaAdmin.id == OaPlan.admin_id, isouter=True
        )

        conditions = []
        conditions.append(OaPlan.delete_time == 0)

        if query_object.keywords:
            conditions.append(OaPlan.title.like(f'%{query_object.keywords}%'))

        if query_object.uid:
            conditions.append(OaPlan.admin_id == query_object.uid)

        if query_object.type:
            conditions.append(OaPlan.type == query_object.type)

        if query_object.begin_time and query_object.end_time:
            start_timestamp = int(datetime.strptime(query_object.begin_time, "%Y-%m-%d").timestamp())
            end_timestamp = int(datetime.strptime(query_object.end_time + ' 23:59:59', "%Y-%m-%d %H:%M:%S").timestamp())
            conditions.append(OaPlan.start_time.between(start_timestamp, end_timestamp))

        if data_scope_sql is not None:
            conditions.append(data_scope_sql)

        if conditions:
            query = query.where(*conditions)

        query = query.order_by(desc(OaPlan.id))

        page_list: PageModel | list[list[dict[str, Any]]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return page_list

    @classmethod
    async def get_calendar_list(cls, db: AsyncSession, query_object: OaPlanQueryModel,
                                data_scope_sql: ColumnElement,
                                is_page: bool = False) -> list[dict[str, Any]]:

        from module_admin.entity.do.oa_admin_do import OaAdmin

        conditions = []
        conditions.append(OaPlan.delete_time == 0)

        if query_object.uid:
            conditions.append(OaPlan.admin_id == query_object.uid)

        if query_object.begin_time and query_object.end_time:
            start_timestamp = int(datetime.strptime(query_object.begin_time, "%Y-%m-%d").timestamp())
            end_timestamp = int(datetime.strptime(query_object.end_time + ' 23:59:59', "%Y-%m-%d %H:%M:%S").timestamp())
            conditions.append(and_(
                OaPlan.start_time <= end_timestamp,
                OaPlan.end_time >= start_timestamp
            ))

        if data_scope_sql is not None:
            conditions.append(data_scope_sql)

        query = select(OaPlan).where(*conditions)

        result = await db.execute(query)
        plans = result.scalars().all()

        bg_array = ['#ECECEC', '#FFD3D3', '#F6F6C7', '#D7EBFF', '#CCEBCC', '#E9E9CB']
        border_array = ['#CCCCCC', '#FF9999', '#E8E89B', '#99CCFF', '#99CC99', '#CCCC99']

        calendar_list = []
        for plan in plans:
            type_index = int(plan.type) if plan.type else 0
            if type_index < 0 or type_index >= len(bg_array):
                type_index = 0

            calendar_item = {
                'id': plan.id,
                'title': plan.title,
                'type': plan.type,
                'backgroundColor': bg_array[type_index],
                'borderColor': border_array[type_index],
                'start': datetime.fromtimestamp(plan.start_time).strftime('%Y-%m-%d %H:%M') if plan.start_time else '',
                'end': datetime.fromtimestamp(plan.end_time).strftime('%Y-%m-%d %H:%M') if plan.end_time else '',
                'remindType': plan.remind_type,
            }
            calendar_list.append(calendar_item)

        return calendar_list

    @classmethod
    async def add(cls, db: AsyncSession, model: OaPlanBaseModel):
        db_model = OaPlan(**model.model_dump(exclude={"id", "create_time"}, exclude_none=True),
                                 create_time=model.create_time)
        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)
        return db_model

    @classmethod
    async def update(cls, db: AsyncSession, model: OaPlanBaseModel):
        result = await db.execute(
            update(OaPlan)
            .values(
                **model.model_dump(exclude={"id", "update_time"}, exclude_none=True),
                update_time=model.update_time
            )
            .where(OaPlan.id == model.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def get_info_by_id(cls, db: AsyncSession, id: int):
        from module_admin.entity.do.oa_admin_do import OaAdmin

        query = (select(OaPlan, OaAdmin.name.label('create_admin'))
        .join(OaAdmin, OaAdmin.id == OaPlan.admin_id, isouter=True)
        .where(
            OaPlan.id == id))
        result = await db.execute(query)
        info = result.first()
        return info

    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        result = await db.execute(update(OaPlan).values(delete_time=int(datetime.now().timestamp())).where(OaPlan.id == id))
        await db.commit()
        return result.rowcount
