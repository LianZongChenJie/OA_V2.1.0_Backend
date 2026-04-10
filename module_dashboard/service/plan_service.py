from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from exceptions.exception import ServiceException
from module_dashboard.dao.plan_dao import PlanDao
from sqlalchemy.sql import ColumnElement
from module_dashboard.entity.vo.plan_vo import OaPlanBaseModel, OaPlanQueryModel
from common.vo import PageModel, CrudResponseModel
from datetime import datetime

from utils.camel_converter import ModelConverter
from utils.timeformat import int_time
from module_dashboard.utils.calendar_utils import PlanPriority


class PlanService:
    @classmethod
    async def get_page_list_service(cls, query_db: AsyncSession, query_object: OaPlanQueryModel,
                                    data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel[
                                                                                                 OaPlanBaseModel] | \
                                                                                             list[dict[str, Any]]:
        query_list = await PlanDao.get_page_list(query_db, query_object, data_scope_sql, is_page)
        if is_page:
            result_list = PageModel[OaPlanBaseModel](**{
                **query_list.model_dump(by_alias=True)
            })
        else:
            result_list = []
            if query_list:
                result_list = ModelConverter.list_time_format(query_list)
        return result_list

    @classmethod
    async def add_service(cls, query_db: AsyncSession, model: OaPlanBaseModel) -> CrudResponseModel:
        if model.remind_time:
            model.remind_type = 1
            model.remind_time = int_time(model.start_time) - model.remind_time
        else:
            model.remind_type = 0
        try:
            model.start_time = int_time(model.start_time)
            model.end_time = int_time(model.end_time)
            model.create_time = int(datetime.now().timestamp())
            model.update_time = model.create_time
            await PlanDao.add(query_db, model)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def update_service(cls, query_db: AsyncSession, model: OaPlanBaseModel) -> CrudResponseModel:
        try:
            if model.remind_time:
                model.remind_type = 1
                model.remind_time = int_time(model.start_time) - model.remind_time
            model.update_time = int(datetime.now().timestamp())
            model.start_time = int_time(model.start_time)
            model.end_time = int_time(model.end_time)
            await PlanDao.update(query_db, model)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='修改成功')
        except Exception as e:
            await query_db.rollback()
            raise e


    @classmethod
    async def get_info_service(cls, query_db: AsyncSession, id: int) -> dict[str, Any]:
        try:
            info = await PlanDao.get_info_by_id(query_db, id)
            if not info:
                raise ServiceException(message="未找到该日程")
            
            plan = info[0]
            create_admin = info[1] if len(info) > 1 else None
            
            result = {
                'id': plan.id,
                'title': plan.title,
                'type': plan.type,
                'cid': plan.cid,
                'cmid': plan.cmid,
                'ptid': plan.ptid,
                'adminId': plan.admin_id,
                'did': plan.did,
                'startTime': datetime.fromtimestamp(plan.start_time).strftime('%Y-%m-%d %H:%M') if plan.start_time else '',
                'endTime': datetime.fromtimestamp(plan.end_time).strftime('%Y-%m-%d %H:%M') if plan.end_time else '',
                'startTimeA': datetime.fromtimestamp(plan.start_time).strftime('%Y-%m-%d') if plan.start_time else '',
                'endTimeA': datetime.fromtimestamp(plan.end_time).strftime('%Y-%m-%d') if plan.end_time else '',
                'startTimeB': datetime.fromtimestamp(plan.start_time).strftime('%H:%M') if plan.start_time else '',
                'endTimeB': datetime.fromtimestamp(plan.end_time).strftime('%H:%M') if plan.end_time else '',
                'remindType': plan.remind_type,
                'remindTime': datetime.fromtimestamp(plan.remind_time).strftime('%Y-%m-%d %H:%M') if plan.remind_time and plan.remind_time > 0 else '-',
                'remark': plan.remark,
                'fileIds': plan.file_ids,
                'createTime': datetime.fromtimestamp(plan.create_time).strftime('%Y-%m-%d %H:%M:%S') if plan.create_time else '',
                'updateTime': datetime.fromtimestamp(plan.update_time).strftime('%Y-%m-%d %H:%M:%S') if plan.update_time else '',
                'user': create_admin,
            }
            return result
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        try:
            await PlanDao.del_by_id(db, id)
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def get_calendar_list_service(cls, query_db: AsyncSession, query_object: OaPlanQueryModel,
                                    data_scope_sql: ColumnElement, is_page: bool = False) -> list[dict[str, Any]]:
        calendar_list = await PlanDao.get_calendar_list(query_db, query_object, data_scope_sql, is_page)
        return calendar_list

    @classmethod
    async def get_calendar_info_service(cls, query_db: AsyncSession, id: int) -> dict[str, Any]:
        info = await cls.get_info_service(query_db, id)
        
        type_value = int(info.get('type', 0)) if info.get('type') else 0
        priority = PlanPriority(type_value)
        
        return {
            'backgroundColor': priority.back_ground_colors,
            'borderColor': priority.border_color,
            'end': info.get('endTime'),
            'start': info.get('startTime'),
            'title': info.get('title'),
            'id': info.get('id'),
            'remindType': info.get('remindType'),
            'type': info.get('type')
        }
