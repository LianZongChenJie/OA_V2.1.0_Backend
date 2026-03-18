from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from exceptions.exception import ServiceException
from common.vo import PageModel, CrudResponseModel
from typing import Any
from datetime import datetime

from module_basicdata.dao.public.links_dao import LinksDao
from module_basicdata.entity.vo.public.links_vo import OaLinksBaseModel, OaLinksPageQueryModel


class LinksService:
    @classmethod
    async def get_link_list_service(cls, query_db: AsyncSession, query_object: OaLinksPageQueryModel, data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel[OaLinksBaseModel] | list[dict[str, Any]]:
        query_list = await LinksDao.get_link_list(query_db, query_object, data_scope_sql, is_page)
        if is_page:
            flow_cate_list_result = PageModel[OaLinksBaseModel](**{
                **query_list.model_dump(by_alias=True)
            })
        else:
            flow_cate_list_result = []
            if query_list:
                flow_cate_list_result = [{**row} for row in query_list]
        return flow_cate_list_result

    @classmethod
    async def add_link_service(cls, query_db: AsyncSession, link_model: OaLinksBaseModel) -> CrudResponseModel:
        try:
            link_model.create_time = int(datetime.now().timestamp())
            await LinksDao.add_link(query_db, link_model)
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def update_link_service(cls, query_db: AsyncSession, link_model: OaLinksBaseModel):
        try:
            link_model.update_time = int(datetime.now().timestamp())
            await LinksDao.update_link(query_db, link_model)
            return CrudResponseModel(is_success=True, message='更新成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass
    @classmethod
    async def delete_link_service(cls, query_db: AsyncSession, id: int):
        try:
            await LinksDao.delete_link(query_db, id)
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def get_link_info_service(cls, query_db: \
                                          AsyncSession, id: int) -> OaLinksBaseModel:
        try:
            enterprise_info = await LinksDao.get_link_info(query_db, id)
            if not enterprise_info:
                raise ServiceException(message="未找到该数据")
            return enterprise_info
        except Exception as e:
            await query_db.rollback()
            raise e
        pass