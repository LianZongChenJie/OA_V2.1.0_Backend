from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from module_admin.entity.do.tender_do import OaProjectTender
from module_contract.entity.do.contract_do import OaContract
from module_contract.entity.do.purchase_do import OaPurchase
from module_project.entity.do.project_do import OaProject
from module_project.entity.do.project_task_do import OaProjectTask
from module_project.entity.do.project_user_do import OaProjectUser
from datetime import datetime, timedelta


class DashboardDao:
    """首页仪表盘数据访问层"""

    @classmethod
    async def get_expiring_tender_bid_opening_count(
        cls,
        query_db: AsyncSession,
        hours: int = 72
    ) -> int:
        """
        获取快到期的开标时间数量（72小时内）

        :param query_db: 数据库会话
        :param hours: 小时数，默认72小时
        :return: 数量
        """
        now = datetime.now()
        future_time = now + timedelta(hours=hours)

        query = (
            select(func.count(OaProjectTender.id))
            .where(OaProjectTender.delete_time == 0)
            .where(OaProjectTender.bid_opening_date >= now.date())
            .where(OaProjectTender.bid_opening_date <= future_time.date())
        )

        result = await query_db.execute(query)
        return result.scalar() or 0

    @classmethod
    async def get_expiring_tender_deposit_count(
        cls,
        query_db: AsyncSession,
        hours: int = 72
    ) -> int:
        """
        获取快到期的保证金缴纳数量（72小时内）
        注：由于表中没有 deposit_paid_time 字段，这里统计的是需要缴纳但未缴纳的记录

        :param query_db: 数据库会话
        :param hours: 小时数，默认72小时
        :return: 数量
        """
        # 当前实现：统计需要缴纳保证金但未缴纳的记录
        query = (
            select(func.count(OaProjectTender.id))
            .where(OaProjectTender.delete_time == 0)
            .where(OaProjectTender.is_deposit_paid == '否')
            .where(OaProjectTender.tender_deposit > 0)
        )

        result = await query_db.execute(query)
        return result.scalar() or 0

    @classmethod
    async def get_expiring_contract_count(
        cls,
        query_db: AsyncSession,
        current_user_id: int,
        department_ids: list[int] | None = None,
        days: int = 30
    ) -> int:
        """
        获取快到期的销售合同数量

        :param query_db: 数据库会话
        :param current_user_id: 当前用户ID
        :param department_ids: 部门ID列表
        :param days: 天数，默认30天
        :return: 数量
        """
        now_timestamp = int(datetime.now().timestamp())
        future_timestamp = int((datetime.now() + timedelta(days=days)).timestamp())

        # 构建权限条件
        permission_conditions = [
            OaContract.admin_id == current_user_id,
            OaContract.prepared_uid == current_user_id,
            OaContract.sign_uid == current_user_id,
            OaContract.keeper_uid == current_user_id,
        ]

        if department_ids:
            permission_conditions.append(OaContract.did.in_(department_ids))

        query = (
            select(func.count(OaContract.id))
            .where(OaContract.delete_time == 0)
            .where(OaContract.check_status == 2)
            .where(OaContract.end_time < future_timestamp)
            .where(or_(*permission_conditions))
        )

        result = await query_db.execute(query)
        return result.scalar() or 0

    @classmethod
    async def get_expiring_purchase_count(
        cls,
        query_db: AsyncSession,
        current_user_id: int,
        department_ids: list[int] | None = None,
        days: int = 30
    ) -> int:
        """
        获取快到期的采购合同数量

        :param query_db: 数据库会话
        :param current_user_id: 当前用户ID
        :param department_ids: 部门ID列表
        :param days: 天数，默认30天
        :return: 数量
        """
        now_timestamp = int(datetime.now().timestamp())
        future_timestamp = int((datetime.now() + timedelta(days=days)).timestamp())

        # 构建权限条件
        permission_conditions = [
            OaPurchase.admin_id == current_user_id,
            OaPurchase.prepared_uid == current_user_id,
            OaPurchase.sign_uid == current_user_id,
            OaPurchase.keeper_uid == current_user_id,
        ]

        if department_ids:
            permission_conditions.append(OaPurchase.did.in_(department_ids))

        query = (
            select(func.count(OaPurchase.id))
            .where(OaPurchase.delete_time == 0)
            .where(OaPurchase.check_status == 2)
            .where(OaPurchase.end_time < future_timestamp)
            .where(or_(*permission_conditions))
        )

        result = await query_db.execute(query)
        return result.scalar() or 0

    @classmethod
    async def get_expiring_project_count(
        cls,
        query_db: AsyncSession,
        current_user_id: int,
        days: int = 3
    ) -> int:
        """
        获取快到期的项目数量

        :param query_db: 数据库会话
        :param current_user_id: 当前用户ID
        :param days: 天数，默认3天
        :return: 数量
        """
        now_timestamp = int(datetime.now().timestamp())
        future_timestamp = int((datetime.now() + timedelta(days=days)).timestamp())

        # 获取用户参与的项目ID列表
        project_query = (
            select(OaProjectUser.project_id)
            .where(OaProjectUser.uid == current_user_id)
            .where(OaProjectUser.delete_time == 0)
        )
        project_result = await query_db.execute(project_query)
        project_ids = [row[0] for row in project_result.fetchall()]

        if not project_ids:
            return 0

        query = (
            select(func.count(OaProject.id))
            .where(OaProject.delete_time == 0)
            .where(OaProject.status < 3)
            .where(OaProject.end_time < future_timestamp)
            .where(OaProject.id.in_(project_ids))
        )

        result = await query_db.execute(query)
        return result.scalar() or 0

    @classmethod
    async def get_expiring_task_count(
        cls,
        query_db: AsyncSession,
        current_user_id: int,
        days: int = 3
    ) -> int:
        """
        获取快到期的任务数量

        :param query_db: 数据库会话
        :param current_user_id: 当前用户ID
        :param days: 天数，默认3天
        :return: 数量
        """
        now_timestamp = int(datetime.now().timestamp())
        future_timestamp = int((datetime.now() + timedelta(days=days)).timestamp())

        # 获取用户参与的项目ID列表
        project_query = (
            select(OaProjectUser.project_id)
            .where(OaProjectUser.uid == current_user_id)
            .where(OaProjectUser.delete_time == 0)
        )
        project_result = await query_db.execute(project_query)
        project_ids = [row[0] for row in project_result.fetchall()]

        # 构建任务查询条件
        task_conditions = [
            OaProjectTask.director_uid == current_user_id,
            OaProjectTask.admin_id == current_user_id,
        ]

        if project_ids:
            task_conditions.append(OaProjectTask.project_id.in_(project_ids))

        query = (
            select(func.count(OaProjectTask.id))
            .where(OaProjectTask.delete_time == 0)
            .where(OaProjectTask.status < 3)
            .where(OaProjectTask.end_time < future_timestamp)
            .where(or_(*task_conditions))
        )

        result = await query_db.execute(query)
        return result.scalar() or 0
