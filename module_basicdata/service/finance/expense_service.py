from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from module_basicdata.dao.finance.expense_cate_dao import ExpenseCateDao
from module_basicdata.entity.vo.finance.expense_cate_vo import ExpenseCatePageQueryModel, OaExpenseCateBaseModel
from exceptions.exception import ServiceException
from common.vo import PageModel, CrudResponseModel
from typing import Any
from datetime import datetime


class ExpenseCateService:
    @classmethod
    async def get_cost_cate_list_service(cls, query_db: AsyncSession, query_object: ExpenseCatePageQueryModel,
                                    data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel[
                                                                                                 OaExpenseCateBaseModel] | \
                                                                                             list[dict[str, Any]]:
        query_list = await ExpenseCateDao.get_expense_cate_list(query_db, query_object, data_scope_sql, is_page)
        if is_page:
            expense_cate_list_result = PageModel[OaExpenseCateBaseModel](**{
                **query_list.model_dump(by_alias=True)
            })
        else:
            expense_cate_list_result = []
            if query_list:
                expense_cate_list_result = [{**row} for row in query_list]
        return expense_cate_list_result

    @classmethod
    async def add_expense_cate_service(cls, query_db: AsyncSession, link_model: OaExpenseCateBaseModel) -> CrudResponseModel:
        try:
            link_model.create_time = int(datetime.now().timestamp())
            await ExpenseCateDao.add_expense_cate(query_db, link_model)
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def update_expense_cate_service(cls, query_db: AsyncSession, link_model: OaExpenseCateBaseModel):
        try:
            link_model.update_time = int(datetime.now().timestamp())
            await ExpenseCateDao.update_expense_cate(query_db, link_model)
            return CrudResponseModel(is_success=True, message='更新成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def change_status_expense_cate_service(cls, query_db: AsyncSession, model: OaExpenseCateBaseModel):
        try:
            await ExpenseCateDao.change_status_expense_cate(query_db, model)
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def get_expense_cate_info_service(cls, query_db: \
            AsyncSession, id: int) -> OaExpenseCateBaseModel:
        try:
            cost_cate_info = await ExpenseCateDao.get_expense_cate_info(query_db, id)
            if not cost_cate_info:
                raise ServiceException(message="未找到该数据")
            return cost_cate_info
        except Exception as e:
            await query_db.rollback()
            raise e
        pass