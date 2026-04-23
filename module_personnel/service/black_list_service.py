from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from common.constant import CommonConstant
from exceptions.exception import ServiceException
from module_personnel.dao.black_list_dao import BlackListDao
from sqlalchemy.sql import ColumnElement
from module_personnel.entity.vo.black_list_vo import OaBlacklistBaseModel, OaBlacklistPageQueryModel
from common.vo import PageModel, CrudResponseModel
from datetime import datetime

from utils.camel_converter import ModelConverter


class BlackListService:
    @classmethod
    async def get_page_list_service(cls, query_db: AsyncSession, query_object: OaBlacklistPageQueryModel,
                                    data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel[
                                                                                                 OaBlacklistBaseModel] | \
                                                                                             list[dict[str, Any]]:
        query_list = await BlackListDao.get_page_list(query_db, query_object, data_scope_sql, is_page)
        if is_page:
            row_list = []
            for row in query_list.rows:
                row = dict(row)
                row.update(row['OaBlacklist'].to_dict())
                row.pop('OaBlacklist')
                row_list.append(ModelConverter.convert_to_camel_case(row))
            query_list.rows = row_list
            result_list = query_list
        else:
            result_list = []
            if query_list:
                result_list = [{**row} for row in query_list]
        return result_list

    @classmethod
    async def add_service(cls, query_db: AsyncSession, model: OaBlacklistBaseModel) -> CrudResponseModel:
        try:
            model.create_time = int(datetime.now().timestamp())
            await BlackListDao.add(query_db, model)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def update_service(cls, query_db: AsyncSession, model: OaBlacklistBaseModel) -> CrudResponseModel:
        try:
            model.update_time = int(datetime.now().timestamp())
            change = await BlackListDao.update(query_db, model)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='修改成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass


    @classmethod
    async def get_info_service(cls, query_db: \
            AsyncSession, id: int) -> OaBlacklistBaseModel:
        try:
            info = await BlackListDao.get_info_by_id(query_db, id)
            if not info:
                raise ServiceException(message="未找到该数据")
            return info
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def check_unique_services(cls, query_db: AsyncSession, page_object: OaBlacklistBaseModel) -> bool:
        """
        校验用户名是否唯一service

        :param query_db: orm对象
        :param page_object: 用户对象
        :return: 校验结果
        """
        title = -1 if page_object.uid is None else page_object.uid
        model = await BlackListDao.get_info_by_uid(query_db, page_object)
        if model and model.id == page_object.id:
            return CommonConstant.UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        try:
            await BlackListDao.del_by_id(db, id)
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await db.rollback()
            raise e
