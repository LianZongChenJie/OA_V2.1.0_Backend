from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement
from sqlalchemy import select, update, desc
from typing import Any
from common.vo import PageModel
from module_basicdata.entity.do.finance.expense_cate import OaExpenseCate
from module_basicdata.entity.vo.finance.expense_cate_vo import ExpenseCatePageQueryModel, OaExpenseCateBaseModel
from utils.page_util import PageUtil
class ExpenseCateDao:

    @classmethod
    async def get_expense_cate_list(cls, db: AsyncSession, query_object: ExpenseCatePageQueryModel, data_scope_sql: ColumnElement,
                            is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:
        query = (select(OaExpenseCate)
                 .where(
            data_scope_sql,
        ).order_by(OaExpenseCate.create_time.asc()))
        expense_cate_list: PageModel | list[list[dict[str, Any]]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return expense_cate_list

    @classmethod
    async def add_expense_cate(cls, db: AsyncSession, model: OaExpenseCateBaseModel):
        db_expense = OaExpenseCate(**model.model_dump(exclude={"id"}, exclude_none=True))
        db.add(db_expense)
        await db.commit()
        await db.refresh(db_expense)
        return db_expense
        pass

    @classmethod
    async def update_expense_cate(cls, db: AsyncSession, model: OaExpenseCateBaseModel):
        result = await db.execute(
            update(OaExpenseCate)
            .values(**model.model_dump(exclude={"id", "create_time"}, exclude_none=True))
            .where(OaExpenseCate.id == model.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def change_status_expense_cate(cls, db: AsyncSession, model: OaExpenseCateBaseModel):
        result = await db.execute(
            update(OaExpenseCate).values(status = model.status).where(OaExpenseCate.id == model.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def get_expense_cate_info(cls, db: AsyncSession, id: int):
        query = (select(OaExpenseCate)
        .where(
            OaExpenseCate.id == id))
        expense_info = await db.scalar(query)
        return expense_info

    @classmethod
    async def get_info_by_title(cls, db: AsyncSession, model: OaExpenseCateBaseModel) -> OaExpenseCate | None:
        """
        根据标题用户信息

        :param model:
        :param db: orm对象
        :return: 对象
        """
        query_info = (
            (
                await db.execute(
                    select(OaExpenseCate)
                    .where(
                        OaExpenseCate.status == '1',
                        OaExpenseCate.title == model.title if model.title else True
                    )
                    .order_by(desc(OaExpenseCate.create_time))
                    .distinct()
                )
            )
            .scalars()
            .first()
        )

        return query_info