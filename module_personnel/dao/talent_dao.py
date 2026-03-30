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
        if query_object.admin_id:
            query = (select(OaTalent)
                     .where(
                        OaTalent.check_status == query_object.check_status if query_object.check_status else True,
                        OaTalent.check_time.between(
                            int(datetime.strptime(query_object.begin_time, "%Y-%m-%d %H:%M:%S").timestamp()),
                            int(datetime.strptime(query_object.end_time, "%Y-%m-%d %H:%M:%S").timestamp()),
                        ) if query_object.begin_time and query_object.end_time else True,
                        OaTalent.admin_id == query_object.admin_id,
                data_scope_sql,
            ).order_by(desc(OaTalent.create_time)))

        elif query_object.check_uids:
            query = (select(OaTalent)
                     .where(
                        OaTalent.check_status == query_object.check_status if query_object.check_status else True,
                        OaTalent.check_time.between(
                            int(datetime.strptime(query_object.begin_time, "%Y-%m-%d %H:%M:%S").timestamp()),
                            int(datetime.strptime(query_object.end_time, "%Y-%m-%d %H:%M:%S").timestamp()),
                        ) if query_object.begin_time and query_object.end_time else True,
                    func.find_in_set(query_object.check_uids, OaTalent.check_uids) > 0,
                    data_scope_sql,
            ).order_by(desc(OaTalent.create_time)))
        elif query_object.check_history_uids:
            query = (select(OaTalent)
            .where(
                OaTalent.check_status == query_object.check_status if query_object.check_status else True,
                OaTalent.check_time.between(
                    int(datetime.strptime(query_object.begin_time, "%Y-%m-%d %H:%M:%S").timestamp()),
                    int(datetime.strptime(query_object.end_time, "%Y-%m-%d %H:%M:%S").timestamp()),
                ) if query_object.begin_time and query_object.end_time else True,
                func.find_in_set(query_object.check_history_uids, OaTalent.check_history_uids) > 0,
                data_scope_sql,
            ).order_by(desc(OaTalent.create_time)))
        elif query_object.check_copy_uids:
             query = (select(OaTalent)
                     .where(
                OaTalent.check_status == query_object.check_status if query_object.check_status else True,
                OaTalent.check_time.between(
                    int(datetime.strptime(query_object.begin_time, "%Y-%m-%d %H:%M:%S").timestamp()),
                    int(datetime.strptime(query_object.end_time, "%Y-%m-%d %H:%M:%S").timestamp()),
                ) if query_object.begin_time and query_object.end_time else True,
                func.find_in_set(query_object.check_copy_uids, OaTalent.check_copy_uids) > 0,
                data_scope_sql,
            ).order_by(desc(OaTalent.create_time)))
        else:
            query = (select(OaTalent)
                     .where(
                        and_(
                            OaTalent.check_status == query_object.check_status if query_object.check_status else True,
                            OaTalent.check_time.between(
                                int(datetime.strptime(query_object.begin_time, "%Y-%m-%d %H:%M:%S").timestamp()),
                                int(datetime.strptime(query_object.end_time, "%Y-%m-%d %H:%M:%S").timestamp()),
                            ) if query_object.begin_time and query_object.end_time else True,
                            or_(
                                query_object.admin_id == OaTalent.admin_id,
                                func.find_in_set(query_object.check_uids, OaTalent.check_uids) > 0,
                                func.find_in_set(query_object.check_copy_uids, OaTalent.check_copy_uids) > 0,
                                func.find_in_set(query_object.check_history_uids, OaTalent.check_history_uids) > 0
                            ),
                        ),
                        data_scope_sql,
            ).order_by(desc(OaTalent.create_time)))
        page_list: PageModel | list[list[dict[str, Any]]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return page_list

    @classmethod
    async def add(cls, db: AsyncSession, model: OaTalentBaseModel):
        db_model = OaTalent(**model.model_dump(exclude={"id", "create_time"}, exclude_none=True),
                                 create_time=model.create_time)
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
                **model.model_dump(exclude={"id", "create_time"}, exclude_none=True, update_time=model.update_time)
            )
            .where(OaTalent.id == model.id)
        )
        await db.commit()
        return result.rowcount

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
    async def cancel_change(cls, db: AsyncSession, query_model: OaTalentBaseModel):
        result = await db.execute(update(OaTalent).values(
            update_time=int(datetime.now().timestamp()),
            check_status=query_model.check_status,
            remark=query_model.remark,
        ).where(OaTalent.id == query_model.id))
        await db.commit()
        return result.rowcount

    @classmethod
    async def count_by_uid(cls, db: AsyncSession, uid: str):
        result = await db.execute(select(func.count()).where(OaTalent.uid == uid))
        return result.scalar()
    @classmethod
    async def pass_change(cls, db: AsyncSession, data: OaTalentBaseModel):
        try:
            result = await db.execute(
                update(OaTalent)
                .values(
                    check_status=2,
                    check_time=data.check_time,
                    remark=data.remark,
                )
                .where(OaTalent.id == data.id)
            )
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise e
        return result.rowcount

    @classmethod
    async def reject_change(cls, db: AsyncSession, data: OaTalentBaseModel):
        try:
            result = await db.execute(
                update(OaTalent)
                .values(
                    check_status=3,
                    check_time=data.check_time,
                    remark=data.remark,
                )
                .where(OaTalent.id == data.id)
            )
            await db.commit()
            return result.rowcount
        except Exception as e:
            await db.rollback()
            raise e
