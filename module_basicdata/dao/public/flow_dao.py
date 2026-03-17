from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from common.vo import PageModel
from module_basicdata.entity.do.public.flow_do import OaFlow
from module_basicdata.entity.vo.public.flow_vo import OaFlowPageQueryModel, OaFlowBaseModel
from typing import Any
from sqlalchemy import select, update

from utils.page_util import PageUtil


class OaFlowDao:
    @classmethod
    async def get_flow_list(cls, db: AsyncSession, query_object: OaFlowPageQueryModel, data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:
        query = (select(OaFlow)
                 .where(
            OaFlow.status != "-1"
            if query_object
            else True,
            OaFlow.titel.like(f'%{query_object.title}%') if query_object.title
            else True,
            data_scope_sql,
        ).order_by(OaFlow.id.asc()))
        flow_cate_list: PageModel | list[list[dict[str, Any]]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return flow_cate_list

    @classmethod
    async def add_flow(cls, db: AsyncSession, model: OaFlowBaseModel):
        db_flow = OaFlow(**model.model_dump(exclude={"id"}, exclude_none=True))
        db.add(db_flow)
        await db.commit()
        await db.refresh(db_flow)
        return db_flow

    @classmethod
    async def update_flow(cls, db: AsyncSession, model: OaFlowBaseModel):
        result = await db.execute(
            update(OaFlow).where(model.id == OaFlow.id).values(**model.model_dump(exclude={"id", "create_time"}, exclude_none=True))
        )
        await db.commit()
        return result

    @classmethod
    async def change_status_flow(cls, db: AsyncSession, model: OaFlowBaseModel):
        result = await db.execute(update(OaFlow).where(model.id == OaFlow.id).values(status=model.status))
        await db.commit()
        return result

    @classmethod
    async def get_flow_detail(cls, db: AsyncSession, id: int):
        result = await db.execute(select(OaFlow).where(id == OaFlow.id))
        return result.scalars().first()