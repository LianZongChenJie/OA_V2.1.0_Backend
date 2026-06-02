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
                
                # 处理关联人员
                if model.related_users:
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
                                        is_page: bool = True) -> PageModel[OaSocialSecurityUserBaseModel] | list[dict[str, Any]]:
        """获取社保关联人员分页列表服务"""
        query_list = await SocialSecurityUserDao.get_user_page_list(query_db, query_object, is_page)
        if is_page:
            # 处理 rows 中的数据
            if hasattr(query_list, 'rows') and query_list.rows:
                processed_rows = []
                for item in query_list.rows:
                    if isinstance(item, dict):
                        processed_rows.append(item)
                    else:
                        # 使用 _mapping 转换
                        try:
                            processed_rows.append(dict(item._mapping))
                        except Exception:
                            processed_rows.append(item.__dict__ if hasattr(item, '__dict__') else {})
                
                # 创建 PageModel，使用驼峰命名
                result_list = PageModel[OaSocialSecurityUserBaseModel](
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
                for item in query_list:
                    if isinstance(item, dict):
                        result_list.append(item)
                    else:
                        try:
                            result_list.append(dict(item._mapping))
                        except Exception:
                            result_list.append(item.__dict__ if hasattr(item, '__dict__') else {})
        return result_list

    @classmethod
    async def add_user_service(cls, query_db: AsyncSession, social_id: int, user_id: int, admin_id: int) -> CrudResponseModel:
        """单个添加社保关联人员服务"""
        try:
            success, message = await SocialSecurityUserDao.add_user(query_db, social_id, user_id, admin_id)
            return CrudResponseModel(is_success=success, message=message)
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
    async def remove_user_service(cls, query_db: AsyncSession, id: int) -> CrudResponseModel:
        """删除单个用户社保关联信息服务"""
        try:
            removed_count = await SocialSecurityUserDao.remove_user(query_db, id)
            if removed_count == 0:
                return CrudResponseModel(is_success=False, message='未找到该关联记录或已减员')
            return CrudResponseModel(is_success=True, message='减员成功')
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
    async def get_expiring_reminder_service(cls, query_db: AsyncSession, days: int = 3) -> List[dict]:
        """获取社保到期提醒服务（用于工作台）"""
        try:
            expiring_list = await SocialSecurityUserDao.get_expiring_social_securities(query_db, days)
            return expiring_list
        except Exception as e:
            raise ServiceException(message=f"获取提醒失败: {str(e)}")