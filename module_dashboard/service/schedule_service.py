from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from exceptions.exception import ServiceException
from module_dashboard.dao.schedule_dao import ScheduleDao
from sqlalchemy.sql import ColumnElement
from module_dashboard.entity.vo.schedule_vo import OaScheduleBaseModel, OaSchedulePageQueryModel
from common.vo import PageModel, CrudResponseModel
from datetime import datetime

from utils.camel_converter import ModelConverter
from utils.timeformat import int_time
from module_dashboard.utils.calendar_utils import SchedulePriority


class ScheduleService:
    @classmethod
    async def get_page_list_service(cls, query_db: AsyncSession, query_object: OaSchedulePageQueryModel,
                                    data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel[
                                                                                                 OaScheduleBaseModel] | \
                                                                                             list[dict[str, Any]]:
        query_list = await ScheduleDao.get_page_list(query_db, query_object, data_scope_sql, is_page)
        if is_page:
            result_list = PageModel[OaScheduleBaseModel](
                **{
                    **query_list.model_dump(by_alias=True),
                    'rows': [{ **row[0]} for row in query_list.rows],
                })
        else:
            result_list = []
            if query_list:
                result_list = ModelConverter.list_time_format(query_list)
        return result_list

    @classmethod
    async def add_service(cls, query_db: AsyncSession, model: OaScheduleBaseModel) -> CrudResponseModel:
        try:
            model.start_time = int_time(model.start_time)
            model.end_time = int_time(model.end_time)
            model.create_time = int(datetime.now().timestamp())
            model.labor_time = (model.end_time - model.start_time)/3600
            await ScheduleDao.add(query_db, model)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def update_service(cls, query_db: AsyncSession, model: OaScheduleBaseModel) -> CrudResponseModel:
        try:
            model.update_time = int(datetime.now().timestamp())
            model.start_time = int_time(model.start_time)
            model.end_time = int_time(model.end_time)
            await ScheduleDao.update(query_db, model)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='修改成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass


    @classmethod
    async def get_info_service(cls, query_db: \
            AsyncSession, id: int) -> OaScheduleBaseModel:
        try:
            info = await ScheduleDao.get_info_by_id(query_db, id)
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
            await ScheduleDao.del_by_id(db, id)
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await db.rollback()
            raise e
    @classmethod
    def safe_get(cls, obj, key, default='未知'):
        """安全获取字典值"""
        if obj and isinstance(obj, dict):
            if key in obj:
                print(obj[key])
            result = obj.get(key, default)
            print(result)
            return result
        return default

    @classmethod
    async def get_calendar_list_service(cls, query_db: AsyncSession, query_object: OaSchedulePageQueryModel,
                                    data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel[
                                                                                                 OaScheduleBaseModel] | \
                                                                                             list[dict[str, Any]]:
        data_list = await cls.get_page_list_service(query_db, query_object, data_scope_sql, is_page)
        calendar_list = []
        for item in data_list.rows:
            calendar_item = {
            'backgroundColor': SchedulePriority(int(item.cid)).back_ground_colors,
            'borderColor': SchedulePriority(int(item.cid)).border_color,
            'end': item.end_time,
            'start': item.start_time,
            'title': item.title,
            'id': item.id,
            'laborTime': item.labor_time
        }
            calendar_list.append(calendar_item)
        return calendar_list

    @classmethod
    async def get_calendar_info_service(cls, query_db: \
            AsyncSession, id: int) -> dict[str, Any]:
        info = await cls.get_info_service(query_db, id)
        return  {
            'backgroundColor': SchedulePriority(int(info.cid)).back_ground_colors,
            'borderColor': SchedulePriority(int(info.cid)).border_color,
            'end': info.end_time,
            'start': info.start_time,
            'title': info.title,
            'id': info.id,
            'laborTime': info.labor_time
        }
