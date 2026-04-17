from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_project.entity.do.project_do import OaProject
from module_project.entity.do.project_task_do import OaProjectTask
from module_project.entity.do.project_step_do import OaProjectStep
from module_project.entity.vo.project_vo import ProjectModel, ProjectPageQueryModel
from utils.page_util import PageUtil


class ProjectDao:
    """
    项目管理模块数据库操作层
    """

    @classmethod
    async def get_project_detail_by_id(cls, db: AsyncSession, project_id: int) -> dict[str, Any] | None:
        """
        根据项目 ID 获取项目详细信息

        :param db: orm 对象
        :param project_id: 项目 ID
        :return: 项目详细信息对象
        """
        query = select(OaProject).where(OaProject.id == project_id, OaProject.delete_time == 0)
        project_info = (await db.execute(query)).scalars().first()

        if not project_info:
            return None

        result = {
            'project_info': project_info,
            'cate_title': None,
            'customer_name': None,
            'contract_name': None,
            'admin_name': None,
            'director_name': None,
            'dept_name': None,
            'status_name': None,
        }

        # 查询分类名称
        if project_info.cate_id and project_info.cate_id > 0:
            from module_basicdata.dao.project.project_cate_dao import ProjectCateDao
            cate_info = await ProjectCateDao.get_info_by_id(db, project_info.cate_id)
            if cate_info:
                result['cate_title'] = cate_info.title

        # 查询创建人姓名
        if project_info.admin_id and project_info.admin_id > 0:
            from module_admin.dao.user_dao import UserDao
            admin_result = await UserDao.get_user_by_id(db, project_info.admin_id)
            if admin_result and admin_result.get('user_basic_info'):
                admin_info = admin_result['user_basic_info']
                result['admin_name'] = admin_info.nick_name or admin_info.user_name

        # 查询项目负责人姓名
        if project_info.director_uid and project_info.director_uid > 0:
            from module_admin.dao.user_dao import UserDao
            director_result = await UserDao.get_user_by_id(db, project_info.director_uid)
            if director_result and director_result.get('user_basic_info'):
                director_info = director_result['user_basic_info']
                result['director_name'] = director_info.nick_name or director_info.user_name

        # 查询部门名称
        if project_info.did and project_info.did > 0:
            from module_admin.dao.dept_dao import DeptDao
            dept_info = await DeptDao.get_dept_by_id(db, project_info.did)
            if dept_info:
                result['dept_name'] = dept_info.dept_name

        # 设置状态名称
        status_map = {
            0: '未设置',
            1: '未开始',
            2: '进行中',
            3: '已完成',
            4: '已关闭'
        }
        if project_info.status is not None:
            result['status_name'] = status_map.get(project_info.status, '未知')

        return result

    @classmethod
    async def get_project_list(
            cls, db: AsyncSession, query_object: ProjectPageQueryModel, user_id: int,
            auth_dids: str = '', son_dids: str = '', is_admin: bool = False,
            is_project_admin: bool = False, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        根据查询参数获取项目列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param user_id: 当前用户 ID
        :param auth_dids: 可见部门数据
        :param son_dids: 可见子部门数据
        :param is_admin: 是否为超级管理员
        :param is_project_admin: 是否为项目管理员
        :param is_page: 是否开启分页
        :return: 项目列表信息对象
        """
        # 基础条件：未删除
        conditions = [OaProject.delete_time == 0]

        # 状态筛选
        if query_object.status_filter is not None:
            conditions.append(OaProject.status == query_object.status_filter)

        # 分类筛选
        if query_object.cate_id_filter is not None:
            conditions.append(OaProject.cate_id == query_object.cate_id_filter)

        # 客户筛选（支持多选）
        if query_object.customer_id_filter:
            conditions.append(OaProject.customer_id.in_(query_object.customer_id_filter))

        # 关键词搜索
        if query_object.keywords:
            conditions.append(
                or_(
                    OaProject.name.like(f'%{query_object.keywords}%'),
                    OaProject.content.like(f'%{query_object.keywords}%')
                )
            )

        # 负责人筛选
        if query_object.director_uid_filter:
            conditions.append(OaProject.director_uid.in_(query_object.director_uid_filter))

        # 根据 tab 参数设置查询条件
        current_time = int(datetime.now().timestamp())
        if query_object.tab == 0:
            # 全部项目
            pass
        elif query_object.tab == 1:
            # 进行中的项目
            conditions.append(OaProject.status == 2)
        elif query_object.tab == 2:
            # 即将到期的项目（7 天内）
            seven_days_later = current_time + 7 * 86400
            conditions.append(OaProject.status < 3)
            conditions.append(OaProject.end_time.between(current_time, seven_days_later))
        elif query_object.tab == 3:
            # 已逾期的项目
            conditions.append(OaProject.status < 3)
            conditions.append(OaProject.end_time < current_time)

        # 数据权限过滤（非管理员且非项目管理员）
        if not is_admin and not is_project_admin:
            permission_conditions = [
                OaProject.admin_id == user_id,
                OaProject.director_uid == user_id,
                ]

            # 部门权限
            if auth_dids or son_dids:
                dept_ids = set()
                if auth_dids:
                    dept_ids.update([int(d.strip()) for d in auth_dids.split(',') if d.strip()])
                if son_dids:
                    dept_ids.update([int(d.strip()) for d in son_dids.split(',') if d.strip()])

                if dept_ids:
                    permission_conditions.append(OaProject.did.in_(dept_ids))

            if permission_conditions:
                conditions.append(or_(*permission_conditions))

        query = (
            select(OaProject)
            .where(*conditions)
            .order_by(OaProject.create_time.desc())
            .distinct()
        )

        project_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        # 为每个项目添加扩展字段
        if isinstance(project_list, PageModel) and hasattr(project_list, 'rows'):
            enhanced_rows = []
            for project in project_list.rows:
                try:
                    enhanced_project = await cls._enrich_project_data(db, project)
                    enhanced_rows.append(enhanced_project)
                except Exception as e:
                    # 如果出错，记录日志并返回基础数据
                    from utils.log_util import logger
                    logger.error(f" enrich project data error: {str(e)}, project_id: {project.id}")
                    enhanced_project = cls._get_basic_project_data(project)
                    enhanced_rows.append(enhanced_project)
            project_list.rows = enhanced_rows
        elif isinstance(project_list, list):
            enhanced_list = []
            for project in project_list:
                try:
                    enhanced_project = await cls._enrich_project_data(db, project)
                    enhanced_list.append(enhanced_project)
                except Exception as e:
                    from utils.log_util import logger
                    logger.error(f" enrich project data error: {str(e)}, project_id: {project.id}")
                    enhanced_project = cls._get_basic_project_data(project)
                    enhanced_list.append(enhanced_project)
            project_list = enhanced_list

        return project_list

    @classmethod
    async def _enrich_project_data(cls, db: AsyncSession, project: OaProject) -> dict[str, Any]:
        """
        为项目数据添加扩展字段

        :param db: orm 对象
        :param project: 项目对象
        :return: 增强后的项目数据字典
        """
        from datetime import datetime as dt
        
        # 从 ORM 对象获取字典，保留所有原始字段值
        project_dict = {}
        for column in OaProject.__table__.columns:
            value = getattr(project, column.name)
            project_dict[column.name] = value

        # 添加 title 字段（与 name 相同）
        project_dict['title'] = project.name or ''

        # 查询分类名称
        if project.cate_id and project.cate_id > 0:
            from module_basicdata.dao.project.project_cate_dao import ProjectCateDao
            cate_info = await ProjectCateDao.get_info_by_id(db, project.cate_id)
            if cate_info:
                project_dict['cate'] = cate_info.title
                project_dict['cate_title'] = cate_info.title
            else:
                project_dict['cate'] = ''
                project_dict['cate_title'] = ''
        else:
            project_dict['cate'] = ''
            project_dict['cate_title'] = ''

        # 查询创建人姓名
        if project.admin_id and project.admin_id > 0:
            from module_admin.dao.user_dao import UserDao
            admin_result = await UserDao.get_user_by_id(db, project.admin_id)
            if admin_result and admin_result.get('user_basic_info'):
                admin_info = admin_result['user_basic_info']
                project_dict['admin_name'] = admin_info.nick_name or admin_info.user_name
            else:
                project_dict['admin_name'] = ''
        else:
            project_dict['admin_name'] = ''

        # 查询项目负责人姓名
        if project.director_uid and project.director_uid > 0:
            from module_admin.dao.user_dao import UserDao
            director_result = await UserDao.get_user_by_id(db, project.director_uid)
            if director_result and director_result.get('user_basic_info'):
                director_info = director_result['user_basic_info']
                project_dict['director_name'] = director_info.nick_name or director_info.user_name
            else:
                project_dict['director_name'] = ''
        else:
            project_dict['director_name'] = ''

        # 查询部门名称
        if project.did and project.did > 0:
            from module_admin.dao.dept_dao import DeptDao
            dept_info = await DeptDao.get_dept_by_id(db, project.did)
            if dept_info:
                project_dict['department'] = dept_info.dept_name
                project_dict['dept_name'] = dept_info.dept_name
            else:
                project_dict['department'] = ''
                project_dict['dept_name'] = ''
        else:
            project_dict['department'] = ''
            project_dict['dept_name'] = ''

        # 设置状态名称
        status_map = {
            0: '未设置',
            1: '未开始',
            2: '进行中',
            3: '已完成',
            4: '已关闭'
        }
        project_dict['status_name'] = status_map.get(project.status if project.status is not None else 0, '未知')

        # 计算时间范围字符串
        if project.start_time and project.end_time:
            from utils.time_format_util import timestamp_to_datetime
            start_str = timestamp_to_datetime(project.start_time, '%Y-%m-%d')
            end_str = timestamp_to_datetime(project.end_time, '%Y-%m-%d')
            project_dict['range_time'] = f"{start_str} 至 {end_str}"
        else:
            project_dict['range_time'] = ''

        # 计算延迟天数
        current_timestamp = int(dt.now().timestamp())
        if project.end_time and project.status is not None and project.status < 3:
            if current_timestamp > project.end_time:
                delay_days = (current_timestamp - project.end_time) // 86400
                project_dict['delay'] = delay_days
            else:
                project_dict['delay'] = 0
        else:
            project_dict['delay'] = 0

        # 统计任务数量
        task_stats = await cls._get_task_statistics(db, project.id)
        project_dict.update(task_stats)

        # 获取当前阶段信息
        step_info = await cls._get_current_step_info(db, project.id)
        project_dict.update(step_info)

        return project_dict

    @classmethod
    def _get_basic_project_data(cls, project: OaProject) -> dict[str, Any]:
        """
        获取项目基础数据（不带关联查询）

        :param project: 项目对象
        :return: 基础项目数据字典
        """
        project_dict = project.__dict__.copy()
        project_dict.pop('_sa_instance_state', None)
        
        # 设置默认值
        project_dict['title'] = project.name or ''
        project_dict['cate'] = ''
        project_dict['cate_title'] = ''
        project_dict['admin_name'] = ''
        project_dict['director_name'] = ''
        project_dict['department'] = ''
        project_dict['dept_name'] = ''
        
        status_map = {
            0: '未设置',
            1: '未开始',
            2: '进行中',
            3: '已完成',
            4: '已关闭'
        }
        project_dict['status_name'] = status_map.get(project.status if project.status is not None else 0, '未知')
        project_dict['range_time'] = ''
        project_dict['delay'] = 0
        project_dict['tasks_total'] = 0
        project_dict['tasks_finish'] = 0
        project_dict['tasks_unfinish'] = 0
        project_dict['tasks_pensent'] = "0％"
        project_dict['step_director'] = ''
        project_dict['step'] = ''
        
        return project_dict

    @classmethod
    async def _get_task_statistics(cls, db: AsyncSession, project_id: int) -> dict[str, Any]:
        """
        获取项目任务统计信息

        :param db: orm 对象
        :param project_id: 项目 ID
        :return: 任务统计信息
        """
        # 任务总数
        total_query = select(func.count()).select_from(OaProjectTask).where(
            OaProjectTask.project_id == project_id,
            OaProjectTask.delete_time == 0
        )
        tasks_total = (await db.execute(total_query)).scalar() or 0

        # 已完成任务数（status > 2 表示已完成）
        finish_query = select(func.count()).select_from(OaProjectTask).where(
            OaProjectTask.project_id == project_id,
            OaProjectTask.status > 2,
            OaProjectTask.delete_time == 0
        )
        tasks_finish = (await db.execute(finish_query)).scalar() or 0

        # 未完成任务数
        tasks_unfinish = tasks_total - tasks_finish

        # 任务完成百分比
        if tasks_total > 0:
            percentage = int((tasks_finish / tasks_total) * 100)
            tasks_pensent = f"{percentage}％"
        else:
            tasks_pensent = "0％"

        return {
            'tasks_total': tasks_total,
            'tasks_finish': tasks_finish,
            'tasks_unfinish': tasks_unfinish,
            'tasks_pensent': tasks_pensent
        }

    @classmethod
    async def _get_current_step_info(cls, db: AsyncSession, project_id: int) -> dict[str, Any]:
        """
        获取当前阶段信息

        :param db: orm 对象
        :param project_id: 项目 ID
        :return: 当前阶段信息
        """
        # 查询当前阶段
        step_query = select(OaProjectStep).where(
            OaProjectStep.project_id == project_id,
            OaProjectStep.is_current == 1,
            OaProjectStep.delete_time == 0
        )
        current_step = (await db.execute(step_query)).scalars().first()

        if current_step:
            # 获取阶段负责人姓名
            step_director = ''
            if current_step.director_uid and current_step.director_uid > 0:
                from module_admin.dao.user_dao import UserDao
                director_result = await UserDao.get_user_by_id(db, current_step.director_uid)
                if director_result and director_result.get('user_basic_info'):
                    step_director = director_result['user_basic_info'].nick_name or director_result['user_basic_info'].user_name

            # 构建阶段信息字符串：阶段名称『负责人姓名』
            step_info = f"{current_step.title}『{step_director}』" if step_director else current_step.title

            return {
                'step_director': step_director,
                'step': step_info
            }
        else:
            return {
                'step_director': '',
                'step': ''
            }

    @classmethod
    async def get_project_detail_by_info(cls, db: AsyncSession, project: ProjectModel) -> OaProject | None:
        """
        根据项目参数获取信息

        :param db: orm 对象
        :param project: 项目参数对象
        :return: 项目信息对象
        """
        query_conditions = [OaProject.delete_time == 0]

        if project.id is not None:
            query_conditions.append(OaProject.id == project.id)
        if project.name:
            query_conditions.append(OaProject.name == project.name)

        if query_conditions:
            project_info = (
                (await db.execute(select(OaProject).where(and_(*query_conditions))))
                .scalars()
                .first()
            )
        else:
            project_info = None

        return project_info

    @classmethod
    async def add_project_dao(cls, db: AsyncSession, project: dict | ProjectModel) -> OaProject:
        """
        新增项目数据库操作

        :param db: orm 对象
        :param project: 项目对象或字典
        :return:
        """
        from pydantic import BaseModel

        # 如果是 Pydantic 模型，转换为字典
        if isinstance(project, BaseModel):
            project_data = project.model_dump()
        else:
            project_data = project

        # 只提取 OaProject 模型中存在的字段
        valid_fields = {c.name for c in OaProject.__table__.columns}
        filtered_data = {
            k: v for k, v in project_data.items()
            if k in valid_fields
        }
        db_project = OaProject(**filtered_data)
        db.add(db_project)
        await db.flush()

        return db_project

    @classmethod
    async def edit_project_dao(cls, db: AsyncSession, project_id: int, project: dict) -> None:
        """
        编辑项目数据库操作

        :param db: orm 对象
        :param project_id: 项目 ID
        :param project: 需要更新的项目字典
        :return:
        """
        await db.execute(
            update(OaProject)
            .where(OaProject.id == project_id)
            .values(**project)
        )

    @classmethod
    async def delete_project_dao(cls, db: AsyncSession, project: ProjectModel) -> None:
        """
        删除项目数据库操作（逻辑删除）

        :param db: orm 对象
        :param project: 项目对象
        :return:
        """
        update_time = project.update_time if project.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(OaProject)
            .where(OaProject.id == project.id)
            .values(delete_time=update_time, update_time=update_time)
        )

    @classmethod
    async def get_project_count(cls, db: AsyncSession, user_id:int) -> None:
        """
        恢复项目数据库操作（逻辑恢复）

        :param user_id: 用户 ID
        :param db: orm 对象
        :return:
        """
        query = select(func.count()).select_from(OaProject).where(OaProject.director_uid == user_id, OaProject.delete_time == 0)
        result = await db.execute(query)
        count = result.scalar()
        return count
