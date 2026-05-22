# module_dashboard/service/dashboard_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from module_dashboard.dao.dashboard_dao import DashboardDao
from module_dashboard.entity.vo.dashboard_vo import (
    UrgentItemModel,
)


class DashboardService:
    """首页仪表盘服务层"""

    @classmethod
    async def get_urgent_items_service(
        cls,
        query_db: AsyncSession,
        current_user_id: int,
        department_ids: list[int] | None = None,
        contract_delay_days: int = 30,
        project_delay_days: int = 3
    ) -> list[UrgentItemModel]:
        """
        获取首页紧急事项统计

        :param query_db: 数据库会话
        :param current_user_id: 当前用户ID
        :param department_ids: 部门ID列表
        :param contract_delay_days: 合同到期提醒天数，默认30天
        :param project_delay_days: 项目/任务到期提醒天数，默认3天
        :return: 紧急事项统计结果列表
        """

        # 到期提醒统计
        result = []

        # 1. 快到期的开标时间（72小时内）
        expiring_tender_bid_count = await DashboardDao.get_expiring_tender_bid_opening_count(query_db, 72)
        result.append(UrgentItemModel(
            name='快到期的开标时间',
            num=expiring_tender_bid_count,
            target_name='Bidinfo',
            target_path='/bidding/bidInfo'
        ))

        # 2. 快到期的保证金缴纳（72小时内）
        expiring_tender_deposit_count = await DashboardDao.get_expiring_tender_deposit_count(query_db, 72)
        result.append(UrgentItemModel(
            name='快到期的保证金缴纳',
            num=expiring_tender_deposit_count,
            target_name='Bidinfo',
            target_path='/bidding/bidInfo'
        ))

        # 3. 快到期的销售合同
        expiring_contract_count = await DashboardDao.get_expiring_contract_count(
            query_db,
            current_user_id,
            department_ids,
            contract_delay_days
        )
        result.append(UrgentItemModel(
            name='快到期的销售合同',
            num=expiring_contract_count,
            target_name='Salescontract',
            target_path='/contract/salesContract'
        ))

        # 4. 快到期的采购合同
        expiring_purchase_count = await DashboardDao.get_expiring_purchase_count(
            query_db,
            current_user_id,
            department_ids,
            contract_delay_days
        )
        result.append(UrgentItemModel(
            name='快到期的采购合同',
            num=expiring_purchase_count,
            target_name='Procurementcontract',
            target_path='/contract/procurementContract'
        ))

        # 5. 快到期的项目
        expiring_project_count = await DashboardDao.get_expiring_project_count(
            query_db,
            current_user_id,
            project_delay_days
        )
        result.append(UrgentItemModel(
            name='快到期的项目',
            num=expiring_project_count,
            target_name='Itemlist',
            target_path='/project/itemList'
        ))

        # 6. 快到期的任务
        expiring_task_count = await DashboardDao.get_expiring_task_count(
            query_db,
            current_user_id,
            project_delay_days
        )
        result.append(UrgentItemModel(
            name='快到期的任务',
            num=expiring_task_count,
            target_name='Task',
            target_path='/project/task'
        ))

        return result