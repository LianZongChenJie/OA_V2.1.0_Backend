# module_personnel/dao/social_security_dao.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc, func, or_, and_
from sqlalchemy.sql import ColumnElement
from common.vo import PageModel
from utils.page_util import PageUtil
from module_personnel.entity.vo.social_security_vo import (
    OaSocialSecurityBaseModel, 
    OaSocialSecurityPageQueryModel,
    OaSocialSecurityUserBaseModel,
    OaSocialSecurityUserPageQueryModel
)
from module_personnel.entity.do.social_security_do import OaSocialSecurity, OaSocialSecurityUser
from module_admin.entity.do.user_do import SysUser
from module_admin.entity.do.dept_do import SysDept
from typing import Any, List
from datetime import datetime


class SocialSecurityDao:
    """社保信息数据访问对象"""

    @classmethod
    async def get_page_list(cls, db: AsyncSession, query_object: OaSocialSecurityPageQueryModel,
                           data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel | list[dict[str, Any]]:
        """获取社保信息分页列表"""
        # 构建基础查询 - 明确指定字段
        query = select(
            OaSocialSecurity.id,
            OaSocialSecurity.city,
            OaSocialSecurity.city_id,
            OaSocialSecurity.project_name,
            OaSocialSecurity.social_date,
            OaSocialSecurity.remark,
            OaSocialSecurity.create_by,
            OaSocialSecurity.create_by_id,
            OaSocialSecurity.manager,
            OaSocialSecurity.manager_id,
            OaSocialSecurity.status,
            OaSocialSecurity.create_time,
            OaSocialSecurity.update_time,
            OaSocialSecurity.delete_time
        ).where(OaSocialSecurity.delete_time == 0)

        # 构建条件列表
        conditions = []

        # 状态筛选
        if query_object.status is not None:
            conditions.append(OaSocialSecurity.status == query_object.status)

        # 关键词搜索
        if query_object.keywords:
            keyword = f'%{query_object.keywords}%'
            conditions.append(
                or_(
                    OaSocialSecurity.city.like(keyword),
                    OaSocialSecurity.project_name.like(keyword)
                )
            )

        # 负责人筛选
        if query_object.manager:
            conditions.append(OaSocialSecurity.manager.like(f'%{query_object.manager}%'))

        # 负责人ID筛选（精确匹配）
        if query_object.manager_id:
            conditions.append(OaSocialSecurity.manager_id == query_object.manager_id)

        # 城市筛选
        if query_object.city:
            conditions.append(OaSocialSecurity.city.like(f'%{query_object.city}%'))

        # 项目名称筛选
        if query_object.project_name:
            conditions.append(OaSocialSecurity.project_name.like(f'%{query_object.project_name}%'))

        # 添加数据权限条件
        if data_scope_sql is not None:
            conditions.append(data_scope_sql)

        # 应用所有条件
        if conditions:
            query = query.where(*conditions)

        # 排序
        query = query.order_by(desc(OaSocialSecurity.create_time))

        # 分页查询
        page_list = await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, is_page)
        
        # 处理结果，添加相关人员字段
        if is_page and hasattr(page_list, 'rows') and page_list.rows:
            processed_rows = []
            for row in page_list.rows:
                # 将 Row 对象转换为字典
                if isinstance(row, dict):
                    row_dict = row
                else:
                    try:
                        row_dict = dict(row._mapping)
                    except Exception:
                        row_dict = {
                            'id': row.id,
                            'city': row.city,
                            'city_id': row.city_id,
                            'project_name': row.project_name,
                            'social_date': row.social_date,
                            'remark': row.remark,
                            'create_by': row.create_by,
                            'create_by_id': row.create_by_id,
                            'manager': row.manager,
                            'manager_id': row.manager_id,
                            'status': row.status,
                            'create_time': row.create_time,
                            'update_time': row.update_time,
                            'delete_time': row.delete_time
                        }
                
                # 获取关联的人员
                social_id = row_dict.get('id')
                users_query = select(OaSocialSecurityUser.user_id).where(
                    and_(
                        OaSocialSecurityUser.social_id == social_id,
                        OaSocialSecurityUser.status == 1,
                        OaSocialSecurityUser.delete_time == 0
                    )
                )
                users_result = await db.execute(users_query)
                user_ids = [r[0] for r in users_result.all()]
                
                # 获取用户姓名
                if user_ids:
                    users_name_query = select(SysUser.nick_name).where(SysUser.user_id.in_(user_ids))
                    users_name_result = await db.execute(users_name_query)
                    user_names = [r[0] for r in users_name_result.all()]
                    row_dict['related_users'] = ','.join(user_names)
                else:
                    row_dict['related_users'] = ''
                
                processed_rows.append(row_dict)
            
            page_list.rows = processed_rows
        
        return page_list

    @classmethod
    async def add(cls, db: AsyncSession, model: OaSocialSecurityBaseModel):
        """新增社保信息"""
        db_model = OaSocialSecurity(**model.model_dump(exclude={"id", "create_time", "update_time", "related_users", "social_date_str", "create_time_str"}, exclude_none=True),
                                   create_time=int(datetime.now().timestamp()))
        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)
        return db_model

    @classmethod
    async def update(cls, db: AsyncSession, model: OaSocialSecurityBaseModel):
        """更新社保信息"""
        update_data = model.model_dump(exclude={"id", "update_time", "related_users", "social_date_str", "create_time_str"}, exclude_none=True)
        update_data['update_time'] = int(datetime.now().timestamp())

        result = await db.execute(
            update(OaSocialSecurity)
            .values(**update_data)
            .where(OaSocialSecurity.id == model.id)
        )
        await db.commit()
        return await cls.get_info_by_id(db, model.id)

    @classmethod
    async def get_info_by_id(cls, db: AsyncSession, id: int):
        """根据ID获取社保信息"""
        query = select(OaSocialSecurity).where(OaSocialSecurity.id == id)
        info = await db.scalar(query)
        return info

    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        """逻辑删除社保信息"""
        result = await db.execute(
            update(OaSocialSecurity)
            .values(delete_time=int(datetime.now().timestamp()))
            .where(OaSocialSecurity.id == id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def terminate_social_security(cls, db: AsyncSession, id: int):
        """终止社保信息"""
        result = await db.execute(
            update(OaSocialSecurity)
            .values(status=0, update_time=int(datetime.now().timestamp()))
            .where(OaSocialSecurity.id == id)
        )
        await db.commit()
        return result.rowcount


class SocialSecurityUserDao:
    """社保关联人员数据访问对象"""

    @classmethod
    async def get_user_page_list(cls, db: AsyncSession, query_object: OaSocialSecurityUserPageQueryModel,
                                is_page: bool = False) -> PageModel | list[dict[str, Any]]:
        """获取社保关联人员分页列表"""
        # 构建基础查询
        query = (
            select(
                OaSocialSecurityUser.id,
                OaSocialSecurityUser.social_id,
                OaSocialSecurityUser.user_id,
                OaSocialSecurityUser.status,
                OaSocialSecurityUser.create_time,
                OaSocialSecurityUser.update_time,
                SysUser.nick_name.label('user_name'),
                SysUser.work_date.label('entry_time'),
                SysDept.dept_name.label('department_name'),
                OaSocialSecurity.city.label('city'),
                OaSocialSecurity.project_name.label('project_name')
            )
            .outerjoin(SysUser, OaSocialSecurityUser.user_id == SysUser.user_id)
            .outerjoin(SysDept, SysUser.dept_id == SysDept.dept_id)
            .outerjoin(OaSocialSecurity, OaSocialSecurityUser.social_id == OaSocialSecurity.id)
            .where(OaSocialSecurityUser.delete_time == 0)
        )

        # 构建条件列表
        conditions = []

        # 社保ID筛选（可选）
        if query_object.social_id:
            conditions.append(OaSocialSecurityUser.social_id == query_object.social_id)
        
        # 状态筛选
        if query_object.status is not None:
            conditions.append(OaSocialSecurityUser.status == query_object.status)

        # 用户名模糊查询
        if query_object.user_name:
            conditions.append(SysUser.nick_name.like(f'%{query_object.user_name}%'))

        # 应用所有条件
        if conditions:
            query = query.where(*conditions)

        # 排序
        query = query.order_by(desc(OaSocialSecurityUser.create_time))

        # 分页查询
        page_list = await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, is_page)
        
        # 处理结果，将 Row 对象转换为字典
        if is_page and hasattr(page_list, 'rows') and page_list.rows:
            processed_rows = []
            for row in page_list.rows:
                if isinstance(row, dict):
                    processed_rows.append(row)
                else:
                    # Row 对象转换为字典 - 使用 _mapping 属性
                    try:
                        row_dict = dict(row._mapping)
                    except Exception:
                        # 如果 _mapping 不可用，手动构建字典
                        row_dict = {
                            'id': row.id,
                            'social_id': row.social_id,
                            'user_id': row.user_id,
                            'status': row.status,
                            'create_time': row.create_time,
                            'update_time': row.update_time,
                            'user_name': row.user_name,
                            'entry_time': row.entry_time,
                            'department_name': row.department_name,
                            'city': row.city,
                            'project_name': row.project_name
                        }
                    processed_rows.append(row_dict)
            page_list.rows = processed_rows
        
        return page_list

    @classmethod
    async def add_user(cls, db: AsyncSession, social_id: int, user_id: int, admin_id: int):
        """单个添加社保关联人员"""
        current_time = int(datetime.now().timestamp())

        # 检查是否已存在
        existing_query = select(OaSocialSecurityUser).where(
            and_(
                OaSocialSecurityUser.social_id == social_id,
                OaSocialSecurityUser.user_id == user_id,
                OaSocialSecurityUser.delete_time == 0
            )
        )
        existing = await db.scalar(existing_query)

        if existing:
            return False, '该人员已存在于该社保信息中'

        # 添加新记录
        new_record = OaSocialSecurityUser(
            social_id=social_id,
            user_id=user_id,
            status=1,
            create_time=current_time,
            update_time=current_time
        )
        db.add(new_record)
        await db.commit()
        return True, '添加成功'

    @classmethod
    async def batch_add_users(cls, db: AsyncSession, social_id: int, user_ids: List[int], admin_id: int):
        """批量添加社保关联人员"""
        current_time = int(datetime.now().timestamp())
        added_count = 0

        for user_id in user_ids:
            # 检查是否已存在
            existing_query = select(OaSocialSecurityUser).where(
                and_(
                    OaSocialSecurityUser.social_id == social_id,
                    OaSocialSecurityUser.user_id == user_id,
                    OaSocialSecurityUser.delete_time == 0
                )
            )
            existing = await db.scalar(existing_query)

            if not existing:
                # 添加新记录
                new_record = OaSocialSecurityUser(
                    social_id=social_id,
                    user_id=user_id,
                    status=1,
                    create_time=current_time,
                    update_time=current_time
                )
                db.add(new_record)
                added_count += 1

        await db.commit()
        return added_count

    @classmethod
    async def batch_remove_users(cls, db: AsyncSession, social_id: int, user_ids: List[int]):
        """批量减员社保关联人员"""
        current_time = int(datetime.now().timestamp())
        removed_count = 0

        for user_id in user_ids:
            # 查找现有记录
            existing_query = select(OaSocialSecurityUser).where(
                and_(
                    OaSocialSecurityUser.social_id == social_id,
                    OaSocialSecurityUser.user_id == user_id,
                    OaSocialSecurityUser.delete_time == 0,
                    OaSocialSecurityUser.status == 1
                )
            )
            existing = await db.scalar(existing_query)

            if existing:
                # 更新状态为减员
                result = await db.execute(
                    update(OaSocialSecurityUser)
                    .values(status=0, update_time=current_time)
                    .where(OaSocialSecurityUser.id == existing.id)
                )
                removed_count += result.rowcount

        await db.commit()
        return removed_count

    @classmethod
    async def update_user(cls, db: AsyncSession, id: int, social_id: int = None, user_id: int = None):
        """修改用户社保关联信息"""
        current_time = int(datetime.now().timestamp())
        update_data = {'update_time': current_time}

        if social_id is not None:
            update_data['social_id'] = social_id
        if user_id is not None:
            update_data['user_id'] = user_id

        result = await db.execute(
            update(OaSocialSecurityUser)
            .values(**update_data)
            .where(
                and_(
                    OaSocialSecurityUser.id == id,
                    OaSocialSecurityUser.delete_time == 0
                )
            )
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def remove_user(cls, db: AsyncSession, id: int):
        """删除单个社保关联人员（减员）"""
        current_time = int(datetime.now().timestamp())

        result = await db.execute(
            update(OaSocialSecurityUser)
            .values(status=0, update_time=current_time, delete_time=current_time)
            .where(
                and_(
                    OaSocialSecurityUser.id == id,
                    OaSocialSecurityUser.delete_time == 0,
                    OaSocialSecurityUser.status == 1
                )
            )
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def get_users_by_social_id(cls, db: AsyncSession, social_id: int) -> List[dict]:
        """根据社保ID获取关联人员（包含用户详细信息）"""
        query = (
            select(
                OaSocialSecurityUser.id,
                OaSocialSecurityUser.social_id,
                OaSocialSecurityUser.user_id,
                OaSocialSecurityUser.status,
                OaSocialSecurityUser.create_time,
                OaSocialSecurityUser.update_time,
                OaSocialSecurityUser.delete_time,
                SysUser.nick_name.label('user_name'),
                SysUser.work_date.label('entry_time'),
                SysDept.dept_name.label('department_name'),
                OaSocialSecurity.city,
                OaSocialSecurity.project_name
            )
            .outerjoin(SysUser, OaSocialSecurityUser.user_id == SysUser.user_id)
            .outerjoin(SysDept, SysUser.dept_id == SysDept.dept_id)
            .outerjoin(OaSocialSecurity, OaSocialSecurityUser.social_id == OaSocialSecurity.id)
            .where(
                and_(
                    OaSocialSecurityUser.social_id == social_id,
                    OaSocialSecurityUser.status == 1,
                    OaSocialSecurityUser.delete_time == 0
                )
            )
        )
        result = await db.execute(query)
        rows = result.all()
        
        # 转换为字典列表
        user_list = []
        for row in rows:
            try:
                row_dict = dict(row._mapping)
            except Exception:
                row_dict = {
                    'id': row.id,
                    'social_id': row.social_id,
                    'user_id': row.user_id,
                    'status': row.status,
                    'create_time': row.create_time,
                    'update_time': row.update_time,
                    'delete_time': row.delete_time,
                    'user_name': row.user_name,
                    'entry_time': row.entry_time,
                    'department_name': row.department_name,
                    'city': row.city,
                    'project_name': row.project_name
                }
            user_list.append(row_dict)
        
        return user_list

    @classmethod
    async def import_users_from_excel(cls, db: AsyncSession, social_id: int, user_data: List[dict], admin_id: int):
        """从Excel导入社保关联人员"""
        current_time = int(datetime.now().timestamp())
        added_count = 0

        for data in user_data:
            user_id = data.get('user_id')
            if user_id:
                # 检查是否已存在
                existing_query = select(OaSocialSecurityUser).where(
                    and_(
                        OaSocialSecurityUser.social_id == social_id,
                        OaSocialSecurityUser.user_id == user_id,
                        OaSocialSecurityUser.delete_time == 0
                    )
                )
                existing = await db.scalar(existing_query)

                if not existing:
                    # 添加新记录
                    new_record = OaSocialSecurityUser(
                        social_id=social_id,
                        user_id=user_id,
                        status=1,
                        create_time=current_time,
                        update_time=current_time
                    )
                    db.add(new_record)
                    added_count += 1

        await db.commit()
        return added_count

    @classmethod
    async def get_expiring_count(cls, db: AsyncSession, days: int = 3) -> int:
        """获取即将到期的社保数量（用于预警统计）"""
        from datetime import timedelta

        today = datetime.now().day

        # 计算即将到期的日期范围（考虑跨月情况）
        expiring_days = []
        for d in range(days + 1):
            expiring_days.append((today + d - 1) % 31 + 1)

        # 查询即将到期的社保数量
        query = select(func.count(OaSocialSecurity.id)).where(
            and_(
                OaSocialSecurity.status == 1,
                OaSocialSecurity.delete_time == 0,
                OaSocialSecurity.social_date.in_(expiring_days)
            )
        )

        result = await db.execute(query)
        count = result.scalar()
        return count or 0

    @classmethod
    async def get_expiring_social_securities(cls, db: AsyncSession, days: int = 3, manager: str = None, manager_id: int = None) -> List[dict]:
        """获取即将到期的社保信息（用于工作台提醒）"""
        from datetime import timedelta

        today = datetime.now().day

        # 计算即将到期的日期范围
        expiring_days = []
        for d in range(days + 1):
            expiring_days.append((today + d - 1) % 31 + 1)

        # 构建条件列表
        conditions = [
            OaSocialSecurity.status == 1,
            OaSocialSecurity.delete_time == 0,
            OaSocialSecurity.social_date.in_(expiring_days),
            OaSocialSecurityUser.status == 1,
            OaSocialSecurityUser.delete_time == 0
        ]

        # 添加负责人筛选条件
        if manager:
            conditions.append(OaSocialSecurity.manager.like(f'%{manager}%'))
        if manager_id:
            conditions.append(OaSocialSecurity.manager_id == manager_id)

        # 查询即将到期的社保信息
        query = (
            select(
                OaSocialSecurity,
                func.group_concat(SysUser.nick_name).label('related_users')
            )
            .outerjoin(OaSocialSecurityUser, OaSocialSecurity.id == OaSocialSecurityUser.social_id)
            .outerjoin(SysUser, OaSocialSecurityUser.user_id == SysUser.user_id)
            .where(and_(*conditions))
            .group_by(OaSocialSecurity.id)
        )

        result = await db.execute(query)
        rows = result.all()

        expiring_list = []
        for row in rows:
            social_info = row[0]
            related_users = row[1] or ''

            expiring_list.append({
                'id': social_info.id,
                'city': social_info.city,
                'projectName': social_info.project_name,
                'socialDate': social_info.social_date,
                'relatedUsers': related_users,
                'createTime': social_info.create_time
            })

        return expiring_list