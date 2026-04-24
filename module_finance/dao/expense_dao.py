from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from sqlalchemy.orm import aliased
from sqlalchemy.sql import ColumnElement, func,or_
from common.vo import PageModel
from module_admin.entity.do.dept_do import SysDept
from module_admin.entity.do.user_do import SysUser
from module_finance.entity.do.loan_do import OaLoan
from utils.page_util import PageUtil
from module_finance.entity.vo.expense_vo import OaExpenseBaseModel, OaExpensePageQueryModel
from module_finance.entity.do.expense_do import OaExpense
from typing import Any
from datetime import datetime

class ExpenseDao:
    @classmethod
    async def get_page_list(cls, db: AsyncSession, query_object: OaExpensePageQueryModel,
                            data_scope_sql: ColumnElement,
                            is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:

        # 构建基础查询
        pay = aliased(SysUser, name='pay')
        admin = aliased(SysUser, name='admin')
        dept = aliased(SysDept, name='dept')
        query = (select(OaExpense,
                        pay.nick_name.label('pay_name'),
                        admin.nick_name.label('admin_name'),
                        dept.dept_name.label('dept_name'),
                        )
                 .join(pay, OaExpense.admin_id == pay.user_id, isouter=True)
                 .join(admin, OaExpense.pay_admin_id == admin.user_id, isouter=True)
                 .join(dept, OaExpense.did == dept.dept_id, isouter=True))

        # 构建条件列表
        conditions = []
        conditions.append(OaExpense.delete_time == 0)
        # 通用条件：审核状态
        if query_object.check_status is not None:
            conditions.append(OaExpense.check_status == query_object.check_status)

        # 通用条件：审核时间范围
        if query_object.begin_time and query_object.end_time:
            start_timestamp = int(datetime.strptime(query_object.begin_time, "%Y-%m-%d %H:%M:%S").timestamp())
            end_timestamp = int(datetime.strptime(query_object.end_time, "%Y-%m-%d %H:%M:%S").timestamp())
            conditions.append(OaExpense.check_time.between(start_timestamp, end_timestamp))

        # 根据不同的查询条件添加特定条件
        if query_object.admin_id:
            conditions.append(OaExpense.admin_id == query_object.admin_id)

        elif query_object.check_uids:
            conditions.append(func.find_in_set(query_object.check_uids, OaExpense.check_uids) > 0)

        elif query_object.check_history_uids:
            conditions.append(
                func.find_in_set(query_object.check_history_uids, OaExpense.check_history_uids) > 0)

        elif query_object.check_copy_uids:
            conditions.append(func.find_in_set(query_object.check_copy_uids, OaExpense.check_copy_uids) > 0)

        else:
            # 没有特定条件时，使用 OR 组合
            or_conditions = []
            if query_object.admin_id:
                or_conditions.append(OaExpense.admin_id == query_object.admin_id)
            if query_object.check_uids:
                or_conditions.append(func.find_in_set(query_object.check_uids, OaExpense.check_uids) > 0)
            if query_object.check_copy_uids:
                or_conditions.append(
                    func.find_in_set(query_object.check_copy_uids, OaExpense.check_copy_uids) > 0)
            if query_object.check_history_uids:
                or_conditions.append(
                    func.find_in_set(query_object.check_history_uids, OaExpense.check_history_uids) > 0)

            if or_conditions:
                conditions.append(or_(*or_conditions))

        # 添加数据权限条件
        if data_scope_sql is not None:
            conditions.append(data_scope_sql)

        # 应用所有条件
        if conditions:
            query = query.where(*conditions)

        # 排序
        query = query.order_by(desc(OaExpense.create_time))

        # 分页查询
        page_list: PageModel | list[list[dict[str, Any]]] = await PageUtil.paginate_dict(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return page_list

    @classmethod
    async def add(cls, db: AsyncSession, model: OaExpenseBaseModel):
        db_model = OaExpense(**model.model_dump(exclude={"id", "create_time",'income_month', 'expense_time'}, exclude_none=True),
                                 create_time=model.create_time, income_month=model.income_month, expense_time=model.expense_time)
        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)
        return db_model

    @classmethod
    async def update(cls, db: AsyncSession, model: OaExpenseBaseModel):
        result = await db.execute(
            update(OaExpense)
            .values(
                **model.model_dump(exclude={"id", "update_time",'income_month', 'expense_time','pay_time'}, exclude_none=True),
                update_time=model.update_time,  income_month=model.income_month, expense_time=model.expense_time,
            )
            .where(OaExpense.id == model.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def get_info_by_id(cls, db: AsyncSession, id: int):
        pay = aliased(SysUser, name='pay')
        admin = aliased(SysUser, name='admin')
        dept = aliased(SysDept, name='dept')
        query = (select(OaExpense,
                        pay.nick_name.label('pay_name'),
                        admin.nick_name.label('admin_name'),
                        dept.dept_name.label('dept_name'),
                        OaLoan.cost.label('loan_cost'),
                        )
                 .join(pay, OaExpense.admin_id == pay.user_id, isouter=True)
                 .join(admin, OaExpense.pay_admin_id == admin.user_id, isouter=True)
                 .join(dept, OaExpense.did == dept.dept_id, isouter=True)
                 .join(OaLoan, OaExpense.loan_id == OaLoan.id, isouter=True)

    .where(
            OaExpense.id == id))
        info = await db.execute(query)
        return info.mappings().first()
    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        result = await db.execute(update(OaExpense).values(delete_time=int(datetime.now().timestamp())).where(OaExpense.id == id))
        await db.commit()
        return result.rowcount

    # @classmethod
    # async def cancel_expense(cls, db: AsyncSession, query_model: OaExpenseBaseModel):
    #     result = await db.execute(update(OaExpense).values(
    #         update_time=int(datetime.now().timestamp()),
    #         check_status=query_model.check_status,
    #         remark=query_model.remark
    #     ).where(OaExpense.id == query_model.id))
    #     await db.commit()
    #     return result.rowcount
    #
    # # @classmethod
    # # async def count_by_uid(cls, db: AsyncSession, uid: str):
    # #     result = await db.execute(select(func.count()).where(OaExpense.uid == uid))
    # #     return result.scalar()
    # @classmethod
    # async def pass_expense(cls, db: AsyncSession, data: OaExpenseBaseModel):
    #     try:
    #         result = await db.execute(
    #             update(OaExpense)
    #             .values(
    #                 check_status=2,
    #                 check_time=data.check_time,
    #                 remark=data.remark
    #             )
    #             .where(OaExpense.id == data.id)
    #         )
    #         await db.commit()
    #     except Exception as e:
    #         await db.rollback()
    #         raise e
    #     return result.rowcount
    #
    # @classmethod
    # async def reject_expense(cls, db: AsyncSession, data: OaExpenseBaseModel):
    #     try:
    #         result = await db.execute(
    #             update(OaExpense)
    #             .values(
    #                 check_status=3,
    #                 check_time=data.check_time,
    #                 remark=data.remark
    #             )
    #             .where(OaExpense.id == data.id)
    #         )
    #         await db.commit()
    #         return result.rowcount
    #     except Exception as e:
    #         await db.rollback()
    #         raise e

    @classmethod
    async def pay_expense(cls, db: AsyncSession, data: OaExpenseBaseModel, userId: int):
        try:
            result = await db.execute(
                update(OaExpense)
                .values(
                    pay_time=int(datetime.now().timestamp()),
                    pay_status=1,
                    pay_admin_id=userId,
                )
                .where(OaExpense.id == data.id)
            )
            await db.commit()
            return result.rowcount
        except Exception as e:
            await db.rollback()
            raise e
    @classmethod
    async def get_count(cls, query_db: AsyncSession, user_id: int):
        """
        获取首页我的报销开票等数据统计信息
        """
        query = select(func.count()).select_from(OaExpense).where(OaExpense.admin_id == user_id, OaExpense.delete_time == 0, OaExpense.check_status == 2)
        count = await query_db.execute(query)
        return count.scalar()

    @classmethod
    async def get_wait_check_count(cls, db: AsyncSession, user_id: int):
        """
        获取待审采报销数量

        :param db: orm 对象
        :param user_id: 用户 ID
        :return: 待审报销数量
        """
        query = select(func.count()).select_from(OaExpense).where(
            OaExpense.delete_time == 0,
            OaExpense.check_status == 1,
            func.find_in_set(str(user_id), OaExpense.check_uids),
        )
        result = await db.execute(query)
        count = result.scalar()
        return count
