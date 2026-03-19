from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement
from sqlalchemy import select, update, delete, desc
from typing import Any
from common.vo import PageModel
from module_basicdata.entity.do.public.lnks_do import OaLinks
from module_basicdata.entity.vo.public.links_vo import OaLinksBaseModel, OaLinksPageQueryModel
from utils.page_util import PageUtil


class LinksDao:
    @classmethod
    async def get_link_list(cls, db: AsyncSession, query_object: OaLinksBaseModel, data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:
        query = (select(OaLinks)
                 .where(
                 data_scope_sql,
                 ).order_by(OaLinks.sort.asc()))
        links_list: PageModel | list[list[dict[str, Any]]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return links_list

    @classmethod
    async def add_link(cls, db: AsyncSession, model: OaLinksBaseModel):
        db_link = OaLinks(**model.model_dump(exclude={"id", "create_time"}, exclude_none=True), create_time = model.create_time)
        db.add(db_link)
        await db.commit()
        await db.refresh(db_link)
        return db_link
        pass

    @classmethod
    async def update_link(cls, db: AsyncSession, model: OaLinksBaseModel):
        result = await db.execute(
            update(OaLinks)
            .values(**model.model_dump(exclude={"id", "update_time"}, exclude_none=True), update_time = model.update_time)
            .where(OaLinks.id == model.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def delete_link(cls, db: AsyncSession, id: int):
        result = await db.execute(
            delete(OaLinks).where(OaLinks.id == id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def get_link_info(cls, db: AsyncSession, id: int):
        query = (select(OaLinks)
        .where(
            OaLinks.id == id))
        link_info = await db.scalar(query)
        return link_info

    @classmethod
    async def get_info_by_title(cls, db: AsyncSession, model: OaLinksBaseModel) -> OaLinks | None:
        """
        根据用户参数获取用户信息

        :param model:
        :param db: orm对象
        :return: 对象
        """
        query_info = (
            (
                await db.execute(
                    select(OaLinks)
                    .where(
                        OaLinks.title == model.title if model.title else True
                    )
                    .order_by(desc(OaLinks.create_time))
                    .distinct()
                )
            )
            .scalars()
            .first()
        )

        return query_info