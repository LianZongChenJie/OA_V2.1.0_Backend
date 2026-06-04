# module_personnel/service/social_security_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, List
from common.vo import PageModel, CrudResponseModel
from exceptions.exception import ServiceException
from module_personnel.dao.social_security_dao import SocialSecurityDao, SocialSecurityUserDao
from module_personnel.entity.vo.social_security_vo import (
    OaSocialSecurityBaseModel,
    OaSocialSecurityPageQueryModel,
    OaSocialSecurityUserBaseModel,
    OaSocialSecurityUserPageQueryModel,
    SocialSecurityWithUsersModel
)
from sqlalchemy.sql import ColumnElement
from datetime import datetime
import pandas as pd
from io import BytesIO


class SocialSecurityService:
    """社保信息服务类"""

    @classmethod
    async def get_page_list_service(cls, query_db: AsyncSession, query_object: OaSocialSecurityPageQueryModel,
                                   data_scope_sql: ColumnElement, is_page: bool = True) -> PageModel[OaSocialSecurityBaseModel] | list[dict[str, Any]]:
        """获取社保信息分页列表服务"""
        query_list = await SocialSecurityDao.get_page_list(query_db, query_object, data_scope_sql, is_page)
        if is_page:
            # 处理 rows 中的数据，确保可以正确序列化
            if hasattr(query_list, 'rows') and query_list.rows:
                # rows 已经是字典格式，直接使用
                processed_rows = query_list.rows
                
                # 创建 PageModel，使用驼峰命名
                result_list = PageModel[OaSocialSecurityBaseModel](
                    rows=processed_rows,
                    total=query_list.total if hasattr(query_list, 'total') else 0,
                    pageNum=query_list.pageNum if hasattr(query_list, 'pageNum') else query_object.page_num,
                    pageSize=query_list.pageSize if hasattr(query_list, 'pageSize') else query_object.page_size,
                    hasNext=query_list.hasNext if hasattr(query_list, 'hasNext') else False
                )
            else:
                result_list = query_list
        else:
            result_list = []
            if query_list:
                result_list = [{**row} if isinstance(row, dict) else row.__dict__ for row in query_list]
        return result_list

    @classmethod
    async def add_or_update_service(cls, query_db: AsyncSession, model: OaSocialSecurityBaseModel) -> CrudResponseModel:
        """新增或编辑社保信息服务"""
        try:
            if model.id:
                # 编辑
                update_data = model.model_dump(exclude={"id", "update_time", "create_by", "create_by_id", "related_users", "social_date_str", "create_time_str", "social_date"}, exclude_none=True)
                await SocialSecurityDao.update(query_db, model)
                
                # 处理关联人员 - 先删除旧的关联记录，再添加新的
                if model.related_users:
                    # 获取当前已关联的用户ID
                    existing_users = await SocialSecurityUserDao.get_users_by_social_id(query_db, model.id)
                    existing_user_ids = [user.get('user_id') for user in existing_users]
                    
                    # 物理删除旧的关联记录
                    from module_personnel.entity.do.social_security_do import OaSocialSecurityUser
                    from sqlalchemy import delete
                    
                    await query_db.execute(
                        delete(OaSocialSecurityUser)
                        .where(OaSocialSecurityUser.social_id == model.id)
                    )
                    await query_db.commit()
                    
                    # 添加新的关联用户
                    user_ids = [int(u.strip()) for u in model.related_users.split(',') if u.strip()]
                    await SocialSecurityUserDao.batch_add_users(query_db, model.id, user_ids, model.create_by_id or 0)
                
                return CrudResponseModel(is_success=True, message='编辑成功')
            else:
                # 新增
                db_model = await SocialSecurityDao.add(query_db, model)
                
                # 处理关联人员
                if model.related_users:
                    user_ids = [int(u.strip()) for u in model.related_users.split(',') if u.strip()]
                    await SocialSecurityUserDao.batch_add_users(query_db, db_model.id, user_ids, model.create_by_id or 0)
                
                return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f"操作失败: {str(e)}")

    @classmethod
    async def get_detail_service(cls, query_db: AsyncSession, id: int) -> dict:
        """获取社保信息详情服务"""
        try:
            social_info = await SocialSecurityDao.get_info_by_id(query_db, id)
            if not social_info:
                raise ServiceException(message="未找到该社保信息")

            # 获取关联人员
            users = await SocialSecurityUserDao.get_users_by_social_id(query_db, id)

            # 直接构建字典返回，避免Pydantic验证问题
            social_dict = social_info.to_dict()
            
            # 转换字段名为驼峰命名 - 将 socialInfo 的字段直接提升到与 users 同级
            result = {
                'id': social_dict.get('id'),
                'city': social_dict.get('city'),
                'cityId': social_dict.get('city_id'),
                'projectName': social_dict.get('project_name'),
                'socialDate': social_dict.get('social_date'),
                'remark': social_dict.get('remark'),
                'socialDateStr': None,
                'relatedUsers': None,
                'createBy': social_dict.get('create_by'),
                'createById': social_dict.get('create_by_id'),
                'manager': social_dict.get('manager'),
                'managerId': social_dict.get('manager_id'),
                'status': social_dict.get('status'),
                'createTime': social_dict.get('create_time'),
                'createTimeStr': None,
                'updateTime': social_dict.get('update_time'),
                'deleteTime': social_dict.get('delete_time'),
                'users': [{
                    'id': user.get('id'),
                    'socialId': user.get('social_id'),
                    'userId': user.get('user_id'),
                    'userName': user.get('user_name'),
                    'entryTime': user.get('entry_time'),
                    'entryTimeStr': user.get('entry_time'),  # 直接返回原始字符串
                    'departmentName': user.get('department_name'),
                    'city': user.get('city'),
                    'projectName': user.get('project_name'),
                    'status': user.get('status'),
                    'createTime': user.get('create_time'),
                    'updateTime': user.get('update_time'),
                    'deleteTime': user.get('delete_time')
                } for user in users]
            }

            return result
        except Exception as e:
            raise ServiceException(message=f"查询失败: {str(e)}")

    @classmethod
    async def terminate_service(cls, query_db: AsyncSession, id: int) -> CrudResponseModel:
        """终止社保信息服务"""
        try:
            await SocialSecurityDao.terminate_social_security(query_db, id)
            return CrudResponseModel(is_success=True, message='终止成功')
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f"终止失败: {str(e)}")

    @classmethod
    async def delete_service(cls, query_db: AsyncSession, id: int) -> CrudResponseModel:
        """删除社保信息服务"""
        try:
            # 检查是否存在关联的参保人员
            users = await SocialSecurityUserDao.get_users_by_social_id(query_db, id)
            if users:
                raise ServiceException(message="该社保信息下还有参保人员，请先移除所有人员后再删除")
            
            await SocialSecurityDao.del_by_id(query_db, id)
            return CrudResponseModel(is_success=True, message='删除成功')
        except ServiceException:
            raise
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f"删除失败: {str(e)}")

    @classmethod
    async def get_user_page_list_service(cls, query_db: AsyncSession, query_object: OaSocialSecurityUserPageQueryModel,
                                        is_page: bool = True) -> dict | list[dict[str, Any]]:
        """获取社保关联人员分页列表服务"""
        query_list = await SocialSecurityUserDao.get_user_page_list(query_db, query_object, is_page)
        if is_page:
            # 处理 rows 中的数据
            processed_rows = []
            if hasattr(query_list, 'rows') and query_list.rows:
                for item in query_list.rows:
                    # 尝试多种方式获取数据
                    if isinstance(item, dict):
                        row_dict = item
                    elif hasattr(item, '_asdict'):
                        # Row 对象使用 _asdict() 方法
                        row_dict = item._asdict()
                    elif hasattr(item, '_mapping'):
                        row_dict = dict(item._mapping)
                    elif hasattr(item, '__dict__'):
                        row_dict = item.__dict__
                    else:
                        row_dict = {}
                    
                    # 转换为驼峰命名并处理 entryTime
                    processed_rows.append({
                        'id': row_dict.get('id'),
                        'socialId': row_dict.get('social_id') or row_dict.get('socialId'),
                        'userId': row_dict.get('user_id') or row_dict.get('userId'),
                        'userName': row_dict.get('user_name') or row_dict.get('userName'),
                        'entryTime': row_dict.get('entry_time') or row_dict.get('entryTime'),
                        'entryTimeStr': row_dict.get('entry_time') or row_dict.get('entryTime'),
                        'departmentName': row_dict.get('department_name') or row_dict.get('departmentName'),
                        'city': row_dict.get('city'),
                        'projectName': row_dict.get('project_name') or row_dict.get('projectName'),
                        'status': row_dict.get('status'),
                        'createTime': row_dict.get('create_time') or row_dict.get('createTime'),
                        'updateTime': row_dict.get('update_time') or row_dict.get('updateTime'),
                        'deleteTime': row_dict.get('delete_time') or row_dict.get('deleteTime')
                    })
            
            # 直接返回字典格式，避免Pydantic验证
            result_list = {
                'rows': processed_rows,
                'total': query_list.total if hasattr(query_list, 'total') else 0,
                'pageNum': query_list.pageNum if hasattr(query_list, 'pageNum') else query_object.page_num,
                'pageSize': query_list.pageSize if hasattr(query_list, 'pageSize') else query_object.page_size,
                'hasNext': query_list.hasNext if hasattr(query_list, 'hasNext') else False
            }
        else:
            result_list = []
            if query_list:
                for item in query_list:
                    if isinstance(item, dict):
                        row_dict = item
                    elif hasattr(item, '_asdict'):
                        row_dict = item._asdict()
                    elif hasattr(item, '_mapping'):
                        row_dict = dict(item._mapping)
                    elif hasattr(item, '__dict__'):
                        row_dict = item.__dict__
                    else:
                        row_dict = {}
                    
                    result_list.append({
                        'id': row_dict.get('id'),
                        'socialId': row_dict.get('social_id') or row_dict.get('socialId'),
                        'userId': row_dict.get('user_id') or row_dict.get('userId'),
                        'userName': row_dict.get('user_name') or row_dict.get('userName'),
                        'entryTime': row_dict.get('entry_time') or row_dict.get('entryTime'),
                        'entryTimeStr': row_dict.get('entry_time') or row_dict.get('entryTime'),
                        'departmentName': row_dict.get('department_name') or row_dict.get('departmentName'),
                        'city': row_dict.get('city'),
                        'projectName': row_dict.get('project_name') or row_dict.get('projectName'),
                        'status': row_dict.get('status'),
                        'createTime': row_dict.get('create_time') or row_dict.get('createTime'),
                        'updateTime': row_dict.get('update_time') or row_dict.get('updateTime'),
                        'deleteTime': row_dict.get('delete_time') or row_dict.get('deleteTime')
                    })
        return result_list

    @classmethod
    async def add_user_service(cls, query_db: AsyncSession, social_id: int, user_ids: List[int], admin_id: int) -> CrudResponseModel:
        """添加社保关联人员服务（支持单个或批量添加）"""
        try:
            added_count = await SocialSecurityUserDao.batch_add_users(query_db, social_id, user_ids, admin_id)
            if added_count == 0:
                return CrudResponseModel(is_success=False, message='未添加任何人员，可能已全部存在')
            return CrudResponseModel(is_success=True, message=f'成功添加{added_count}名人员')
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f"添加人员失败: {str(e)}")

    @classmethod
    async def batch_add_users_service(cls, query_db: AsyncSession, social_id: int, user_ids: List[int], admin_id: int) -> CrudResponseModel:
        """批量添加社保关联人员服务"""
        try:
            added_count = await SocialSecurityUserDao.batch_add_users(query_db, social_id, user_ids, admin_id)
            return CrudResponseModel(is_success=True, message=f'成功添加{added_count}名人员')
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f"添加人员失败: {str(e)}")

    @classmethod
    async def batch_remove_users_service(cls, query_db: AsyncSession, social_id: int, user_ids: List[int]) -> CrudResponseModel:
        """批量减员社保关联人员服务"""
        try:
            removed_count = await SocialSecurityUserDao.batch_remove_users(query_db, social_id, user_ids)
            return CrudResponseModel(is_success=True, message=f'成功减员{removed_count}名人员')
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f"减员失败: {str(e)}")

    @classmethod
    async def update_user_service(cls, query_db: AsyncSession, id: int, social_id: int = None, user_id: int = None) -> CrudResponseModel:
        """修改用户社保关联信息服务"""
        try:
            updated_count = await SocialSecurityUserDao.update_user(query_db, id, social_id, user_id)
            if updated_count == 0:
                return CrudResponseModel(is_success=False, message='未找到该关联记录')
            return CrudResponseModel(is_success=True, message='修改成功')
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f"修改失败: {str(e)}")

    @classmethod
    async def remove_user_service(cls, query_db: AsyncSession, social_id: int, user_ids: List[int]) -> CrudResponseModel:
        """删除用户社保关联信息服务（支持批量删除）"""
        try:
            from module_personnel.entity.do.social_security_do import OaSocialSecurityUser
            from sqlalchemy import update
            from sqlalchemy.sql import and_
            from datetime import datetime
            
            current_time = int(datetime.now().timestamp())
            
            # 直接在 Service 层执行批量更新，避免多次 commit
            result = await query_db.execute(
                update(OaSocialSecurityUser)
                .values(status=0, update_time=current_time, delete_time=current_time)
                .where(
                    and_(
                        OaSocialSecurityUser.social_id == social_id,
                        OaSocialSecurityUser.user_id.in_(user_ids),
                        OaSocialSecurityUser.delete_time == 0,
                        OaSocialSecurityUser.status == 1
                    )
                )
            )
            
            await query_db.commit()
            removed_count = result.rowcount
            
            if removed_count == 0:
                return CrudResponseModel(is_success=False, message='未找到任何关联记录或已全部减员')
            elif removed_count == len(user_ids):
                return CrudResponseModel(is_success=True, message=f'成功减员{removed_count}名人员')
            else:
                return CrudResponseModel(is_success=True, message=f'成功减员{removed_count}名人员，{len(user_ids)-removed_count}条记录未找到或已减员')
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f"减员失败: {str(e)}")

    @classmethod
    async def import_users_service(cls, query_db: AsyncSession, social_id: int, file_content: bytes, admin_id: int) -> CrudResponseModel:
        """导入社保关联人员服务"""
        try:
            # 读取Excel文件
            df = pd.read_excel(BytesIO(file_content))

            # 转换数据格式
            user_data = []
            for _, row in df.iterrows():
                user_data.append({
                    'user_id': int(row.get('user_id', 0))
                })

            added_count = await SocialSecurityUserDao.import_users_from_excel(query_db, social_id, user_data, admin_id)
            return CrudResponseModel(is_success=True, message=f'成功导入{added_count}名人员')
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f"导入失败: {str(e)}")

    @classmethod
    async def get_expiring_reminder_service(cls, query_db: AsyncSession, days: int = 3, manager_id: int = None) -> List[dict]:
        """获取社保到期提醒服务（用于工作台）"""
        try:
            expiring_list = await SocialSecurityUserDao.get_expiring_social_securities(query_db, days, manager_id=manager_id)
            return expiring_list
        except Exception as e:
            raise ServiceException(message=f"获取提醒失败: {str(e)}")

    @classmethod
    async def get_expiring_count_service(cls, query_db: AsyncSession, days: int = 3) -> dict:
        """获取即将到期的社保数量服务（用于预警统计）"""
        try:
            count = await SocialSecurityUserDao.get_expiring_count(query_db, days)
            return {'expiringCount': count, 'days': days}
        except Exception as e:
            raise ServiceException(message=f"获取预警数量失败: {str(e)}")