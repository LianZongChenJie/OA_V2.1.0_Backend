from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from exceptions.exception import ServiceException
from module_finance.dao.ticket_dao import TicketDao
from module_finance.entity.do.ticket_do import OaTicket
from module_personnel.dao.flow_record_dao import FlowRecordDao
from sqlalchemy.sql import ColumnElement
from module_finance.entity.vo.ticket_vo import OaTicketBaseModel, \
    OaTicketPageQueryModel, OaTicketPaymentBaseModel
from common.vo import PageModel, CrudResponseModel
from datetime import datetime
from utils.camel_converter import ModelConverter
from utils.timeformat import int_time


class TicketService:
    @classmethod
    async def get_page_list_service(cls, query_db: AsyncSession, query_object: OaTicketPageQueryModel,
                                    data_scope_sql: ColumnElement,user_id:int, is_page: bool = False) -> PageModel[
                                                                                                 OaTicketBaseModel] | \
                                                                                             list[dict[str, Any]]:
        query_list = await TicketDao.get_page_list(query_db, query_object, data_scope_sql, user_id, is_page)
        if is_page:
            row_list = []
            for row in query_list.rows:
                row = dict(row)
                row.update(row['OaTicket'].to_dict())
                row.pop('OaTicket')
                row_list.append(ModelConverter.convert_to_camel_case(row))
            query_list.rows = row_list
            result_list = ModelConverter.convert_to_camel_case(query_list)
        else:
            result_list = []
            if query_list:
                result_list = [{**row} for row in query_list]
        return result_list

    @classmethod
    async def add_service(cls, query_db: AsyncSession, model: OaTicketBaseModel) -> CrudResponseModel:
        try:
            if model.id:
                ticket = await TicketDao.get_info_by_id(query_db, model.id)
                ticket = ticket['OaTicket']
                if ticket.check_status !=0 and ticket.check_last_status !=4:
                    return CrudResponseModel(is_success=False, message='当前收票发票已审核，请操作审核相关功能！')
                model.update_time = int(datetime.now().timestamp())
                model.open_time = int_time(model.open_time)
                model.pay_time = int_time(model.pay_time)
                if model.project_id == '':
                    model.project_id = 0
                if model.purchase_id == '':
                    model.purchase_id = 0
                await TicketDao.update(query_db, model)
                return CrudResponseModel(is_success=True, message='修改成功')
            else:
                model.create_time = int(datetime.now().timestamp())
                model.open_time = int_time(model.open_time)
                model.pay_time = int_time(model.pay_time)
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
            records = await FlowRecordDao.get_records_dict(query_db, info['OaTicket'].id, info['OaTicket'].check_flow_id)
            info = dict(info)
            info.update(info['OaTicket'].to_dict())
            info.pop('OaTicket')
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
            ticket = await TicketDao.get_info_by_id(db, id)
            ticket = ticket['OaTicket']
            if ticket.check_status !=0 and ticket.check_status !=4:
                return CrudResponseModel(is_success=False, message='当前收票发票已审核，请操作审核相关功能！')
            await TicketDao.del_by_id(db, id)
            return CrudResponseModel(is_success=True, message='删除成功')
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
            ticket = await TicketDao.get_info_by_id(db, data.id)
            ticket = ticket['OaTicket']
            if ticket.pay_status != 0:
                return CrudResponseModel(is_success=False, message='当前收票发票已付款，无法作废')
            if ticket.check_status !=0 and ticket.check_status !=4:
                return CrudResponseModel(is_success=False, message='当前收票发票已审核，请操作审核相关功能！')
            if data.open_time:
                data.open_time = int_time(data.open_time)
            else:
                data.open_time = int(datetime.now().timestamp())
            await TicketDao.open_status(db, data)
            await db.commit()
            return CrudResponseModel(is_success=True, message='操作成功！')
        except Exception as e:
            await db.rollback()
            raise e
            return CrudResponseModel(is_success=False, message='操作失败')

# -------------------------- 以上为发票到账记录0_0 ----------------------------------

    @classmethod
    async def payment_add(cls, db: AsyncSession, data_list: list[OaTicketPaymentBaseModel], userId: int):
        try:
            ticket = await TicketDao.get_info_by_id(db, data_list[0].ticket_id)
            ticket = ticket['OaTicket']
            ticket_dict = ticket.to_dict()
            if ticket.open_status != 1:
                return CrudResponseModel(is_success=False, message='当前收票发票已作废，无法付款')
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
            ticket_dict['pay_amount'] = amount
            ticket_dict['pay_time'] = pay_time
            if amount > ticket_dict['amount']:
                return CrudResponseModel(is_success=False, message='付款金额不能大于发票金额')
            if amount < ticket_dict['pay_amount']:
                ticket_dict['pay_status'] = 1
            else:
                ticket_dict['pay_status'] = 2
            update_model = OaTicket(**ticket_dict)
            update_model.update_time = int(datetime.now().timestamp())
            update_model.delete_time = 0
            await TicketDao.update_by_entity(db, update_model)
            await db.commit()
            return CrudResponseModel(is_success=True, message='操作成功')
        except Exception as e:
            await db.rollback()
            raise e
            return CrudResponseModel(is_success=False, message='操作失败')

    @classmethod
    async def payment_del(cls, db: AsyncSession, ids: list[int]):
        try:
            ticket_id = await TicketDao.get_ticket_by_payment_id(db, ids[0])
            ticket = await TicketDao.get_info_by_id(db, ticket_id['ticket_id'])
            if not ticket:
                return CrudResponseModel(is_success=False, message='数据不存在')
            ticket = ticket['OaTicket']
            if ticket.open_status != 1:
                return CrudResponseModel(is_success=False, message='当前收票发票已作废，无法删除付款')
            if ticket.pay_status == 0:
                return CrudResponseModel(is_success=False, message='当前收票未付款，没有付款记录')
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
            ticket = ticket['OaTicket']
            ticket.pay_amount = amount
            ticket.pay_time = pay_time
            if payments:
                ticket.pay_status = 1
            else:
                ticket.pay_status = 0
            ticket.update_time = int(datetime.now().timestamp())
            await TicketDao.update_by_entity(db, ticket)
            return CrudResponseModel(is_success=True, message='操作成功')
        except Exception as e:
            await db.rollback()
            raise e
            return CrudResponseModel(is_success=False, message='操作失败')

    @classmethod
    async def ticket_get_payment(cls, db: AsyncSession, ticket_id: int):
        try:
            payments = await TicketDao.ticket_get_payments(db, ticket_id)
            ticket = await TicketDao.get_info_dict(db, ticket_id)
            detail = {}
            detail.update(ticket)
            payment_list = []
            if payments is not None:
                for pay in payments:
                    pay = pay.to_dict()
                    payment_list.append(pay)
            detail['payments'] = payment_list
            return ModelConverter.convert_to_camel_case(detail)
        except Exception as e:
            await db.rollback()
            raise e
    @classmethod
    async def ticket_get_payment_list(cls, db: AsyncSession, query_object: OaTicketBaseModel, data_scope_sql: ColumnElement,
                            is_page: bool = False):
        try:
            query_list = await TicketDao.ticket_get_payment_list(db, query_object, data_scope_sql,is_page)
            if is_page:
                row_list = []
                for row in query_list.rows:
                    row = dict(row)
                    row.update(row['OaTicketPayment'].to_dict())
                    row.pop('OaTicketPayment')
                    row_list.append(ModelConverter.convert_to_camel_case(row))
                query_list.rows = row_list
                return query_list
        except Exception as e:
            await db.rollback()
            raise e
