from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_project.entity.do.project_do import OaProject
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

        return project_list

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
