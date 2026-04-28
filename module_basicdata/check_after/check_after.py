from sqlalchemy.ext.asyncio import AsyncSession

from module_finance.dao.expense_dao import ExpenseDao
from module_finance.dao.loan_dao import LoanDao
from module_finance.entity.do.expense_do import OaExpense


class CheckAfter:
    """
    审核通过后的一些后续操作
    """
    @classmethod
    async def check_after(cls,db:AsyncSession, id:int, check_table:str):
        """

        :param db:
        :param id:审核id
        :param check_table:审核表
        :return:
        """

        if check_table == "expense":
            await cls.update_expense(db, id)
        elif check_table == "invoice":
            pass
        else:
            pass

    @classmethod
    async def update_expense(cls,db:AsyncSession, id:int):
        """
        报销表审核通过后自动修改冲抵信息，借支表冲抵信息更新
        """
        expense = await ExpenseDao.get_info_by_id(db, id)
        expense = expense['OaExpense']
        if expense.loan_id == 0:
            return

        loan = await LoanDao.get_info_by_id(db, expense.loan_id)
        loan = loan['OaLoan']
        # 更新loan表中的冲抵金额、冲抵状态，expense表中的冲抵金额、支付金额、支付状态等信息
        balance_cost = loan.cost - loan.balance_cost
        if balance_cost - expense.cost > 0:
            loan.balance_cost += expense.cost
            loan.balance_status = 1
            expense.balance_cost = expense.cost
            expense.pay_amount = 0
            expense.pay_status = 1
        else:
            loan.balance_cost = loan.cost
            loan.balance_status = 2
            expense.balance_cost = balance_cost
            expense.pay_amount = expense.cost - balance_cost
            expense.pay_status = 0
        await ExpenseDao.update_by_entity(db, expense)
        await LoanDao.update_by_entity(db, loan)
        return

    @classmethod
    async def update_invoice(cls,db:AsyncSession, id:int):
        """
        无发票回款时自动变更回款状态
        :param db:
        :param id:
        :return:
        """
        pass