from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, delete
from common.vo import PageModel
from module_finance.entity.do.expense_interfix_do import OaExpenseInterfix
from module_finance.entity.vo.expense_interfix_vo import OaExpenseInterfixBaseModel
from module_finance.entity.do.expense_do import OaExpense
from typing import Any
from module_basicdata.entity.do.finance.expense_cate import OaExpenseCate

class ExpenseInterfixDao:
    @classmethod
    async def get_list_by_exid(cls, db: AsyncSession, exid: int) -> list[list[dict[str, Any]]]:

        # 构建基础查询
        query = select(
            OaExpenseInterfix
        ).where(
            OaExpenseInterfix.exid == exid
        ).order_by(
            desc(OaExpenseInterfix.id)
        )
        # 执行查询并获取结果
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def delete_by_exid(cls, db: AsyncSession, exid: int) -> PageModel:
        # 构建基础查询
        query = delete(OaExpenseInterfix).where(
            OaExpenseInterfix.exid == exid if isinstance(exid, int) else None
        )
        result =  await db.execute(query)
        return result.rowcount
        # 执行查询并获取结果

    @classmethod
    async def add(cls, db: AsyncSession, interfixes: list[OaExpenseInterfixBaseModel]) -> PageModel:
        expense_interfix_list : list[OaExpenseInterfix] = []
        for ex in interfixes:
            db_model = OaExpenseInterfix(**ex.model_dump(exclude={"id", "create_time", 'cate_name'}, exclude_none=True), create_time=ex.create_time)
            expense_interfix_list.append(db_model)
        db.add_all(expense_interfix_list)
        return await db.commit()



