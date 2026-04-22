from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.dao.official_docs_dao import OfficialDocsDao
from module_admin.entity.do.log_do import SysOperLog
from module_administrative.dao.seal_dao import SealDao
from module_basicdata.dao.public.check_dao import CheckDao
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

from utils.camel_converter import ModelConverter
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
        try:
            datas = await OperationLogDao.get_view_log(query_db, create_time)
            data_list = []
            for data in datas:
                data_list.append(dict(data))
            return ModelConverter.convert_to_camel_case(data_list)
        except Exception as e:
            await query_db.rollback()
            raise e
    @classmethod
    async def get_last_data(cls, db:AsyncSession,user_name:str) -> dict:
        """
        获取用户昨天和今天操作数据统计
        :param user_name:
        :param db:
        :return:
        """
        today = datetime.today()
        yesterday = today - timedelta(days=1)
        today = today.strftime('%Y-%m-%d')
        yesterday = yesterday.strftime('%Y-%m-%d')
        sql = 'SELECT HOUR(oper_time) AS hour, COUNT(*) AS count FROM sys_oper_log WHERE oper_name = :user_name AND DATE(oper_time) = :param_time GROUP BY HOUR(oper_time) ORDER BY hour ASC'
        try:
            today_data = await CheckDao.execute_list_sql(db, sql, {'user_name': user_name, 'param_time': today})
            yesterday_data = await CheckDao.execute_list_sql(db, sql, {'user_name': user_name, 'param_time': yesterday})
            today_data = await cls.get_user_info(today_data)
            yesterday_data = await cls.get_user_info(yesterday_data)
            return {'today': today_data, 'yesterday': yesterday_data}
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def get_user_info(cls, hours : list) -> list:
        """
        获取用户信息
        :param hours:小时数据数组
        :param db:
        :return:
        """
        datas = []
        for time in range(24):
            if time < 24:
                for hour in hours:
                    if hour['hour']  == time:
                        datas.append(hour['count'])
                else:
                    datas.append(0)
        return datas

    @classmethod
    async def get_year_log(cls, query_db: AsyncSession) -> dict:
        """
          获取访问记录数据
          """
        result = await OperationLogDao.get_year_log(query_db)

        return result





