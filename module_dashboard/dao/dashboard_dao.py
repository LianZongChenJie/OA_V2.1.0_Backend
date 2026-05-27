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
        today_start = datetime(now.year, now.month, now.day, 0, 0, 0)
        now_timestamp = int(today_start.timestamp())
        future_time = now + timedelta(hours=hours)
        future_timestamp = int(future_time.timestamp())

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
        获取快到期的销售合同数量（与销售合同列表权限一致）

        :param query_db: 数据库会话
        :param current_user_id: 当前用户ID
        :param department_ids: 部门ID列表
        :param days: 天数，默认30天
        :return: 数量
        """
        now = datetime.now()
        today_start = datetime(now.year, now.month, now.day, 0, 0, 0)
        now_timestamp = int(today_start.timestamp())
        future_timestamp = int((datetime.now() + timedelta(days=days)).timestamp())

        # 与销售合同列表保持一致的查询逻辑
        # 基础条件：未删除、审核通过、未归档、未中止、未作废
        query = (
            select(func.count(OaContract.id))
            .where(OaContract.delete_time == 0)
            .where(OaContract.check_status == 2)
            .where(OaContract.archive_time == 0)
            .where(OaContract.stop_time == 0)
            .where(OaContract.void_time == 0)
            .where(OaContract.end_time.between(now_timestamp, future_timestamp))
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
        获取快到期的采购合同数量（与采购合同列表权限一致）

        :param query_db: 数据库会话
        :param current_user_id: 当前用户ID
        :param department_ids: 部门ID列表
        :param days: 天数，默认30天
        :return: 数量
        """
        now = datetime.now()
        today_start = datetime(now.year, now.month, now.day, 0, 0, 0)
        now_timestamp = int(today_start.timestamp())
        future_timestamp = int((datetime.now() + timedelta(days=days)).timestamp())

        # 与采购合同列表保持一致的查询逻辑
        # 基础条件：未删除、审核通过、未归档、未中止、未作废
        query = (
            select(func.count(OaPurchase.id))
            .where(OaPurchase.delete_time == 0)
            .where(OaPurchase.check_status == 2)
            .where(OaPurchase.archive_time == 0)
            .where(OaPurchase.stop_time == 0)
            .where(OaPurchase.void_time == 0)
            .where(OaPurchase.end_time.between(now_timestamp, future_timestamp))
        )

        result = await query_db.execute(query)
        return result.scalar() or 0

    @classmethod
    async def get_expiring_project_count(
        cls,
        query_db: AsyncSession,
        current_user_id: int,
        days: int = 3,
        is_admin: bool = False,
        auth_dids: str = '',
        son_dids: str = ''
    ) -> int:
        """
        获取快到期的项目数量（与项目列表权限一致）

        :param query_db: 数据库会话
        :param current_user_id: 当前用户ID
        :param days: 天数，默认3天
        :param is_admin: 是否为超级管理员
        :param auth_dids: 可见部门数据
        :param son_dids: 可见子部门数据
        :return: 数量
        """
        from sqlalchemy import text
        
        now = datetime.now()
        today_start = datetime(now.year, now.month, now.day, 0, 0, 0)
        now_timestamp = int(today_start.timestamp())
        future_timestamp = int((datetime.now() + timedelta(days=days)).timestamp())

        params = {
            'now_timestamp': now_timestamp,
            'future_timestamp': future_timestamp,
            'user_id': current_user_id
        }
        
        # 基础条件
        conditions = ["p.delete_time = 0", "p.end_time BETWEEN :now_timestamp AND :future_timestamp"]
        
        # 数据权限过滤（与项目列表完全一致）
        if not is_admin:
            permission_conditions = [
                "p.admin_id = :user_id",
                "p.director_uid = :user_id",
            ]
            
            # 项目成员权限（通过 oa_project_user 表）
            permission_conditions.append("EXISTS (SELECT 1 FROM oa_project_user pu WHERE pu.project_id = p.id AND pu.uid = :user_id AND pu.delete_time = 0)")
            
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
        
        # 执行查询
        sql = text(f"""
            SELECT COUNT(*) as count
            FROM oa_project p
            WHERE {where_clause}
        """)
        
        result = await query_db.execute(sql, params)
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
        now = datetime.now()
        today_start = datetime(now.year, now.month, now.day, 0, 0, 0)
        now_timestamp = int(today_start.timestamp())
        future_timestamp = int((datetime.now() + timedelta(days=days)).timestamp())

        # 构建任务查询条件
        task_conditions = [
            OaProjectTask.director_uid == current_user_id,
            OaProjectTask.admin_id == current_user_id,
        ]

        query = (
            select(func.count(OaProjectTask.id))
            .where(OaProjectTask.delete_time == 0)
            .where(OaProjectTask.end_time.between(now_timestamp, future_timestamp))
            .where(or_(*task_conditions))
        )

        result = await query_db.execute(query)
        return result.scalar() or 0
