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
                                    data_scope_sql: ColumnElement, user_id: int, is_page: bool = False) -> PageModel[
                                                                                                 OaInvoiceBaseModel] | \
                                                                                             list[dict[str, Any]]:
        query_list = await InvoiceDao.get_page_list(query_db, query_object, data_scope_sql, user_id, is_page)
        if is_page:
            row_list = []
            for row in query_list.rows:
                row = dict(row)
                row.update(row['OaInvoice'].to_dict())
                row.pop('OaInvoice')
                if row.get('check_name') is not None:
                    row['check_name'] = row['check_name'].strip(',')
                    row['check_name'] = row['check_name'].replace(',,', ',')
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
                if model.project_id == '':
                    model.project_id = 0
                if model.contract_id == '':
                    model.contract_id = 0
                await InvoiceDao.update(query_db, model)
                return CrudResponseModel(is_success=True, message='编辑成功')
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
            records = await FlowRecordDao.get_records_dict(query_db, info['OaInvoice'].id, info['OaInvoice'].check_flow_id)
            detail = OaInvoiceDetailModel(info=None, records=None)
            info = dict(info)
            info.update(info['OaInvoice'].to_dict())
            info.pop('OaInvoice')
            records = records
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
            if info['OaInvoice'].enter_status !=2:
                return CrudResponseModel(is_success=False, message='仅支持全部回款后执行此操作！')
            if data.open_status == 1:
                if data.open_time:
                    data.open_time = int_time(data.open_time)
            else:
                data.code = ''
                data.open_time = 0
                data.open_admin_id = 0
                data.delivery = ''
            await InvoiceDao.open_status(db, data)
            await db.commit()
            return CrudResponseModel(is_success=True, message='操作成功！')
        except Exception as e:
            await db.rollback()
            raise e
            return CrudResponseModel(is_success=False, message='操作失败')

# -------------------------- 以上为发票到账记录0_0 ----------------------------------

    @classmethod
    async def income_add(cls, db: AsyncSession, data_list: list[OaInvoiceIncome], userId: int):
        try:
            invoice = await InvoiceDao.get_info_by_id(db, data_list[0].invoice_id)
            invoice  = invoice['OaInvoice']
            old_amount = invoice.amount
            enter_time = int(datetime.now().timestamp())
            create_time = int(datetime.now().timestamp())
            amount = 0
            for data in data_list:
                amount += data.amount
                data.enter_time = enter_time
                data.admin_id =userId
                data.create_time = create_time
            amount = amount + invoice.enter_amount

            invoice.enter_amount = amount
            invoice.enter_time = enter_time
            if amount > old_amount:
                raise ServiceException(message='回款金额不能大于发票金额')
            else:
                await InvoiceDao.income_add(db, data_list)
            if amount < old_amount:
                invoice.enter_status = 1
            else:
                invoice.enter_status = 2
            invoice.update_time = int(datetime.now().timestamp())
            await InvoiceDao.update_by_entity(db, invoice)
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
            invoice : OaInvoiceBaseModel =  OaInvoiceBaseModel.model_validate(invoice['OaInvoice'])
            invoice.enter_amount = amount
            invoice.enter_time = enter_time
            if invoice.enter_amount == 0:
                invoice.enter_status = 0
            elif invoice.enter_amount < 0 and invoice.enter_amount < invoice.amount:
                invoice.enter_status = 1
            else:
                invoice.enter_status = 2
            invoice.update_time = int(datetime.now().timestamp())
            if invoice.project_id is None:
                invoice.project_id = 0
            if invoice.contract_id is None:
                invoice.contract_id = 0
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

    @classmethod
    async def get_invoice_incomes_details(cls, db: AsyncSession, query_model: OaInvoicePageQueryModel, data_scope_sql: ColumnElement, is_page: bool = False) -> list[list[dict[str, Any]]]:
        try:
            details = await InvoiceDao.get_invoices_incomes_detail(db, query_model, data_scope_sql, is_page)
            if len(details.rows) > 0:
                row_list = []
                for row in details.rows:
                    row = dict(row)
                    row.update(row['OaInvoiceIncome'].to_dict())
                    row.pop('OaInvoiceIncome')
                    row_list.append(ModelConverter.convert_to_camel_case(row))
                details.rows = ModelConverter.convert_to_camel_case(row_list)
            return details
        except Exception as e:
            await db.rollback()
            raise e

