from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from exceptions.exception import ServiceException
from module_basicdata.dao.public.enterprise_dao import EnterpriseDao
from module_basicdata.entity.vo.public.enterprise_vo import OaEnterpriseBaseModel, OaEnterprisePageModel
from common.vo import PageModel, CrudResponseModel
from typing import Any
from datetime import datetime

class EnterpriseService:
    @classmethod
    async def get_enterprise_list_service(cls, query_db: AsyncSession, query_object: OaEnterprisePageModel, data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel[OaEnterpriseBaseModel] | list[dict[str, Any]]:
        query_list = await EnterpriseDao.get_enterprise_list(query_db, query_object, data_scope_sql, is_page)
        if is_page:
            flow_cate_list_result = PageModel[OaEnterpriseBaseModel](**{
                **query_list.model_dump(by_alias=True)
            })
        else:
            flow_cate_list_result = []
            if query_list:
                flow_cate_list_result = [{**row} for row in query_list]
        return flow_cate_list_result

    @classmethod
    async def add_enterprise_service(cls, query_db: AsyncSession, enterprise_model: OaEnterpriseBaseModel) -> CrudResponseModel:
        try:
            enterprise_model.create_time = int(datetime.now().timestamp() * 1000)
            await EnterpriseDao.add_enterprise(query_db, enterprise_model)
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def update_enterprise_service(cls, query_db: AsyncSession, enterprise_model: OaEnterpriseBaseModel):
        try:
            enterprise_model.update_time = int(datetime.now().timestamp() * 1000)
            await EnterpriseDao.update_enterprise(query_db, enterprise_model)
            return CrudResponseModel(is_success=True, message='更新成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass
    @classmethod
    async def delete_enterprise_service(cls, query_db: AsyncSession, id: int):
        try:
            await EnterpriseDao.delete_enterprise(query_db, id)
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def get_enterprise_info_service(cls, query_db:
                                          AsyncSession, id: int) -> OaEnterpriseBaseModel:
        try:
            enterprise_info = await EnterpriseDao.get_enterprise_info(query_db, id)
            if not enterprise_info:
                raise ServiceException(message="未找到该数据")
            return enterprise_info
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def change_status_enterprise_service(cls, query_db: AsyncSession, model: OaEnterpriseBaseModel):
        try:
            await EnterpriseDao.change_status_enterprise(query_db, model)
            return CrudResponseModel(is_success=True, message='状态变更成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass