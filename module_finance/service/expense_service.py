from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from exceptions.exception import ServiceException
from module_basicdata.dao.public.flow_cate_dao import FlowCateDao
from module_basicdata.dao.public.flow_step_dao import OaFlowStepDao
from module_finance.dao.expense_dao import ExpenseDao
from module_finance.dao.expense_interfix_dao import ExpenseInterfixDao
from module_finance.dao.loan_dao import LoanDao
from module_personnel.dao.flow_record_dao import FlowRecordDao
from sqlalchemy.sql import ColumnElement
from module_finance.entity.vo.expense_vo import OaExpenseBaseModel, \
    OaExpenseDetailModel, OaExpensePageQueryModel
from common.vo import PageModel, CrudResponseModel
from datetime import datetime

from module_personnel.entity.vo.flow_record_vo import OaFlowRecordBaseModel
from utils.timeformat import int_time
from decimal import Decimal


class OaExpenseService:
    @classmethod
    async def get_page_list_service(cls, query_db: AsyncSession, query_object: OaExpensePageQueryModel,
                                    data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel[
                                                                                                 OaExpenseBaseModel] | \
                                                                                             list[dict[str, Any]]:
        query_list = await ExpenseDao.get_page_list(query_db, query_object, data_scope_sql, is_page)
        if is_page:
            result_list = PageModel[OaExpenseBaseModel](**{
                **query_list.model_dump(by_alias=True)
            })
        else:
            result_list = []
            if query_list:
                result_list = [{**row} for row in query_list]
        return result_list

    @classmethod
    async def add_service(cls, query_db: AsyncSession, model_detail: OaExpenseDetailModel) -> CrudResponseModel:
        try:
            model = model_detail.info
            model.create_time = int(datetime.now().timestamp())
            model.income_month = int_time(model.income_month)
            model.expense_time = int_time(model.expense_time)
            if model.loan_id:
                loan = await LoanDao.get_info_by_id(query_db, model.loan_id)
                model.cost = model.cost - loan.cost
                if model.cost < 0:
                    model.cost = Decimal(0)
                    model.expense_time = int_time(model.expense_time)
            model = await ExpenseDao.add(query_db, model)
            for item in model_detail.interfix:
                item.create_time = int(datetime.now().timestamp())
                item.admin_id = model.admin_id
                item.exid = model.id
            await ExpenseInterfixDao.add(query_db, model_detail.interfix)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def update_service(cls, query_db: AsyncSession, model_detail: OaExpenseDetailModel) -> CrudResponseModel:
        try:
            model = model_detail.info
            model.update_time = int(datetime.now().timestamp())
            model.income_month = int_time(model.income_month)
            model.expense_time = int_time(model.expense_time)
            if model.loan_id:
                loan = await LoanDao.get_info_by_id(query_db, model.loan_id)
                model.cost = model.cost - loan.cost
                if model.cost < 0:
                    model.cost = Decimal(0)
                    model.expense_time = int_time(model.expense_time)
            await ExpenseInterfixDao.delete_by_exid(query_db, model.id)
            await ExpenseDao.update(query_db, model)
            for item in model_detail.interfix:
                item.create_time = int(datetime.now().timestamp())
                item.admin_id = model.admin_id
                item.exid = model.id
            await ExpenseInterfixDao.add(query_db, model_detail.interfix)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='修改成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass


    @classmethod
    async def get_info_service(cls, query_db: \
            AsyncSession, id: int) -> OaExpenseBaseModel:
        try:
            info = await ExpenseDao.get_info_by_id(query_db, id)
            records = await FlowRecordDao.get_records_by_action_id(query_db, info.id, info.check_flow_id)
            inter = await ExpenseInterfixDao.get_list_by_exid(query_db, info.id)
            detail = OaExpenseDetailModel(info=info, interfix=inter, flow_records=records)
            if not detail:
                raise ServiceException(message="未找到该数据")
            return detail
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        try:
            await ExpenseDao.del_by_id(db, id)
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def pass_expense(cls, db: AsyncSession, data: OaExpenseBaseModel, userId: int):
        try:
            data.check_time = int(datetime.now().timestamp())
            await cls.set_check_uid(db, data, userId)
            await ExpenseDao.pass_expense(db, data)
            seal = await ExpenseDao.get_info_by_id(db, data.id)
            await cls.add_record(db, seal, data, userId)
            await db.commit()
            return CrudResponseModel(is_success=True, message='审核通过成功')
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def reject_expense(cls, db: AsyncSession, data: OaExpenseBaseModel, userId: int):
        try:
            data.check_time = int(datetime.now().timestamp())
            await cls.set_check_uid(db, data, userId)
            await ExpenseDao.reject_expense(db, data)
            seal = await ExpenseDao.get_info_by_id(db, data.id)
            await cls.add_record(db, seal, data, userId)
            await db.commit()
            return CrudResponseModel(is_success=True, message='审核拒绝成功')
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def cancel_expense(cls, db: AsyncSession, data: OaExpenseBaseModel, userId: int):
        try:
            await cls.set_check_uid(db, data, userId)
            await ExpenseDao.cancel_expense(db, data)
            loan = await ExpenseDao.get_info_by_id(db, data.id)
            await cls.add_record(db, loan, data, userId)
            await db.commit()
            return CrudResponseModel(is_success=True, message='撤销申请成功')
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def pay_expense(cls, db: AsyncSession, data: OaExpenseBaseModel, userId: int):
        try:
            await ExpenseDao.pay_expense(db, data, userId)
            await db.commit()
            return CrudResponseModel(is_success=True, message='打款成功')
        except Exception as e:
            await db.rollback()
            return CrudResponseModel(is_success=False, message='打款失败')

    @classmethod
    async def back_expense(cls, db: AsyncSession, data: OaExpenseBaseModel, userId: int):
        try:
            await ExpenseDao.back_expense(db, data, userId)
            await db.commit()
            return CrudResponseModel(is_success=True, message='还款成功')
        except Exception as e:
            await db.rollback()
            return CrudResponseModel(is_success=False, message='还款失败')

    @classmethod
    async def add_record(cls, db: AsyncSession, change: OaFlowRecordBaseModel, model: OaExpenseBaseModel, userId: int):
        try:
            flow_cate = await FlowCateDao.get_flow_cate_info(db, change.check_flow_id)
            step = await OaFlowStepDao.get_info_by_flow_id(db, change.check_flow_id)
            record = OaFlowRecordBaseModel()
            record.action_id = change.id
            record.check_table = flow_cate.check_table
            record.flow_id = change.check_flow_id
            record.check_files = model.file_ids
            record.check_uid = userId
            record.check_status = model.check_status
            record.step_id = step.id if step is not None else 0
            record.content = model.remark
            record.check_time = int(datetime.now().timestamp())
            await FlowRecordDao.add(db, record)
        except Exception as e:
            await db.rollback()
            raise e

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
