from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from exceptions.exception import ServiceException
from module_basicdata.dao.public.flow_cate_dao import FlowCateDao
from module_basicdata.dao.public.flow_step_dao import OaFlowStepDao
from module_finance.dao.invoice_dao import InvoiceDao
from module_finance.entity.do.invoice_do import OaInvoiceIncome
from module_personnel.dao.flow_record_dao import FlowRecordDao
from sqlalchemy.sql import ColumnElement
from module_finance.entity.vo.invoice_vo import OaInvoiceBaseModel, \
    OaInvoicePageQueryModel, OaInvoiceDetailModel, OaInvoiceIncomeDetailModel
from common.vo import PageModel, CrudResponseModel
from datetime import datetime

from module_personnel.entity.vo.flow_record_vo import OaFlowRecordBaseModel
from utils.camel_converter import ModelConverter
from utils.timeformat import int_time


class InvoiceService:
    @classmethod
    async def get_page_list_service(cls, query_db: AsyncSession, query_object: OaInvoicePageQueryModel,
                                    data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel[
                                                                                                 OaInvoiceBaseModel] | \
                                                                                             list[dict[str, Any]]:
        query_list = await InvoiceDao.get_page_list(query_db, query_object, data_scope_sql, is_page)
        if is_page:
            row_list = []
            for row in query_list.rows:
                row = dict(row)
                row.update(row['OaInvoice'].to_dict())
                row.pop('OaInvoice')
                row_list.append(row)
            query_list.rows = ModelConverter.convert_to_camel_case(row_list)
            result_list = query_list
        else:
            result_list = []
            if query_list:
                result_list = [{**row} for row in query_list]
        return result_list

    @classmethod
    async def add_service(cls, query_db: AsyncSession, model: OaInvoiceBaseModel) -> CrudResponseModel:
        try:
            if model.id:
                model.update_time = int(datetime.now().timestamp())
                model.open_time = int_time(model.open_time)
                model.enter_time = int_time(model.enter_time)
                await InvoiceDao.update(query_db, model)
                return CrudResponseModel(is_success=True, message='修改成功')
            else:
                model.create_time = int(datetime.now().timestamp())
                await InvoiceDao.add(query_db, model)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            return CrudResponseModel(is_success=False, message='操作失败')


    @classmethod
    async def get_info_service(cls, query_db: \
            AsyncSession, id: int) -> dict[str, Any]:
        try:
            info = await InvoiceDao.get_info_by_id(query_db, id)
            records = await FlowRecordDao.get_records_by_action_id(query_db, info['OaInvoice'].id, info['OaInvoice'].check_flow_id)
            detail = OaInvoiceDetailModel(info=None, records=None)
            info = dict(info)
            info.update(info['OaInvoice'].to_dict())
            info.pop('OaInvoice')
            record_list = []
            for record in records:
                record_list.append(record.to_dict())
            records = record_list
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
            info = await InvoiceDao.get_info_by_id(db, id)
            if info['OaInvoice'].check_status !=0 and info['OaInvoice'].check_status !=4:
                raise CrudResponseModel(is_success=False, message='请先撤销申请再删除')
            await InvoiceDao.del_by_id(db, id)
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await db.rollback()
            raise e

    # @classmethod
    # async def review(cls, db: AsyncSession, data: OaInvoiceBaseModel, userId: int):
    #     try:
    #         data.check_time = int(datetime.now().timestamp())
    #         await cls.set_check_uid(db, data, userId)
    #         await InvoiceDao.review(db, data)
    #         invoice = await InvoiceDao.get_info_by_id(db, data.id)
    #         await cls.add_record(db, invoice, data, userId)
    #         await db.commit()
    #         return CrudResponseModel(is_success=True, message='操作成功！')
    #     except Exception as e:
    #         await db.rollback()
    #         return CrudResponseModel(is_success=False, message='操作失败')

    @classmethod
    async def payment(cls, db: AsyncSession, data: OaInvoiceBaseModel, userId: int):
        try:
            info = await InvoiceDao.get_info_by_id(db, data.id)
            if info['OaInvoice'].check_status !=0 or info['OaInvoice'].check_flow_id !=0:
                raise CrudResponseModel(is_success=False, message='请先审批通过再打款')
            await InvoiceDao.payment(db, data, userId)
            await db.commit()
            return CrudResponseModel(is_success=True, message='打款成功')
        except Exception as e:
            await db.rollback()
            return CrudResponseModel(is_success=False, message='打款失败')

    # @classmethod
    # async def back_expense(cls, db: AsyncSession, data: OaInvoiceBaseModel, userId: int):
    #     try:
    #         await InvoiceDao.back_expense(db, data, userId)
    #         await db.commit()
    #         return CrudResponseModel(is_success=True, message='还款成功')
    #     except Exception as e:
    #         await db.rollback()
    #         return CrudResponseModel(is_success=False, message='还款失败')

    @classmethod
    async def add_record(cls, db: AsyncSession, change: OaFlowRecordBaseModel, model: OaInvoiceBaseModel, userId: int):
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
    async def set_check_uid(cls, query_db: AsyncSession, query_object: OaInvoiceBaseModel, userId: int):
        db_model = await InvoiceDao.get_info_by_id(query_db, query_object.id)
        if userId not in db_model.check_history_uids.split(','):
            query_object.check_history_uids = ','.join([str(userId), db_model.check_history_uids])
        query_object.check_last_uid = str(userId)

    @classmethod
    async def open_status(cls, db: AsyncSession, data: OaInvoiceBaseModel):
        try:
            info = await InvoiceDao.get_info_by_id(db, data.id)
            if info['OaInvoice'].enter_status !=2 or info['OaInvoice'].enter_status !=0:
                raise CrudResponseModel(is_success=False, message='仅支持全部回款或未回款！')
            data.open_time = int(datetime.now().timestamp())
            if data.open_status == 2:
                income_count = await InvoiceDao.income_income_count(db, data.id)
                if income_count > 0:
                    return CrudResponseModel(is_success=False, message='存在回款记录，禁止作废')
            if data.open_time:
                data.open_time = int_time(data.open_time)
            await InvoiceDao.open_status(db, data)
            await db.commit()
            return CrudResponseModel(is_success=True, message='操作成功！')
        except Exception as e:
            await db.rollback()
            # raise e
            return CrudResponseModel(is_success=False, message='操作失败')

# -------------------------- 以上为发票到账记录0_0 ----------------------------------

    @classmethod
    async def income_add(cls, db: AsyncSession, data_list: list[OaInvoiceIncome], userId: int):
        try:
            invoice = await InvoiceDao.get_info_by_id(db, data_list[0].invoice_id)
            invoice : OaInvoiceBaseModel =  OaInvoiceBaseModel.model_validate(invoice['OaInvoice'])
            old_amount = invoice.amount
            enter_time = int(datetime.now().timestamp())
            create_time = int(datetime.now().timestamp())
            amount = 0
            for data in data_list:
                amount += data.amount
                data.enter_time = enter_time
                data.admin_id =userId
                data.create_time = create_time
            await InvoiceDao.income_add(db, data_list)
            invoice.enter_amount = amount
            invoice.enter_time = enter_time
            if amount > old_amount:
                return CrudResponseModel(is_success=False, message='回款金额不能大于发票金额')
            if amount < old_amount:
                invoice.enter_status = 1
            else:
                invoice.enter_status = 2
            invoice.update_time = int(datetime.now().timestamp())
            await InvoiceDao.update(db, invoice)
            await db.commit()
            return CrudResponseModel(is_success=True, message='操作成功')
        except Exception as e:
            await db.rollback()
            raise e
            return CrudResponseModel(is_success=False, message='操作失败')

    @classmethod
    async def income_del(cls, db: AsyncSession, ids: list[int]):
        try:
            income = await InvoiceDao.income_get_id(db, ids[0])

            if not income['id']:
                return CrudResponseModel(is_success=False, message='未找到该数据')
            await InvoiceDao.income_del(db, ids)
            invoice_id = income['invoice_id']
            incomes = await InvoiceDao.income_get_incomes(db,invoice_id)
            amount = 0
            enter_time = 0
            for inc in incomes:
                amount += inc.amount
                if inc.enter_time > enter_time:
                    enter_time = inc.enter_time
            invoice = await InvoiceDao.get_info_by_id(db, invoice_id)
            invoice : OaInvoiceBaseModel =  OaInvoiceBaseModel.model_validate(invoice)
            invoice.enter_amount = amount
            invoice.enter_time = enter_time
            if incomes:
                invoice.enter_status = 1
            else:
                invoice.enter_status = 2
            invoice.update_time = int(datetime.now().timestamp())
            await InvoiceDao.update(db, invoice)
            return CrudResponseModel(is_success=True, message='操作成功')
        except Exception as e:
            await db.rollback()
            raise e
            return CrudResponseModel(is_success=False, message='操作失败')

    @classmethod
    async def income_get_incomes(cls, db: AsyncSession, invoice_id: int):
        try:
            incomes = await InvoiceDao.income_get_incomes(db, invoice_id)
            invoice = await InvoiceDao.get_info_by_id(db, invoice_id)
            detail = OaInvoiceIncomeDetailModel(invoice=None, income_list=None)
            detail.income_list = incomes
            detail.invoice = invoice
            return detail
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def income_get_id(cls, db: AsyncSession, user_id: int):
        try:
            income = await InvoiceDao.get_invoice_count(db, user_id)
            return income
        except Exception as e:
            await db.rollback()
            raise e


