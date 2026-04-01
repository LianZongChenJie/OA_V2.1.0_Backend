from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
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

        # 构建基础查询
        query = select(OaPlan)

        # 构建条件列表
        conditions = []
        conditions.append(OaPlan.delete_time == 0)

        if query_object.begin_time and query_object.end_time:
            start_timestamp = int(datetime.strptime(query_object.begin_time, "%Y-%m-%d %H:%M:%S").timestamp())
            end_timestamp = int(datetime.strptime(query_object.end_time, "%Y-%m-%d %H:%M:%S").timestamp())
            conditions.append(OaPlan.check_time.between(start_timestamp, end_timestamp))

        # 添加数据权限条件
        if data_scope_sql is not None:
            conditions.append(data_scope_sql)

        # 应用所有条件
        if conditions:
            query = query.where(*conditions)

        # 排序
        query = query.order_by(desc(OaPlan.create_time))

        # 分页查询+
        page_list: PageModel | list[list[dict[str, Any]]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return page_list

    @classmethod
    async def add(cls, db: AsyncSession, model: OaPlanBaseModel):
        db_model = OaPlan(**model.model_dump(exclude={"id", "create_time"}, exclude_none=True),
                                 create_time=model.create_time)
        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)
        return db_model
        pass

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
        query = (select(OaPlan)
        .where(
            OaPlan.id == id))
        info = await db.scalar(query)
        return info
    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        result = await db.execute(update(OaPlan).values(delete_time=int(datetime.now().timestamp())).where(OaPlan.id == id))
        await db.commit()
        return result.rowcount
