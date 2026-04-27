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
        根据查询参数获取项目列表信息（使用原生SQL）

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
        from sqlalchemy import text
        from utils.log_util import logger
        
        # 构建 WHERE 条件
        conditions = ["p.delete_time = 0"]
        params = {}
        
        # 状态筛选
        if query_object.status_filter is not None:
            conditions.append("p.status = :status_filter")
            params['status_filter'] = query_object.status_filter
        
        # 分类筛选
        if query_object.cate_id_filter is not None:
            conditions.append("p.cate_id = :cate_id_filter")
            params['cate_id_filter'] = query_object.cate_id_filter
        
        # 客户筛选（支持多选）
        if query_object.customer_id_filter:
            conditions.append("p.customer_id IN :customer_ids")
            params['customer_ids'] = tuple(query_object.customer_id_filter)
        
        # 关键词搜索
        if query_object.keywords:
            conditions.append("(p.name LIKE :keywords OR p.content LIKE :keywords)")
            params['keywords'] = f"%{query_object.keywords}%"
        
        # 负责人筛选
        if query_object.director_uid_filter:
            conditions.append("p.director_uid IN :director_uids")
            params['director_uids'] = tuple(query_object.director_uid_filter)
        
        # 根据 tab 参数设置查询条件
        current_time = int(datetime.now().timestamp())
        if query_object.tab == 1:
            # 进行中的项目
            conditions.append("p.status = 2")
        elif query_object.tab == 2:
            # 即将到期的项目（7 天内）
            seven_days_later = current_time + 7 * 86400
            conditions.append("p.status < 3")
            conditions.append("p.end_time BETWEEN :current_time AND :seven_days_later")
            params['current_time'] = current_time
            params['seven_days_later'] = seven_days_later
        elif query_object.tab == 3:
            # 已逾期的项目
            conditions.append("p.status < 3")
            conditions.append("p.end_time < :current_time")
            params['current_time'] = current_time
        
        # 数据权限过滤（非管理员且非项目管理员）
        if not is_admin and not is_project_admin:
            permission_conditions = [
                "p.admin_id = :user_id",
                "p.director_uid = :user_id",
            ]
            params['user_id'] = user_id
            
            # 部门权限
            if auth_dids or son_dids:
                dept_ids = set()
                if auth_dids:
                    dept_ids.update([int(d.strip()) for d in auth_dids.split(',') if d.strip()])
                if son_dids:
                    dept_ids.update([int(d.strip()) for d in son_dids.split(',') if d.strip()])
                
                if dept_ids:
                    permission_conditions.append("p.did IN :dept_ids")
                    params['dept_ids'] = tuple(dept_ids)
            
            if permission_conditions:
                conditions.append("(" + " OR ".join(permission_conditions) + ")")
        
        where_clause = " AND ".join(conditions)
        
        # 分页参数
        page_num = query_object.page_num if query_object.page_num else 1
        page_size = query_object.page_size if query_object.page_size else 10
        offset = (page_num - 1) * page_size
        
        # 主查询 SQL
        sql = text(f"""
            SELECT 
                p.id,
                p.name,
                p.code,
                p.amount,
                p.cate_id AS cateId,
                p.customer_id AS customerId,
                p.contract_id AS contractId,
                p.admin_id AS adminId,
                p.director_uid AS directorUid,
                p.did,
                p.start_time AS startTime,
                p.end_time AS endTime,
                p.status,
                p.content,
                p.create_time AS createTime,
                p.update_time AS updateTime,
                p.delete_time AS deleteTime,
                p.name AS title,
                '' AS cate,
                '' AS cateTitle,
                '' AS adminName,
                '' AS directorName,
                '' AS department,
                '' AS deptName,
                CASE p.status
                    WHEN 0 THEN '未设置'
                    WHEN 1 THEN '未开始'
                    WHEN 2 THEN '进行中'
                    WHEN 3 THEN '已完成'
                    WHEN 4 THEN '已关闭'
                    ELSE '未知'
                END AS statusName,
                '' AS rangeTime,
                0 AS delay,
                0 AS tasksTotal,
                0 AS tasksOngoing,
                0 AS tasksFinish,
                0 AS tasksUnfinish,
                '0％' AS tasksPensent,
                '' AS stepDirector,
                '' AS step
            FROM oa_project p
            WHERE {where_clause}
            ORDER BY p.create_time DESC
            LIMIT :limit OFFSET :offset
        """)
        
        # 总数查询 SQL
        count_sql = text(f"""
            SELECT COUNT(*) as total
            FROM oa_project p
            WHERE {where_clause}
        """)
        
        # 添加分页参数
        params['limit'] = page_size
        params['offset'] = offset
        
        # 执行总数查询
        count_result = await db.execute(count_sql, params)
        total = count_result.scalar()
        
        # 执行主查询
        result = await db.execute(sql, params)
        rows = result.mappings().all()
        
        # 转换为字典列表并处理数据
        project_list = []
        for row in rows:
            project_dict = dict(row)
            
            # 处理数值类型
            for key in ['id', 'cateId', 'customerId', 'contractId', 'adminId', 'directorUid', 'did',
                        'startTime', 'endTime', 'status', 'createTime', 'updateTime', 'deleteTime',
                        'delay', 'tasksTotal', 'tasksOngoing', 'tasksFinish', 'tasksUnfinish']:
                if key in project_dict and project_dict[key] is not None:
                    project_dict[key] = int(project_dict[key])
            
            # 处理浮点数
            if 'amount' in project_dict and project_dict['amount'] is not None:
                project_dict['amount'] = float(project_dict['amount'])
            
            # 处理字符串默认值
            for str_key in ['code', 'cate', 'cateTitle', 'adminName', 'directorName', 
                           'department', 'deptName', 'rangeTime', 'stepDirector', 'step', 'tasksPensent']:
                if str_key not in project_dict or project_dict[str_key] is None:
                    project_dict[str_key] = ''
            
            project_list.append(project_dict)
        
        # 为每个项目补充关联数据和任务统计
        for project_dict in project_list:
            project_id = project_dict['id']
            
            # 查询分类名称
            if project_dict.get('cateId') and project_dict['cateId'] > 0:
                from module_basicdata.dao.project.project_cate_dao import ProjectCateDao
                cate_info = await ProjectCateDao.get_info_by_id(db, project_dict['cateId'])
                if cate_info:
                    project_dict['cate'] = cate_info.title
                    project_dict['cateTitle'] = cate_info.title
            
            # 查询创建人姓名
            if project_dict.get('adminId') and project_dict['adminId'] > 0:
                from module_admin.dao.user_dao import UserDao
                admin_result = await UserDao.get_user_by_id(db, project_dict['adminId'])
                if admin_result and admin_result.get('user_basic_info'):
                    admin_info = admin_result['user_basic_info']
                    project_dict['adminName'] = admin_info.nick_name or admin_info.user_name
            
            # 查询项目负责人姓名
            if project_dict.get('directorUid') and project_dict['directorUid'] > 0:
                from module_admin.dao.user_dao import UserDao
                director_result = await UserDao.get_user_by_id(db, project_dict['directorUid'])
                if director_result and director_result.get('user_basic_info'):
                    director_info = director_result['user_basic_info']
                    project_dict['directorName'] = director_info.nick_name or director_info.user_name
            
            # 查询部门名称
            if project_dict.get('did') and project_dict['did'] > 0:
                from module_admin.dao.dept_dao import DeptDao
                dept_info = await DeptDao.get_dept_by_id(db, project_dict['did'])
                if dept_info:
                    project_dict['department'] = dept_info.dept_name
                    project_dict['deptName'] = dept_info.dept_name
            
            # 计算时间范围字符串
            if project_dict.get('startTime') and project_dict.get('endTime'):
                from utils.time_format_util import timestamp_to_datetime
                start_str = timestamp_to_datetime(project_dict['startTime'], '%Y-%m-%d')
                end_str = timestamp_to_datetime(project_dict['endTime'], '%Y-%m-%d')
                project_dict['rangeTime'] = f"{start_str} 至 {end_str}"
            
            # 计算延迟天数
            current_timestamp = int(datetime.now().timestamp())
            if project_dict.get('endTime') and project_dict.get('status') is not None and project_dict['status'] < 3:
                if current_timestamp > project_dict['endTime']:
                    delay_days = (current_timestamp - project_dict['endTime']) // 86400
                    project_dict['delay'] = delay_days
            
            # 统计任务数量
            task_stats = await cls._get_task_statistics(db, project_id)
            project_dict['tasksTotal'] = task_stats['tasks_total']
            project_dict['tasksOngoing'] = task_stats['tasks_ongoing']
            project_dict['tasksFinish'] = task_stats['tasks_finish']
            project_dict['tasksUnfinish'] = task_stats['tasks_unfinish']
            project_dict['tasksPensent'] = task_stats['tasks_pensent']
            
            # 获取当前阶段信息
            step_info = await cls._get_current_step_info(db, project_id)
            if project_dict.get('status') == 4:
                project_dict['step'] = ''
            else:
                project_dict['stepDirector'] = step_info.get('step_director', '')
                project_dict['step'] = step_info.get('step', '')
        
        # 构建返回结果
        if is_page:
            has_next = page_num * page_size < total
            logger.info(f"【项目列表】返回分页结果，总数:{total}, 当前页:{page_num}, 每页:{page_size}, 是否有下一页:{has_next}")
            return {
                'rows': project_list,
                'pageNum': page_num,
                'pageSize': page_size,
                'total': total,
                'hasNext': has_next
            }
        else:
            logger.info(f"【项目列表】返回非分页结果，共{len(project_list)}条记录")
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
        
        # 当 status=4（已关闭）时，step 显示为空
        if project.status == 4:
            step_info = {
                'step': ''
            }
        
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
        project_dict['tasks_ongoing'] = 0
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
        from utils.log_util import logger
        
        logger.info(f"【任务统计】开始统计项目 {project_id} 的任务")
        
        # 任务总数（排除已删除）
        total_query = select(func.count()).select_from(OaProjectTask).where(
            OaProjectTask.project_id == project_id,
            OaProjectTask.delete_time == 0
        )
        tasks_total = (await db.execute(total_query)).scalar() or 0
        logger.info(f"【任务统计】项目 {project_id} - 总任务数: {tasks_total}")

        # 进行中任务数（status = 2，仅进行中）
        ongoing_query = select(func.count()).select_from(OaProjectTask).where(
            OaProjectTask.project_id == project_id,
            OaProjectTask.status == 2,
            OaProjectTask.delete_time == 0
        )
        tasks_ongoing = (await db.execute(ongoing_query)).scalar() or 0
        logger.info(f"【任务统计】项目 {project_id} - 进行中任务数(status=2): {tasks_ongoing}")

        # 已完成任务数（status = 3，仅已完成）
        finish_query = select(func.count()).select_from(OaProjectTask).where(
            OaProjectTask.project_id == project_id,
            OaProjectTask.status == 3,
            OaProjectTask.delete_time == 0
        )
        tasks_finish = (await db.execute(finish_query)).scalar() or 0
        logger.info(f"【任务统计】项目 {project_id} - 已完成任务数(status=3): {tasks_finish}")

        # 未完成任务数（总任务数 - 已完成任务数）
        tasks_unfinish = tasks_total - tasks_finish
        logger.info(f"【任务统计】项目 {project_id} - 未完成任务数: {tasks_unfinish}")

        # 任务完成百分比（已完成 / 总任务数 * 100）
        if tasks_total > 0:
            percentage = int((tasks_finish / tasks_total) * 100)
            tasks_pensent = f"{percentage}％"
        else:
            tasks_pensent = "0％"
        
        logger.info(f"【任务统计】项目 {project_id} - 完成率: {tasks_pensent}")
        logger.info(f"【任务统计】项目 {project_id} 最终统计结果 - 总数:{tasks_total}, 进行中:{tasks_ongoing}, 已完成:{tasks_finish}, 未完成:{tasks_unfinish}, 完成率:{tasks_pensent}")

        return {
            'tasks_total': tasks_total,
            'tasks_ongoing': tasks_ongoing,
            'tasks_finish': tasks_finish,
            'tasks_unfinish': tasks_unfinish,
            'tasks_pensent': tasks_pensent
        }

    @classmethod
    async def _get_current_step_info(cls, db: AsyncSession, project_id: int) -> dict[str, Any]:
        """
        获取当前阶段信息（查询 is_current=1 且 delete_time=0 的记录）

        :param db: orm 对象
        :param project_id: 项目 ID
        :return: 当前阶段信息
        """
        # 查询当前阶段（is_current=1 且 delete_time=0）
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
