from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.dao.official_docs_dao import OfficialDocsDao
from module_administrative.dao.seal_dao import SealDao
from module_finance.dao.expense_dao import ExpenseDao
from module_finance.dao.invoice_dao import InvoiceDao
from module_finance.dao.ticket_dao import TicketDao
from module_admin.dao.customer_dao import CustomerDao
from module_contract.dao.contract_dao import ContractDao
from module_contract.dao.purchase_dao import PurchaseDao
from module_main.entity.vo.main_count_vo import CountBaseModel, AwaitReviewBaseModel
from module_project.dao.project_dao import ProjectDao
from module_project.dao.project_task_dao import ProjectTaskDao
from module_admin.dao.log_dao import OperationLogDao

from datetime import datetime, timedelta

from utils.timeformat import format_timestamp


class MainService:
    @classmethod
    async def get_count(cls, query_db: \
            AsyncSession, user_id: int) -> dict:
        try:
            expense = await ExpenseDao.get_count(query_db, user_id)
            invoice = await InvoiceDao.get_invoice_count(query_db, user_id)
            ticket = await TicketDao.get_ticket_count(query_db, user_id)
            customer = await CustomerDao.get_customer_count(query_db)
            contract = await ContractDao.get_contract_count(query_db, user_id)
            purchase = await PurchaseDao.get_purchase_count(query_db, user_id)
            project = await ProjectDao.get_project_count(query_db, user_id)
            project_task = await ProjectTaskDao.get_project_task_count(query_db, user_id, status=3)
            return CountBaseModel(expense=expense, invoice=invoice, ticket=ticket,
                                 customer=customer, contract=contract, purchase=purchase,
                                 project=project, projectTask=project_task)
        except Exception as e:
            await query_db.rollback()
            raise e


    @classmethod
    async def get_await_review(cls, query_db: \
            AsyncSession, user_id: int) -> dict:
        try:
            official_doc = await OfficialDocsDao.get_official_count(query_db, user_id)
            seal = await SealDao.get_wait_check_count(query_db, user_id)
            contract = await ContractDao.get_wait_check_count(query_db, user_id)
            purchase = await PurchaseDao.get_wait_check_count(query_db, user_id)
            expense = await ExpenseDao.get_wait_check_count(query_db, user_id)
            ticket = await TicketDao.get_wait_check_count(query_db, user_id)
            invoice = await InvoiceDao.get_wait_check_count(query_db, user_id)
            project_task = await ProjectTaskDao.get_project_task_count(query_db, user_id, status=2)
            return AwaitReviewBaseModel(officialDoc=official_doc, seal=seal,
                                        contract=contract, purchase=purchase,
                                        expense=expense, ticket=ticket,
                                        invoice=invoice, projectTask=project_task)
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def get_view_log(cls, query_db: AsyncSession) -> dict:
        """
        获取最近30天用户操作日志数据
        :param query_db:
        :return:
        """
        create_time = format_timestamp(int((datetime.now() - timedelta(days=30)).timestamp()))



