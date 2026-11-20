from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class HrCostModel(BaseModel):
    """人力总成本 VO"""

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    id: int | None = Field(default=None, description='主键ID')
    stat_month: str | None = Field(default=None, description='月份 YYYY-MM')
    employee_status: str | None = Field(default=None, description='员工状态')
    city_id: int | None = Field(default=None, description='城市ID')
    city_name: str | None = Field(default=None, description='城市名称')
    org_id: int | None = Field(default=None, description='组织架构ID')
    org_name: str | None = Field(default=None, description='组织架构名称')
    employee_name: str | None = Field(default=None, description='姓名')
    id_card: str | None = Field(default=None, description='身份证号码')
    entry_date: str | int | None = Field(default=None, description='入职日期（日期字符串或秒级时间戳）')
    entry_record_date: str | None = Field(default=None, description='入职记录（新入职/重新入职）')
    project_name: str | None = Field(default=None, description='目前所在项目')
    contract_salary: Decimal | None = Field(default=None, description='合同工资')
    salary_ratio: Decimal | None = Field(default=None, description='算薪比例')
    base_salary: Decimal | None = Field(default=None, description='基本工资')
    performance_salary: Decimal | None = Field(default=None, description='绩效工资')
    post_salary: Decimal | None = Field(default=None, description='岗位工资')
    attendance_days: Decimal | None = Field(default=None, description='考勤（天）')
    customer_fee_tax_included: Decimal | None = Field(default=None, description='客户费用单（含税）')
    computer_subsidy: Decimal | None = Field(default=None, description='电脑补助（加）')
    meal_subsidy: Decimal | None = Field(default=None, description='工作日餐补（加）')
    bonus: Decimal | None = Field(default=None, description='奖金（加）')
    subsidy: Decimal | None = Field(default=None, description='补助（加）')
    deduction: Decimal | None = Field(default=None, description='扣款（减）')
    other_deduction: Decimal | None = Field(default=None, description='其他扣款（减）')
    gross_salary: Decimal | None = Field(default=None, description='未扣五险一金薪资总额')
    pension_personal: Decimal | None = Field(default=None, description='养老个人部分')
    medical_personal: Decimal | None = Field(default=None, description='医疗个人部分')
    unemployment_personal: Decimal | None = Field(default=None, description='失业个人部分')
    social_personal_total: Decimal | None = Field(default=None, description='社保个人合计')
    housing_fund_personal: Decimal | None = Field(default=None, description='公积金个人部分')
    taxable_salary: Decimal | None = Field(default=None, description='扣除五险一金税前工资')
    income_tax: Decimal | None = Field(default=None, description='个税代扣代缴')
    bank_pay_amount: Decimal | None = Field(default=None, description='银行实际支付金额')
    pension_company: Decimal | None = Field(default=None, description='养老单位部分')
    unemployment_company: Decimal | None = Field(default=None, description='失业单位部分')
    injury_company: Decimal | None = Field(default=None, description='工伤单位部分')
    medical_maternity_company: Decimal | None = Field(default=None, description='（医疗+生育）单位部分')
    social_company_total: Decimal | None = Field(default=None, description='社保单位合计')
    housing_fund_company: Decimal | None = Field(default=None, description='公积金单位部分')
    social_total: Decimal | None = Field(default=None, description='社保总合计')
    housing_fund_total: Decimal | None = Field(default=None, description='公积金总合计')
    company_total_cost: Decimal | None = Field(default=None, description='企业总成本')
    social_base: Decimal | None = Field(default=None, description='社保基数')
    housing_fund_base: Decimal | None = Field(default=None, description='公积金基数')
    remark: str | None = Field(default=None, description='备注')
    tax_excluded_revenue: Decimal | None = Field(default=None, description='不含税收入')
    gross_profit: Decimal | None = Field(default=None, description='毛利')
    tax_declaration_amount: Decimal | None = Field(default=None, description='个税申报金额')
    admin_id: int | None = Field(default=None, description='创建人')
    create_time: int | None = Field(default=None, description='创建时间')
    update_time: int | None = Field(default=None, description='更新时间')
    delete_time: int | None = Field(default=None, description='删除时间')

    seq: int | None = Field(default=None, description='分页序号')
    create_time_str: str | None = Field(default=None, description='创建时间字符串')
    update_time_str: str | None = Field(default=None, description='更新时间字符串')


class HrCostPageQueryModel(HrCostModel):
    """人力总成本分页查询模型"""

    stat_month: str | None = Field(default=None, description='月份筛选')
    org_id: str | int | None = Field(default=None, description='组织架构筛选')
    city_id: str | int | None = Field(default=None, description='城市筛选')
    include_children: str | int | None = Field(default=1, description='是否包含子部门')
    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
    keywords: str | None = Field(default=None, description='姓名/身份证/项目模糊搜索')


class AddHrCostModel(HrCostModel):
    """新增人力总成本模型"""


class EditHrCostModel(AddHrCostModel):
    """编辑人力总成本模型"""


class HrCostImportResponseModel(BaseModel):
    """导入结果模型"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    is_success: bool = True
    message: str = ''
    success_count: int = 0
    fail_count: int = 0
    fail_data: list[dict] | None = None
