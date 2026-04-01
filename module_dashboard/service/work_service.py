from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from exceptions.exception import ServiceException
from module_dashboard.dao.work_dao import WorkDao
from sqlalchemy.sql import ColumnElement
from module_dashboard.entity.vo.work_vo import OaWorkBaseModel, OaWorkPageQueryModel, OaWorkQueryModel
from common.vo import PageModel, CrudResponseModel
from datetime import datetime

from utils.camel_converter import ModelConverter
from utils.timeformat import int_time


class WorkService:
    @classmethod
    async def get_page_list_service(cls, query_db: AsyncSession, query_object: OaWorkPageQueryModel,
                                    data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel[
                                                                                                 OaWorkBaseModel] | \
                                                                                             list[dict[str, Any]]:
        query_list = await WorkDao.get_page_list(query_db, query_object, data_scope_sql, is_page)
        if is_page:
            result_list = PageModel[OaWorkBaseModel](**{
                **query_list.model_dump(by_alias=True),
                'rows': [{**row[0]} for row in query_list.rows]
            })
        else:
            result_list = []
            if query_list:
                result_list = ModelConverter.list_time_format(query_list)
        return result_list

    @classmethod
    async def add_service(cls, query_db: AsyncSession, model: OaWorkQueryModel) -> CrudResponseModel:
        try:
            add_model = OaWorkBaseModel(**model.model_dump(exclude_none=True))
            add_model.start_date = int_time(model.start_date)
            add_model.end_date = int_time(model.end_date)
            add_model.create_time = int(datetime.now().timestamp())
            if model.is_send:
                add_model.send_time = int(datetime.now().timestamp())
            await WorkDao.add(query_db, add_model)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def update_service(cls, query_db: AsyncSession, model: OaWorkQueryModel) -> CrudResponseModel:
        try:

            update_model = OaWorkBaseModel(**model.model_dump(exclude_none=True))
            update_model.start_date = int_time(model.start_date)
            update_model.end_date = int_time(model.end_date)
            update_model.update_time = int(datetime.now().timestamp())
            if model.is_send:
                update_model.send_time = int(datetime.now().timestamp())
            await WorkDao.update(query_db, update_model)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='修改成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass


    @classmethod
    async def get_info_service(cls, query_db: \
            AsyncSession, id: int) -> OaWorkBaseModel:
        try:
            info = await WorkDao.get_info_by_id(query_db, id)
            if not info:
                raise ServiceException(message="未找到该日程")
            return info
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        try:
            await WorkDao.del_by_id(db, id)
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await db.rollback()
            raise e