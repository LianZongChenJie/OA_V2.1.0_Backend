from sqlalchemy import BigInteger, CHAR, DECIMAL, Column, Index, Integer, String, UniqueConstraint

from config.database import Base


class OaHrCost(Base):
    """人力总成本明细 ORM 模型"""

    __tablename__ = 'oa_hr_cost'
    __table_args__ = (
        UniqueConstraint('stat_month', 'id_card', 'delete_time', name='uk_month_id_card'),
        Index('idx_stat_month', 'stat_month'),
        Index('idx_org_id', 'org_id'),
        Index('idx_city_id', 'city_id'),
        Index('idx_employee_name', 'employee_name'),
        Index('idx_delete_time', 'delete_time'),
        {'comment': '人力总成本明细表'},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    stat_month = Column(CHAR(7), nullable=False, server_default="''", comment='月份 YYYY-MM')
    employee_status = Column(String(20), nullable=False, server_default="''", comment='员工状态')
    city_id = Column(Integer, nullable=False, server_default='0', comment='城市ID，关联 oa_area.id')
    city_name = Column(String(100), nullable=False, server_default="''", comment='城市名称快照')
    org_id = Column(Integer, nullable=False, server_default='0', comment='组织架构ID，关联 sys_dept.dept_id')
    org_name = Column(String(100), nullable=False, server_default="''", comment='组织架构名称快照')
    employee_name = Column(String(100), nullable=False, server_default="''", comment='姓名')
    id_card = Column(String(32), nullable=False, comment='身份证号码')
    entry_date = Column(BigInteger, nullable=False, server_default='0', comment='入职日期（秒）')
    entry_record_date = Column(String(20), nullable=False, server_default='', comment='入职记录（新入职/重新入职）')
    project_name = Column(String(255), nullable=False, server_default="''", comment='目前所在项目')
    contract_salary = Column(DECIMAL(18, 6), nullable=False, server_default='0', comment='合同工资')
    salary_ratio = Column(DECIMAL(5, 2), nullable=False, server_default='1.00', comment='算薪比例')
    base_salary = Column(DECIMAL(18, 6), nullable=False, server_default='0', comment='基本工资')
    performance_salary = Column(DECIMAL(18, 6), nullable=False, server_default='0', comment='绩效工资')
    post_salary = Column(DECIMAL(18, 6), nullable=False, server_default='0', comment='岗位工资')
    attendance_days = Column(DECIMAL(10, 2), nullable=False, server_default='0', comment='考勤（天）')
    customer_fee_tax_included = Column(DECIMAL(18, 6), nullable=False, server_default='0', comment='客户费用单（含税）')
    computer_subsidy = Column(DECIMAL(18, 6), nullable=False, server_default='0', comment='电脑补助（加）')
    meal_subsidy = Column(DECIMAL(18, 6), nullable=False, server_default='0', comment='工作日餐补（加）')
    bonus = Column(DECIMAL(18, 6), nullable=False, server_default='0', comment='奖金（加）')
    subsidy = Column(DECIMAL(18, 6), nullable=False, server_default='0', comment='补助（加）')
    deduction = Column(DECIMAL(18, 6), nullable=False, server_default='0', comment='扣款（减）')
    other_deduction = Column(DECIMAL(18, 6), nullable=False, server_default='0', comment='其他扣款（减）')
    gross_salary = Column(DECIMAL(18, 6), nullable=False, server_default='0', comment='未扣五险一金薪资总额（计算）')
    pension_personal = Column(DECIMAL(18, 6), nullable=False, server_default='0', comment='养老个人部分')
    medical_personal = Column(DECIMAL(18, 6), nullable=False, server_default='0', comment='医疗个人部分')
    unemployment_personal = Column(DECIMAL(18, 6), nullable=False, server_default='0', comment='失业个人部分')
    social_personal_total = Column(DECIMAL(18, 6), nullable=False, server_default='0', comment='社保个人合计（计算）')
    housing_fund_personal = Column(DECIMAL(18, 6), nullable=False, server_default='0', comment='公积金个人部分')
    taxable_salary = Column(DECIMAL(18, 6), nullable=False, server_default='0', comment='扣除五险一金税前工资（计算）')
    income_tax = Column(DECIMAL(18, 6), nullable=False, server_default='0', comment='个税代扣代缴')
    bank_pay_amount = Column(DECIMAL(18, 6), nullable=False, server_default='0', comment='银行实际支付金额（计算）')
    pension_company = Column(DECIMAL(18, 6), nullable=False, server_default='0', comment='养老单位部分')
    unemployment_company = Column(DECIMAL(18, 6), nullable=False, server_default='0', comment='失业单位部分')
    injury_company = Column(DECIMAL(18, 6), nullable=False, server_default='0', comment='工伤单位部分')
    medical_maternity_company = Column(DECIMAL(18, 6), nullable=False, server_default='0', comment='（医疗+生育）单位部分')
    social_company_total = Column(DECIMAL(18, 6), nullable=False, server_default='0', comment='社保单位合计（计算）')
    housing_fund_company = Column(DECIMAL(18, 6), nullable=False, server_default='0', comment='公积金单位部分')
    social_total = Column(DECIMAL(18, 6), nullable=False, server_default='0', comment='社保总合计（计算）')
    housing_fund_total = Column(DECIMAL(18, 6), nullable=False, server_default='0', comment='公积金总合计（计算）')
    company_total_cost = Column(DECIMAL(18, 6), nullable=False, server_default='0', comment='企业总成本（计算）')
    social_base = Column(DECIMAL(18, 6), nullable=False, server_default='0', comment='社保基数')
    housing_fund_base = Column(DECIMAL(18, 6), nullable=False, server_default='0', comment='公积金基数')
    remark = Column(String(1000), nullable=False, server_default="''", comment='备注')
    tax_excluded_revenue = Column(DECIMAL(18, 6), nullable=False, server_default='0', comment='不含税收入（计算）')
    gross_profit = Column(DECIMAL(18, 6), nullable=False, server_default='0', comment='毛利（计算）')
    tax_declaration_amount = Column(DECIMAL(18, 6), nullable=False, server_default='0', comment='个税申报金额（计算）')
    admin_id = Column(Integer, nullable=False, server_default='0', comment='创建人')
    create_time = Column(BigInteger, nullable=False, server_default='0', comment='创建时间（秒）')
    update_time = Column(BigInteger, nullable=False, server_default='0', comment='更新时间（秒）')
    delete_time = Column(BigInteger, nullable=False, server_default='0', comment='删除时间（秒）')
    tenant_id = Column(BigInteger, nullable=False, server_default='1', comment='租户ID')
