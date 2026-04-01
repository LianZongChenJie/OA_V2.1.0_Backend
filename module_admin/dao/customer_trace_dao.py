# 3. 创建 DAO 文件：module_admin/dao/customer_trace_dao.py
from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.customer_trace_do import CustomerTrace
from module_admin.entity.vo.customer_trace_vo import CustomerTraceModel, CustomerTracePageQueryModel
from utils.page_util import PageUtil


class CustomerTraceDao:
    """
    客户跟进记录管理模块数据库操作层
    """

    @classmethod
    async def get_customer_trace_detail_by_id(cls, db: AsyncSession, trace_id: int) -> CustomerTrace | None:
        """
        根据跟进记录 ID 获取客户跟进记录详细信息

        :param db: orm 对象
        :param trace_id: 跟进记录 ID
        :return: 客户跟进记录详细信息对象
        """
        query = select(CustomerTrace).where(CustomerTrace.id == trace_id, CustomerTrace.delete_time == 0)
        trace_info = (await db.execute(query)).scalars().first()

        return trace_info

    @classmethod
    async def get_customer_trace_detail_by_info(cls, db: AsyncSession, trace: CustomerTraceModel) -> CustomerTrace | None:
        """
        根据客户跟进记录参数获取信息

        :param db: orm 对象
        :param trace: 客户跟进记录参数对象
        :return: 客户跟进记录信息对象
        """
        query_conditions = []
        if trace.id is not None:
            query_conditions.append(CustomerTrace.id == trace.id)
        if trace.cid is not None:
            query_conditions.append(CustomerTrace.cid == trace.cid)

        if query_conditions:
            trace_info = (
                (await db.execute(select(CustomerTrace).where(and_(*query_conditions))))
                .scalars()
                .first()
            )
        else:
            trace_info = None

        return trace_info

    @classmethod
    async def get_customer_trace_list(
            cls, db: AsyncSession, query_object: CustomerTracePageQueryModel, user_id: int,
            auth_dids: str = '', son_dids: str = '', is_admin: bool = False, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        根据查询参数获取客户跟进记录列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param user_id: 当前用户 ID
        :param auth_dids: 可见部门数据
        :param son_dids: 可见子部门数据
        :param is_admin: 是否为管理员
        :param is_page: 是否开启分页
        :return: 客户跟进记录列表信息对象
        """
        # 主表别名 a
        conditions = [CustomerTrace.delete_time == 0]

        # 关键词搜索：a.content|c.name|cc.title
        if query_object.keywords:
            conditions.append(
                or_(
                    CustomerTrace.content.like(f'%{query_object.keywords}%'),
                )
            )

        # 跟进时间范围筛选
        if query_object.follow_time_start is not None:
            conditions.append(CustomerTrace.follow_time >= query_object.follow_time_start)
        if query_object.follow_time_end is not None:
            conditions.append(CustomerTrace.follow_time <= query_object.follow_time_end)

        # 创建人筛选
        if query_object.admin_id_filter is not None:
            conditions.append(CustomerTrace.admin_id == query_object.admin_id_filter)

        # 构建权限相关的 OR 条件
        # 权限逻辑：
        # 1. belong_uid = 当前用户 ID (自己负责的客户)
        # 2. FIND_IN_SET(user_id, share_ids) (共享给自己的客户)
        # 3. belong_did IN (用户可见部门) (部门负责人可见本部门客户)

        map_conditions = []
        map_or_conditions = []

        # 自己负责的客户
        map_or_conditions.append(CustomerTrace.admin_id == user_id)

        # 如果不是管理员，需要根据数据权限过滤
        if not is_admin:
            # 处理部门权限
            if auth_dids or son_dids:
                dept_ids = set()
                if auth_dids:
                    dept_ids.update([int(d.strip()) for d in auth_dids.split(',') if d.strip()])
                if son_dids:
                    dept_ids.update([int(d.strip()) for d in son_dids.split(',') if d.strip()])

                if dept_ids:
                    map_or_conditions.append(CustomerTrace.admin_id.in_(dept_ids))

        if map_or_conditions:
            map_conditions.append(or_(*map_or_conditions))

        # 合并所有条件
        all_conditions = conditions + map_conditions

        query = (
            select(CustomerTrace)
            .where(*all_conditions)
            .order_by(CustomerTrace.create_time.desc())
            .distinct()
        )

        trace_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return trace_list

    @classmethod
    async def add_customer_trace_dao(cls, db: AsyncSession, trace: CustomerTraceModel) -> CustomerTrace:
        """
        新增客户跟进记录数据库操作

        :param db: orm 对象
        :param trace: 客户跟进记录对象
        :return:
        """
        db_trace = CustomerTrace(**trace.model_dump())
        db.add(db_trace)
        await db.flush()

        return db_trace

    @classmethod
    async def edit_customer_trace_dao(cls, db: AsyncSession, trace: dict) -> None:
        """
        编辑客户跟进记录数据库操作

        :param db: orm 对象
        :param trace: 需要更新的客户跟进记录字典
        :return:
        """
        await db.execute(update(CustomerTrace), [trace])

    @classmethod
    async def delete_customer_trace_dao(cls, db: AsyncSession, trace: CustomerTraceModel) -> None:
        """
        删除客户跟进记录数据库操作（逻辑删除）

        :param db: orm 对象
        :param trace: 客户跟进记录对象
        :return:
        """
        update_time = trace.update_time if trace.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(CustomerTrace)
            .where(CustomerTrace.id == trace.id)
            .values(delete_time=update_time, update_time=update_time)
        )

