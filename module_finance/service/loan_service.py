from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from exceptions.exception import ServiceException
from module_basicdata.dao.public.flow_cate_dao import FlowCateDao
from module_basicdata.dao.public.flow_step_dao import OaFlowStepDao
from module_finance.dao.loan_dao import LoanDao
from module_personnel.dao.flow_record_dao import FlowRecordDao
from sqlalchemy.sql import ColumnElement
from module_finance.entity.vo.loan_vo import OaLoanBaseModel, \
    OaLoanPageQueryModel, OaLoanDetailModel
from common.vo import PageModel, CrudResponseModel
from datetime import datetime

from module_personnel.entity.vo.flow_record_vo import OaFlowRecordBaseModel
from utils.camel_converter import ModelConverter
from utils.timeformat import int_time


class OaLoanService:
    @classmethod
    async def get_page_list_service(cls, query_db: AsyncSession, query_object: OaLoanPageQueryModel,
                                    data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel[
                                                                                                 OaLoanBaseModel] | \
                                                                                             list[dict[str, Any]]:
        query_list = await LoanDao.get_page_list(query_db, query_object, data_scope_sql, is_page)
        if is_page:
            result_list = PageModel[OaLoanBaseModel](**{
                **query_list.model_dump(by_alias=True)
            })
        else:
            result_list = []
            if query_list:
                result_list = [{**row} for row in query_list]
        return result_list

    @classmethod
    async def add_service(cls, query_db: AsyncSession, model: OaLoanBaseModel) -> CrudResponseModel:
        if model.id:
            return await cls.update_service(query_db, model)

        try:
            model.create_time = int(datetime.now().timestamp())
            model.loan_time = int_time(model.loan_time)
            model.plan_time = int_time(model.plan_time)
            await LoanDao.add(query_db, model)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def update_service(cls, query_db: AsyncSession, model: OaLoanBaseModel) -> CrudResponseModel:
        try:
            model.update_time = int(datetime.now().timestamp())
            model.loan_time = int_time(model.loan_time)
            model.plan_time = int_time(model.plan_time)
            if model.loan_id:
                loan = await LoanDao.get_info_by_id(query_db, model.loan_id)
                model.cost = model.cost - loan.cost
                if model.cost < 0:
                    model.cost = Decimal(0)
            change = await LoanDao.update(query_db, model)
            # await cls.add_record(query_db, change, model)
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
            info = await LoanDao.get_info_by_id(query_db, id)
            records = await FlowRecordDao.get_records_by_action_id(query_db, info.id, info.check_flow_id)
            detail = {}
            detail.update(info)
            detail['records'] = records
            if not detail:
                raise ServiceException(message="未找到该数据")
            return ModelConverter.convert_to_camel_case(detail)
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        try:
            await LoanDao.del_by_id(db, id)
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def pass_loan(cls, db: AsyncSession, data: OaLoanBaseModel, userId: int):
        try:
            data.check_time = int(datetime.now().timestamp())
            await cls.set_check_uid(db, data, userId)
            await LoanDao.pass_loan(db, data)
            seal = await LoanDao.get_info_by_id(db, data.id)
            await cls.add_record(db, seal, data, userId)
            await db.commit()
            return CrudResponseModel(is_success=True, message='审核通过成功')
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def reject_loan(cls, db: AsyncSession, data: OaLoanBaseModel, userId: int):
        try:
            data.check_time = int(datetime.now().timestamp())
            await cls.set_check_uid(db, data, userId)
            await LoanDao.reject_loan(db, data)
            seal = await LoanDao.get_info_by_id(db, data.id)
            await cls.add_record(db, seal, data, userId)
            await db.commit()
            return CrudResponseModel(is_success=True, message='审核拒绝成功')
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def cancel_loan(cls, db: AsyncSession, data: OaLoanBaseModel, userId: int):
        try:
            await cls.set_check_uid(db, data, userId)
            await LoanDao.cancel_loan(db, data)
            loan = await LoanDao.get_info_by_id(db, data.id)
            await cls.add_record(db, loan, data, userId)
            await db.commit()
            return CrudResponseModel(is_success=True, message='撤销申请成功')
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def pay_loan(cls, db: AsyncSession, data: OaLoanBaseModel, userId: int):
        try:
            await LoanDao.pay_loan(db, data, userId)
            await db.commit()
            return CrudResponseModel(is_success=True, message='打款成功')
        except Exception as e:
            await db.rollback()
            return CrudResponseModel(is_success=False, message='打款失败')

    @classmethod
    async def back_loan(cls, db: AsyncSession, data: OaLoanBaseModel, userId: int):
        try:
            await LoanDao.back_loan(db, data, userId)
            await db.commit()
            return CrudResponseModel(is_success=True, message='还款成功')
        except Exception as e:
            await db.rollback()
            return CrudResponseModel(is_success=False, message='还款失败')

    @classmethod
    async def add_record(cls, db: AsyncSession, change: OaFlowRecordBaseModel, model: OaLoanBaseModel, userId: int):
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
            record.content = model.content
            record.check_time = int(datetime.now().timestamp())
            await FlowRecordDao.add(db, record)
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def set_check_uid(cls, query_db: AsyncSession, query_object: OaLoanBaseModel, userId: int):
        db_model = await LoanDao.get_info_by_id(query_db, query_object.id)
        if userId not in db_model.check_history_uids.split(','):
            query_object.check_history_uids = ','.join([str(userId), db_model.check_history_uids])
        query_object.check_last_uid = str(userId)
