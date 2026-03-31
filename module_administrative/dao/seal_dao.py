from operator import and_

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from sqlalchemy.sql import ColumnElement, func,or_
from common.vo import PageModel
from utils.page_util import PageUtil
from module_administrative.entity.vo.seal_vo import OaSealBaseModel, OaSealPageQueryModel
from module_administrative.entity.do.seal_do import OaSeal
from typing import Any
from datetime import datetime

class SealDao:
    @classmethod
    async def get_page_list(cls, db: AsyncSession, query_object: OaSealPageQueryModel,
                            data_scope_sql: ColumnElement,
                            is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:

        # 构建基础查询
        query = select(OaSeal)

        # 构建条件列表
        conditions = []
        conditions.append(OaSeal.delete_time == 0)
        # 通用条件：审核状态
        if query_object.check_status is not None:
            conditions.append(OaSeal.check_status == query_object.check_status)

        # 通用条件：审核时间范围
        # if query_object.begin_time and query_object.end_time:
        #     start_timestamp = int(datetime.strptime(query_object.begin_time, "%Y-%m-%d %H:%M:%S").timestamp())
        #     end_timestamp = int(datetime.strptime(query_object.end_time, "%Y-%m-%d %H:%M:%S").timestamp())
        #     conditions.append(OaSeal.check_time.between(start_timestamp, end_timestamp))

        # 根据不同的查询条件添加特定条件
        if query_object.admin_id:
            conditions.append(OaSeal.admin_id == query_object.admin_id)

        elif query_object.check_uids:
            conditions.append(func.find_in_set(query_object.check_uids, OaSeal.check_uids) > 0)

        elif query_object.check_history_uids:
            conditions.append(
                func.find_in_set(query_object.check_history_uids, OaSeal.check_history_uids) > 0)

        elif query_object.check_copy_uids:
            conditions.append(func.find_in_set(query_object.check_copy_uids, OaSeal.check_copy_uids) > 0)

        else:
            # 没有特定条件时，使用 OR 组合
            or_conditions = []
            if query_object.admin_id:
                or_conditions.append(OaSeal.admin_id == query_object.admin_id)
            if query_object.check_uids:
                or_conditions.append(func.find_in_set(query_object.check_uids, OaSeal.check_uids) > 0)
            if query_object.check_copy_uids:
                or_conditions.append(
                    func.find_in_set(query_object.check_copy_uids, OaSeal.check_copy_uids) > 0)
            if query_object.check_history_uids:
                or_conditions.append(
                    func.find_in_set(query_object.check_history_uids, OaSeal.check_history_uids) > 0)

            if or_conditions:
                conditions.append(or_(*or_conditions))

        # 添加数据权限条件
        if data_scope_sql is not None:
            conditions.append(data_scope_sql)

        # 应用所有条件
        if conditions:
            query = query.where(*conditions)

        # 排序
        query = query.order_by(desc(OaSeal.create_time))

        # 分页查询
        page_list: PageModel | list[list[dict[str, Any]]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return page_list

    @classmethod
    async def add(cls, db: AsyncSession, model: OaSealBaseModel):
        db_model = OaSeal(**model.model_dump(exclude={"id", "create_time", "use_time", "start_time", "end_time","check_time"}, exclude_none=True),
                                 create_time=model.create_time)
        db_model.use_time = model.use_time
        db_model.start_time = model.start_time
        db_model.end_time = model.end_time
        db_model.check_time = model.check_time
        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)
        return db_model
        pass

    @classmethod
    async def update(cls, db: AsyncSession, model: OaSealBaseModel):
        result = await db.execute(
            update(OaSeal)
            .values(
                **model.model_dump(exclude={"id", "update_time"}, exclude_none=True), update_time=model.update_time
            )
            .where(OaSeal.id == model.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def get_info_by_id(cls, db: AsyncSession, id: int):
        query = (select(OaSeal)
        .where(
            OaSeal.id == id))
        link_info = await db.scalar(query)
        return link_info
    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        result = await db.execute(update(OaSeal).values(delete_time=int(datetime.now().timestamp())).where(OaSeal.id == id))
        await db.commit()
        return result.rowcount

    @classmethod
    async def cancel_change(cls, db: AsyncSession, query_model: OaSealBaseModel):
        result = await db.execute(update(OaSeal).values(
            update_time=int(datetime.now().timestamp()),
            check_status=query_model.check_status,
            content=query_model.content,
        ).where(OaSeal.id == query_model.id))
        await db.commit()
        return result.rowcount

    @classmethod
    async def count_by_uid(cls, db: AsyncSession, uid: str):
        result = await db.execute(select(func.count()).where(OaSeal.uid == uid))
        return result.scalar()
    @classmethod
    async def pass_change(cls, db: AsyncSession, data: OaSealBaseModel):
        try:
            result = await db.execute(
                update(OaSeal)
                .values(
                    check_status=2,
                    check_time=data.check_time,
                    content=data.content,
                )
                .where(OaSeal.id == data.id)
            )
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise e
        return result.rowcount

    @classmethod
    async def reject_change(cls, db: AsyncSession, data: OaSealBaseModel):
        try:
            result = await db.execute(
                update(OaSeal)
                .values(
                    check_status=3,
                    check_time=data.check_time,
                    content=data.content,
                )
                .where(OaSeal.id == data.id)
            )
            await db.commit()
            return result.rowcount
        except Exception as e:
            await db.rollback()
            raise e
