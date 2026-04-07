from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, or_, select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_project.entity.do.project_task_do import OaProjectTask
from module_project.entity.vo.project_task_vo import ProjectTaskModel, ProjectTaskPageQueryModel
from utils.page_util import PageUtil
from utils.timeformat import format_date


class ProjectTaskDao:
    """
    项目任务管理模块数据库操作层
    """

    @classmethod
    async def get_project_task_detail_by_id(cls, db: AsyncSession, task_id: int) -> dict[str, Any] | None:
        """
        根据任务 ID 获取任务详细信息

        :param db: orm 对象
        :param task_id: 任务 ID
        :return: 任务详细信息对象
        """
        query = select(OaProjectTask).where(OaProjectTask.id == task_id, OaProjectTask.delete_time == 0)
        task_info = (await db.execute(query)).scalars().first()

        if not task_info:
            return None

        result = {
            'task_info': task_info,
            'project_name': None,
            'admin_name': None,
            'director_name': None,
            'dept_name': None,
            'priority_name': None,
            'status_name': None,
            'end_time_str': None,
        }

        # 查询项目名称
        if task_info.project_id and task_info.project_id > 0:
            from module_project.dao.project_dao import ProjectDao
            project_info = await ProjectDao.get_project_detail_by_id(db, task_info.project_id)
            if project_info:
                result['project_name'] = project_info.get('name')

        # 查询创建人姓名
        if task_info.admin_id and task_info.admin_id > 0:
            from module_admin.dao.user_dao import UserDao
            admin_result = await UserDao.get_user_by_id(db, task_info.admin_id)
            if admin_result and admin_result.get('user_basic_info'):
                admin_info = admin_result['user_basic_info']
                result['admin_name'] = admin_info.nick_name or admin_info.user_name

        # 查询负责人姓名
        if task_info.director_uid and task_info.director_uid > 0:
            from module_admin.dao.user_dao import UserDao
            director_result = await UserDao.get_user_by_id(db, task_info.director_uid)
            if director_result and director_result.get('user_basic_info'):
                director_info = director_result['user_basic_info']
                result['director_name'] = director_info.nick_name or director_info.user_name

        # 查询部门名称
        if task_info.did and task_info.did > 0:
            from module_admin.dao.dept_dao import DeptDao
            dept_info = await DeptDao.get_dept_detail_by_id(db, task_info.did)
            if dept_info:
                result['dept_name'] = dept_info.dept_name

        # 设置优先级名称
        priority_map = {
            1: '低',
            2: '中',
            3: '高',
            4: '紧急'
        }
        if task_info.priority is not None:
            result['priority_name'] = priority_map.get(task_info.priority, '未知')

        # 设置状态名称
        status_map = {
            1: '待办的',
            2: '进行中',
            3: '已完成',
            4: '已拒绝',
            5: '已关闭'
        }
        if task_info.status is not None:
            result['status_name'] = status_map.get(task_info.status, '未知')

        # 格式化时间
        if task_info.end_time:
            result['end_time_str'] = format_date(task_info.end_time, '%Y-%m-%d')

        return result

    @classmethod
    async def get_project_task_detail_by_info(cls, db: AsyncSession, task: ProjectTaskModel) -> OaProjectTask | None:
        """
        根据任务参数获取信息

        :param db: orm 对象
        :param task: 任务参数对象
        :return: 任务信息对象
        """
        query_conditions = [OaProjectTask.delete_time == 0]

        if task.id is not None:
            query_conditions.append(OaProjectTask.id == task.id)
        if task.title:
            query_conditions.append(OaProjectTask.title == task.title)

        if query_conditions:
            task_info = (
                (await db.execute(select(OaProjectTask).where(and_(*query_conditions))))
                .scalars()
                .first()
            )
        else:
            task_info = None

        return task_info

    @classmethod
    async def check_task_title_unique(cls, db: AsyncSession, title: str, project_id: int, exclude_id: int | None = None) -> bool:
        """
        检查任务主题在同一项目下是否唯一

        :param db: orm 对象
        :param title: 任务主题
        :param project_id: 项目 ID
        :param exclude_id: 排除的任务 ID（编辑时使用）
        :return: True 表示唯一，False 表示重复
        """
        # 构建查询条件
        conditions = [
            OaProjectTask.delete_time == 0,
            OaProjectTask.title == (title if title else ''),
            OaProjectTask.project_id == (project_id if project_id else 0)
        ]
        
        if exclude_id is not None and exclude_id > 0:
            conditions.append(OaProjectTask.id != exclude_id)
        
        # 执行查询
        count_query = select(func.count('*')).select_from(OaProjectTask).where(and_(*conditions))
        count_result = await db.execute(count_query)
        count = count_result.scalar()
        
        logger.info(f'任务验重 - title: {title}, project_id: {project_id}, exclude_id: {exclude_id}, 重复数量：{count}')
        
        return count == 0

    @classmethod
    async def get_project_task_list(
            cls, db: AsyncSession, query_object: ProjectTaskPageQueryModel, user_id: int,
            auth_dids: str = '', son_dids: str = '', is_admin: bool = False,
            is_project_admin: bool = False, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        根据查询参数获取任务列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param user_id: 当前用户 ID
        :param auth_dids: 可见部门数据
        :param son_dids: 可见子部门数据
        :param is_admin: 是否为超级管理员
        :param is_project_admin: 是否为项目管理员
        :param is_page: 是否开启分页
        :return: 任务列表信息对象
        """
        # 基础条件：未删除
        conditions = [OaProjectTask.delete_time == 0]

        # 状态筛选
        if query_object.status_filter is not None:
            conditions.append(OaProjectTask.status == query_object.status_filter)

        # 优先级筛选
        if query_object.priority_filter is not None:
            conditions.append(OaProjectTask.priority == query_object.priority_filter)

        # 工作类型筛选
        if query_object.work_id_filter is not None:
            conditions.append(OaProjectTask.work_id == query_object.work_id_filter)

        # 项目筛选
        if query_object.project_id_filter is not None:
            conditions.append(OaProjectTask.project_id == query_object.project_id_filter)

        # 关键词搜索
        if query_object.keywords:
            conditions.append(
                or_(
                    OaProjectTask.title.like(f'%{query_object.keywords}%'),
                    OaProjectTask.content.like(f'%{query_object.keywords}%')
                )
            )

        # 负责人筛选
        if query_object.director_uid_filter:
            conditions.append(OaProjectTask.director_uid.in_(query_object.director_uid_filter))

        # 根据 tab 参数设置查询条件
        current_time = int(datetime.now().timestamp())
        seven_days_later = current_time + 7 * 86400

        if query_object.tab == 1:
            # 进行中
            conditions.append(OaProjectTask.status < 3)
        elif query_object.tab == 2:
            # 即将逾期
            conditions.append(OaProjectTask.status < 3)
            conditions.append(OaProjectTask.end_time.between(current_time, seven_days_later))
        elif query_object.tab == 3:
            # 已逾期
            conditions.append(OaProjectTask.status < 3)
            conditions.append(OaProjectTask.end_time < current_time)

        # 数据权限过滤（非管理员且非项目管理员）
        if not is_admin and not is_project_admin:
            permission_conditions = [
                OaProjectTask.admin_id == user_id,
                OaProjectTask.director_uid == user_id,
                ]

            # 部门权限
            if auth_dids or son_dids:
                dept_ids = set()
                if auth_dids:
                    dept_ids.update([int(d.strip()) for d in auth_dids.split(',') if d.strip()])
                if son_dids:
                    dept_ids.update([int(d.strip()) for d in son_dids.split(',') if d.strip()])

                if dept_ids:
                    permission_conditions.append(OaProjectTask.did.in_(dept_ids))

            # 协助人员
            permission_conditions.append(
                OaProjectTask.assist_admin_ids.like(f'%{user_id}%')
            )

            if permission_conditions:
                conditions.append(or_(*permission_conditions))

        query = (
            select(OaProjectTask)
            .where(*conditions)
            .order_by(OaProjectTask.status.asc(), OaProjectTask.create_time.desc())
            .distinct()
        )

        task_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return task_list

    @classmethod
    async def add_project_task_dao(cls, db: AsyncSession, task: dict | ProjectTaskModel) -> OaProjectTask:
        """
        新增项目任务数据库操作

        :param db: orm 对象
        :param task: 任务对象或字典
        :return:
        """
        from pydantic import BaseModel

        # 如果是 Pydantic 模型，转换为字典
        if isinstance(task, BaseModel):
            task_data = task.model_dump()
        else:
            task_data = task

        # 只提取 OaProjectTask 模型中存在的字段
        valid_fields = {c.name for c in OaProjectTask.__table__.columns}
        filtered_data = {
            k: v for k, v in task_data.items()
            if k in valid_fields
        }
        db_task = OaProjectTask(**filtered_data)
        db.add(db_task)
        await db.flush()

        return db_task

    @classmethod
    async def edit_project_task_dao(cls, db: AsyncSession, task_id: int, task: dict) -> None:
        """
        编辑项目任务数据库操作

        :param db: orm 对象
        :param task_id: 任务 ID
        :param task: 需要更新的任务字典
        :return:
        """
        # 只提取 OaProjectTask 模型中存在的字段，过滤掉扩展字段
        valid_fields = {c.name for c in OaProjectTask.__table__.columns}
        filtered_data = {
            k: v for k, v in task.items()
            if k in valid_fields
        }
        
        await db.execute(
            update(OaProjectTask)
            .where(OaProjectTask.id == task_id)
            .values(**filtered_data)
        )

    @classmethod
    async def delete_project_task_dao(cls, db: AsyncSession, task_id: int) -> None:
        """
        删除项目任务数据库操作（逻辑删除）

        :param db: orm 对象
        :param task_id: 任务 ID
        :return:
        """
        update_time = int(datetime.now().timestamp())
        await db.execute(
            update(OaProjectTask)
            .where(OaProjectTask.id == task_id)
            .values(delete_time=update_time, update_time=update_time)
        )
