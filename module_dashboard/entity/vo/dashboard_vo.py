# module_dashboard/entity/vo/dashboard_vo.py
from pydantic import BaseModel, Field


class UrgentItemModel(BaseModel):
    """紧急事项项模型"""
    name: str | None = Field(default=None, description='事项名称')
    num: int = Field(default=0, description='数量')
    id: int | None = Field(default=None, description='菜单ID')
    url: str | None = Field(default=None, description='跳转链接')


class DashboardUrgentResponseModel(BaseModel):
    """首页紧急事项响应模型"""
    total: list[UrgentItemModel] = Field(default=[], description='统计数据')
    handle: list[UrgentItemModel] = Field(default=[], description='待办事项')
    todue: list[UrgentItemModel] = Field(default=[], description='到期提醒')
