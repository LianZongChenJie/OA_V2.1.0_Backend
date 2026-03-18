from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from exceptions.exception import ServiceException
from common.vo import PageModel, CrudResponseModel
from typing import Any
from datetime import datetime

from module_basicdata.dao.finance.cost_cate_dao import CostCateDao
from module_basicdata.entity.vo.finance.cost_cate_vo import OaCostCateBaseModel, CostCatePageQueryModel


class CostCateService:
    @classmethod
    async def get_cost_cate_list_service(cls, query_db: AsyncSession, query_object: CostCatePageQueryModel,
                                    data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel[
                                                                                                 OaCostCateBaseModel] | \
                                                                                             list[dict[str, Any]]:
        query_list = await CostCateDao.get_cost_cate_list(query_db, query_object, data_scope_sql, is_page)
        if is_page:
            cost_cate_list_result = PageModel[OaCostCateBaseModel](**{
                **query_list.model_dump(by_alias=True)
            })
        else:
            cost_cate_list_result = []
            if query_list:
                cost_cate_list_result = [{**row} for row in query_list]
        return cost_cate_list_result

    @classmethod
    async def add_cost_cate_service(cls, query_db: AsyncSession, link_model: OaCostCateBaseModel) -> CrudResponseModel:
        try:
            link_model.create_time = int(datetime.now().timestamp())
            await CostCateDao.add_cost_cate(query_db, link_model)
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def update_cost_cate_service(cls, query_db: AsyncSession, link_model: OaCostCateBaseModel):
        try:
            link_model.update_time = int(datetime.now().timestamp())
            await CostCateDao.update_cost_cate(query_db, link_model)
            return CrudResponseModel(is_success=True, message='更新成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def change_status_cost_cate_service(cls, query_db: AsyncSession, model: OaCostCateBaseModel):
        try:
            await CostCateDao.change_status_cost_cate(query_db, model)
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def get_cost_cate_info_service(cls, query_db: \
            AsyncSession, id: int) -> OaCostCateBaseModel:
        try:
            cost_cate_info = await CostCateDao.get_cost_cate_info(query_db, id)
            if not cost_cate_info:
                raise ServiceException(message="未找到该数据")
            return cost_cate_info
        except Exception as e:
            await query_db.rollback()
            raise e
        pass