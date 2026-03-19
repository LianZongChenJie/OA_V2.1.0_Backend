from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement
from sqlalchemy import select, update, desc
from typing import Any
from common.vo import PageModel
from utils.page_util import PageUtil
from module_basicdata.entity.vo.custom.customer_gradle_vo import OaCustomerGradeBaseModel, OaCustomerGradePageQueryModel
from module_basicdata.entity.do.custom.customer_gradle_do import OaCustomerGrade

class CustomerGradleDao:

    @classmethod
    async def get_page_list(cls, db: AsyncSession, query_object: OaCustomerGradePageQueryModel, data_scope_sql: ColumnElement,
                            is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:
        query = (select(OaCustomerGrade)
                 .where(
            data_scope_sql,
        ).order_by(OaCustomerGrade.create_time.asc()))
        page_list: PageModel | list[list[dict[str, Any]]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return page_list

    @classmethod
    async def add(cls, db: AsyncSession, model: OaCustomerGradeBaseModel):
        db_model = OaCustomerGrade(**model.model_dump(exclude={"id", "create_time"}, exclude_none=True), create_time=model.create_time)
        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)
        return db_model
        pass

    @classmethod
    async def update(cls, db: AsyncSession, model: OaCustomerGradeBaseModel):
        result = await db.execute(
            update(OaCustomerGrade)
            .values(
                title = model.title,
                update_time = model.update_time,
            )
            .where(OaCustomerGrade.id == model.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def change_status(cls, db: AsyncSession, model: OaCustomerGradeBaseModel):
        result = await db.execute(
            update(OaCustomerGrade).values(status = model.status).where(OaCustomerGrade.id == model.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def get_info_by_id(cls, db: AsyncSession, id: int):
        query = (select(OaCustomerGrade)
        .where(
            OaCustomerGrade.id == id))
        link_info = await db.scalar(query)
        return link_info

    @classmethod
    async def get_info_by_title(cls, db: AsyncSession, model: OaCustomerGradeBaseModel) -> OaCustomerGrade | None:
        """
        根据用户参数获取用户信息

        :param model:
        :param db: orm对象
        :return: 当前用户参数的用户信息对象
        """
        query_template_info = (
            (
                await db.execute(
                    select(OaCustomerGrade)
                    .where(
                        OaCustomerGrade.status == '1',
                        OaCustomerGrade.title == model.title if model.title else True
                    )
                    .order_by(desc(OaCustomerGrade.create_time))
                    .distinct()
                )
            )
            .scalars()
            .first()
        )

        return query_template_info