from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.sql import ColumnElement
from typing import Any
from datetime import datetime
from common.vo import PageModel
from module_admin.entity.do.basic_adm_do import OaBasicAdm
from module_admin.entity.vo.basic_adm_vo import BasicAdmPageQueryModel, OaBasicAdmModel
from utils.page_util import PageUtil


class BasicAdmDao:
    @classmethod
    async def get_basic_adm_list(cls, db: AsyncSession, query_object: BasicAdmPageQueryModel, data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:
        query = (select(OaBasicAdm)
                 .where(
            OaBasicAdm.status != -1,
            OaBasicAdm.types == query_object.types if query_object.types else True,
            OaBasicAdm.title.like(f'%{query_object.title}%') if query_object.title else True,
            OaBasicAdm.status == query_object.status if query_object.status is not None else True,
            data_scope_sql,
            ).order_by(OaBasicAdm.id.asc()))
        basic_adm_list: PageModel | list[list[dict[str, Any]]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return basic_adm_list

    @classmethod
    async def add_basic_adm(cls, db: AsyncSession, model: OaBasicAdmModel):
        db_basic_adm = OaBasicAdm(**model.model_dump(exclude={"id"}, exclude_none=True))
        db.add(db_basic_adm)
        await db.commit()
        await db.refresh(db_basic_adm)
        return db_basic_adm

    @classmethod
    async def update_basic_adm(cls, db: AsyncSession, model: OaBasicAdmModel):
        result = await db.execute(
            update(OaBasicAdm)
            .values(**model.model_dump(exclude={"id", "create_time"}, exclude_none=True))
            .where(OaBasicAdm.id == model.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def delete_basic_adm(cls, db: AsyncSession, id: int):
        current_time = int(datetime.now().timestamp())
        result = await db.execute(
            update(OaBasicAdm)
            .values(status=-1, update_time=current_time)
            .where(OaBasicAdm.id == id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def get_basic_adm_info(cls, db: AsyncSession, id: int):
        result = await db.execute(select(OaBasicAdm).where(OaBasicAdm.id == id))
        return result.scalars().first()

    @classmethod
    async def change_status_basic_adm(cls, db: AsyncSession, model: OaBasicAdmModel):
        result = await db.execute(update(OaBasicAdm).values(status=model.status).where(OaBasicAdm.id == model.id))
        await db.commit()
        return result.rowcount

