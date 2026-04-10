# module_dashboard/controller/dashboard_controller.py
from fastapi import Request
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import PreAuthDependency, CurrentUserDependency
from common.router import APIRouterPro
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_dashboard.service.dashboard_service import DashboardService
from utils.response_util import ResponseUtil

dashboard_controller = APIRouterPro(
    prefix='/dashboard',
    order_num=1,
    tags=['首页-紧急事项'],
    dependencies=[PreAuthDependency()]
)


@dashboard_controller.get(
    "/urgent",
    summary='获取首页紧急事项统计',
    description='用于获取首页紧急事项统计，包括快到期的开标时间、保证金缴纳、销售合同、采购合同、项目、任务等',
    response_model=None,
)
async def get_urgent_items(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
):
    """
    获取首页紧急事项统计

    返回数据包含：
    - todue: 到期提醒列表
      - 快到期的开标时间（72小时内）
      - 快到期的保证金缴纳（72小时内）
      - 快到期的销售合同（30天内）
      - 快到期的采购合同（30天内）
      - 快到期的项目（3天内）
      - 快到期的任务（3天内）
    """
    # TODO: 根据实际需求获取用户的部门ID列表
    # 这里暂时传None，后续可以根据实际业务逻辑获取
    department_ids = None

    # TODO: 从配置中读取到期提醒天数
    contract_delay_days = 30  # 合同到期提醒天数
    project_delay_days = 3    # 项目/任务到期提醒天数

    result = await DashboardService.get_urgent_items_service(
        query_db,
        current_user.user.user_id,
        department_ids,
        contract_delay_days,
        project_delay_days
    )

    return ResponseUtil.success(data=result.model_dump())
