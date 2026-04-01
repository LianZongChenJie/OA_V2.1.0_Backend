from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update,asc,or_
from sqlalchemy.sql import ColumnElement, func
from common.vo import PageModel
from module_admin.entity.do.user_do import SysUser
from utils.page_util import PageUtil
from module_dashboard.entity.vo.work_vo import OaWorkBaseModel, OaWorkPageQueryModel
from module_dashboard.entity.do.work_do import OaWork
from typing import Any
from datetime import datetime

class WorkDao:
    @classmethod
    async def get_page_list(cls, db: AsyncSession, query_object: OaWorkPageQueryModel,
                            data_scope_sql: ColumnElement,
                            is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:

        # 构建基础查询
        query = select(OaWork,SysUser).join(SysUser, OaWork.admin_id == SysUser.user_id, isouter=True)

        # 构建条件列表
        conditions = []
        conditions.append(OaWork.delete_time == 0)

        if query_object.begin_time and query_object.end_time:
            start_timestamp = int(datetime.strptime(query_object.begin_time, "%Y-%m-%d %H:%M:%S").timestamp())
            end_timestamp = int(datetime.strptime(query_object.end_time, "%Y-%m-%d %H:%M:%S").timestamp())
            conditions.append(OaWork.check_time.between(start_timestamp, end_timestamp))
        if query_object.types is not None:
            conditions.append(OaWork.type == query_object.types)
        if query_object.keywork is not None:
            conditions.append(or_(OaWork.title.like("%" + query_object.keywork + "%"),
                                  OaWork.remark.like("%" + query_object.keywork + "%"),
                                  OaWork.content.like("%" + query_object.keywork + "%")
                                  ))
        # 添加数据权限条件
        if data_scope_sql is not None:
            conditions.append(data_scope_sql)

        # 应用所有条件
        if conditions:
            query = query.where(*conditions)

        # 排序
        query = query.order_by(asc(OaWork.start_date))

        # 分页查询+
        page_list: PageModel | list[list[dict[str, Any]]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return page_list

    @classmethod
    async def add(cls, db: AsyncSession, model: OaWorkBaseModel):
        db_model = OaWork(**model.model_dump(exclude={"id", "create_time","start_date", "end_date", "send_time"}, exclude_none=True),
                                 create_time=model.create_time, start_date=model.start_date, end_date=model.end_date, send_time=model.send_time)
        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)
        return db_model
        pass

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
        query = (select(OaWork)
        .where(
            OaWork.id == id))
        info = await db.scalar(query)
        return info
    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        result = await db.execute(update(OaWork).values(delete_time=int(datetime.now().timestamp())).where(OaWork.id == id))
        await db.commit()
        return result.rowcount
