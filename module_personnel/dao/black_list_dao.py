from operator import and_

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc, delete
from sqlalchemy.sql import ColumnElement, func,or_
from common.vo import PageModel
from module_admin.entity.do.user_do import SysUser
from utils.page_util import PageUtil
from module_personnel.entity.vo.black_list_vo import OaBlacklistBaseModel, OaBlacklistPageQueryModel
from module_personnel.entity.do.black_list_do import OaBlacklist
from typing import Any
from datetime import datetime

class BlackListDao:
    @classmethod
    async def get_page_list(cls, db: AsyncSession, query_object: OaBlacklistPageQueryModel,
                            data_scope_sql: ColumnElement,
                            is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:
        query = (select(OaBlacklist, SysUser.nick_name.label("admin_name"))
                 .join(SysUser, OaBlacklist.admin_id == SysUser.user_id, isouter=True)
                     .where(
                        and_(
                            OaBlacklist.delete_time == 0,
                            or_(
                                OaBlacklist.name.like("%" + query_object.keyword + "%") if query_object.keyword else True,
                                OaBlacklist.remark.like("%" + query_object.keyword + "%") if query_object.keyword else True
                            )
                        ),
                        data_scope_sql,
            ).order_by(desc(OaBlacklist.create_time)))
        page_list: PageModel | list[list[dict[str, Any]]] = await PageUtil.paginate_dict(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return page_list

    @classmethod
    async def add(cls, db: AsyncSession, model: OaBlacklistBaseModel):
        db_model = OaBlacklist(**model.model_dump(exclude={"id", "create_time"}, exclude_none=True),
                                 create_time=model.create_time)
        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)
        return db_model
        pass

    @classmethod
    async def update(cls, db: AsyncSession, model: OaBlacklistBaseModel):
        result = await db.execute(
            update(OaBlacklist)
            .values(
                **model.model_dump(exclude={"id", "update_time"}, exclude_none=True), update_time=model.update_time
            )
            .where(OaBlacklist.id == model.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def get_info_by_id(cls, db: AsyncSession, id: int):
        query = (select(OaBlacklist)
        .where(
            OaBlacklist.id == id))
        link_info = await db.scalar(query)
        return link_info

    @classmethod
    async def get_info_by_uid(cls, db: AsyncSession, model: OaBlacklistBaseModel) -> OaBlacklist | None:
        """
        根据标题获取信息

        :param model:
        :param db: orm对象
        :return:
        """
        query_info = (
            (
                await db.execute(
                    select(OaBlacklist)
                    .where(
                        OaBlacklist.uid == model.uid if model.uid else True
                        and OaBlacklist.check_status != 2 if model.check_status else True
                    )
                    .order_by(desc(OaBlacklist.create_time))
                    .distinct()
                )
            )
            .scalars()
            .first()
        )

        return query_info

    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        result = await db.execute(delete(OaBlacklist).where(OaBlacklist.id == id))
        await db.commit()
        return result.rowcount

