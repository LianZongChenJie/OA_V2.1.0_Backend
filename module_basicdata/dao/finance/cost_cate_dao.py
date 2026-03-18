from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement
from sqlalchemy import select, update
from typing import Any
from common.vo import PageModel
from module_basicdata.entity.do.finance.cost_cate_do import OaCostCate
from module_basicdata.entity.vo.finance.cost_cate_vo import OaCostCateBaseModel, CostCatePageQueryModel
from utils.page_util import PageUtil
class CostCateDao:

    @classmethod
    async def get_cost_cate_list(cls, db: AsyncSession, query_object: CostCatePageQueryModel, data_scope_sql: ColumnElement,
                            is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:
        query = (select(OaCostCate)
                 .where(
            data_scope_sql,
        ).order_by(OaCostCate.create_time.asc()))
        links_list: PageModel | list[list[dict[str, Any]]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return links_list

    @classmethod
    async def add_cost_cate(cls, db: AsyncSession, model: OaCostCateBaseModel):
        db_link = OaCostCate(**model.model_dump(exclude={"id"}, exclude_none=True))
        db.add(db_link)
        await db.commit()
        await db.refresh(db_link)
        return db_link
        pass

    @classmethod
    async def update_cost_cate(cls, db: AsyncSession, model: OaCostCateBaseModel):
        result = await db.execute(
            update(OaCostCate)
            .values(**model.model_dump(exclude={"id", "create_time"}, exclude_none=True))
            .where(OaCostCate.id == model.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def change_status_cost_cate(cls, db: AsyncSession, model: OaCostCateBaseModel):
        result = await db.execute(
            update(OaCostCate).values(status = model.status).where(OaCostCate.id == model.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def get_cost_cate_info(cls, db: AsyncSession, id: int):
        query = (select(OaCostCate)
        .where(
            OaCostCate.id == id))
        link_info = await db.scalar(query)
        return link_info