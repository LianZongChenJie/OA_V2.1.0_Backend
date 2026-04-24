from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from exceptions.exception import ServiceException
from module_finance.dao.expense_dao import ExpenseDao
from module_finance.dao.expense_interfix_dao import ExpenseInterfixDao
from module_finance.dao.loan_dao import LoanDao
from module_personnel.dao.flow_record_dao import FlowRecordDao
from sqlalchemy.sql import ColumnElement
from module_finance.entity.vo.expense_vo import OaExpenseBaseModel, \
    OaExpenseDetailModel, OaExpensePageQueryModel
from common.vo import PageModel, CrudResponseModel
from datetime import datetime
from utils.camel_converter import ResponseConverter, ModelConverter
from utils.timeformat import int_time, int_month, format_month
from decimal import Decimal


class OaExpenseService:
    time_fields = ['create_time', 'update_time', 'income_month', 'expense_time']
    @classmethod
    async def get_page_list_service(cls, query_db: AsyncSession, query_object: OaExpensePageQueryModel,
                                    data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel[
                                                                                                 OaExpenseBaseModel] | \
                                                                                             list[dict[str, Any]]:
        query_list = await ExpenseDao.get_page_list(query_db, query_object, data_scope_sql, is_page)
        if is_page:
            row_list = []
            for row in query_list.rows:
                row = dict(row)
                row.update(row['OaExpense'].to_dict())
                row.pop('OaExpense')
                row['income_month'] = format_month(row['income_month'])
                row_list.append(ModelConverter.convert_to_camel_case(row))
            query_list.rows = row_list
            result_list = query_list
        else:
            result_list = []
            if query_list:
                result_list = [{**row} for row in query_list]
        return result_list

    @classmethod
    async def add_service(cls, query_db: AsyncSession, model_detail: OaExpenseDetailModel) -> CrudResponseModel:
        try:
            interfix = model_detail.interfix
            model = model_detail
            delattr(model_detail, 'interfix')
            delattr(model_detail, 'flow_records')
            model.create_time = int(datetime.now().timestamp())
            model.income_month = int_month(model.income_month)
            model.expense_time = int_time(model.expense_time)
            if model.loan_id:
                loan = await LoanDao.get_info_by_id(query_db, model.loan_id)
                model.balance_cost = loan['OaLoan'].cost
                if model.cost < 0:
                    model.cost = Decimal(0)
                    model.expense_time = int_time(model.expense_time)
            model = await ExpenseDao.add(query_db, model)
            for item in interfix:
                item.create_time = int(datetime.now().timestamp())
                item.admin_id = model.admin_id
                item.exid = model.id
            await ExpenseInterfixDao.add(query_db, interfix)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def update_service(cls, query_db: AsyncSession, model_detail: OaExpenseDetailModel) -> CrudResponseModel:
        try:
            expense = await ExpenseDao.get_info_by_id(query_db, model_detail.id)
            if expense['OaExpense'].check_status != 0 and expense['OaExpense'].check_status != 4:
                return CrudResponseModel(is_success=False, message='请先撤销申请再编辑')
            interfix  = model_detail.interfix
            delattr(model_detail, 'interfix')
            delattr(model_detail, 'flow_records')
            model = model_detail
            model.update_time = int(datetime.now().timestamp())
            model.income_month = int_time(model.income_month)
            model.expense_time = int_time(model.expense_time)
            if model.loan_id:
                loan = await LoanDao.get_info_by_id(query_db, model.loan_id)
                model.balance_cost = loan['OaLoan'].cost
                if model.cost < 0:
                    model.cost = Decimal(0)
                    model.expense_time = int_time(model.expense_time)
            await ExpenseInterfixDao.delete_by_exid(query_db, model.id)
            await ExpenseDao.update(query_db, model)
            for item in interfix:
                item.create_time = int(datetime.now().timestamp())
                item.admin_id = model.admin_id
                item.exid = model.id
            await ExpenseInterfixDao.add(query_db, interfix)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='修改成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass


    @classmethod
    async def get_info_service(cls, query_db: \
            AsyncSession, id: int) -> dict[str, Any]:
        try:
            info = await ExpenseDao.get_info_by_id(query_db, id)
            if not info:
                raise ServiceException(message="未找到该数据")
            records = await FlowRecordDao.get_records_by_action_id(query_db, info['OaExpense'].id, info['OaExpense'].check_flow_id)
            inter = await ExpenseInterfixDao.get_list_by_exid(query_db, info['OaExpense'].id)
            detail = {}
            info = dict(info)
            info.update(info['OaExpense'].to_dict())
            info.pop('OaExpense')
            detail.update(info)
            record_list = []
            for record in records:
                record_list.append(ModelConverter.convert_to_camel_case(record.to_dict()))
            detail['records'] = record_list
            inter_list = []
            for item in inter:
                inter_list.append(ModelConverter.convert_to_camel_case(item.to_dict()))
            detail['interfix'] = inter_list
            if not detail:
                raise ServiceException(message="未找到该数据")
            detail = ResponseConverter.convert_to_camel_and_format_time(detail, cls.time_fields)
            return detail
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        try:
            expense = await ExpenseDao.get_info_by_id(db, id)
            if not expense:
                return CrudResponseModel(is_success=False, message='未找到该数据')
            if expense['OaExpense'].check_status != 0 and expense['OaExpense'].check_status != 4:
                return CrudResponseModel(is_success=False, message='请先撤销申请再删除')
            await ExpenseDao.del_by_id(db, id)
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await db.rollback()
            raise e

    # @classmethod
    # async def pass_expense(cls, db: AsyncSession, data: OaExpenseBaseModel, userId: int):
    #     try:
    #         data.check_time = int(datetime.now().timestamp())
    #         await cls.set_check_uid(db, data, userId)
    #         await ExpenseDao.pass_expense(db, data)
    #         seal = await ExpenseDao.get_info_by_id(db, data.id)
    #         await cls.add_record(db, seal, data, userId)
    #         await db.commit()
    #         return CrudResponseModel(is_success=True, message='审核通过成功')
    #     except Exception as e:
    #         await db.rollback()
    #         raise e
    #
    # @classmethod
    # async def reject_expense(cls, db: AsyncSession, data: OaExpenseBaseModel, userId: int):
    #     try:
    #         data.check_time = int(datetime.now().timestamp())
    #         await cls.set_check_uid(db, data, userId)
    #         await ExpenseDao.reject_expense(db, data)
    #         seal = await ExpenseDao.get_info_by_id(db, data.id)
    #         await cls.add_record(db, seal, data, userId)
    #         await db.commit()
    #         return CrudResponseModel(is_success=True, message='审核拒绝成功')
    #     except Exception as e:
    #         await db.rollback()
    #         raise e
    #
    # @classmethod
    # async def cancel_expense(cls, db: AsyncSession, data: OaExpenseBaseModel, userId: int):
    #     try:
    #         await cls.set_check_uid(db, data, userId)
    #         await ExpenseDao.cancel_expense(db, data)
    #         loan = await ExpenseDao.get_info_by_id(db, data.id)
    #         await cls.add_record(db, loan, data, userId)
    #         await db.commit()
    #         return CrudResponseModel(is_success=True, message='撤销申请成功')
    #     except Exception as e:
    #         await db.rollback()
    #         raise e

    @classmethod
    async def pay_expense(cls, db: AsyncSession, data: OaExpenseBaseModel, userId: int):
        try:
            expense = await ExpenseDao.get_info_by_id(db, data.id)
            if expense['OaExpense'].check_status !=2 and expense['OaExpense'].pay_status !=0:
                return CrudResponseModel(is_success=False, message='当前状态不支持打款操作')
            await ExpenseDao.pay_expense(db, data, userId)
            await db.commit()
            return CrudResponseModel(is_success=True, message='打款成功')
        except Exception as e:
            await db.rollback()
            return CrudResponseModel(is_success=False, message='打款失败')

    # @classmethod
    # async def back_expense(cls, db: AsyncSession, data: OaExpenseBaseModel, userId: int):
    #     try:
    #         expense = await ExpenseDao.get_info_by_id(db, data.id)
    #         if expense.check_status !=2 or expense.pay_status !=1:
    #             return CrudResponseModel(is_success=False,message='当前状态不支持还款！')
    #         await ExpenseDao.back_expense(db, data, userId)
    #         await db.commit()
    #         return CrudResponseModel(is_success=True, message='还款成功')
    #     except Exception as e:
    #         await db.rollback()
    #         return CrudResponseModel(is_success=False, message='还款失败')

    # @classmethod
    # async def add_record(cls, db: AsyncSession, change: OaFlowRecordBaseModel, model: OaExpenseBaseModel, userId: int):
    #     try:
    #         flow_cate = await FlowCateDao.get_flow_cate_info(db, change.check_flow_id)
    #         step = await OaFlowStepDao.get_info_by_flow_id(db, change.check_flow_id)
    #         record = OaFlowRecordBaseModel()
    #         record.action_id = change.id
    #         record.check_table = flow_cate.check_table
    #         record.flow_id = change.check_flow_id
    #         record.check_files = model.file_ids
    #         record.check_uid = userId
    #         record.check_status = model.check_status
    #         record.step_id = step.id if step is not None else 0
    #         record.content = model.remark
    #         record.check_time = int(datetime.now().timestamp())
    #         await FlowRecordDao.add(db, record)
    #     except Exception as e:
    #         await db.rollback()
    #         raise e

    @classmethod
    async def set_check_uid(cls, query_db: AsyncSession, query_object: OaExpenseBaseModel, userId: int):
        db_model = await ExpenseDao.get_info_by_id(query_db, query_object.id)
        if userId not in db_model.check_history_uids.split(','):
            query_object.check_history_uids = ','.join([str(userId), db_model.check_history_uids])
        query_object.check_last_uid = str(userId)

    @classmethod
    async def get_count(cls, query_db: AsyncSession, user_id: int):
        """
        获取首页我的报销开票等数据统计信息
        """
        return await ExpenseDao.get_count(query_db, user_id)
