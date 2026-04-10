from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.vo.user_vo import ContactsBookPageQueryModel
from utils.page_util import PageUtil

try:
    from module_admin.entity.do.oa_admin_do import OaAdmin
except ImportError:
    OaAdmin = None

try:
    from module_admin.entity.do.oa_department_do import OaDepartment
except ImportError:
    OaDepartment = None

try:
    from module_admin.entity.do.department_admin_do import OaDepartmentAdmin
except ImportError:
    OaDepartmentAdmin = None

try:
    from module_admin.entity.do.position_do import OaPosition
except ImportError:
    OaPosition = None


class ContactsBookDao:
    """
    通讯录数据访问层
    """

    @classmethod
    async def get_contacts_book_list(
        cls, db: AsyncSession, query_object: ContactsBookPageQueryModel, is_page: bool = True
    ) -> dict[str, Any]:
        """
        获取通讯录员工列表

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 通讯录员工列表
        """
        if not OaAdmin:
            return {'rows': [], 'total': 0}

        # 构建查询
        query = (
            select(
                OaAdmin,
                OaDepartment.title.label('department'),
            )
            .outerjoin(OaDepartment, OaAdmin.did == OaDepartment.id)
            .where(
                OaAdmin.status == 1,
                OaAdmin.id > 1,
            )
        )

        # 添加职位信息
        if OaPosition:
            query = query.add_columns(OaPosition.title.label('position'))
            query = query.outerjoin(OaPosition, OaAdmin.position_id == OaPosition.id)
        else:
            query = query.add_columns(None)

        # 关键词搜索
        if query_object.keywords:
            keyword = f'%{query_object.keywords}%'
            query = query.where(
                OaAdmin.id.like(keyword)
                | OaAdmin.username.like(keyword)
                | OaAdmin.name.like(keyword)
                | OaAdmin.nickname.like(keyword)
                | str(OaAdmin.mobile).like(keyword)
                | OaAdmin.desc.like(keyword)
            )

        # 部门筛选
        if query_object.did:
            # 查询该部门的主要员工
            main_dept_condition = OaAdmin.did == query_object.did

            # 查询该部门的次要员工
            if OaDepartmentAdmin:
                sub_admin_ids = (
                    select(OaDepartmentAdmin.admin_id)
                    .where(OaDepartmentAdmin.department_id == query_object.did)
                ).scalar_subquery()

                query = query.where(
                    main_dept_condition | OaAdmin.id.in_(sub_admin_ids)
                )
            else:
                query = query.where(main_dept_condition)

        # 排序
        query = query.order_by(OaAdmin.id.desc())

        # 执行查询
        result = await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, is_page)

        return result

    @classmethod
    async def get_department_admins(cls, db: AsyncSession, department_id: int) -> list[int]:
        """
        获取部门的次要员工ID列表

        :param db: orm 对象
        :param department_id: 部门ID
        :return: 员工ID列表
        """
        if not OaDepartmentAdmin:
            return []

        result = (
            await db.execute(
                select(OaDepartmentAdmin.admin_id)
                .where(OaDepartmentAdmin.department_id == department_id)
            )
        ).scalars().all()

        return list(result)
