from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement
from sqlalchemy import select, update, desc
from typing import Any
from common.vo import PageModel
from utils.page_util import PageUtil
from module_basicdata.entity.vo.custom.customer_source_vo import OaCustomerSourceBaseModel, OaCustomerSourcePageQueryModel
from module_basicdata.entity.do.custom.custome_source_do import OaCustomerSource

class CustomerSourceDao:

    @classmethod
    async def get_page_list(cls, db: AsyncSession, query_object: OaCustomerSourcePageQueryModel, data_scope_sql: ColumnElement,
                            is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:
        query = (select(OaCustomerSource)
                 .where(
            data_scope_sql,
        ).order_by(OaCustomerSource.create_time.asc()))
        page_list: PageModel | list[list[dict[str, Any]]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return page_list

    @classmethod
    async def add(cls, db: AsyncSession, model: OaCustomerSourceBaseModel):
        db_model = OaCustomerSource(**model.model_dump(exclude={"id", "create_time"}, exclude_none=True), create_time=model.create_time)
        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)
        return db_model
        pass

    @classmethod
    async def update(cls, db: AsyncSession, model: OaCustomerSourceBaseModel):
        result = await db.execute(
            update(OaCustomerSource)
            .values(
                title = model.title,
                update_time = model.update_time,
            )
            .where(OaCustomerSource.id == model.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def change_status(cls, db: AsyncSession, model: OaCustomerSourceBaseModel):
        result = await db.execute(
            update(OaCustomerSource).values(status = model.status).where(OaCustomerSource.id == model.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def get_info_by_id(cls, db: AsyncSession, id: int):
        query = (select(OaCustomerSource)
        .where(
            OaCustomerSource.id == id))
        link_info = await db.scalar(query)
        return link_info

    @classmethod
    async def get_info_by_title(cls, db: AsyncSession, model: OaCustomerSourceBaseModel) -> OaCustomerSource | None:
        """
        根据标题获取信息

        :param model:
        :param db: orm对象
        :return:
        """
        query_template_info = (
            (
                await db.execute(
                    select(OaCustomerSource)
                    .where(
                        OaCustomerSource.status == '1',
                        OaCustomerSource.title == model.title if model.title else True
                    )
                    .order_by(desc(OaCustomerSource.create_time))
                    .distinct()
                )
            )
            .scalars()
            .first()
        )

        return query_template_info