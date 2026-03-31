from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from exceptions.exception import ServiceException
from module_administrative.dao.note_dao import NoteDao
from sqlalchemy.sql import ColumnElement
from module_administrative.entity.vo.note_vo import OaNoteBaseModel, \
    OaNoteQueryPageModel
from common.vo import PageModel, CrudResponseModel
from datetime import datetime


class NoteService:
    @classmethod
    async def get_page_list_service(cls, query_db: AsyncSession, query_object: OaNoteQueryPageModel,
                                    data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel[
                                                                                                 OaNoteBaseModel] | \
                                                                                             list[dict[str, Any]]:
        query_list = await NoteDao.get_page_list(query_db, query_object, data_scope_sql, is_page)
        if is_page:
            result_list = PageModel[OaNoteBaseModel](**{
                **query_list.model_dump(by_alias=True)
            })
        else:
            result_list = []
            if query_list:
                result_list = [{**row} for row in query_list]
        return result_list

    @classmethod
    async def add_service(cls, query_db: AsyncSession, model: OaNoteBaseModel) -> CrudResponseModel:
        if model.id:
            return await cls.update_service(query_db, model)

        try:
            model.create_time = int(datetime.now().timestamp())
            model.status = 1
            await NoteDao.add(query_db, model)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def update_service(cls, query_db: AsyncSession, model: OaNoteBaseModel) -> CrudResponseModel:
        try:
            model.update_time = int(datetime.now().timestamp())
            await NoteDao.update(query_db, model)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='修改成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass


    @classmethod
    async def get_info_service(cls, query_db: \
            AsyncSession, id: int) -> OaNoteBaseModel:
        try:
            info = await NoteDao.get_info_by_id(query_db, id)
            if not info:
                raise ServiceException(message="未找到该公告")
            return info
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        try:
            await NoteDao.del_by_id(db, id)
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await db.rollback()
            raise e
