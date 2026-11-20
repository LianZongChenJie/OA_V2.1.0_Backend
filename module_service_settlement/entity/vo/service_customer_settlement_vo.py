from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ServiceCustomerSettlementModel(BaseModel):
    """服务客户结算 VO"""

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    id: int | None = Field(default=None, description='主键ID')
    stat_year: int | None = Field(default=None, description='年度，如 2026')
    stat_month: int | None = Field(default=None, description='月份，1-12')
    customer_name: str | None = Field(default=None, description='客户名称')
    employee_name: str | None = Field(default=None, description='姓名')
    position_name: str | None = Field(default=None, description='职位')
    level_name: str | None = Field(default=None, description='级别')
    unit_price: Decimal | None = Field(default=None, description='单价（元）')
    actual_attendance_days: Decimal | None = Field(default=None, description='实际出勤（天）')
    leave_days: Decimal | None = Field(default=None, description='请假（天）')
    overtime_days: Decimal | None = Field(default=None, description='加班（天）')
    comp_off_days: Decimal | None = Field(default=None, description='调休（天）')
    payable_amount: Decimal | None = Field(default=None, description='实际应结算费用（元）')
    settled_amount: Decimal | None = Field(default=None, description='实际结算费用（元）')
    is_settled: Literal[0, 1] | None = Field(default=None, description='是否结算：0否 1是')
    remark: str | None = Field(default=None, description='备注')
    admin_id: int | None = Field(default=None, description='创建人')
    create_time: int | None = Field(default=None, description='创建时间')
    update_time: int | None = Field(default=None, description='更新时间')
    delete_time: int | None = Field(default=None, description='删除时间')

    # 列表返回扩展字段
    seq: int | None = Field(default=None, description='分页序号')
    create_time_str: str | None = Field(default=None, description='创建时间字符串 YYYY-MM-DD HH:mm:ss')
    update_time_str: str | None = Field(default=None, description='更新时间字符串 YYYY-MM-DD HH:mm:ss')


class ServiceCustomerSettlementPageQueryModel(ServiceCustomerSettlementModel):
    """服务客户结算分页查询模型"""

    # 查询条件允许前端传空串（清除筛选），Service 层统一归一化
    stat_year: str | int | None = Field(default=None, description='年度筛选')
    stat_month: str | int | None = Field(default=None, description='月份筛选')
    is_settled: str | int | None = Field(default=None, description='是否结算筛选：0否 1是')
    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
    keywords: str | None = Field(default=None, description='客户名称/姓名模糊搜索')


class AddServiceCustomerSettlementModel(ServiceCustomerSettlementModel):
    """新增服务客户结算模型"""


class EditServiceCustomerSettlementModel(AddServiceCustomerSettlementModel):
    """编辑服务客户结算模型"""


class DeleteServiceCustomerSettlementModel(BaseModel):
    """删除服务客户结算模型"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: int = Field(description='需要删除的记录ID')


class ServiceCustomerSettlementImportResponseModel(BaseModel):
    """导入结果模型"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    is_success: bool = True
    message: str = ''
    success_count: int = 0
    fail_count: int = 0
    fail_data: list[dict] | None = None
