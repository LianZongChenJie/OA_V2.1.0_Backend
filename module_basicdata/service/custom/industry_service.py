from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from exceptions.exception import ServiceException
from common.vo import PageModel, CrudResponseModel
from typing import Any
from datetime import datetime

from module_basicdata.dao.custom.industry_dao import IndustryDao
from module_basicdata.entity.vo.custom.industry_vo import IndustryPageQueryModel, OaIndustryBaseModel


class IndustryService:
    @classmethod
    async def get_industry_list_service(cls, query_db: AsyncSession, query_object: IndustryPageQueryModel,
                                    data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel[
                                                                                                 OaIndustryBaseModel] | \
                                                                                             list[dict[str, Any]]:
        query_list = await IndustryDao.get_cost_cate_list(query_db, query_object, data_scope_sql, is_page)
        if is_page:
            industry_list_result = PageModel[OaIndustryBaseModel](**{
                **query_list.model_dump(by_alias=True)
            })
        else:
            industry_list_result = []
            if query_list:
                industry_list_result = [{**row} for row in query_list]
        return industry_list_result

    @classmethod
    async def add_industry_service(cls, query_db: AsyncSession, model: OaIndustryBaseModel) -> CrudResponseModel:
        try:
            model.create_time = int(datetime.now().timestamp())
            model.status = 1
            await IndustryDao.add_db_industry(query_db, model)
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def update_industry_service(cls, query_db: AsyncSession, model: OaIndustryBaseModel):
        try:
            model.update_time = int(datetime.now().timestamp())
            await IndustryDao.update_industry(query_db, model)
            return CrudResponseModel(is_success=True, message='更新成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def change_status_industry_service(cls, query_db: AsyncSession, model: OaIndustryBaseModel):
        try:
            await IndustryDao.change_status_industry(query_db, model)
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def get_industry_info_service(cls, query_db: \
            AsyncSession, id: int) -> OaIndustryBaseModel:
        try:
            industry_info = await IndustryDao.get_industry_info(query_db, id)
            if not industry_info:
                raise ServiceException(message="未找到该数据")
            return industry_info
        except Exception as e:
            await query_db.rollback()
            raise e
        pass