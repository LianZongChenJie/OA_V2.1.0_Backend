from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ProjectMonthlyModel(BaseModel):
    """月度项目台账 VO"""

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    id: int | None = Field(default=None, description='主键ID')
    stat_month: str | None = Field(default=None, description='年度/统计月份 YYYY-MM')
    customer_name: str | None = Field(default=None, description='客户名称')
    project_name: str | None = Field(default=None, description='项目名称')
    contract_signed: Literal[0, 1] | None = Field(default=None, description='合同是否签订：0否 1是')
    planned_cost: Decimal | None = Field(default=None, description='预计投入成本')
    actual_cost: Decimal | None = Field(default=None, description='实际投入成本')
    planned_profit: Decimal | None = Field(default=None, description='预计项目利润')
    actual_profit: Decimal | None = Field(default=None, description='实际项目利润')
    collection_agreement: str | None = Field(default=None, description='合同收款约定')
    invoiced_amount: Decimal | None = Field(default=None, description='实际开票金额')
    received_amount: Decimal | None = Field(default=None, description='实际收款金额')
    project_closed: Literal[0, 1] | None = Field(default=None, description='是否结项：0否 1是')
    project_id: int | None = Field(default=None, description='关联旧项目ID')
    remark: str | None = Field(default=None, description='备注')
    admin_id: int | None = Field(default=None, description='创建人')
    create_time: int | None = Field(default=None, description='创建时间')
    update_time: int | None = Field(default=None, description='更新时间')
    delete_time: int | None = Field(default=None, description='删除时间')

    # 列表返回扩展字段
    seq: int | None = Field(default=None, description='分页序号')
    create_time_str: str | None = Field(default=None, description='创建时间字符串 YYYY-MM-DD HH:mm:ss')
    update_time_str: str | None = Field(default=None, description='更新时间字符串 YYYY-MM-DD HH:mm:ss')


class ProjectMonthlyPageQueryModel(ProjectMonthlyModel):
    """月度项目台账分页查询模型"""

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
    keywords: str | None = Field(default=None, description='客户名称/项目名称模糊搜索')


class AddProjectMonthlyModel(ProjectMonthlyModel):
    """新增月度项目台账模型"""



class EditProjectMonthlyModel(AddProjectMonthlyModel):
    """编辑月度项目台账模型"""



class DeleteProjectMonthlyModel(BaseModel):
    """删除月度项目台账模型"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: int = Field(description='需要删除的记录ID')


class ProjectMonthlyImportResponseModel(BaseModel):
    """导入结果模型"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    is_success: bool = True
    message: str = ''
    success_count: int = 0
    fail_count: int = 0
    fail_data: list[dict] | None = None
