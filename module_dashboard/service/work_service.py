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
from module_admin.entity.do.oa_admin_do import OaAdmin


class WorkService:
    @classmethod
    async def get_send_list_service(cls, query_db: AsyncSession, query_object: OaWorkPageQueryModel,
                                    data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel | list[dict[str, Any]]:
        """
        获取我发出的汇报列表
        """
        query_list = await WorkDao.get_send_list(query_db, query_object, data_scope_sql, is_page)
        
        if is_page:
            result_list = PageModel[OaWorkBaseModel](**{
                **query_list.model_dump(by_alias=True)
            })
        else:
            result_list = []
            if query_list:
                result_list = ModelConverter.list_time_format(query_list)
        return result_list

    @classmethod
    async def get_accept_list_service(cls, query_db: AsyncSession, query_object: OaWorkPageQueryModel,
                                      data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel | list[dict[str, Any]]:
        """
        获取我接收的汇报列表
        """
        query_list = await WorkDao.get_accept_list(query_db, query_object, data_scope_sql, is_page)
        
        if is_page:
            result_list = PageModel[OaWorkBaseModel](**{
                **query_list.model_dump(by_alias=True)
            })
        else:
            result_list = []
            if query_list:
                result_list = ModelConverter.list_time_format(query_list)
        return result_list

    @classmethod
    async def add_service(cls, query_db: AsyncSession, model: OaWorkQueryModel, current_user_id: int) -> CrudResponseModel:
        """
        新增工作汇报
        """
        try:
            add_model = OaWorkBaseModel(**model.model_dump(exclude_none=True, exclude={'users', 'read_users', 'comment_auth', 'person_name'}))
            add_model.admin_id = current_user_id
            add_model.start_date = int_time(str(model.start_date)) if model.start_date and isinstance(model.start_date, str) and len(str(model.start_date).strip()) > 0 else (model.start_date if isinstance(model.start_date, int) else 0)
            add_model.end_date = int_time(str(model.end_date)) if model.end_date and isinstance(model.end_date, str) and len(str(model.end_date).strip()) > 0 else (model.end_date if isinstance(model.end_date, int) else 0)
            add_model.create_time = int(datetime.now().timestamp())
            add_model.update_time = add_model.create_time
            
            if model.is_send:
                add_model.send_time = add_model.create_time
            
            work_record = await WorkDao.add(query_db, add_model)
            
            if model.is_send and model.to_uids:
                users = [uid.strip() for uid in model.to_uids.split(',') if uid.strip()]
                send_data = []
                for uid in users:
                    try:
                        uid_int = int(uid)
                        if uid_int != current_user_id:
                            send_data.append({
                                'work_id': work_record.id,
                                'to_uid': uid_int,
                                'from_uid': current_user_id,
                                'send_time': add_model.create_time
                            })
                    except (ValueError, TypeError):
                        continue
                
                if send_data:
                    await WorkDao.add_work_records(query_db, send_data)
                    await WorkDao.update_send_time(query_db, work_record.id, add_model.create_time)
            
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='发送成功' if model.is_send else '保存成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def update_service(cls, query_db: AsyncSession, model: OaWorkQueryModel, current_user_id: int) -> CrudResponseModel:
        """
        更新工作汇报
        """
        try:
            work_info = await WorkDao.get_info_by_id(query_db, model.id)
            if not work_info or not work_info[0]:
                raise ServiceException(message="汇报不存在")
            
            work = work_info[0]
            if work.admin_id != current_user_id:
                raise ServiceException(message="无权限修改此汇报")

            update_model = OaWorkBaseModel(**model.model_dump(exclude_none=True, exclude={'users', 'read_users', 'comment_auth', 'person_name'}))
            update_model.start_date = int_time(str(model.start_date)) if model.start_date and isinstance(model.start_date, str) and len(str(model.start_date).strip()) > 0 else (model.start_date if isinstance(model.start_date, int) else 0)
            update_model.end_date = int_time(str(model.end_date)) if model.end_date and isinstance(model.end_date, str) and len(str(model.end_date).strip()) > 0 else (model.end_date if isinstance(model.end_date, int) else 0)
            update_model.update_time = int(datetime.now().timestamp())
            
            if model.is_send:
                update_model.send_time = update_model.update_time
            
            await WorkDao.update(query_db, update_model)
            
            if model.is_send and model.to_uids:
                users = [uid.strip() for uid in model.to_uids.split(',') if uid.strip()]
                send_data = []
                for uid in users:
                    try:
                        uid_int = int(uid)
                        existing_record = await WorkDao.check_work_record(query_db, model.id, uid_int)
                        if not existing_record:
                            send_data.append({
                                'work_id': model.id,
                                'to_uid': uid_int,
                                'from_uid': current_user_id,
                                'send_time': update_model.update_time
                            })
                    except (ValueError, TypeError):
                        continue
                
                if send_data:
                    await WorkDao.add_work_records(query_db, send_data)
                    await WorkDao.update_send_time(query_db, model.id, update_model.update_time)
            
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='修改成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def get_info_service(cls, query_db: AsyncSession, id: int, current_user_id: int) -> dict[str, Any]:
        """
        获取工作汇报详情
        """
        try:
            work_info = await WorkDao.get_info_by_id(query_db, id)
            if not work_info or not work_info[0]:
                raise ServiceException(message="汇报不存在")
            
            work = work_info[0]
            person_name = work_info[1] if len(work_info) > 1 else None
            
            result = {
                'id': work.id,
                'types': work.types,
                'startDate': datetime.fromtimestamp(work.start_date).strftime('%Y-%m-%d') if work.start_date and work.start_date > 0 else '',
                'endDate': datetime.fromtimestamp(work.end_date).strftime('%Y-%m-%d') if work.end_date and work.end_date > 0 else '',
                'toUids': work.to_uids,
                'works': work.works,
                'plans': work.plans,
                'remark': work.remark,
                'fileIds': work.file_ids,
                'sendTime': datetime.fromtimestamp(work.send_time).strftime('%Y-%m-%d %H:%M:%S') if work.send_time and work.send_time > 0 else '',
                'adminId': work.admin_id,
                'createTime': datetime.fromtimestamp(work.create_time).strftime('%Y-%m-%d %H:%M:%S') if work.create_time else '',
                'updateTime': datetime.fromtimestamp(work.update_time).strftime('%Y-%m-%d %H:%M:%S') if work.update_time else '',
                'personName': person_name,
            }
            
            if work.admin_id != current_user_id:
                record = await WorkDao.check_work_record(query_db, id, current_user_id)
                if not record:
                    raise ServiceException(message="该汇报不存在或您无权查看")
                
                if record.read_time == 0:
                    await WorkDao.update_read_time(query_db, id, current_user_id, int(datetime.now().timestamp()))
                    await query_db.commit()
                
                result['commentAuth'] = 1
                result['users'] = ''
                result['readUsers'] = ''
            else:
                read_user_ids = await WorkDao.get_read_user_ids(query_db, id)
                
                if read_user_ids:
                    read_users_result = await query_db.execute(
                        select(OaAdmin.name).where(OaAdmin.id.in_(read_user_ids))
                    )
                    read_user_names = read_users_result.scalars().all()
                    result['readUsers'] = ','.join(read_user_names)
                else:
                    result['readUsers'] = ''
                
                if work.to_uids:
                    to_uid_list = []
                    for uid in work.to_uids.split(','):
                        uid = uid.strip()
                        if uid:
                            try:
                                to_uid_list.append(int(uid))
                            except (ValueError, TypeError):
                                continue
                    if to_uid_list:
                        users_result = await query_db.execute(
                            select(OaAdmin.name).where(OaAdmin.id.in_(to_uid_list))
                        )
                        user_names = users_result.scalars().all()
                        result['users'] = ','.join(user_names)
                    else:
                        result['users'] = ''
                else:
                    result['users'] = ''
                
                result['commentAuth'] = 0
            
            return result
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int, current_user_id: int):
        """
        删除工作汇报
        """
        try:
            work_info = await WorkDao.get_info_by_id(db, id)
            if not work_info or not work_info[0]:
                raise ServiceException(message="汇报不存在")
            
            work = work_info[0]
            if work.admin_id != current_user_id:
                raise ServiceException(message="无权限删除此汇报")
            
            await WorkDao.del_by_id(db, id)
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await db.rollback()
            raise e