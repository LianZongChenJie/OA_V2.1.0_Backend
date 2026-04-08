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
from utils.log_util import logger


class ScheduleService:
    @classmethod
    async def get_page_list_service(cls, query_db: AsyncSession, query_object: OaSchedulePageQueryModel,
                                    data_scope_sql: ColumnElement, is_page: bool = False):
        try:
            query_list = await ScheduleDao.get_page_list(query_db, query_object, data_scope_sql, is_page)
            if is_page:
                # 处理分页结果
                processed_rows = []
                for row in query_list.rows:
                    if row and len(row) > 0:
                        schedule_obj = row[0]  # 可能是 OaSchedule 对象或字典
                        
                        # 判断是字典还是 ORM 对象
                        if isinstance(schedule_obj, dict):
                            # 如果已经是字典，直接使用
                            schedule_dict = {
                                'id': schedule_obj.get('id'),
                                'title': schedule_obj.get('title'),
                                'cid': schedule_obj.get('cid'),
                                'cmid': schedule_obj.get('cmid'),
                                'ptid': schedule_obj.get('ptid'),
                                'tid': schedule_obj.get('tid'),
                                'admin_id': schedule_obj.get('admin_id'),
                                'did': schedule_obj.get('did'),
                                'start_time': schedule_obj.get('start_time'),
                                'end_time': schedule_obj.get('end_time'),
                                'labor_time': float(schedule_obj.get('labor_time', 0)) if schedule_obj.get('labor_time') else 0.0,
                                'labor_type': schedule_obj.get('labor_type'),
                                'remark': schedule_obj.get('remark'),
                                'file_ids': schedule_obj.get('file_ids'),
                                'delete_time': schedule_obj.get('delete_time'),
                                'create_time': schedule_obj.get('create_time'),
                                'update_time': schedule_obj.get('update_time'),
                            }
                        else:
                            # 如果是 ORM 对象，转换为字典
                            schedule_dict = {
                                'id': schedule_obj.id,
                                'title': schedule_obj.title,
                                'cid': schedule_obj.cid,
                                'cmid': schedule_obj.cmid,
                                'ptid': schedule_obj.ptid,
                                'tid': schedule_obj.tid,
                                'admin_id': schedule_obj.admin_id,
                                'did': schedule_obj.did,
                                'start_time': schedule_obj.start_time,
                                'end_time': schedule_obj.end_time,
                                'labor_time': float(schedule_obj.labor_time) if schedule_obj.labor_time else 0.0,
                                'labor_type': schedule_obj.labor_type,
                                'remark': schedule_obj.remark,
                                'file_ids': schedule_obj.file_ids,
                                'delete_time': schedule_obj.delete_time,
                                'create_time': schedule_obj.create_time,
                                'update_time': schedule_obj.update_time,
                            }
                        processed_rows.append(schedule_dict)
                
                # 直接返回字典，避免 Pydantic 验证问题
                result_dict = {
                    'rows': processed_rows,
                    'pageNum': query_list.page_num,
                    'pageSize': query_list.page_size,
                    'total': query_list.total,
                    'hasNext': query_list.has_next,
                }
                logger.info(f'分页查询成功，共 {len(processed_rows)} 条记录')
                return result_dict
            else:
                result_list = []
                if query_list:
                    result_list = ModelConverter.list_time_format(query_list)
                return result_list
        except AttributeError as e:
            logger.error(f'属性访问错误: {str(e)}', exc_info=True)
            raise
        except Exception as e:
            logger.error(f'获取工时列表失败: {str(e)}', exc_info=True)
            raise

    @classmethod
    async def add_service(cls, query_db: AsyncSession, model: OaScheduleBaseModel) -> CrudResponseModel:
        try:
            model.start_time = int_time(model.start_time)
            model.end_time = int_time(model.end_time)
            model.create_time = int(datetime.now().timestamp())
            model.labor_time = (model.end_time - model.start_time)/3600
            if not model.delete_time:
                model.delete_time = 0
            await ScheduleDao.add(query_db, model)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

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

    @classmethod
    async def get_info_service(cls, query_db: AsyncSession, id: int):
        try:
            info = await ScheduleDao.get_info_by_id(query_db, id)
            if not info:
                raise ServiceException(message="未找到该日程")
            return info
        except Exception as e:
            raise e

    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        try:
            await ScheduleDao.del_by_id(db, id)
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def get_calendar_list_service(cls, query_db: AsyncSession, query_object: OaSchedulePageQueryModel,
                                    data_scope_sql: ColumnElement, is_page: bool = False):
        data_list = await cls.get_page_list_service(query_db, query_object, data_scope_sql, is_page)
        calendar_list = []
        
        # 判断 data_list 是字典还是对象
        rows = data_list.get('rows', []) if isinstance(data_list, dict) else data_list.rows
        
        for item in rows:
            calendar_item = {
                'backgroundColor': SchedulePriority(int(item['cid'])).back_ground_colors,
                'borderColor': SchedulePriority(int(item['cid'])).border_color,
                'end': item['end_time'],
                'start': item['start_time'],
                'title': item['title'],
                'id': item['id'],
                'laborTime': item['labor_time']
            }
            calendar_list.append(calendar_item)
        return calendar_list

    @classmethod
    async def get_calendar_info_service(cls, query_db: AsyncSession, id: int) -> dict[str, Any]:
        info = await cls.get_info_service(query_db, id)
        return {
            'backgroundColor': SchedulePriority(int(info.cid)).back_ground_colors,
            'borderColor': SchedulePriority(int(info.cid)).border_color,
            'end': info.end_time,
            'start': info.start_time,
            'title': info.title,
            'id': info.id,
            'laborTime': info.labor_time
        }
