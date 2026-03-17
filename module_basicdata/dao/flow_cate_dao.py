from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.sql import ColumnElement
from typing import Any
from datetime import datetime, time
from common.vo import PageModel
from module_basicdata.entity.do.flow_cate_do import OaFlowCate
from module_basicdata.entity.vo.flow_cate_vo import FlowCatePageQueryModel, OaFlowCateModel
from utils.page_util import PageUtil


class FlowCateDao:
    @classmethod
    async def get_flow_cate_list(cls, db: AsyncSession, query_object: FlowCatePageQueryModel, data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:
        query = (select(OaFlowCate)
                 .where(
                    OaFlowCate.status != "-1"
                 if query_object
                 else True,
                 OaFlowCate.titel.like(f'%{query_object.title}%') if query_object.title
                 else True,
                 data_scope_sql,
                 ).order_by(OaFlowCate.id.asc()))
        flow_cate_list: PageModel | list[list[dict[str, Any]]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return flow_cate_list

    @classmethod
    async def add_flow_cate(cls, db: AsyncSession, model: OaFlowCateModel):
        db_flow_cate = OaFlowCate(**model.model_dump(exclude={"id"}, exclude_none=True))
        db.add(db_flow_cate)
        await db.commit()
        await db.refresh(db_flow_cate)
        return db_flow_cate
        pass

    @classmethod
    async def update_flow_cate(cls, db: AsyncSession, model: OaFlowCateModel):
        result = await db.execute(
            update(OaFlowCate)
            .values(**model.model_dump(exclude={"id", "create_time"}, exclude_none=True))
            .where(OaFlowCate.id == model.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def delete_flow_cate(cls, db: AsyncSession, id: int):
        result = await db.execute(update(OaFlowCate).values(status="-1").where(OaFlowCate.id == id))
        await db.commit()
        return result.rowcount

    @classmethod
    async def get_flow_cate_info(cls, db: AsyncSession, id: int):
        result = await db.execute(select(OaFlowCate).where(OaFlowCate.id == id))
        return result.scalars().first()

    @classmethod
    async def change_status_flow_cate(cls, db: AsyncSession, model: OaFlowCateModel):
        result = await db.execute(update(OaFlowCate).values(status=model.status).where(OaFlowCate.id == model.id))
        await db.commit()
        return result.rowcount



