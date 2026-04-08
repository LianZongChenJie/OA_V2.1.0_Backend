from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from sqlalchemy.sql import ColumnElement, func,or_
from common.vo import PageModel
from utils.page_util import PageUtil
from module_personnel.entity.vo.personnel_quit_vo import OaPersonalQuitBaseModel, OaPersonnelQuitPageQueryModel
from module_personnel.entity.do.personnel_quit_do import OaPersonalQuit
from typing import Any
from datetime import datetime

class PersonnelQuitDao:
    @classmethod
    async def get_page_list(cls, db: AsyncSession, query_object: OaPersonnelQuitPageQueryModel,
                            data_scope_sql: ColumnElement,
                            is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:
        # 构建基础查询
        query = select(OaPersonalQuit)

        # 构建条件列表
        conditions = []

        # 通用条件：审核状态
        if query_object.check_status is not None:
            conditions.append(OaPersonalQuit.check_status == query_object.check_status)

        # 通用条件：审核时间范围
        if query_object.begin_time and query_object.end_time:
            start_timestamp = int(datetime.strptime(query_object.begin_time, "%Y-%m-%d %H:%M:%S").timestamp())
            end_timestamp = int(datetime.strptime(query_object.end_time, "%Y-%m-%d %H:%M:%S").timestamp())
            conditions.append(OaPersonalQuit.check_time.between(start_timestamp, end_timestamp))

        # 根据不同的查询条件添加特定条件
        if query_object.admin_id:
            conditions.append(OaPersonalQuit.admin_id == query_object.admin_id)

        elif query_object.check_uids:
            conditions.append(func.find_in_set(query_object.check_uids, OaPersonalQuit.check_uids) > 0)

        elif query_object.check_history_uids:
            conditions.append(
                func.find_in_set(query_object.check_history_uids, OaPersonalQuit.check_history_uids) > 0)

        elif query_object.check_copy_uids:
            conditions.append(func.find_in_set(query_object.check_copy_uids, OaPersonalQuit.check_copy_uids) > 0)

        else:
            # 没有特定条件时，使用 OR 组合
            or_conditions = []
            if query_object.admin_id:
                or_conditions.append(OaPersonalQuit.admin_id == query_object.admin_id)
            if query_object.check_uids:
                or_conditions.append(func.find_in_set(query_object.check_uids, OaPersonalQuit.check_uids) > 0)
            if query_object.check_copy_uids:
                or_conditions.append(
                    func.find_in_set(query_object.check_copy_uids, OaPersonalQuit.check_copy_uids) > 0)
            if query_object.check_history_uids:
                or_conditions.append(
                    func.find_in_set(query_object.check_history_uids, OaPersonalQuit.check_history_uids) > 0)

            if or_conditions:
                conditions.append(or_(*or_conditions))

        # 添加数据权限条件
        if data_scope_sql is not None:
            conditions.append(data_scope_sql)

        # 应用所有条件
        if conditions:
            query = query.where(*conditions)

        # 排序
        query = query.order_by(desc(OaPersonalQuit.create_time))

        # 分页查询
        page_list: PageModel | list[list[dict[str, Any]]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return page_list

    @classmethod
    async def add(cls, db: AsyncSession, model: OaPersonalQuitBaseModel):
        db_model = OaPersonalQuit(**model.model_dump(exclude={"id", "create_time"}, exclude_none=True),
                                 create_time=model.create_time)
        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)
        return db_model
        pass

    @classmethod
    async def update(cls, db: AsyncSession, model: OaPersonalQuitBaseModel):
        result = await db.execute(
            update(OaPersonalQuit)
            .values(
                **model.model_dump(exclude={"id", "update_time"}, exclude_none=True),update_time=model.update_time
            )
            .where(OaPersonalQuit.id == model.id)
        )
        await db.commit()
        return await cls.get_info_by_id(db, model.id)

    @classmethod
    async def get_info_by_id(cls, db: AsyncSession, id: int):
        query = (select(OaPersonalQuit)
        .where(
            OaPersonalQuit.id == id))
        link_info = await db.scalar(query)
        return link_info

    @classmethod
    async def get_info_by_uid(cls, db: AsyncSession, model: OaPersonalQuitBaseModel) -> OaPersonalQuit | None:
        """
        根据标题获取信息

        :param model:
        :param db: orm对象
        :return:
        """
        query_info = (
            (
                await db.execute(
                    select(OaPersonalQuit)
                    .where(
                        OaPersonalQuit.uid == model.uid if model.uid else True
                        and OaPersonalQuit.check_status != 2 if model.check_status else True
                    )
                    .order_by(desc(OaPersonalQuit.create_time))
                    .distinct()
                )
            )
            .scalars()
            .first()
        )

        return query_info
    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        result = await db.execute(update(OaPersonalQuit).values(delete_time=int(datetime.now().timestamp())).where(OaPersonalQuit.id == id))
        await db.commit()
        return result.rowcount

    @classmethod
    async def count_by_uid(cls, db: AsyncSession, uid: str):
        result = await db.execute(select(func.count()).where(OaPersonalQuit.uid == uid))
        return result.scalar()
    @classmethod
    async def review(cls, db: AsyncSession, data: OaPersonalQuitBaseModel):
        try:
            await db.execute(
                update(OaPersonalQuit)
                .values(
                    check_status=data.check_status,
                    check_time=data.check_time
                )
                .where(OaPersonalQuit.id == data.id)
            )
            await db.commit()
            return await cls.get_info_by_id(db, data.id)
        except Exception as e:
            await db.rollback()
            raise e