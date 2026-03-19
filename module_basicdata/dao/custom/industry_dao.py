from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement
from sqlalchemy import select, update
from typing import Any
from common.vo import PageModel
from module_basicdata.entity.do.custom.industry_do import OaIndustry
from module_basicdata.entity.vo.custom.industry_vo import IndustryPageQueryModel, OaIndustryBaseModel
from utils.page_util import PageUtil
class IndustryDao:

    @classmethod
    async def get_cost_cate_list(cls, db: AsyncSession, query_object: IndustryPageQueryModel, data_scope_sql: ColumnElement,
                            is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:
        query = (select(OaIndustry)
                 .where(
            data_scope_sql,
        ).order_by(OaIndustry.create_time.asc()))
        industry_list: PageModel | list[list[dict[str, Any]]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return industry_list

    @classmethod
    async def add_db_industry(cls, db: AsyncSession, model: OaIndustryBaseModel):
        db_industry = OaIndustry(**model.model_dump(exclude={"id", "create_time"}, exclude_none=True), create_time=model.create_time)
        db.add(db_industry)
        await db.commit()
        await db.refresh(db_industry)
        return db_industry
        pass

    @classmethod
    async def update_industry(cls, db: AsyncSession, model: OaIndustryBaseModel):
        result = await db.execute(
            update(OaIndustry)
            .values(
                title = model.title,
                update_time = model.update_time,
            )
            .where(OaIndustry.id == model.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def change_status_industry(cls, db: AsyncSession, model: OaIndustryBaseModel):
        result = await db.execute(
            update(OaIndustry).values(status = model.status).where(OaIndustry.id == model.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def get_industry_info(cls, db: AsyncSession, id: int):
        query = (select(OaIndustry)
        .where(
            OaIndustry.id == id))
        link_info = await db.scalar(query)
        return link_info