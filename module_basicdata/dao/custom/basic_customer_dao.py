from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement
from sqlalchemy import select, update, desc
from typing import Any
from common.vo import PageModel
from utils.page_util import PageUtil
from module_basicdata.entity.vo.custom.basic_customer_vo import OaBasicCustomerBaseModel, OaBasicCustomerPageQueryModel
from module_basicdata.entity.do.custom.basic_customer_do import OaBasicCustomer

class BasicCustomerDao:

    @classmethod
    async def get_page_list(cls, db: AsyncSession, query_object: OaBasicCustomerPageQueryModel, data_scope_sql: ColumnElement,
                            is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:
        query = (select(OaBasicCustomer)
                 .where(
                    OaBasicCustomer.types == query_object.types,
            data_scope_sql,
        ).order_by(OaBasicCustomer.create_time.asc()))
        page_list: PageModel | list[list[dict[str, Any]]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return page_list

    @classmethod
    async def add(cls, db: AsyncSession, model: OaBasicCustomerBaseModel):
        db_model = OaBasicCustomer(**model.model_dump(exclude={"id", "create_time"}, exclude_none=True), create_time=model.create_time)
        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)
        return db_model
        pass

    @classmethod
    async def update(cls, db: AsyncSession, model: OaBasicCustomerBaseModel):
        result = await db.execute(
            update(OaBasicCustomer)
            .values(
                title = model.title,
                update_time = model.update_time,
            )
            .where(OaBasicCustomer.id == model.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def change_status(cls, db: AsyncSession, model: OaBasicCustomerBaseModel):
        result = await db.execute(
            update(OaBasicCustomer).values(status = model.status).where(OaBasicCustomer.id == model.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def get_info_by_id(cls, db: AsyncSession, id: int):
        query = (select(OaBasicCustomer)
        .where(
            OaBasicCustomer.id == id))
        link_info = await db.scalar(query)
        return link_info

    @classmethod
    async def get_info_by_title(cls, db: AsyncSession, model: OaBasicCustomerBaseModel) -> OaBasicCustomer | None:
        """
        根据标题获取信息

        :param model:
        :param db: orm对象
        :return:
        """
        query_template_info = (
            (
                await db.execute(
                    select(OaBasicCustomer)
                    .where(
                        OaBasicCustomer.status == model.types,
                        OaBasicCustomer.title == model.title if model.title else True
                    )
                    .order_by(desc(OaBasicCustomer.create_time))
                    .distinct()
                )
            )
            .scalars()
            .first()
        )

        return query_template_info