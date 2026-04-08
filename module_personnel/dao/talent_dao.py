from operator import and_

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from sqlalchemy.sql import ColumnElement, func,or_
from common.vo import PageModel
from utils.page_util import PageUtil
from module_personnel.entity.vo.talent_vo import OaTalentBaseModel, OaTalentPageQueryModel
from module_personnel.entity.do.talent_do import OaTalent
from typing import Any
from datetime import datetime

class TalentDao:
    @classmethod
    async def get_page_list(cls, db: AsyncSession, query_object: OaTalentPageQueryModel,
                            data_scope_sql: ColumnElement,
                            is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:
        # 构建基础查询
        query = select(OaTalent)

        # 构建条件列表
        conditions = []

        # 通用条件：审核状态
        if query_object.check_status is not None:
            conditions.append(OaTalent.check_status == query_object.check_status)

        # 通用条件：审核时间范围
        if query_object.begin_time and query_object.end_time:
            start_timestamp = int(datetime.strptime(query_object.begin_time, "%Y-%m-%d %H:%M:%S").timestamp())
            end_timestamp = int(datetime.strptime(query_object.end_time, "%Y-%m-%d %H:%M:%S").timestamp())
            conditions.append(OaTalent.check_time.between(start_timestamp, end_timestamp))

        # 根据不同的查询条件添加特定条件
        if query_object.admin_id:
            conditions.append(OaTalent.admin_id == query_object.admin_id)

        elif query_object.check_uids:
            conditions.append(func.find_in_set(query_object.check_uids, OaTalent.check_uids) > 0)

        elif query_object.check_history_uids:
            conditions.append(
                func.find_in_set(query_object.check_history_uids, OaTalent.check_history_uids) > 0)

        elif query_object.check_copy_uids:
            conditions.append(func.find_in_set(query_object.check_copy_uids, OaTalent.check_copy_uids) > 0)

        else:
            # 没有特定条件时，使用 OR 组合
            or_conditions = []
            if query_object.admin_id:
                or_conditions.append(OaTalent.admin_id == query_object.admin_id)
            if query_object.check_uids:
                or_conditions.append(func.find_in_set(query_object.check_uids, OaTalent.check_uids) > 0)
            if query_object.check_copy_uids:
                or_conditions.append(
                    func.find_in_set(query_object.check_copy_uids, OaTalent.check_copy_uids) > 0)
            if query_object.check_history_uids:
                or_conditions.append(
                    func.find_in_set(query_object.check_history_uids, OaTalent.check_history_uids) > 0)

            if or_conditions:
                conditions.append(or_(*or_conditions))

        # 添加数据权限条件
        if data_scope_sql is not None:
            conditions.append(data_scope_sql)

        # 应用所有条件
        if conditions:
            query = query.where(*conditions)

        # 排序
        query = query.order_by(desc(OaTalent.create_time))

        # 分页查询
        page_list: PageModel | list[list[dict[str, Any]]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return page_list

    @classmethod
    async def add(cls, db: AsyncSession, model: OaTalentBaseModel):
        db_model = OaTalent(**model.model_dump(exclude={"id", "create_time", 'entry_time'}, exclude_none=True),
                                 create_time=model.create_time,
                                 entry_time = model.entry_time,
                                )
        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)
        return db_model
        pass

    @classmethod
    async def update(cls, db: AsyncSession, model: OaTalentBaseModel):
        result = await db.execute(
            update(OaTalent)
            .values(
                **model.model_dump(exclude={"id", "update_time", 'entry_time'}, exclude_none=True)
                , update_time=model.update_time
                , entry_time = model.entry_time
            )
            .where(OaTalent.id == model.id)
        )
        await db.commit()
        return await cls.get_info_by_id(db, model.id)

    @classmethod
    async def get_info_by_id(cls, db: AsyncSession, id: int):
        query = (select(OaTalent)
        .where(
            OaTalent.id == id))
        link_info = await db.scalar(query)
        return link_info

    @classmethod
    async def get_info_by_uid(cls, db: AsyncSession, model: OaTalentBaseModel) -> OaTalent | None:
        """
        根据标题获取信息

        :param model:
        :param db: orm对象
        :return:
        """
        query_info = (
            (
                await db.execute(
                    select(OaTalent)
                    .where(
                        OaTalent.uid == model.uid if model.uid else True
                        and OaTalent.check_status != 2 if model.check_status else True
                    )
                    .order_by(desc(OaTalent.create_time))
                    .distinct()
                )
            )
            .scalars()
            .first()
        )

        return query_info
    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        result = await db.execute(update(OaTalent).values(delete_time=int(datetime.now().timestamp())).where(OaTalent.id == id))
        await db.commit()
        return result.rowcount

    @classmethod
    async def count_by_uid(cls, db: AsyncSession, uid: str):
        result = await db.execute(select(func.count()).where(OaTalent.uid == uid))
        return result.scalar()
    @classmethod
    async def review(cls, db: AsyncSession, data: OaTalentBaseModel):
        try:
            result = await db.execute(
                update(OaTalent)
                .values(
                    check_status=data.check_status,
                    check_time=data.check_time
                )
                .where(OaTalent.id == data.id)
            )
            await db.commit()
            info =  await cls.get_info_by_id(db, data.id)
            return info
        except Exception as e:
            await db.rollback()
            raise e
        return result.rowcount

