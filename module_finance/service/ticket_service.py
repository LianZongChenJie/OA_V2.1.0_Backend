from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from exceptions.exception import ServiceException
from module_basicdata.dao.public.flow_cate_dao import FlowCateDao
from module_basicdata.dao.public.flow_step_dao import OaFlowStepDao
from module_finance.dao.ticket_dao import TicketDao
from module_finance.entity.do.ticket_do import OaTicketPayment
from module_personnel.dao.flow_record_dao import FlowRecordDao
from sqlalchemy.sql import ColumnElement
from module_finance.entity.vo.ticket_vo import OaTicketBaseModel, \
    OaTicketPageQueryModel, OaTicketPayMentDetailModel
from common.vo import PageModel, CrudResponseModel
from datetime import datetime

from module_personnel.entity.vo.flow_record_vo import OaFlowRecordBaseModel
from utils.camel_converter import ModelConverter
from utils.timeformat import int_time


class TicketService:
    @classmethod
    async def get_page_list_service(cls, query_db: AsyncSession, query_object: OaTicketPageQueryModel,
                                    data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel[
                                                                                                 OaTicketBaseModel] | \
                                                                                             list[dict[str, Any]]:
        query_list = await TicketDao.get_page_list(query_db, query_object, data_scope_sql, is_page)
        if is_page:
            result_list = PageModel[OaTicketBaseModel](**{
                **query_list.model_dump(by_alias=True)
            })
        else:
            result_list = []
            if query_list:
                result_list = [{**row} for row in query_list]
        return result_list

    @classmethod
    async def add_service(cls, query_db: AsyncSession, model: OaTicketBaseModel) -> CrudResponseModel:
        try:
            if model.id:
                model.update_time = int(datetime.now().timestamp())
                model.open_time = int_time(model.open_time)
                model.pay_time = int_time(model.pay_time)
                await TicketDao.update(query_db, model)
                return CrudResponseModel(is_success=True, message='修改成功')
            else:
                model.create_time = int(datetime.now().timestamp())
                await TicketDao.add(query_db, model)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e
            return CrudResponseModel(is_success=False, message='操作失败')


    @classmethod
    async def get_info_service(cls, query_db: \
            AsyncSession, id: int) -> dict[str, Any]:
        try:
            info = await TicketDao.get_info_by_id(query_db, id)
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
            await TicketDao.del_by_id(db, id)
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def review(cls, db: AsyncSession, data: OaTicketBaseModel, userId: int):
        try:
            data.check_time = int(datetime.now().timestamp())
            await cls.set_check_uid(db, data, userId)
            await TicketDao.review(db, data)
            invoice = await TicketDao.get_info_by_id(db, data.id)
            await cls.add_record(db, invoice, data, userId)
            await db.commit()
            return CrudResponseModel(is_success=True, message='操作成功！')
        except Exception as e:
            await db.rollback()
            return CrudResponseModel(is_success=False, message='操作失败')

    # @classmethod
    # async def payment(cls, db: AsyncSession, data: OaTicketBaseModel, userId: int):
    #     try:
    #         await TicketDao.payment(db, data, userId)
    #         await db.commit()
    #         return CrudResponseModel(is_success=True, message='打款成功')
    #     except Exception as e:
    #         await db.rollback()
    #         return CrudResponseModel(is_success=False, message='打款失败')
    #
    # @classmethod
    # async def back_expense(cls, db: AsyncSession, data: OaTicketBaseModel, userId: int):
    #     try:
    #         await TicketDao.back_expense(db, data, userId)
    #         await db.commit()
    #         return CrudResponseModel(is_success=True, message='还款成功')
    #     except Exception as e:
    #         await db.rollback()
    #         return CrudResponseModel(is_success=False, message='还款失败')

    @classmethod
    async def add_record(cls, db: AsyncSession, change: OaFlowRecordBaseModel, model: OaTicketBaseModel, userId: int):
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
    async def set_check_uid(cls, query_db: AsyncSession, query_object: OaTicketBaseModel, userId: int):
        db_model = await TicketDao.get_info_by_id(query_db, query_object.id)
        if userId not in db_model.check_history_uids.split(','):
            query_object.check_history_uids = ','.join([str(userId), db_model.check_history_uids])
        query_object.check_last_uid = str(userId)

    @classmethod
    async def open_status(cls, db: AsyncSession, data: OaTicketBaseModel):
        try:
            data.open_time = int(datetime.now().timestamp())
            if data.open_status == 2:
                income_count = await TicketDao.payment_count(db, data.id)
                if income_count > 0:
                    return CrudResponseModel(is_success=False, message='存在付款记录，禁止作废')
            if data.open_time:
                data.open_time = int_time(data.open_time)
            await TicketDao.open_status(db, data)
            await db.commit()
            return CrudResponseModel(is_success=True, message='操作成功！')
        except Exception as e:
            await db.rollback()
            raise e
            return CrudResponseModel(is_success=False, message='操作失败')

# -------------------------- 以上为发票到账记录0_0 ----------------------------------

    @classmethod
    async def payment_add(cls, db: AsyncSession, data_list: list[OaTicketPayment], userId: int):
        try:
            ticket = await TicketDao.get_info_by_id(db, data_list[0].ticket_id)
            ticket : OaTicketBaseModel =  OaTicketBaseModel.model_validate(ticket)
            old_amount = ticket.pay_amount if ticket.pay_amount else 0
            pay_time = int(datetime.now().timestamp())
            create_time = int(datetime.now().timestamp())
            amount = 0
            for data in data_list:
                amount += data.amount
                data.pay_time = pay_time
                data.admin_id =userId
                data.create_time = create_time
            await TicketDao.payment_add(db, data_list)
            ticket.pay_amount = amount
            ticket.pay_time = pay_time
            if amount > ticket.amount:
                return CrudResponseModel(is_success=False, message='付款金额不能大于发票金额')
            if amount < ticket.amount:
                ticket.pay_status = 1
            else:
                ticket.pay_status = 2
            ticket.update_time = int(datetime.now().timestamp())
            await TicketDao.update(db, ticket)
            await db.commit()
            return CrudResponseModel(is_success=True, message='操作成功')
        except Exception as e:
            await db.rollback()
            raise e
            return CrudResponseModel(is_success=False, message='操作失败')

    @classmethod
    async def payment_del(cls, db: AsyncSession, ids: list[int]):
        try:
            ticket_id = await TicketDao.payment_get_id(db, ids[0])
            await TicketDao.payment_del(db, ids)
            payments = await TicketDao.ticket_get_payments(db,ticket_id)
            amount = 0
            pay_time = 0
            for inc in payments:
                amount += inc.amount
                if inc.pay_time > pay_time:
                    pay_time = inc.pay_time
            ticket = await TicketDao.get_info_by_id(db, ticket_id)
            ticket : OaTicketBaseModel =  OaTicketBaseModel.model_validate(ticket)
            ticket.pay_amount = amount
            ticket.pay_time = pay_time
            if payments:
                ticket.pay_status = 1
            else:
                ticket.pay_status = 0
            ticket.update_time = int(datetime.now().timestamp())
            await TicketDao.update(db, ticket)
            return CrudResponseModel(is_success=True, message='操作成功')
        except Exception as e:
            await db.rollback()
            raise e
            return CrudResponseModel(is_success=False, message='操作失败')

    @classmethod
    async def ticket_get_payment(cls, db: AsyncSession, invoice_id: int):
        try:
            incomes = await TicketDao.ticket_get_payments(db, invoice_id)
            invoice = await TicketDao.get_info_by_id(db, invoice_id)
            detail = OaTicketPayMentDetailModel(invoice=None, ticket_list=None)
            detail.ticket_list = incomes
            detail.invoice = invoice
            return detail
        except Exception as e:
            await db.rollback()
            raise e

